#!/usr/bin/env python3
"""scream-scan — anomaly channel, independent of the semantic timeline (spec §11).

Scans RAW logcat for high-signal anomalies (spec §16 signal taxonomy), each with
a source prefix. Aggregates identical (rule, tag, message-skeleton) into one
folded row with a count and first/last sample line numbers, so a noisy repeated
error can't blow the context budget (output hard-capped at SCREAM_LINE_CAP).
Loss markers (chatty / lost N lines) are reported in a separate section so
"absence" is never mistaken for "did not happen" (red line R13).

Channel-2 output is presented ALONGSIDE the timeline, never merged (R10).
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402
import presets_data as P  # noqa: E402
from config import SCREAM_LINE_CAP  # noqa: E402

_NUM = re.compile(r"\d+")


def skeleton(msg):
    """Collapse variable parts (numbers, hex) so repeats fold together."""
    s = _NUM.sub("#", msg)
    return s[:80]


def main():
    ap = argparse.ArgumentParser(description="anomaly scan (channel 2)")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="round-scream.md")
    ap.add_argument("--cap", type=int, default=SCREAM_LINE_CAP)
    args = ap.parse_args()

    folded = {}   # key -> [rule, sev, count, first_loc, last_loc, sample]
    loss = []
    for path in args.files:
        for lineno, raw, ll in C.iter_log(path):
            base = os.path.basename(path)
            # loss markers work on raw text
            low = raw.lower()
            if "chatty" in low and "expire" in low:
                loss.append(("chatty", "%s:%d" % (base, lineno), raw.strip()[:100]))
            elif "lost" in low and "line" in low:
                loss.append(("lost", "%s:%d" % (base, lineno), raw.strip()[:100]))
            if ll is None:
                continue
            hay = ll.tag + " " + ll.msg
            for rule, sev, pat in P.SIGNALS:
                if pat in hay:
                    key = (rule, ll.tag, skeleton(ll.msg))
                    loc = "%s:%d" % (base, lineno)
                    if key in folded:
                        e = folded[key]
                        e[2] += 1
                        e[4] = loc
                    else:
                        folded[key] = [rule, sev, 1, loc, loc,
                                       ll.emit().rstrip()]
                    break

    rows = sorted(folded.values(),
                  key=lambda e: (_sev_rank(e[1]), -e[2]))
    capped = rows[:args.cap]

    with open(args.out, "w") as w:
        w.write("# scream-scan (channel 2 — do not merge with timeline, R10)\n\n")
        w.write("## 异常信号(按严重度、命中数排序;已折叠去重)\n")
        w.write("| rule | sev | count | first [file:line] | last | 样本 |\n")
        w.write("|---|---|---:|---|---|---|\n")
        for e in capped:
            w.write("| %s | %s | %d | %s | %s | `%s` |\n"
                    % (e[0], e[1], e[2], e[3], e[4], e[5].replace("|", "\\|")[:120]))
        if len(rows) > args.cap:
            w.write("\n> 截断:%d 类命中,仅列前 %d(超 SCREAM_LINE_CAP);"
                    "收紧文件范围或按 rule 过滤。\n" % (len(rows), args.cap))
        w.write("\n## 日志损耗标志(R13:以下区间内'无日志'不作证据)\n")
        if loss:
            for t, loc, s in loss[:100]:
                w.write("- [%s] %s — `%s`\n" % (t, loc, s))
        else:
            w.write("- 无\n")

    print("scream: %s" % os.path.abspath(args.out))
    print("signal_classes: %d (shown %d), loss_markers: %d"
          % (len(rows), len(capped), len(loss)))


def _sev_rank(s):
    return {"high": 0, "med": 1, "low": 2, "info": 3}.get(s, 4)


if __name__ == "__main__":
    main()
