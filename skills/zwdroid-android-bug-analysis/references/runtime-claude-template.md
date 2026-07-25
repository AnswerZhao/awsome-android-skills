# CLAUDE.md — Android/AAOS Bug 分析项目(运行时模板)

> 这是随 zwdroid-android-bug-analysis skill 附带的模板:复制到目标项目根作为(或并入)
> 项目 CLAUDE.md,**把下面的环境事实逐条改成目标项目的真实值**(当前值来自一个
> AAOS/Android 12 项目,仅作示例)。只放事实与配置,不放方法论(方法论在 skill 里)。
> 准入标准:每条信息每次分析任务都用得到。

做 Android/AAOS 日志根因分析时,使用 **zwdroid-android-bug-analysis** skill
(它含状态机、红线 R1-R13、脚本)。

## 环境事实

- **目标 ROM**:AAOS,基于 Android 12。源码 tag(如启用源码验证):`android-12.0.0_r34`。
- **日志格式**:threadtime —— `MM-DD HH:MM:SS.mmm PID TID L TAG: MSG`。**无年份**(须注入)、
  **无时区**(设备本地时区)。main/system/events 合并为单流;events 的 tag 已是符号名。
- **日志文件命名**:`log_logcat@YYYYMMDD_HH-MM-SS-mmm-PC_<n>.log`,约 20MB 轮转。
  辅助文件 `log_net`/`log_top`/`log_topmen`/`si_log` **不是 logcat**,解析时排除。
  ⚠️ 文件名里的 `@时间` **不等于**文件首行日志时间;一律信 manifest 的 time_span,不信文件名。
- **制品定位**:按原生文件夹名递归查找 `anr` / `tombstones` / `dropbox`(不写死绝对路径,各项目不同)。

## 配置区(占位符集中在此,改一处生效)

```yaml
# 预算参数(agent 行为侧)
MAX_ROUNDS: 4              # S2 locate 轮询上限
SLICE_LINE_CAP: 2000       # 单日志切片行数硬顶(R6)
SRC_READ_CAP: 2000         # 源码单文件精读阈值,超过交 subagent
EXPLORE_WINDOW_SEC: 10     # explore 默认 ±秒
SAMPLE_STRIDE: 5           # slow 剖面采样步长(每 N 文件)

# 源码开关(默认关 → 日志-only 出结论,形态 B)
AOSP_ROOT: ""             # 留空=源码开关关。填源码根路径 + 用户要求结合源码,才做 S5 验证
AOSP_BRANCH: "android-12.0.0_r34"

# 使用规模
MODE: personal            # personal | team(影响文档防呆程度)
```

> 脚本侧参数(SCREAM_LINE_CAP、回退年份、日志文件名模式、boot 切分标志、时钟跳变阈值)
> **唯一定义在 `scripts/config.py`**,脚本自行读取,不在此重复。

## 已知坑(每次分析都要记得)
- **cross-buffer 乱序**:合并流里相邻行毫秒级乱序正常,别当时钟跳变(真跳变阈值 60s,见 manifest)。
- **selinux_denial 噪声极大**(单会话数百条),命中多≠根因,须与症状对齐。
- **boot 切分**只信 `Linux version`/`init first stage`/`boot_progress_start`,忌用宽松 Zygote 标志。
- **跨 boot session 关联无效**(pid/时间戳语义重置),扩展禁止静默跨 session(R12)。
