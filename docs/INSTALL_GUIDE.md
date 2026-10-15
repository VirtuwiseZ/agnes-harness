# AI 物理科研工作站安装与快速入门指引

本文档面向从 GitHub Release 下载预编译包或克隆本项目的用户，介绍如何在本地计算机上完成环境自检、依赖配置、服务启动以及常见问题的排查。

---

## 一、 系统环境要求

| 组件 | 推荐配置 / 最低要求 | 说明 |
| :--- | :--- | :--- |
| **操作系统** | Windows 10 / 11 (x64)<br>macOS 12+ (Apple Silicon / Intel)<br>Linux (Ubuntu 20.04+ / Debian 11+) | 提供 Windows 原生批处理脚本与全平台通用命令。 |
| **系统架构** | 64 位操作系统 (x64 / arm64) | 科学计算与数值积分需要 64 位支持。 |
| **Node.js** | `>= 24.10`（推荐使用 Node.js 24 LTS） | Agnes Harness 底座运行环境。 |
| **包管理器** | `pnpm >= 10.0` | 项目依赖包管理工具。 |
| **Python** | Python 3.10+ | 用于执行物理数值求解、量纲检验与矢量图表绘制。<br>*（若未安装，系统支持调用内置的便携式 Python 运行时）* |
| **硬件要求** | 双核 CPU，4 GB 可用内存，2 GB 可用硬盘空间 | 无需独立 GPU，物理求解与绘图均为轻量 CPU 高精度算法。 |

---

## 二、 安装与部署方式选择

本项目提供三档不同维度的安装部署方式，您可以根据本地使用习惯选择最适合的方式：

| 安装方式 | 适用人群 | 核心特性 | 入口文件 |
| :--- | :--- | :--- | :--- |
| **方式一：Windows 原生图形化安装向导**<br>（强烈推荐普通用户使用） | Windows 10 / 11 桌面用户 | 具备完整的图形向导界面，实时查看环境状态、自适应勾选下载缺失依赖、自由选择安装磁盘与目录、自动生成桌面与开始菜单快捷方式、正规注册至系统控制面板，并配备安全卸载程序。 | 双击运行：<br>**`图形化安装.bat`**<br>或运行：<br>`installer\AI_Physics_Agent_Setup.exe` |
| **方式二：双击批处理一键脚本安装** | 偏好自动化无交互安装的用户 | 终端自动执行 Node/pnpm/Python 检测与依赖构建，两步即可拉起浏览器工作台。 | 双击运行：<br>**`一键安装.bat`**<br>随后双击：<br>**`一键启动.bat`** |
| **方式三：跨平台终端手动编译部署** | Linux / macOS / 开发者 | 纯命令行控制，适合二次开发与定制化部署。 | 终端执行标准 `git`、`pnpm`、`pip` 与 `node` 命令 |

---

## 三、 方式一：Windows 图形化安装向导详解（推荐）

从 GitHub Release 下载项目解压后，双击运行项目根目录下的 **`图形化安装.bat`**（或直接运行 `installer\AI_Physics_Agent_Setup.exe`），即可进入图形安装向导：

### 1. 步骤一：环境自检与功能选项
- **运行环境状态查看**：界面上方实时检测并显示操作系统的 64 位架构、Node.js 版本、pnpm 包管理器、Python 科学环境以及内置离线便携包的状态，绿色代表已通过，红色或黄色提示缺失项；
- **智能自适应勾选（用户可根据需要勾选）**：
  - `[✓] 若未检测到 Node.js，自动下载并启动官方安装包 (Node.js 24 LTS)`：智能体检测到本地缺失 Node.js 时会自动勾选此项，在安装过程中调用官方源完成部署；
  - `[✓] 自动配置 Python 科学计算依赖库`：自动调用 pip 安装 SymPy、Pint、NumPy、SciPy、Matplotlib，若脱网则自动启用内置的 20 个离线 wheels 便携包；
  - `[✓] 在桌面创建启动快捷方式 (AI 物理科研工作站.lnk)`；
  - `[✓] 在 Windows 开始菜单中创建程序组与卸载快捷方式`；
  - `[✓] 正规注册至 Windows 系统已安装应用列表 (Apps & Features)`。

