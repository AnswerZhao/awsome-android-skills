# reconstruct.md — S3 事件重建

输入:S2 的精确时间点 + explore 切片 + 取证范围内的制品。
产出:写入 `timeline.md` 的事件序列,**≤一屏(约 20-30 条)**;超量说明窗口/tag 未收敛,退回 S2 收紧。

## 时间线条目格式
`[精确时间戳] [userId/进程:pid] [事件] [证据 原始文件:行号]`
- **pid 一律附进程名与 userId**。AAOS 是 user 0(headless system)+ user 10+(驾驶员)双活,
  大量焦点/权限/服务 bug 本质是 userId 错乱——userId 是一等字段,不是可选。
- 进程名/userId 从 `manifest/procs-*.tsv` 查(`logcat-around-pid.py` 会自动解析并报冲突)。

## 关注点
- **进程生命周期**:zygote fork、`am_proc_start`/`am_proc_died`;native 进程看 init service start/exited。
- **跨 pid 接续**:进程 crash 重启换 pid,追踪同一进程必须查对照表跨 pid 接续;
  查表若报**同 pid 双名冲突**,显式上报后再继续。
- **焦点/窗口转移**:`input_focus`、`wm_` 事件。
- **谁启动了 Activity**:优先取 `ActivityTaskManager: START u<id> ... from uid` 行的
  **callingUid**;`am_create_activity`(events)提供组件/任务维度,二者互补闭合因果。
  callingPid 一般不可得,勿承诺;勿用时序吻合代替调用方证据。
- **跨进程调用**:经 `am_*`/`wm_*` 事件与 ANR trace 栈做**间接配对**;
  binder 事务默认不打日志,**不承诺 binder 级追踪**。
- **events buffer 结构化**:`am_*`/`wm_*` 是固定 schema(tag 为数字,经 vendor/aosp_event_log_tags.py
  翻译;msg 为元组),按字段提取 pid/userId/组件/原因码,**禁止当自由文本读**。
  am_proc_start 字段序:`[User, PID, UID, ProcName, Type, Component]`;am_proc_died:`[User, PID, ProcName]`。

## 时间与空洞
- 时间窗计算**避让** `manifest/clock-*.tsv` 的跳变点(开机校时回退)与静默区间(suspend 前跳);
  跳变两侧时间戳不可直接比较。
- **时序空洞**(预期事件缺失)可作证据,**但先对照 `loss-*.tsv` 与静默区间**;
  缺失落在损耗/静默区间内 → **不作证据(R13)**。可入账的空洞记入 ledger 待验证区。

## 制品解析(取证范围含 trace/tombstone/dropbox 时为必做项)
按 artifacts.md 提取关键结构,关键行以**制品 `文件:行号`** 入账,**与时间线并列呈现,不混入时间线条目**。
对 ANR/native crash,制品往往才是主证据,logcat 只是入口线索。
