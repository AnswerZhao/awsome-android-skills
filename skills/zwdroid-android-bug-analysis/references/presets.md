# presets.md — S1 路由表

tag preset 内容与尖叫扫描信号集**唯一定义在 `${CLAUDE_SKILL_DIR}/scripts/presets_data.py`**(`PRESETS`/`SIGNALS`);
本文件只管路由决策(bug 类型 → preset 名)。需要看某 preset 具体含哪些 tag、或信号分档时,读该文件。

## 路由表
| bug 类型 | 时间剖面 | 取证范围(logcat 之外) | tag preset |
|----------|----------|------------------------|-----------|
| Java crash | fast | dropbox | PRESET_CRASH |
| Native crash | fast | tombstone | PRESET_NATIVE_CRASH |
| ANR | fast~中 | anr(`/data/anr/` trace) | PRESET_ANR |
| UI/焦点/显示 | fast | — | PRESET_UI |
| 重启/watchdog | fast | kernel log | PRESET_REBOOT |
| 性能/泄漏/累积 | slow | — | PRESET_LEAK |
| HAL/VHAL/CarService | 视情况 | vendor 日志(待补) | PRESET_CAR |
| 多用户/多屏 | 视情况 | — | PRESET_MULTIUSER |

某类 bug 高频出现、且有稳定私有 tag 时,可在 `presets_data.py` 增设项目级 preset;
一次性 bug 场景的 tag 用 `--tags` 临时传入,不沉积进 preset 表。

## 路由规则
- 用户明确报 crash/ANR/重启 → 对应异常 tag 直接作首要过滤条件。
- **重启/watchdog 类**:boot session 边界本身即锚点,直接用 manifest 的 session 切分定位,
  无需常规锚点解析;这是**唯一默认允许跨 session** 的类型(须在 ledger 显式声明,R12)。
- **slow 剖面**跳过同心扩展,改大跨度采样(locate.md 步骤 7)。
- 取证范围含 logcat 之外来源:**按原生文件夹名递归查找**(`tombstones`/`anr`/`dropbox`,
  不写死绝对路径,不同项目落盘位置不同);先确认文件存在再纳入,解析见 artifacts.md。
- 尖叫扫描信号按 high/med/low/info 分档;高噪声信号的采信注意事项见运行时 CLAUDE.md「已知坑」。
