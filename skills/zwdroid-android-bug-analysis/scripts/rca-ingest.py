#!/usr/bin/env python3
"""rca-ingest — one-shot index of a logcat directory (spec §11, §8.3).

Produces, under the output manifest dir, the five TSV tables of spec §8.3:
  sessions.tsv, files.tsv, procs-<sid>.tsv, clock-<sid>.tsv, loss-<sid>.tsv

Key design points (why, not what):
- Files are ordered by their first PARSED timestamp, never by filename — the
  `@time` in the name need not equal the first log time (observed in samples).
- Boot sessions are cut at file:line granularity; a single file may span a
  boot boundary (spec §8.3).
- Clock anomalies split into `backward` (RTC set at boot) and `forward`
  (suspend/STR silence) — both must be avoided by windowing (R13 / §5).
- Loss regions (chatty, "lost N lines") are recorded so "absence" is never
  read as evidence (red line R13).

stdout: output paths + row counts (idempotent). Python 3 stdlib only.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402
from config import (  # noqa: E402
    LOGCAT_GLOB, AUX_HINTS, DEFAULT_YEAR, BOOT_MARKERS,
    CLOCK_BACKWARD_MS, CLOCK_FORWARD_MS,
)

LOSS_MARKERS = [
    ("chatty", re.compile(r"chatty.*expire \d+ line", re.I)),
    ("logd_lost", re.compile(r"lost \d+ line", re.I)),
]
# events tags used for the Java process table
EV_PROC_START = "am_proc_start"   # [User,PID,UID,Process Name,Type,Component]
EV_PROC_DIED = "am_proc_died"     # [User,PID,Process Name,...]
# native process lifecycle (init / servicemanager)
RE_INIT_START = re.compile(r"Starting service '([^']+)'")
RE_INIT_EXIT = re.compile(r"Service '([^']+)'.*\(pid (\d+)\).*(?:exited|killed|died)", re.I)


def year_from_name(name):
    m = re.search(r"@(\d{4})\d{4}", name)
    return int(m.group(1)) if m else DEFAULT_YEAR


def is_logcat(name):
    if any(h in name for h in AUX_HINTS):
        return False
    return bool(LOGCAT_GLOB.search(name))


class FileScan:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.year = year_from_name(self.name)
        self.first = None       # first LogLine
        self.last = None        # last LogLine
        self.nlines = 0
        self.levels = {}
        self.tags = {}
        self.anomalies = 0
        self.boot_hits = []     # (lineno, kind, msg)
        self.loss_hits = []     # (lineno, kind, msg)
        self.clock_hits = []    # (lineno, kind, delta_ms)
        self.procs = []         # (name, pid, userId, kind, start_lineno, end_lineno, source)


def scan_file(path):
    fs = FileScan(path)
    prev_ms = None
    # track native services started here so an exit can close the interval
    for lineno, raw, ll in C.iter_log(path):
        fs.nlines += 1
        # boot / loss markers work on raw text (they are not always threadtime)
        for kind, rgx in BOOT_MARKERS:
            if rgx.search(raw):
                mts = _ts(ll, fs.year) if ll else "?"
                fs.boot_hits.append((lineno, kind, raw.strip()[:120], mts))
                break
        for kind, rgx in LOSS_MARKERS:
            if rgx.search(raw):
                fs.loss_hits.append((lineno, kind, raw.strip()[:120]))
                break
        if ll is None:
            continue
        if fs.first is None:
            fs.first = ll
        fs.last = ll
        fs.levels[ll.level] = fs.levels.get(ll.level, 0) + 1
        fs.tags[ll.tag] = fs.tags.get(ll.tag, 0) + 1
        if C.LEVEL_ORDER.get(ll.level, 0) >= C.LEVEL_ORDER["E"]:
            fs.anomalies += 1
        # clock jump detection (within one file only), date-aware
        cur = ll.abs_ms()
        if prev_ms is not None:
            d = cur - prev_ms
            if d <= -CLOCK_BACKWARD_MS:
                fs.clock_hits.append((lineno, "backward", d))
            elif d >= CLOCK_FORWARD_MS:
                fs.clock_hits.append((lineno, "forward", d))
        prev_ms = cur
        # process table
        if ll.tag == EV_PROC_START:
            f = C.parse_event_msg(ll.msg)
            if len(f) >= 4:
                fs.procs.append((f[3], _int(f[1]), _int(f[0]), "am_proc",
                                 lineno, "", "am_proc_start"))
        elif ll.tag == EV_PROC_DIED:
            f = C.parse_event_msg(ll.msg)
            if len(f) >= 3:
                fs.procs.append((f[2], _int(f[1]), _int(f[0]), "am_proc",
                                 "", lineno, "am_proc_died"))
        else:
            mstart = RE_INIT_START.search(ll.msg)
            if mstart and ll.tag == "init":
                fs.procs.append((mstart.group(1), "", "-", "init",
                                 lineno, "", "init"))
            mexit = RE_INIT_EXIT.search(ll.msg)
            if mexit:
                fs.procs.append((mexit.group(1), _int(mexit.group(2)), "-",
                                 "init", "", lineno, "init"))
    return fs


def _int(s):
    try:
        return int(str(s).strip())
    except (ValueError, TypeError):
        return ""


COALESCE_SECS = 90   # boot markers within this gap belong to the SAME boot


def _mts_ms(mts):
    """Parse 'YYYY-MM-DD HH:MM:SS.mmm' to abs ms; None if unknown ('?')."""
    try:
        d = mts[5:]  # drop year
        mon, day = int(d[0:2]), int(d[3:5])
        h, m, s = int(d[6:8]), int(d[9:11]), int(d[12:14])
        ms = int(d[15:18]) if len(d) >= 18 else 0
        return (C._DOY[mon - 1] + (day - 1)) * 86400000 + \
               ((h * 60 + m) * 60 + s) * 1000 + ms
    except (ValueError, IndexError):
        return None


def assign_sessions(scans):
    """Order files by first timestamp, collect boot markers globally, COALESCE
    markers of the same boot (a single boot emits several: kernel/init/
    boot_progress within seconds), then cut one session per coalesced boot.

    Coalescing avoids the failure where one boot's multiple markers each open a
    session. Same-boot markers are seconds apart; different boots are minutes+
    apart (the first boot's uptime), so a time-gap threshold separates them.
    """
    ordered = sorted([s for s in scans if s.first],
                     key=lambda s: s.first.ts_key(s.year))
    if not ordered:
        return [], ordered

    # global marker list in file/line order
    marks = []
    for fs in ordered:
        for (lineno, kind, msg, mts) in fs.boot_hits:
            marks.append((fs, lineno, kind, mts, _mts_ms(mts)))

    # coalesce: keep a marker as a boot-start unless within COALESCE_SECS of the
    # previous kept one (by abs ms; if either ts unknown, coalesce iff same file
    # and < 2000 lines apart — a conservative same-boot proxy).
    boot_starts, prev = [], None
    for mk in marks:
        if prev is None:
            boot_starts.append(mk); prev = mk; continue
        _, plineno, _, _, pms = prev
        fs, lineno, _, _, ms = mk
        same_boot = False
        if ms is not None and pms is not None:
            same_boot = abs(ms - pms) <= COALESCE_SECS * 1000
        else:
            same_boot = (fs is prev[0]) and (lineno - plineno) < 2000
        if not same_boot:
            boot_starts.append(mk); prev = mk

    # build sessions: dir-start .. first boot-start, then between boot-starts
    sessions = []
    sid = 0
    first = ordered[0]
    cur = _new_session(sid, first, first.first.lineno)
    for (fs, lineno, kind, mts, _ms) in boot_starts:
        # close current just before this boot-start
        cur["end_file"] = fs.name
        cur["end_line"] = max(lineno - 1, 1)
        cur["end_ts"] = mts
        # drop an empty leading dir-start fragment (boot-start at very top)
        if not (sid == 0 and cur["start_file"] == fs.name
                and cur["start_line"] >= lineno - 1):
            _collect_files(cur, ordered)
            sessions.append(cur)
        sid += 1
        cur = _new_session(sid, fs, lineno, marker=(fs.name, lineno, kind),
                           start_ts=mts)
    last = ordered[-1]
    cur["end_file"] = last.name
    cur["end_line"] = last.last.lineno if last.last else 1
    cur["end_ts"] = _ts(last.last, last.year) if last.last else cur["start_ts"]
    _collect_files(cur, ordered)
    sessions.append(cur)
    # renumber sids compactly (dropped fragments may leave gaps)
    for i, s in enumerate(sessions):
        s["sid"] = "s%d" % i
    return sessions, ordered


def _collect_files(session, ordered):
    """A file belongs to a session if the session's [start,end] line span
    overlaps that file. Approximate by name range using ordered position."""
    names = [fs.name for fs in ordered]
    try:
        si = names.index(session["start_file"])
        ei = names.index(session.get("end_file", session["start_file"]))
    except ValueError:
        si = ei = 0
    session["files"] = names[si:ei + 1]


def _new_session(sid, fs, lineno, marker=None, start_ts=None):
    return {
        "sid": "s%d" % sid,
        "start_file": fs.name, "start_line": lineno,
        "start_ts": start_ts or (_ts(fs.first, fs.year) if fs.first else "?"),
        "marker": "%s:%d %s" % marker if marker else "dir-start",
        "files": [],
    }


def _ts(ll, year):
    if ll is None:
        return "?"
    return "%04d-%02d-%02d %02d:%02d:%02d.%03d" % (
        year, ll.mon, ll.day, ll.h, ll.m, ll.s, ll.ms)


def main():
    ap = argparse.ArgumentParser(description="one-shot logcat index (spec §8.3)")
    ap.add_argument("log_dir")
    ap.add_argument("--out", default=None, help="manifest output dir")
    args = ap.parse_args()

    log_dir = os.path.abspath(args.log_dir)
    out = os.path.abspath(args.out) if args.out else os.path.join(log_dir, "manifest")
    os.makedirs(out, exist_ok=True)

    files = [os.path.join(log_dir, f) for f in sorted(os.listdir(log_dir))
             if is_logcat(f)]
    if not files:
        print("no logcat files matched in %s" % log_dir, file=sys.stderr)
        sys.exit(2)

    scans = []
    for p in files:
        try:
            scans.append(scan_file(p))
        except ValueError as e:
            print("skip: %s" % e, file=sys.stderr)
    sessions, ordered = assign_sessions(scans)

    # map file -> session id (by session that contains its first line);
    # a file appearing under multiple sessions lists multiple segments.
    file_sid = {}
    for s in sessions:
        for fn in s.get("files", []):
            file_sid.setdefault(fn, s["sid"])

    written = []
    n = C.write_tsv(os.path.join(out, "sessions.tsv"),
                    ["session_id", "start", "end", "start_ts", "end_ts", "marker"],
                    [[s["sid"],
                      "%s:%d" % (s["start_file"], s["start_line"]),
                      "%s:%d" % (s.get("end_file", "?"), s.get("end_line", 0)),
                      s["start_ts"], s.get("end_ts", "?"), s["marker"]]
                     for s in sessions])
    written.append(("sessions.tsv", n))

    frows = []
    for fs in ordered:
        top = ",".join("%s:%d" % (t, c) for t, c in
                       sorted(fs.tags.items(), key=lambda x: -x[1])[:8])
        lev = ",".join("%s:%d" % (k, fs.levels.get(k, 0))
                       for k in ["V", "D", "I", "W", "E", "F"])
        span = "%s..%s" % (_ts(fs.first, fs.year), _ts(fs.last, fs.year))
        frows.append([fs.name, file_sid.get(fs.name, "?"), fs.nlines,
                      span, lev, fs.anomalies, top])
    n = C.write_tsv(os.path.join(out, "files.tsv"),
                    ["file", "session_id", "lines", "time_span", "level_hist",
                     "anomaly_count", "top_tags"], frows)
    written.append(("files.tsv", n))

    # per-session proc/clock/loss tables
    for s in sessions:
        sid = s["sid"]
        sfiles = set(s.get("files", []))
        procs, clocks, losses = [], [], []
        for fs in ordered:
            if fs.name not in sfiles:
                continue
            for (name, pid, uid, kind, sl, el, src) in fs.procs:
                procs.append([name, pid, uid,
                              "%s:%s" % (fs.name, sl) if sl else "",
                              "%s:%s" % (fs.name, el) if el else "alive",
                              src])
            for (lineno, ck, delta) in fs.clock_hits:
                # direction alone can't tell RTC-set from suspend; label honestly
                typ = ("backward=clock-set" if ck == "backward"
                       else "forward=RTC-set-or-suspend")
                clocks.append([typ, "%s:%d" % (fs.name, lineno), delta, "heuristic"])
            for (lineno, lk, msg) in fs.loss_hits:
                losses.append([lk, "%s:%d" % (fs.name, lineno), "?",
                               "%s:%d" % (fs.name, lineno)])
        n1 = C.write_tsv(os.path.join(out, "procs-%s.tsv" % sid),
                         ["proc", "pid", "userId", "start", "end", "source"], procs)
        n2 = C.write_tsv(os.path.join(out, "clock-%s.tsv" % sid),
                         ["type", "loc", "delta_ms", "confidence"], clocks)
        n3 = C.write_tsv(os.path.join(out, "loss-%s.tsv" % sid),
                         ["type", "range", "est_lost", "evidence"], losses)
        written.append(("procs-%s.tsv" % sid, n1))
        written.append(("clock-%s.tsv" % sid, n2))
        written.append(("loss-%s.tsv" % sid, n3))

    print("manifest: %s" % out)
    for name, cnt in written:
        print("  %-18s %d rows" % (name, cnt))
    print("sessions=%d logcat_files=%d" % (len(sessions), len(ordered)))


if __name__ == "__main__":
    main()
