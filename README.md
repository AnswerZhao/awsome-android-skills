# Awesome Android Skills [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> English | [中文](README.cn.md)

> A curated collection of agent skills for Android development — official skills from the Android team plus hand-picked community skills.

Agent Skills are modular `SKILL.md` instruction files that teach AI coding agents (Claude Code, Gemini CLI, Cursor, etc.) how to perform specific Android tasks — loaded on demand, grounded in current best practices.

## Contents

- [Official Skills](#official-skills) — maintained by the Android team at [android/skills](https://github.com/android/skills)
  - [Build](#build) · [Camera](#camera) · [Device AI](#device-ai) · [DevTools](#devtools) · [Identity](#identity) · [Jetpack Compose](#jetpack-compose) · [Navigation](#navigation) · [Performance](#performance) · [Play](#play) · [Profilers](#profilers) · [Security](#security) · [System](#system) · [Testing](#testing) · [Wear](#wear) · [XR](#xr)
- [Community Skills](#community-skills) — included in this repo
- [Using the Skills in This Repo](#using-the-skills-in-this-repo)
- [Contributing](#contributing)

## Official Skills

Maintained by the Android team → [github.com/android/skills](https://github.com/android/skills). Install via the `android` CLI or copy the skill directory into your agent's skills folder.

### Build

- [agp-9-upgrade](https://github.com/android/skills/tree/main/build/agp/agp-9-upgrade) — Upgrade or migrate an Android project to Android Gradle Plugin 9.

### Camera

- [camerax](https://github.com/android/skills/tree/main/camera/camerax) — Technical guidance for Android camera development with CameraX.

### Device AI

- [appfunctions](https://github.com/android/skills/tree/main/device-ai/appfunctions) — Analyze an app to identify key user workflows and expose them via AppFunctions.

### DevTools

- [android-cli](https://github.com/android/skills/tree/main/devtools/android-cli) — Install and use the `android` CLI: create projects, run apps on devices, manage the toolchain.

### Identity

- [verified-email](https://github.com/android/skills/tree/main/identity/verified-email) — Complete workflow for implementing verified email retrieval.

### Jetpack Compose

- [adaptive](https://github.com/android/skills/tree/main/jetpack-compose/adaptive) — Make or update UI so it adapts to different screen sizes and form factors.
- [migrate-xml-views-to-jetpack-compose](https://github.com/android/skills/tree/main/jetpack-compose/migration/migrate-xml-views-to-jetpack-compose) — Structured workflow for migrating XML Views to Jetpack Compose.
- [styles](https://github.com/android/skills/tree/main/jetpack-compose/theming/styles) — Integrate the Jetpack Compose Styles API into an app.

### Navigation

- [navigation-3](https://github.com/android/skills/tree/main/navigation/navigation-3) — Install and migrate to Jetpack Navigation 3.

### Performance

- [r8-analyzer](https://github.com/android/skills/tree/main/performance/r8-analyzer) — Analyze build files and R8 keep rules to find redundancies and shrinking issues.

### Play

- [engage-sdk-integration](https://github.com/android/skills/tree/main/play/engage-sdk-integration) — Integrate, debug, and resolve Play Engage SDK implementation issues.
- [play-billing-library-version-upgrade](https://github.com/android/skills/tree/main/play/play-billing-library-version-upgrade) — Upgrade or migrate a project to a newer Play Billing Library version.
- [play-policy-insights](https://github.com/android/skills/tree/main/play/play-policy-insights) — Audit an app against Google Play policy domains; cross-references static analysis with Play Console declarations into a compliance report.

### Profilers

- [perfetto-sql](https://github.com/android/skills/tree/main/profilers/perfetto-sql) — Translate natural-language questions into valid PerfettoSQL queries.
- [perfetto-trace-analysis](https://github.com/android/skills/tree/main/profilers/perfetto-trace-analysis) — Analyze Perfetto traces to root-cause latency, memory, or jank issues.

### Security

- [android-intent-security](https://github.com/android/skills/tree/main/security/android-intent-security) — Best practices for auditing and hardening Android Intent usage.

### System

- [edge-to-edge](https://github.com/android/skills/tree/main/system/edge-to-edge) — Migrate a Jetpack Compose app to adaptive edge-to-edge display.

### Testing

- [testing-setup](https://github.com/android/skills/tree/main/testing/testing-setup) — Analyze a project and create a testing strategy for native Android apps.

### Wear

- [wear-compose-m3](https://github.com/android/skills/tree/main/wear/wear-compose-m3) — Expert guidance for Wear OS Compose Material3 development.

### XR

- [display-glasses-with-jetpack-compose-glimmer](https://github.com/android/skills/tree/main/xr/display-glasses-with-jetpack-compose-glimmer) — Guidelines for building projected Android XR apps for display glasses with Jetpack Compose Glimmer.

## Community Skills

Skills included in this repo (source in [`skills/`](skills/)), authored by [zwdroid](https://github.com/zwdroid):

- [zwdroid-android-bug-analysis](skills/zwdroid-android-bug-analysis/) — Android/AAOS bug 根因分析（RCA）工作流：状态机 + 证据链纪律，boot session/时钟跳变/日志损耗感知的索引与切片，双通道定位，ANR trace/tombstone/dropbox 制品解析。
- [zwdroid-android-jadx](skills/zwdroid-android-jadx/) — 使用 jadx 反编译 Android APK / dex / jar / aar；将 logcat 与源码交叉引用以定位 Bug。
- [zwdroid-android-logcat-analysis](skills/zwdroid-android-logcat-analysis/) — 解析 Android/AAOS logcat（threadtime 格式）；结构化事件索引、时间线、异常信号检测，playbook 驱动的 framework 问题诊断。

## Using the Skills in This Repo

The repo's `.claude/skills/` is auto-loaded by Claude Code as **project-scoped skills** when you start a session inside the repo:

```bash
git clone https://github.com/AnswerZhao/awsome-android-skills
cd awsome-android-skills
# Open Claude Code here — skills are immediately available
```

For **global** availability, symlink a skill into your user-level skills dir:

```bash
ln -s "$PWD/skills/zwdroid-android-jadx" ~/.claude/skills/zwdroid-android-jadx
```

## Contributing

Suggestions welcome — open an issue to propose new community skills or fixes. When adding an entry, follow the awesome-list format: `- [name](link) — one-line description.`

## License

TBD — MIT or Apache-2.0. Official skills are licensed by Google under the terms in [android/skills](https://github.com/android/skills/blob/main/LICENSE.txt).
