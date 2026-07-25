# 维护说明（非运行时）

> 本文件是给 **skill 维护者** 看的开发流程，不属于 logcat 分析的运行时指令，故从 `SKILL.md` 剥离。
> 运行时 agent 在分析日志时**不需要**读本文件。

## 何时追加 TODO

发现 SKILL 本身的盲区或问题时，追加到 `TODO.md` 的"待处理(MVP 后)"段（参考 CLAUDE.md 既定模板）。两个高频触发点：

1. **步骤 1 后查 sources.json.unknown_event_tags**
   - 列表中出现"看起来与本次问题相关、但字典未覆盖"的 tag → 追加 TODO："event-log-tags 字典缺失 tag:xxx（步骤 X，YYYY-MM-DD 真实 case 中遇到）"
   - **不要为此中断分析**——继续走 playbook，结束后再写

2. **步骤 4 playbook 下钻时的脚本/规则异常**
   - detect_signals 误报 / 漏报某种已知模式
   - 某 query 脚本输出格式不符合 playbook 预期
   - 某 playbook 的判断准则在新 case 中不成立
   - → 追加 TODO，附带 `source_file:line_no` 证据，便于后续修

> TODO.md 中的条目由用户决定何时实施。**MVP 阶段不要直接改算法/规则去"修复"这些发现**——按 CLAUDE.md 的"单向前进，不回头重构"原则。
