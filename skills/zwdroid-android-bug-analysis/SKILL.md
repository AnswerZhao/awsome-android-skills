---
name: zwdroid-android-bug-analysis
description: >-
  Android/AAOS bug 根因分析(RCA)工作流。当用户提供 logcat 日志(及 ANR
  trace/tombstone/dropbox 制品)要求定位问题、分析崩溃/ANR/重启/焦点错乱/
  卡顿/泄漏,或追踪某进程/某时间点发生了什么时使用。触发词:logcat、
  日志分析、根因、RCA、ANR、crash、tombstone、watchdog、AAOS、
  CarService、VHAL、lmk。不处理日志抓取/解压/分包;不解析 kernel
  log/pstore(硬重启类到此为界);帧级卡顿归因需 perfetto,不在覆盖内;
  仅支持 threadtime 格式。
---

# zwdroid-android-bug-analysis — Android/AAOS 根因分析工作流

有纪律的人机协作:**用户是法官,你是检察官兼调查员**。你的产出是一条从症状回溯到
责任组件/代码位置的**证据链**,或一份"证据不足 + 补抓建议"。没有证据链的结论不输出。

日志总量(单文件约 10 万行,常跨多文件)远超 context。因此核心方法是:
**脚本做廉价的结构过滤,你只做昂贵的语义判断;一切结论落盘到 ledger 对抗 context 腐烂。**

## 先做:读目标项目的运行时 CLAUDE.md「配置区」
环境事实(时间戳格式、文件命名、源码目录是否配置、各预算参数)都在那里,不要凭记忆假设。
项目还没有这份文件 → 从 `${CLAUDE_SKILL_DIR}/references/runtime-claude-template.md` 复制一份到
项目根,和用户确认环境事实后再开始(脚本侧默认值在 `scripts/config.py`,与模板一致)。
源码目录未配置 → **源码开关默认关**,走日志-only 路径。

## 工作区
每个 bug 一个工作区(建在目标项目内,不在 skill 目录里),从模板复制:
```
cp -r ${CLAUDE_SKILL_DIR}/workspace-template rca-workspace/<bug-id>
```
结构:`ledger.md`(唯一真相源,只有你能写)· `manifest/`(ingest 索引)· `timeline.md` ·
`slices/` · `findings/` · `report.md`。**context 被压缩或换新会话后,读 ledger.md 即可恢复续跑。**

## 脚本(Python3 标准库;详见 references)
一律以 `python3 ${CLAUDE_SKILL_DIR}/scripts/<name>.py` 调用(相对路径会解析到项目根而非 skill 目录):
| 脚本 | 用途 |
|------|------|
| `rca-ingest.py <log-dir> --out <manifest>` | 一次性索引:boot session/文件统计/进程-pid 表/时钟跳变/损耗区间 |
| `log-batch.py <anchor> <radius> --manifest <dir>` | session 内产出 batch 文件清单(不跨 session) |
| `logcat-window.py <start> <dur> --manifest <dir> [--preset\|--tags] [--level] --files ...` | 通道一:时间窗+tag/level 切片 |
| `scream-scan.py <files...>` | 通道二:异常信号扫描(折叠去重、带 loss 段) |
| `logcat-around-pid.py <pid> --manifest <dir> --files ...` | 某进程上下文,跨 pid 接续 |
| `aaos-grep.py <pattern>` | 源码搜索(仅源码开关开时) |

脚本铁律:输入只接受**原始日志**(喂切片会报错);输出每行带 `原始文件:原始行号|` 前缀;
过滤先解析字段不做纯文本 grep;引用证据一律回指原始 `文件:行号`,不引切片坐标。

## 主状态机

```
S0 接收 → S1 Triage → S2 Locate ⇄ S3 Reconstruct → S4 Hypothesize
                          ↓(穷尽)              ↑(候选耗尽)   ↓
                       S6b 证据不足           源码开关?——关→ S6a 结论(形态 B)
                                                        └开→ S5 Verify → S6a(形态 A)/证伪回 S4
```

- **S0 接收**:复述用户输入(时间/现象/线索),**全部标注为假设**入账 ledger(R8);复制工作区;
  跑 `rca-ingest.py` 产出 manifest(仅首次)。
