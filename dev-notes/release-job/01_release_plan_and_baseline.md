# Release 总体工作规划与基线状态报告

> **文档属性**：项目交付与 Release 准备总体工作规划（内部追踪档案）  
> **归档位置**：`dev-notes/release-job/01_release_plan_and_baseline.md`  
> **建立日期**：2026-10-15  
> **当前开发分支**：`physics-agent`  
> **目标发布分支**：`physics-agent-release`（待本分支全部工作就绪后新建并向 `main` 提交 PR）  

---

## 一、 交付背景与核心目标

本项目现已完成算法研发、多轮系统自测与竞赛材料的归档工作。为使本项目能够作为一个**通用、健壮、对宿主零侵入、开箱即用的开源科学研究智能体系统**正式交付并对外发布，现进入 Release 专项准备阶段。

### 核心交付目标
1. **资产解耦与清晰边界**：
   - 将开发过程中的历史草稿、竞赛专用文件留在 `dev-notes/` 中归档，确保对外发布的 `physics-agent/` 与项目根目录只保留用户真正需要的代码、依赖、技能与规范文档。
2. **审查对 AGH 主体的零侵入性**：
   - 对照 `main` 与 `upstream/main` 逐行审查 `packages/` 与根目录配置改动，明确哪些属于通用 Bug 修复，哪些属于业务扩展，确保底座代码干净，方便未来无缝同步官方最新资产。
3. **面向 GitHub Release 的免门槛一键安装与环境自检**：
   - 考虑终端用户可能未配置 Node.js、pnpm、Python 或科学计算依赖的环境痛点；
   - 提供开箱即用的安装自检脚本，支持自动检测环境缺失项、提供向导式修复指引、支持自定义安装路径，并实现安装后两步内极速启动。
4. **高质量项目根目录 README.md 与配套文档体系**：
   - 重构根目录 `README.md`，替代官方底座 README 作为 GitHub 主页展示；
   - 采用纯中文、平实严谨、不吹嘘、无黑话的学术开源风格；
   - 彻底脱敏：不提及任何具体竞赛题名、不暴露开发者个人隐私信息、不包含临时开发黑话，客观展现项目核心功能与架构。
5. **通用的项目独立演示案例（Demo）**：
   - 准备一套通用、易于复现的经典物理分析 Demo，配备独立的运行与结果解读说明。

---

## 二、 Release 阶段七步执行路线图

```
Step 1: 初始化 Release 追踪体系并冻结基线状态（dev-notes/release-job/01）
   │
   ▼
Step 2: 对照 main 分支逐行排查 AGH 主体文件改动，出具零侵入审计报告（dev-notes/release-job/02）
   │
   ▼
Step 3: 审查 dev-notes 资产，识别并迁移 Release 核心资产至 physics-agent/
   │
   ▼
Step 4: 设计并实现面向 GitHub Release 的一键安装与环境自检程序（跨平台、支持自定义路径）
   │
   ▼
Step 5: 构建脱敏的通用独立 Demo 案例与指引文档
   │
   ▼
Step 6: 编写根目录正式 README.md（纯中文开源主页）及配套模块文档
   │
   ▼
Step 7: 验收全部 Release 资产并在 dev-notes/release-job/03 归档总结，准备检出 release 分支
```

---

## 三、 当前代码库基线状态（Baseline Snapshot）

### 1. 分支与远端配置
- 当前工作分支：`physics-agent`（包含全部最新研发、门禁与自测成果）；
- 远端仓库：
  - `origin`: `https://github.com/VirtuwiseZ/agnes-harness.git`（开发者主 fork）；
  - `upstream`: `https://github.com/AgnesAI-Labs/agnes-harness.git`（AGH 官方上游仓库）。

### 2. 变更文件分布总览（相对于 `main` 分支）
- **核心新增资产**（完全自包含，无侵入）：
  - `.agh/skills/`：10 个符合宿主规范的标准原生工作区技能；
  - `physics-agent/`：包含 `hooks/`（门禁工具链）、`knowledge/`（方法论知识库）、`plugins/`（原生路由器插件）与 `third_party/portable-runtime/`（便携运行时）；
  - 启动与同步脚本：`start-test-runner.ps1`、`sync-and-build-test.ps1`、`一键启动测试环境.bat`；
- **涉及官方主体的变动文件**（需重点审查）：
  - `.gitignore`（增补了自测大体积日志与 Python 缓存忽略规则）；
  - `packages/core/src/step/tool-args.ts`（修复参数包装嵌套 bug）；
  - `packages/core/src/step/inference.ts` & `reentry.ts`（引入工具参数解包防护）；
  - `packages/base/extensions/loop-hygiene/src/verifier.ts`（修复中间轮次验证死锁）；
  - `packages/web/` 与 `packages/web-units/`（增强 Trace URL 深度跳转与 BroadcastChannel 跨标签页通信）。