### 2. 步骤二：选择主程序安装位置
- **自定义安装磁盘与路径**：系统默认推荐安装至用户本地应用程序目录（无需管理员提权，运行稳定），您也可以点击 **“浏览 (Browse)...”** 按钮自由选择任意磁盘分区（如 `D:\AIPhysicsAgent`）；
- **磁盘空间自检**：界面实时显示安装所需磁盘空间（约 280 MB）与目标磁盘的当前剩余可用空间。

### 3. 步骤三：自动部署与快捷方式创建
- 点击 **“立即安装”** 后，安装向导显示进度条并实时滚动文件部署日志；
- 自动部署核心程序、门禁脚本、知识库与参考数据集；
- 通过 Windows 脚本宿主动态生成带有高分辨率科学专属图标（`app.ico`）的快捷方式；
- 正规写入 Windows 注册表项 `Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent`，使软件正规出现在 Windows 10/11 的 **“设置 ➔ 应用 ➔ 已安装的应用”** 以及 **“控制面板 ➔ 程序和功能”** 列表中。

### 4. 步骤四：安装完成与启动
- 安装成功后，您可以选择是否 **“立即启动 AI 物理科研工作站”**；
- 点击 **“完成”** 即可退出向导并自动唤起浏览器工作台。

---

## 四、 系统的正规卸载与数据保护机制

若您未来需要从计算机中移除本系统，可以通过以下正规途径进行一键完整卸载：
1. **途径 A**：打开 Windows **“设置 ➔ 应用 ➔ 已安装的应用”**（或控制面板），找到 **“AI 物理科研工作站 (Physics Research Agent)”**，点击 **“卸载”**；
2. **途径 B**：点击 Windows 开始菜单 ➔ **“AI 物理科研工作站”** 程序组 ➔ 点击 **“卸载 AI 物理科研工作站”**；
3. **途径 C**：直接进入主安装目录，双击运行 **`Uninstall.exe`**。

> **核心数据安全保护**：  
> 卸载程序启动时，会弹出确认窗口，并默认勾选 **“保留工作区中用户自建的物理研究成果与历史报告 (agh-workspace/)”**。这确保了在彻底清除程序文件、注册表项与桌面快捷方式的同时，**绝对不会误删您自己生成的物理仿真数据与学术报告**。若您希望彻底清除所有数据，只需取消勾选即可。

---

## 五、 方式二：双击批处理一键脚本安装

如果您习惯直接通过轻量批处理运行，也可以使用预置的脚本方案：

### 第一步：环境检查与一键安装
双击运行项目根目录下的 **`一键安装.bat`**。  
*脚本将按顺序自动完成：*
1. 检测 Node.js 与 pnpm 状态（若未安装 pnpm，将自动尝试通过 Corepack 启用）；
2. 自动安装项目底座依赖包（`pnpm install`）；
3. 检查系统 Python 与核心科学计算库（SymPy、Pint、NumPy、SciPy、Matplotlib）；
4. 编译本地命令行与底座服务模块。

### 第二步：一键启动服务
安装成功后，双击运行根目录下的 **`一键启动.bat`**。  
*程序启动后将：*
1. 自动同步物理技能与分析工具到工作区；
2. 释放并监听本地端口（默认端口为 `4180`）；
3. 自动调出默认浏览器打开工作台前台：`http://127.0.0.1:4180`。

> **日常自检提示**：任何时候若遇到运行异常，可直接双击运行根目录下的 **`环境自检.bat`**，系统会以表格形式输出当前 Node.js、pnpm、Python 及各科学库的可用状态，并附带针对性的解决建议。

---

## 六、 方式三：跨平台与终端手动安装指南（macOS / Linux / 通用终端）

如果您习惯使用命令行，或在 macOS / Linux 系统下运行，请在终端中执行以下标准流程：

### 1. 克隆代码并进入目录
```bash
git clone https://github.com/VirtuwiseZ/agnes-harness.git
cd agnes-harness
```

### 2. 执行环境诊断（可选）
在 PowerShell 中执行：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/doctor.ps1
```

### 3. 安装依赖与本地编译
```bash
# 启用 pnpm（若未安装）
corepack enable
corepack prepare pnpm@10.34.5 --activate

# 安装底座依赖
pnpm install