- **S1 Triage**:按 references/presets.md 路由表定 bug 类型、时间剖面(fast/slow)、取证范围、tag preset。
  取证范围含制品(anr/tombstone/dropbox,按原生文件夹名查找)时先确认文件存在。
- **S2 Locate**(核心,详见 references/locate.md):查 manifest 两步定位锚点 → batch → **双通道**
  (通道一 preset 切片建 timeline;通道二 scream-scan 扫异常,**两通道并列不合并** R10)→
  锚点 sanity check(三态:三对齐命中 / 部分命中→锚点校正 / 无特征→查损耗区间后策略切换,
  策略切换 ≤2 次)→ 语义匹配 → 未果则 session 内扩展(禁止跨 session R12);穷尽或达
  {{MAX_ROUNDS}} → S6b。找到"哪个进程何时何行为致何结果"→ explore 精定位(预算硬顶
  {{SLICE_LINE_CAP}},超限收紧 tag 禁止扩窗 R6)。
- **S3 Reconstruct**(references/reconstruct.md):精确窗口重建事件序列写 timeline.md
  (每条带 userId/进程:pid + 证据 file:line,≤一屏);取证范围含制品则**解析制品为必做项**
  (ANR trace 主线程栈/锁链、tombstone backtrace);跨 pid 查对照表接续;时序空洞可作证据,
  **但先排除 manifest 损耗/静默区间**(R13)。
- **S4 Hypothesize**(references/hypothesize.md):生成 **2-3 个**候选根因(禁 1 禁 >3),每个带
  支持/反对证据、概率、验证成本,写 ledger。源码开关关 → 最高优先级且有日志证据支撑者
  直接 → S6a;开 → 选定假设 → S5。
- **S5 Verify**(条件,references/verify.md):**仅源码开关开时进入**。先书面写"若假设为真源码
  中应有什么",再 `aaos-grep.py` 实证,任何类/方法/路径入结论前必须有 grep 命中(R2)。
  证实→S6a 形态 A;证伪→S4;无法判定→该候选冻结回 S4。
- **S6a 结论**:输出 report.md。**形态 B(默认)**=责任组件+触发条件+行为,指针为日志/制品
  file:line,闭源组件指向接口+违约行为;**形态 A(源码开关开)**=落到源码 path:line + 修复方向。
- **S6b 证据不足**(合法终态,R7):已确认事实 + 已排除项 + 证据缺口 + **补抓建议** + 下一步。

每次状态转移后执行 **ledger 轮次协议**(references/ledger.md §轮次协议):新证据入账、
**显式声明本轮丢弃项**(排除的候选/无关切片不再参与推理)、更新 next_action(R9)。

## 红线(HARD RULES,优先级最高,逐条不可绕过)
- **R1** 没有证据链的结论不输出;每个结论可回溯到 `文件:行号`(日志/制品/源码)。
- **R2** 源码引用必须 grep 实证,禁止凭记忆引用类/方法/路径。(源码开关开时绝对生效)
- **R3** 描述→日志映射三步走:先写预期签名 → 再 grep → 再三对齐(时间/包名/参数),禁跳步。
- **R4** ledger 单一写者:仅主 agent 可写。
- **R5** subagent 返回指针不返回散文:原文+行号落盘 findings,返回只含结论+路径。
- **R6** explore 预算硬顶 {{SLICE_LINE_CAP}}:超限收紧 tag,禁止扩窗。
- **R7** "证据不足+补抓建议"是合法终态,禁止硬凑结论。
- **R8** 用户线索一律按假设入账,非事实。
- **R9** 每轮执行轮次协议,被排除项不再参与推理。
- **R10** 双通道(时间线/尖叫扫描)结果并列呈现,永不合并、不互相覆盖。
- **R11** 溯源:一切证据引用回指**原始** `文件:行号`;禁止引用派生切片自身坐标。
- **R12** batch 扩展与采样禁止静默跨越 boot session 边界;跨 session 仅在重启类 bug 且 ledger 显式声明。
- **R13** 缺失不即证据:以"日志中不存在 X"为据前,先对照 manifest 损耗区间与静默区间;
  落在区间内则不得作为证据,也不得据此触发策略切换或中断。

## references(进入对应状态才读)
`locate.md` · `reconstruct.md` · `hypothesize.md` · `verify.md` · `artifacts.md` ·
`ledger.md` · `presets.md`。冲突裁决:**红线 > 本文件 > references > 自行判断**。
