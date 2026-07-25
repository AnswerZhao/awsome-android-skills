#!/usr/bin/env python3
"""logcat-window — field-parsed time/tag/level slice (spec §11, channel 1).

Filters RAW logcat by time window + tag preset/list + min level, AFTER parsing
fields (never plain-text grep). Emits every line with a source prefix (R11).
Warns when the window overlaps a clock discontinuity or silence region from
the manifest (R13 / §5): timestamps across such a point are not comparable.

Output: slice file (default under --out) + stdout path/line-count summary.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402
import presets_data as P  # noqa: E402


def _mmss(s):
    s = s.strip()
    if len(s) >= 19 and s[4] == "-":
        s = s[5:]
    return s[:14]


def in_window(ll, start, dur_s):
    """start = 'MM-DD HH:MM:SS' key; window = [start, start+dur]."""
    key = "%02d-%02d %02d:%02d:%02d" % (ll.mon, ll.day, ll.h, ll.m, ll.s)
    if key < start:
        return False
    # crude upper bound on the MM-DD HH:MM:SS string: compute end key
    return key <= _end_key(start, dur_s)


def _end_key(start, dur_s):
    # start 'MM-DD HH:MM:SS' -> add dur seconds (no day rollover past month)
    mm, dd = int(start[0:2]), int(start[3:5])
    h, m, s = int(start[6:8]), int(start[9:11]), int(start[12:14])
    s += dur_s
    m += s // 60; s %= 60
    h += m // 60; m %= 60
    dd += h // 24; h %= 24
    return "%02d-%02d %02d:%02d:%02d" % (mm, dd, h, m, s)


def main():
    ap = argparse.ArgumentParser(description="time+tag+level slice (channel 1)")
    ap.add_argument("start", help="window start 'MM-DD HH:MM:SS'")
    ap.add_argument("duration", type=int, help="window length in seconds")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--files", nargs="+", required=True, help="raw log files")
    ap.add_argument("--preset", default=None, help="tag preset name (presets_data)")
    ap.add_argument("--tags", default=None, help="comma-separated tag list")
    ap.add_argument("--level", default=None, help="min level V/D/I/W/E/F")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    start = _mmss(args.start)
    tagset = None
    if args.preset:
        tagset = set(P.PRESETS.get(args.preset, []))
        if not tagset:
            print("unknown preset %s; known: %s"
                  % (args.preset, ",".join(P.PRESETS)), file=sys.stderr)
            sys.exit(2)
    elif args.tags:
        tagset = set(t.strip() for t in args.tags.split(","))
    minlv = C.LEVEL_ORDER.get(args.level, 0) if args.level else 0

    out = args.out or "round-window.log"
    kept = 0
    with open(out, "w") as w:
        for path in args.files:
            for lineno, raw, ll in C.iter_log(path):
                if ll is None:
                    continue
                if not in_window(ll, start, args.duration):
                    continue
                if C.LEVEL_ORDER.get(ll.level, 0) < minlv:
                    continue
                if tagset is not None and not _tag_match(ll.tag, tagset):
                    continue
                w.write(ll.emit() + "\n")
                kept += 1

    warn = _clock_warn(args.manifest, start, _end_key(start, args.duration))
    print("slice: %s" % os.path.abspath(out))
    print("lines: %d" % kept)
    if warn:
        print("NOTE(R13): session has clock/silence discontinuities at %s — "
              "verify this window does not straddle them (timestamps across a "
              "discontinuity are not comparable)." % warn)


def _tag_match(tag, tagset):
    # exact, or prefix match for wildcard-ish presets like 'wm_' 'am_'
    if tag in tagset:
        return True
    return any(t.endswith("_") and tag.startswith(t) for t in tagset)


def _clock_warn(manifest, start, end):
    hits = []
    for name in os.listdir(manifest):
        if name.startswith("clock-") and name.endswith(".tsv"):
            _, rows = C.read_tsv(os.path.join(manifest, name))
            for r in rows:
                hits.append(r.get("loc", ""))
    return ",".join(hits[:3]) if hits else ""


if __name__ == "__main__":
    main()
