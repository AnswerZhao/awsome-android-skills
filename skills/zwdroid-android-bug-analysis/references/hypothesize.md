# hypothesize.md — S4 假设生成与剪枝

## 强制规则
- 每次生成 **2-3 个**候选根因:**禁止只提 1 个**(确认偏误)、**禁止超过 3 个**(发散)。
- 每个候选写全:`陈述 | 支持证据[指针] | 反对证据 | 概率(高/中/低) | 验证成本(读什么、多少行)`。
- 排序键:**概率 × 验证成本倒数**——先验证"高概率且便宜"的。写入 ledger 假设区后才可进 S5(或源码开关关时直接选顶为结论)。
- 主动找**反对证据**(对抗确认偏误):对每个候选问"什么日志若存在就能证伪它?去找它。"

## 根因模式库(识别特征 → 验证方法)
随案例迭代补全。当前 AAOS/AOSP 高频模式:

1. **生命周期错序 / 竞态**。特征:两事件预期有序却颠倒(如 onDestroy 后仍收到 callback;
   user 切换未完成就触发 restore)。验证:timeline 里对齐两事件精确时间戳 + pid,确认时序;
   查是否缺少"完成"信号(空洞,先排除损耗 R13)。
2. **资源泄漏 / 累积**(slow)。特征:GC 频繁、`am_meminfo` 走高、lmk 逐渐升级、句柄/线程数增长。
   验证:采样建趋势线找拐点;定位泄漏起点进程。
3. **配置 / 状态错乱**。特征:行为与配置项不符;多用户下 userId 上下文取错。
   验证:比对配置读取日志与实际生效值;检查 userId 字段(AAOS user 0 vs 10+)。
4. **HAL / VHAL 超时**(闭源边界)。特征:hwbinder 调用无返回、`VehicleHal` 超时、CarService 降级。
   验证:定位请求与应有响应的时间差;结论多为**形态 B**(接口契约违约,拿不到闭源 file:line)。
5. **Binder 死亡 / 断连**。特征:`binderDied`、`Transaction failed`、服务端进程 died。
   验证:对照 manifest 进程-pid 表确认服务端存亡;找 DeathRecipient 触发。
6. **Watchdog / 主线程阻塞**。特征:`WATCHDOG`、SystemServer 重启、锁等待。
   验证:看 ANR trace/watchdog dump 的主线程栈与锁持有链(制品,见 artifacts.md)。
7. **权限 / SELinux 拒绝**。特征:`avc: denied`、SecurityException。
   验证:确认被拒操作是否即失败主因(selinux_denial 噪声极大,见「已知坑」)。
8. **焦点 / 窗口转移错误**。特征:`input_focus`、`wm_` 事件、Activity 意外 finish/restore。
   验证:重建窗口/焦点转移序列,定位非预期的 start/finish 触发者。
9. **进程被杀重启循环**。特征:同进程短时间多次 `am_proc_start`/`am_proc_died`(跨 pid);
   native 进程看 init service exited。验证:manifest 进程-pid 表看重启频次与触发方。
10. **多用户切换副作用**。特征:`am_switch_user`/user_switch 后大量进程重建、task 自动恢复
    (`task_auto_restored`)。验证:对齐切换完成时间点与副作用事件;检查是否有"刚切换"守卫缺失。

## 输出
候选写入 ledger"当前假设"表。源码开关关:选顶部候选,若有日志证据链支撑 → S6a 形态 B。
源码开关开:选顶部 → S5 验证。候选全部被排除或冻结 → 回 S2 继续定位。
