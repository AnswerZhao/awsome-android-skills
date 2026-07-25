#!/usr/bin/env python3
"""log-batch — produce the batch file list for a round (spec §11).

Given an anchor (file name or time) and a radius, return the ±radius logcat
files WITHIN the anchor's boot session. Never crosses a session boundary
(red line R12). Reads sessions.tsv / files.tsv from the manifest.

stdout: the ordered file list (one per line) + a summary line.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402


def files_in_session(manifest):
    _, files = C.read_tsv(os.path.join(manifest, "files.tsv"))
    # keep manifest order (already first-timestamp ordered by ingest)
    return files


def main():
    ap = argparse.ArgumentParser(description="batch file list within a session (R12)")
    ap.add_argument("anchor", help="anchor file name OR time 'MM-DD HH:MM:SS'")
    ap.add_argument("radius", type=int, help="files to include on each side")
    ap.add_argument("--manifest", required=True,
                    help="manifest dir (run rca-ingest first)")
    args = ap.parse_args()

    if not os.path.isdir(args.manifest):
        print("manifest not found: %s — run rca-ingest.py first" % args.manifest,
              file=sys.stderr)
        sys.exit(2)

    files = files_in_session(args.manifest)
    if not files:
        print("empty files.tsv in manifest", file=sys.stderr)
        sys.exit(2)

    names = [f["file"] for f in files]
    # locate anchor index
    idx = None
    if args.anchor in names:
        idx = names.index(args.anchor)
        sid = files[idx]["session_id"]
    else:
        # anchor given as a time: find the file whose time_span covers it
        sid = None
        key = _mmss(args.anchor)
        for i, f in enumerate(files):
            span = f["time_span"]
            if ".." in span:
                lo, hi = span.split("..", 1)
                if _mmss(lo) <= key <= _mmss(hi):
                    idx, sid = i, f["session_id"]
                    break
        if idx is None:
            print("could not locate anchor '%s' in any file span" % args.anchor,
                  file=sys.stderr)
            sys.exit(3)

    # restrict to same session, then take ±radius around idx
    same = [i for i, f in enumerate(files) if f["session_id"] == sid]
    lo = max(min(same), idx - args.radius)
    hi = min(max(same), idx + args.radius)
    batch = [names[i] for i in range(lo, hi + 1)
             if files[i]["session_id"] == sid]

    for b in batch:
        print(b)
    print("# batch: %d files, session=%s, anchor=%s [R12: session-bounded]"
          % (len(batch), sid, names[idx]), file=sys.stderr)


def _mmss(s):
    """Normalize a timestamp to the year-agnostic 'MM-DD HH:MM:SS' key.
    Accepts 'YYYY-MM-DD HH:MM:SS[.mmm]' (manifest) or 'MM-DD HH:MM:SS' (user)."""
    s = s.strip()
    if len(s) >= 19 and s[4] == "-":     # has YYYY-
        s = s[5:]
    return s[:14]                         # 'MM-DD HH:MM:SS'


if __name__ == "__main__":
    main()
