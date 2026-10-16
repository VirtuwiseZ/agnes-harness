# 针对已有 AGH 用户的最小增量交付指南 (Minimal Add-on Guide)

本文档面向已经通过官方仓库（`https://github.com/AgnesAI-Labs/agnes-harness`）或其他渠道安装了 Agnes Harness (AGH) 的用户，介绍如何将 **AI 物理科研工作站 (Physics Agent)** 作为轻量增量插件（Add-on）引入现有的 AGH 根目录中，确保不与已有的第三方插件、技能及配置发生冲突。

---

## 一、 为什么选择“最小增量交付”？

| 交付类型 | 包含内容与体积 | 适用对象 | 优缺点对比 |
| :--- | :--- | :--- | :--- |
| **全量预构建发行包**<br>(`AI_Physics_Agent_...zip`) | 包含预编译的 AGH 底座、本地 Node 运行时模块与全量资产。<br>体积：**约 34.8 MB** | 适合尚未安装过 AGH 的全新电脑用户或独立测试机。 | • 优势：开箱即用，无需配置底座；<br>• 缺点：体积较大，若解压至已有 AGH 目录会覆盖其源码。 |
| **最小增量插件包 (Add-on)**<br>(`physics-agent-addon-v0.1.0.zip`) | **仅包含** `physics-agent/` 业务套件、10 个物理技能模板及一键注册脚本。<br>体积：**约 0.28 MB (285 KB)** | **适合已从官方克隆或安装了 AGH 的用户。** | • 优势：体积分发小，不修改 AGH 平台源码，不影响用户已有的其它第三方技能；<br>• 缺点：要求目标计算机已具备可运行的 AGH 底座。 |

---

## 二、 避免与官方及第三方内容冲突的隔离机制

在实际使用中，很多 AGH 用户已在自己的工作区 `.agh/skills/` 中存放了其他开发者编写的技能（如文本翻译、代码审查、天气查询等）。为了避免覆盖既有资产，本项目确立了**非破坏性增量导入规范**：

1. **子目录独立命名空间隔离**：
   - 物理智能体的 10 个技能统一采用 `physics-*` 明确前缀（如 `physics-agent-orchestrator/`、`physics-pipeline/`、`physics-defense-lines/` 等），分别部署在 `.agh/skills/` 下各自独立的专属子文件夹内；
2. **保护已有第三方技能**：
   - 注册程序（`register_addon.ps1`）在执行时，首先扫描用户 `.agh/skills/` 目录；
   - 凡是不属于上述 10 个物理技能子目录的既有文件夹，**程序一律标记为 `[PROTECTED]` 并保留，不删除、不重命名用户的非物理技能**；
3. **独立的业务资产存放**：
   - 所有的物理门禁程序（`hooks/`）、物理方法论与官方基准参考数据集（`knowledge/`）、任务模板（`runtime/`）全部封装在 `physics-agent/` 独立根目录中，不散落到 AGH 平台代码或系统根目录下。

---

## 三、 AGH 基座版本检测与兼容性管理

不同用户本地克隆的 AGH 官方底座版本可能存在差异（如早期预览版、近期主分支版本或定制版）。为此，程序提供了**基座版本检测与特性检查功能**：

### 1. 自动检测项与功能检查矩阵 (Feature Probing)
注册程序在执行时，会自动分析目标 AGH 目录的 `package.json`、Git Commit 散列以及平台核心代码，输出以下四项兼容性指标：

| 检测维度 | 探测位置与原理 | 兼容性影响与降级应对说明 |
| :--- | :--- | :--- |
| **基座基础版本** | `package.json` (`name`, `version`) & `.git/HEAD` | 确认是否为合法的 AGH 仓库根目录，识别 Git 提交散列。 |
| **参数解包防护**<br>(Parameter Unwrap Guard) | `packages/core/src/step/tool-args.ts`<br>探测是否包含 `unwrapToolArgs` | • **已具备**：底层自动解开第三方代理对工具参数包裹的 `{ input: "..." }` 外壳；<br>• **未具备（官方原版）**：系统在 `physics-pipeline` 技能中已明确约束大模型输出扁平 `command: "..."` 顶层参数，通过提示词规范实现兼容。 |
| **Trace 深度跳转**<br>(Trace URL Deep-Jump) | `packages/web-units/src/trace.ts`<br>探测是否包含 `selectBySeq` 与事件监听 | • **已具备**：生成的 HTML 报告支持正文蓝链平滑滚动定位并高亮对应 Trace 卡片；<br>• **未具备（官方原版）**：报告右侧依然拥有独立的离线会话甘特图与时序面板，支持离线查验。 |
| **CLI 核心构建状态**<br>(CLI Bundle Status) | 检查 `packages/cli/dist/local/agnes.mjs` 是否已编译 | • **已编译**：可直接运行物理分析；<br>• **未编译**：程序明确提示用户在终端执行 `pnpm --filter @agnes/cli run build:local` 完成底座编译。 |

检测完成后，程序会自动将兼容性体检结果持久化保存至 `physics-agent/runtime/agh_compatibility_report.json`，供用户与开发者随时复查。

---

## 四、 增量插件安装与注册步骤

如果您已经拥有官方 AGH 目录（如 `E:\my-agh` 或 `C:\projects\agnes-harness`）：

### 步骤 1：获取并解压增量插件包
从 GitHub Releases 下载 **`physics-agent-addon-v0.1.0.zip`**（约 0.28 MB），将其解压至您的 AGH 根目录下。  
解压后，您的 AGH 根目录将仅新增以下项目资产：
- `physics-agent/`（业务资产套件）
- `一键注册物理智能体.bat`
- `一键注销物理智能体.bat`

### 步骤 2：执行一键注册
在您的 AGH 根目录下，双击运行 **`一键注册物理智能体.bat`**。  
*(或在 PowerShell 终端执行：`powershell -File physics-agent/register_addon.ps1`)*

*注册向导将自动执行：*
1. 自动定位当前 AGH 根目录并输出基座版本与兼容性检查报告；
2. 检测现有技能，保护既有的第三方技能；
3. 将 10 个物理技能增量导入至 `.agh/skills/`；
4. 检查 Python 科学计算库（SymPy、Pint、NumPy、SciPy、Matplotlib）；
5. 自动在本地生成配套的卸载程序（`physics-agent/unregister_addon.ps1`）。

### 步骤 3：启动并使用
按照您平时启动 AGH 的标准方式启动即可（例如运行您原有的启动脚本或 `node packages/cli/dist/local/agnes.mjs daemon start`）。  
在浏览器中打开工作台，输入包含物理分析、理论推导或数值仿真的题干，系统即会自动激活物理流水线开展推演。

---

## 五、 一键注销与恢复（卸载说明）

如果您未来希望从 AGH 中移除物理智能体，恢复原本的底座状态：

1. 双击运行根目录下的 **`一键注销物理智能体.bat`**  
   *(或在终端执行：`powershell -File physics-agent/unregister_addon.ps1`)*；
2. **程序仅删除属于物理智能体的 10 个技能子目录**；
3. **不影响您的 `.agh/skills/` 目录本身，不删除您自己安装的其他第三方技能**；
4. 您的 AGH 基座即恢复至安装插件前的状态。
