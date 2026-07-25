"""Shared parsing/IO for bug-rca scripts (spec §11).

Rules enforced here so every script inherits them:
- Field-first parsing of threadtime logcat (never plain-text grep). See parse_line().
- Source prefix on every emitted log line: `原始文件:原始行号|` (red line R11).
- Input must be RAW logs: reject lines that already carry a source prefix
  (red line, spec §11 rule 3) via looks_prefixed().

Python 3, standard library only.
"""
import os
import re

# threadtime: "MM-DD HH:MM:SS.mmm  PID  TID L TAG: message"
# No year, no timezone (spec §13 {{TS_FORMAT}}). Year injected externally.
_TT = re.compile(
    r"^(?P<mon>\d{2})-(?P<day>\d{2})\s+"
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})\.(?P<ms>\d{3})\s+"
    r"(?P<pid>\d+)\s+(?P<tid>\d+)\s+(?P<level>[VDIWEFS])\s+"
    r"(?P<tag>.*?):\s?(?P<msg>.*)$"
)

# A line already carrying our source prefix, e.g. "foo.log:1234|04-16 ..."
_PREFIXED = re.compile(r"^[^\s|]+:\d+\|")

LEVEL_ORDER = {"V": 0, "D": 1, "I": 2, "W": 3, "E": 4, "F": 5, "S": 6}

# cumulative days before each month (non-leap; good enough within one capture)
_DOY = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]


class LogLine:
    __slots__ = ("file", "lineno", "mon", "day", "h", "m", "s", "ms",
                 "pid", "tid", "level", "tag", "msg", "raw")

    def __init__(self, file, lineno, gd, raw):
        self.file = file
        self.lineno = lineno
        self.mon = int(gd["mon"]); self.day = int(gd["day"])
        self.h = int(gd["h"]); self.m = int(gd["m"])
        self.s = int(gd["s"]); self.ms = int(gd["ms"])
        self.pid = int(gd["pid"]); self.tid = int(gd["tid"])
        self.level = gd["level"]; self.tag = gd["tag"]; self.msg = gd["msg"]
        self.raw = raw

    def ts_key(self, year):
        """Sortable comparable key WITHIN one boot session only.
        (Cross-session comparison is invalid — red line R12.)"""
        return (year, self.mon, self.day, self.h, self.m, self.s, self.ms)

    def abs_ms(self):
        """Absolute-ish millisecond key across the whole capture (date-aware,
        year-agnostic). Used for clock-jump detection so a date change
        (e.g. 01-01 -> 04-16 boot RTC set) is caught, not just intra-day."""
        return (_DOY[self.mon - 1] + (self.day - 1)) * 86400000 + \
               ((self.h * 60 + self.m) * 60 + self.s) * 1000 + self.ms

    def source_prefix(self):
        return "%s:%d|" % (os.path.basename(self.file), self.lineno)

    def emit(self):
        """Line for slice output: source prefix + original raw (R11)."""
        return self.source_prefix() + self.raw


def looks_prefixed(text):
    return bool(_PREFIXED.match(text))


def parse_line(file, lineno, raw):
    """Return LogLine or None if the line is not a threadtime record."""
    line = raw.rstrip("\n")
    m = _TT.match(line)
    if not m:
        return None
    return LogLine(file, lineno, m.groupdict(), line)


def iter_log(path, reject_prefixed=True):
    """Yield (lineno, raw, LogLine|None) for a raw log file.

    Guards against being fed a derived slice (spec §11 rule 3): if the first
    non-empty line already carries a source prefix, raise ValueError.
    """
    with open(path, "r", errors="replace") as fh:
        for lineno, raw in enumerate(fh, 1):
            if reject_prefixed and lineno <= 5 and raw.strip() and looks_prefixed(raw):
                raise ValueError(
                    "%s looks like a derived slice (has source prefix); "
                    "scripts accept RAW logs only (spec §11 rule 3)" % path)
            yield lineno, raw, parse_line(path, lineno, raw)


# ---- events buffer enrichment (optional) ---------------------------------
# In threadtime `-b all`, event tags already appear symbolically in the TAG
# field (e.g. am_proc_start), so parsing does not depend on numeric mapping.
# The vendor event-log-tags file is available for enrichment/validation.
def is_event_tag(tag):
    """Heuristic: EventLog tags are snake_case with no spaces (am_proc_start,
    wm_on_paused_called, user_switch...). Used to route structured extraction."""
    return bool(re.match(r"^[a-z][a-z0-9_]*$", tag))


def parse_event_msg(msg):
    """EventLog message is a bracketed tuple like [10,5678,com.foo] or a
    scalar. Return a list of field strings (best-effort, never raises)."""
    t = msg.strip()
    if t.startswith("[") and t.endswith("]"):
        inner = t[1:-1]
        # split on commas not inside nested brackets (one level is enough here)
        out, depth, cur = [], 0, []
        for ch in inner:
            if ch in "[(":
                depth += 1; cur.append(ch)
            elif ch in ")]":
                depth -= 1; cur.append(ch)
            elif ch == "," and depth == 0:
                out.append("".join(cur).strip()); cur = []
            else:
                cur.append(ch)
        if cur:
            out.append("".join(cur).strip())
        return out
    return [t]


# ---- manifest IO ---------------------------------------------------------
def write_tsv(path, header, rows):
    with open(path, "w") as fh:
        fh.write("\t".join(header) + "\n")
        for r in rows:
            fh.write("\t".join(str(c) for c in r) + "\n")
    return len(rows)


def read_tsv(path):
    """Return (header, list-of-dict-rows). Missing file -> ([], [])."""
    if not os.path.exists(path):
        return [], []
    rows = []
    with open(path) as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            vals = line.rstrip("\n").split("\t")
            rows.append(dict(zip(header, vals)))
    return header, rows
