# Awesome Android Skills [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> [English](README.md) | 中文

> Android 开发的 agent skill 精选集 —— 收录 Android 团队官方 skill 与精选社区 skill。

Agent Skill 是模块化的 `SKILL.md` 指令文件，教会 AI 编码助手（Claude Code、Gemini CLI、Cursor 等）完成特定 Android 任务 —— 按需加载，始终基于最新最佳实践。

## 目录

- [官方 Skills](#官方-skills) —— 由 Android 团队维护，见 [android/skills](https://github.com/android/skills)
  - [构建](#构建) · [相机](#相机) · [端侧 AI](#端侧-ai) · [开发工具](#开发工具) · [身份认证](#身份认证) · [Jetpack Compose](#jetpack-compose) · [导航](#导航) · [性能](#性能) · [Play](#play) · [性能分析器](#性能分析器) · [安全](#安全) · [系统](#系统) · [测试](#测试) · [Wear](#wear) · [XR](#xr)
- [社区 Skills](#社区-skills) —— 本仓库收录
- [使用本仓库的 Skills](#使用本仓库的-skills)
- [贡献](#贡献)

## 官方 Skills

由 Android 团队维护 → [github.com/android/skills](https://github.com/android/skills)。可通过 `android` CLI 安装，或将对应 skill 目录复制到你的 agent 技能目录。

### 构建

- [agp-9-upgrade](https://github.com/android/skills/tree/main/build/agp/agp-9-upgrade) —— 将 Android 项目升级/迁移到 Android Gradle Plugin 9。

### 相机

- [camerax](https://github.com/android/skills/tree/main/camera/camerax) —— CameraX 相机开发技术指导。

### 端侧 AI

- [appfunctions](https://github.com/android/skills/tree/main/device-ai/appfunctions) —— 分析应用、识别关键用户流程并通过 AppFunctions 暴露。

### 开发工具

- [android-cli](https://github.com/android/skills/tree/main/devtools/android-cli) —— 安装与使用 `android` CLI：创建项目、在设备上运行应用、管理工具链。

### 身份认证

- [verified-email](https://github.com/android/skills/tree/main/identity/verified-email) —— 实现验证邮箱获取的完整工作流。

### Jetpack Compose

- [adaptive](https://github.com/android/skills/tree/main/jetpack-compose/adaptive) —— 让 UI 适配不同屏幕尺寸与设备形态。
- [migrate-xml-views-to-jetpack-compose](https://github.com/android/skills/tree/main/jetpack-compose/migration/migrate-xml-views-to-jetpack-compose) —— XML View 迁移到 Jetpack Compose 的结构化工作流。
- [styles](https://github.com/android/skills/tree/main/jetpack-compose/theming/styles) —— 在应用中集成 Jetpack Compose Styles API。

### 导航

- [navigation-3](https://github.com/android/skills/tree/main/navigation/navigation-3) —— 安装并迁移到 Jetpack Navigation 3。

### 性能

- [r8-analyzer](https://github.com/android/skills/tree/main/performance/r8-analyzer) —— 分析构建文件与 R8 keep 规则，找出冗余与混淆裁剪问题。

### Play

- [engage-sdk-integration](https://github.com/android/skills/tree/main/play/engage-sdk-integration) —— 集成、调试并解决 Play Engage SDK 的实现问题。
- [play-billing-library-version-upgrade](https://github.com/android/skills/tree/main/play/play-billing-library-version-upgrade) —— 将项目升级/迁移到更新的 Play Billing Library 版本。
- [play-policy-insights](https://github.com/android/skills/tree/main/play/play-policy-insights) —— 按 Google Play 政策域审计应用；交叉比对静态代码分析与 Play Console 声明，生成合规报告。

### 性能分析器

- [perfetto-sql](https://github.com/android/skills/tree/main/profilers/perfetto-sql) —— 将自然语言问题翻译成合法的 PerfettoSQL 查询。
- [perfetto-trace-analysis](https://github.com/android/skills/tree/main/profilers/perfetto-trace-analysis) —— 分析 Perfetto trace，定位延迟、内存或卡顿问题的根因。

### 安全

- [android-intent-security](https://github.com/android/skills/tree/main/security/android-intent-security) —— 审计与加固 Android Intent 使用的最佳实践。

### 系统

- [edge-to-edge](https://github.com/android/skills/tree/main/system/edge-to-edge) —— 将 Jetpack Compose 应用迁移到自适应 edge-to-edge 显示。

### 测试

- [testing-setup](https://github.com/android/skills/tree/main/testing/testing-setup) —— 分析项目并为原生 Android 应用制定测试策略。

### Wear

- [wear-compose-m3](https://github.com/android/skills/tree/main/wear/wear-compose-m3) —— Wear OS Compose Material3 开发专家指导。

### XR

- [display-glasses-with-jetpack-compose-glimmer](https://github.com/android/skills/tree/main/xr/display-glasses-with-jetpack-compose-glimmer) —— 使用 Jetpack Compose Glimmer 为显示眼镜开发投射式 Android XR 应用的指南。

## 社区 Skills

本仓库收录的 skill（源码在 [`skills/`](skills/)），由 [zwdroid](https://github.com/zwdroid) 编写：

- [zwdroid-android-bug-analysis](skills/zwdroid-android-bug-analysis/) —— Android/AAOS bug 根因分析（RCA）工作流：状态机 + 证据链纪律，boot session/时钟跳变/日志损耗感知的索引与切片，双通道定位，ANR trace/tombstone/dropbox 制品解析。
- [zwdroid-android-jadx](skills/zwdroid-android-jadx/) —— 使用 jadx 反编译 Android APK / dex / jar / aar；将 logcat 与源码交叉引用以定位 Bug。
- [zwdroid-android-logcat-analysis](skills/zwdroid-android-logcat-analysis/) —— 解析 Android/AAOS logcat（threadtime 格式）；结构化事件索引、时间线、异常信号检测，playbook 驱动的 framework 问题诊断。

## 使用本仓库的 Skills

本仓库的 `.claude/skills/` 会在你在仓库目录内启动 Claude Code 会话时，作为**项目级技能**自动加载：

```bash
git clone https://github.com/AnswerZhao/awsome-android-skills
cd awsome-android-skills
# 在此目录打开 Claude Code —— 技能立即可用
```

如需**全局**可用（任何项目都能使用），将 skill 软链到用户级技能目录：

```bash
ln -s "$PWD/skills/zwdroid-android-jadx" ~/.claude/skills/zwdroid-android-jadx
```

## 贡献

欢迎提交 issue 提议新的社区 skill 或修正。添加条目时请遵循 awesome 列表格式：`- [名称](链接) —— 一句话描述。`

## 许可证

待定 —— MIT 或 Apache-2.0。官方 skills 由 Google 按 [android/skills](https://github.com/android/skills/blob/main/LICENSE.txt) 中的条款授权。
