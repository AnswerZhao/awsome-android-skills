#!/usr/bin/env python3
"""logcat-around-pid — extract one process's context (spec §11).

Pulls all lines for a pid from the given RAW files, each with a source prefix.
Cross-checks the pid against the manifest process table: prints the resolved
process name(s) and userId, flags a same-pid two-name conflict, and lists other
pids the same process ran under (crash-restart changes pid — cross-pid follow).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402


def load_procs(manifest):
    rows = []
    for name in sorted(os.listdir(manifest)):
        if name.startswith("procs-") and name.endswith(".tsv"):
            _, r = C.read_tsv(os.path.join(manifest, name))
            rows.extend(r)
    return rows


def main():
    ap = argparse.ArgumentParser(description="per-process context slice")
    ap.add_argument("pid", type=int)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    procs = load_procs(args.manifest)
    names = sorted({r["proc"] for r in procs if r.get("pid") == str(args.pid)})
    # cross-pid: all pids the resolved process(es) ran under
    sibling_pids = sorted({r["pid"] for r in procs
                           if r.get("proc") in names and r.get("pid")})
    userids = sorted({r.get("userId", "-") for r in procs
                      if r.get("pid") == str(args.pid)})

    out = args.out or ("around-pid-%d.log" % args.pid)
    kept = 0
    with open(out, "w") as w:
        for path in args.files:
            for lineno, raw, ll in C.iter_log(path):
                if ll is None or ll.pid != args.pid:
                    continue
                w.write(ll.emit() + "\n")
                kept += 1

    print("slice: %s" % os.path.abspath(out))
    print("lines: %d  pid=%d" % (kept, args.pid))
    if names:
        print("proc: %s  userId: %s" % (",".join(names), ",".join(userids)))
    else:
        print("proc: <not in manifest table for this pid>")
    if len(names) > 1:
        print("CONFLICT: pid %d maps to multiple process names %s — resolve "
              "before trusting (spec §5)." % (args.pid, names))
    if len(sibling_pids) > 1:
        print("cross-pid: same process also ran as pid(s) %s — follow across "
              "restarts (spec §5)." % ",".join(p for p in sibling_pids
                                                if p != str(args.pid)))


if __name__ == "__main__":
    main()
