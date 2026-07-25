"""Tag presets and anomaly signal rules (spec §3 routing / §11 scream-scan).

Distilled from the prior logcat-analysis signal taxonomy (spec §16) plus AOSP
common landmarks. This file is the SINGLE SOURCE OF TRUTH for preset contents
and scream signals; references/presets.md only routes bug types to preset
names and points here.
"""

# --- tag presets, keyed by S1 routing (spec §3) ---------------------------
# Trailing '_' means prefix match (e.g. 'wm_' matches wm_on_paused_called).
PRESETS = {
    "PRESET_CRASH": ["AndroidRuntime", "FATAL EXCEPTION", "am_crash",
                     "am_proc_died"],
    "PRESET_NATIVE_CRASH": ["DEBUG", "libc", "tombstoned", "backtrace"],
    "PRESET_ANR": ["am_anr", "ActivityManager", "InputDispatcher"],
    # am_create_activity + ActivityTaskManager "START u<id> ... from uid/pid"
    # carry the CALLER identity — the direct evidence for "who started it".
    "PRESET_UI": ["wm_", "am_", "input_focus", "am_create_activity",
                  "ActivityTaskManager", "WindowManager", "SurfaceFlinger",
                  "InputDispatcher"],
    "PRESET_REBOOT": ["Watchdog", "SystemServer", "am_proc_died",
                      "boot_progress_start"],
    "PRESET_LEAK": ["lowmemorykiller", "lmkd", "am_meminfo", "dalvikvm",
                    "kswapd"],
    # AAOS-specific (from real logs: VHalProperty/CarService/CarStateCallBack)
    "PRESET_CAR": ["CarService", "VHalProperty", "CarPropertyManager",
                   "CarStateCallBackManager", "carwatchdog", "VehicleHal"],
    "PRESET_MULTIUSER": ["am_", "UserController", "CarUserService",
                         "user_switch", "am_switch_user", "am_create_activity",
                         "ActivityTaskManager"],
}

# --- anomaly signals for scream-scan (channel 2) --------------------------
# (rule_id, severity, is_regex, pattern-on-(tag|msg)). Kept deliberately small
# and high-signal; message-body match uses the parsed msg field, not raw text.
SIGNALS = [
    ("fatal_exception",     "high", "FATAL EXCEPTION"),
    ("android_runtime",     "high", "AndroidRuntime"),
    ("anr_in_process",      "high", "ANR in "),
    ("input_anr",           "high", "Input dispatching timed out"),
    ("tombstone_written",   "high", "Tombstone written"),
    ("native_crash",        "high", "*** *** ***"),
    ("watchdog",            "high", "WATCHDOG"),
    ("hal_died",            "high", "HAL died"),
    ("system_server_restart", "high", "Boot progress: system server"),
    ("proc_died",           "med",  "am_proc_died"),
    ("binder_died",         "med",  "binderDied"),
    ("lowmem_kill",         "med",  "lowmemorykiller"),
    ("lmk_kill",            "med",  "Kill '"),
    ("selinux_denial",      "med",  "avc: denied"),
    ("force_finishing",     "med",  "Force finishing activity"),
    ("window_freeze",       "med",  "Window freeze timeout"),
    ("skipped_frames",      "low",  "Skipped "),
    ("user_switch",         "info", "am_switch_user"),
    ("task_auto_restored",  "info", "task_auto_restored"),
]
