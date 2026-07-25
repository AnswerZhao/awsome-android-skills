# awsome-android-skills

Agent skills for Android developers — Android/AAOS 诊断、逆向与日志分析场景的开源 Claude Code skills。

所有 skill 均使用 `zwdroid-` 前缀命名。

## 技能列表

| 名称 | 用途 |
|---|---|
| [`zwdroid-android-bug-analysis`](skills/zwdroid-android-bug-analysis/) | Android/AAOS bug 根因分析（RCA）工作流：状态机 + 证据链纪律，boot session/时钟跳变/日志损耗感知的索引与切片，双通道定位，ANR trace/tombstone/dropbox 制品解析，ledger 落盘抗上下文压缩。 |
| [`zwdroid-android-jadx`](skills/zwdroid-android-jadx/) | 使用 jadx 反编译 Android APK / dex / jar / aar；将 logcat 与源码交叉引用以定位 Bug。 |
| [`zwdroid-android-logcat-analysis`](skills/zwdroid-android-logcat-analysis/) | 解析 Android/AAOS logcat（threadtime 格式）；结构化事件索引、时间线、异常信号检测，以及 playbook 驱动的 framework 问题诊断。 |

## 使用方式

本仓库的 `.claude/skills/` 会在你在仓库目录内启动 Claude Code 会话时，作为**项目级技能**自动加载：

```bash
git clone https://github.com/AnswerZhao/awsome-android-skills
cd awsome-android-skills
# 在此目录打开 Claude Code — 技能立即可用
```

如需**全局**可用（任何项目都能使用），将 skill 软链到用户级技能目录：

```bash
ln -s "$PWD/skills/zwdroid-android-jadx" ~/.claude/skills/zwdroid-android-jadx
```

部分 skill 有一次性的本机依赖安装，请按各自 `SKILL.md` 的 *Setup* 段执行。

## 仓库结构

- **`skills/<name>/`** — skill 真正源码。
- **`.claude/skills/<name>/`** — 软链接指向 `../../skills/<name>/`，在本仓库内由 Claude Code 自动加载。
- **`devdoc/<name>/`** — 每个 skill 的开发资料（规格、待办、评估数据）。已 gitignore。

## 许可证

待定 — 考虑 MIT 或 Apache-2.0。