# 本地构建 CLI 模块
pnpm --filter @agnes/cli run build:local
```

### 4. 安装 Python 核心科学计算库
```bash
pip install -r physics-agent/hooks/requirements.txt
```
*所需依赖清单：*
- `sympy>=1.12`：符号数学代数与量纲解析
- `pint>=0.23`：物理单位制与量纲齐次性自动核验
- `numpy>=1.26`：多维数组、空间网格与离散差分
- `scipy>=1.12`：变步长常微分方程积分（`solve_ivp`）与特殊函数
- `matplotlib>=3.8`：出版级矢量图表绘制引擎

### 5. 启动服务
```bash
# 启动后台守护服务（指定端口 4180）
node packages/cli/dist/local/agnes.mjs daemon start --port 4180
```
启动完成后，在浏览器中访问：`http://127.0.0.1:4180`。

---

## 四、 常见依赖缺失的处理指引

### 1. 系统未安装 Node.js 或版本过低
- **现象**：运行脚本时提示 `未检测到 Node.js，无法继续安装` 或版本低于 `24.10`；
- **解决方式**：
  1. 访问 Node.js 官方网站：[https://nodejs.org/](https://nodejs.org/)；
  2. 下载并安装当前最新的 **Node.js 24 LTS** 或最新版本；
  3. 安装完成后重启终端即可。

### 2. 未检测到 pnpm 包管理器
- **现象**：终端提示 `pnpm: command not found`；
- **解决方式**：
  - 如果使用的是 Node.js 24，官方已内置 Corepack，直接在终端执行：
    ```bash
    corepack enable
    corepack prepare pnpm@10.34.5 --activate
    ```
  - 或者通过 npm 进行全局安装：
    ```bash
    npm install -g pnpm@10.34.5
    ```

### 3. 系统未安装 Python 或缺少科学计算库
- **方案 A（联网安装）**：直接在系统终端中执行：
  ```bash
  pip install sympy pint numpy scipy matplotlib
  ```
- **方案 B（脱网环境便携运行时兜底）**：  
  如果所处环境无法联网或无管理员权限，项目在 `physics-agent/third_party/portable-runtime/` 提供了免安装的官方嵌入式 Python 3.13 依赖配置与预烘焙 wheels。系统检测到缺少全局 Python 库时，会自动调度便携运行时与离线 wheels 包进行计算，无需手动安装。

---

## 五、 自定义工作区与数据存储设置

默认情况下：
- 启动脚本会自动在项目根目录下创建 **`agh-workspace/`** 作为解题工作区；
- 用户配置与临时会话保存在 `~/.agh-physics/` 独立目录中，**严格与系统的其他默认开发环境相互隔离**，避免端口或缓存冲突；
- 如需自定义工作区路径，可在执行脚本时传入参数：
  ```powershell
  # 自定义工作区与端口启动
  powershell -File scripts/start.ps1 -Port 4185 -WorkspaceDir "D:\MyPhysicsTasks"
  ```

---

## 六、 常见问题与排查速查（FAQ）

### Q1: 启动时提示端口 4180 被占用怎么办？
启动脚本已内置端口检测与旧进程清理逻辑。如果端口依然冲突，您可以：
1. 在运行 `scripts/start.ps1` 时指定新端口，例如 `-Port 4188`；
2. 或者在终端执行命令停止已存在的守护进程：
   ```bash
   node packages/cli/dist/local/agnes.mjs daemon stop
   ```
   ```

### Q2: Windows 下执行 PowerShell 脚本提示“无法加载脚本，因为在此系统上禁止运行脚本”？
这是 Windows 默认的安全策略（Restricted ExecutionPolicy）。解决方式：
1. 直接双击根目录下的 `.bat` 批处理文件（内部已附带 `-ExecutionPolicy Bypass` 参数，不会触发系统拦截）；
2. 或者在管理员身份打开的 PowerShell 中执行一次允许本地脚本命令：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Q3: 离线生成的 HTML 学术报告能否在断网环境下正常查看？
**完全可以。** 报告采用单文件自包含设计，所有数学公式样式均已本地内联，矢量图表内嵌在 HTML 文件内部，彻底排除了外部 CDN 链接依赖，在完全断开网络的电脑上双击即可正常阅读与交互。
