#!/usr/bin/env python3
"""aaos-grep — source search, gated by the source switch (spec §7, §11).

Searches the configured AOSP/vendor tree for a pattern and prints path:line.
This is the ONLY script that touches source. It refuses to run unless a source
root is configured (env AOSP_ROOT or --root), matching the design that source
verification is opt-in (spec §7). Output path:line is what red line R2 requires
before any class/method/path may enter a conclusion.
"""
import argparse
import os
import re
import subprocess
import sys

SCOPE_HINTS = {
    "framework": ["frameworks/"],
    "vendor": ["vendor/", "packages/services/Car/"],
    "all": [""],
}
TYPE_GLOB = {
    "java": ["*.java", "*.kt"],
    "cpp": ["*.cpp", "*.cc", "*.c", "*.h"],
    "aidl": ["*.aidl", "*.hal"],
}


def main():
    ap = argparse.ArgumentParser(description="source grep (source switch, R2)")
    ap.add_argument("pattern")
    ap.add_argument("--root", default=os.environ.get("AOSP_ROOT"),
                    help="AOSP source root (or env AOSP_ROOT)")
    ap.add_argument("--scope", choices=list(SCOPE_HINTS), default="all")
    ap.add_argument("--type", dest="ftype", choices=list(TYPE_GLOB), default=None)
    ap.add_argument("--max", type=int, default=100)
    args = ap.parse_args()

    if not args.root:
        print("source switch OFF: no AOSP_ROOT configured. Source verification "
              "is opt-in (spec §7); default path concludes from logs (form B). "
              "Set AOSP_ROOT in runtime CLAUDE.md to enable.", file=sys.stderr)
        sys.exit(3)
    if not os.path.isdir(args.root):
        print("AOSP_ROOT not a directory: %s" % args.root, file=sys.stderr)
        sys.exit(2)

    # prefer ripgrep if present, else fall back to grep -r
    globs = TYPE_GLOB.get(args.ftype, [])
    subdirs = [os.path.join(args.root, h) for h in SCOPE_HINTS[args.scope]]
    subdirs = [d for d in subdirs if os.path.exists(d)] or [args.root]

    if _has("rg"):
        cmd = ["rg", "-n", "--no-heading"]
        for g in globs:
            cmd += ["-g", g]
        cmd += [args.pattern] + subdirs
    else:
        cmd = ["grep", "-rnI"]
        for g in globs:
            cmd += ["--include", g]
        cmd += [args.pattern] + subdirs

    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print("search failed: %s" % e, file=sys.stderr)
        sys.exit(1)

    lines = [l for l in p.stdout.splitlines() if l.strip()][:args.max]
    for l in lines:
        print(l)
    print("# hits: %d (scope=%s type=%s root=%s)"
          % (len(lines), args.scope, args.ftype or "any", args.root),
          file=sys.stderr)
    if not lines:
        # R2/R3: a miss is itself a signal — the expected signature is absent.
        print("# no match — expected source signature absent; do NOT assert "
              "this class/method exists (R2).", file=sys.stderr)


def _has(binname):
    return subprocess.call(["which", binname], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL) == 0


if __name__ == "__main__":
    main()
