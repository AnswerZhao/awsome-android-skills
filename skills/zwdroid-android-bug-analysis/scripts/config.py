"""Single source of truth for script-side tunables.

Agent-side budgets (MAX_ROUNDS, SLICE_LINE_CAP, ...) live in the runtime
CLAUDE.md 配置区; everything the scripts read lives here. Edit one place.
"""
import re

# scream-scan output hard cap (lines, after fold/dedup). spec §13 {{SCREAM_LINE_CAP}}
SCREAM_LINE_CAP = 500

# Logcat filename pattern ({{LOG_FILE_PATTERN}}); AUX_HINTS name the auxiliary
# files (not logcat) excluded from parsing.
LOGCAT_GLOB = re.compile(r"log_logcat@.*\.log$")
AUX_HINTS = ("log_net", "log_top", "log_topmen", "si_log")

# Year injected into year-less threadtime stamps; filename @YYYYMMDD wins,
# this is the fallback ({{LOG_YEAR}}).
DEFAULT_YEAR = 2026

# Boot-session split markers ({{BOOT_MARKERS}}). Only high-precision,
# boot-unique markers. Loose ones like /Zygote.*init/ are rejected:
# ZygoteInit.main appears in every runtime stack trace (verified on real
# logs -> 222 false sessions). Markers of one boot are merged by ingest when
# within 90s of each other.
BOOT_MARKERS = [
    ("kernel_boot", re.compile(r"Linux version \d")),
    ("init_first_stage", re.compile(r"init first stage")),
    ("boot_progress_start", re.compile(r"\bboot_progress_start\b")),
]

# Clock-jump thresholds. Set high on purpose: in `-b all` merged output,
# consecutive lines come from different buffers with slightly out-of-order
# timestamps, so sub-minute deltas are interleaving noise, NOT clock jumps
# (verified: 78/83 hits were <1m). Only large, persistent shifts (RTC set at
# boot, real suspend) matter for windowing avoidance (R13).
CLOCK_BACKWARD_MS = 60000    # jump back >60s => clock adjustment
CLOCK_FORWARD_MS = 60000     # jump forward >60s => RTC set at boot / suspend silence
