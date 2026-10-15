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

## 二、 极速两步使用指南（Windows 用户推荐）

如果您是在 Windows 操作系统下使用从 GitHub Release 下载的源码包，可以通过双击批处理脚本实现快速启动：

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

## 三、 跨平台与终端手动安装指南（macOS / Linux / 通用终端）

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
node packages/cli/dist/index.js daemon start --port 4180
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
   node packages/cli/dist/index.js daemon stop
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
