# Windows 原生 .exe 安装包与卸载程序体系架构设计规范

> **文档属性**：Windows 可执行安装包（Setup.exe）、卸载器（Uninstall.exe）与系统注册架构设计规范  
> **归档位置**：`dev-notes/release-job/08_exe_installer_and_uninstall_architecture.md`  
> **制定日期**：2026-10-15  

---

## 一、 设计背景与工程考量

为了让开源物理科研工作站在 Windows 桌面环境下具备标准的商业级安装体验，摆脱仅靠控制台批处理脚本的初级形态，本项目设计并实现了**全原生、图形化、支持环境智能诊断与系统正规注册的 Windows 可执行安装与卸载体系**：

### 核心设计原则
1. **零外部 SDK 依赖编译（Pure Native Compilation）**：
   - 充分利用 Windows 10 与 Windows 11 系统内置的 Microsoft .NET Framework 4.8 官方 C# 编译器（`csc.exe`），无需用户或开发者额外安装 Visual Studio、.NET SDK 或第三方打包工具，即可一键将源码编译为体积轻巧（~26 KB）、高响应速度的独立可执行文件；
2. **环境可视化与智能自适应勾选（Smart Adaptive Options）**：
   - 安装向导第一屏即对 64 位系统架构、Node.js 运行时、pnpm、Python 核心科学库及内置便携包进行只读健康诊断；
   - 界面根据检测结果智能自适应预选安装项：若检测到缺少 Node.js，则自动勾选“下载并安装 Node.js 24 LTS”；若已安装，则自动取消勾选，避免重复部署；
3. **主程序安装位置自由定制（Custom Location Selection）**：
   - 默认安装在当前用户的本地应用程序目录（`%LOCALAPPDATA%\Programs\AIPhysicsAgent`），无需管理员 UAC 提权，运行安全稳定；
   - 提供标准目录选择对话框，支持用户自由选择任意磁盘分区（如 `D:\AIPhysicsAgent`），并实时动态核算目标磁盘可用空间与所需空间；
4. **Windows 原生注册表正规注册（Add/Remove Programs Integration）**：
   - 正规写入 Windows 卸载注册表项 `Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent`，使软件正规出现在 Windows 10/11 的 **“设置 ➔ 应用 ➔ 已安装的应用”** 及 **“控制面板 ➔ 程序和功能”** 列表中；
5. **带成果保护的正规卸载程序（Safe Uninstallation）**：
   - 独立编译并部署 `Uninstall.exe`；
   - 卸载时贴心询问并默认勾选 **“保留用户在工作区中自建的物理研究成果 (agh-workspace/)”**，在干净清理程序文件、注册表与快捷方式的同时，杜绝误删用户的科研资产。

---

## 二、 安装程序架构与向导流程（`SetupProgram.cs`）

安装程序采用四步向导式界面（Wizard Form），尺寸锁定为 720x560 像素，界面美观、层级分明：

```
[启动 Setup.exe]
       │
       ▼
【第 1 步：环境健康自检与安装项配置】
  • 实时诊断 OS / Node / pnpm / Python / 离线便携包
  • 智能自适应勾选：[✓] 自动下载Node (若缺失)  [✓] 配置Python库  [✓] 桌面快捷方式  [✓] 注册至系统
       │
       ▼
【第 2 步：选择主程序安装位置】
  • 文本输入框 + 浏览 (Browse) 文件夹选择器
  • 动态检测并显示：所需磁盘空间 (~280 MB) vs 目标磁盘剩余可用空间 (如 128 GB)
       │
       ▼
【第 3 步：执行文件部署与快捷方式创建】
  • 进度条 (0% -> 100%) 与实时日志滚屏
  • 复制核心目录 (.agh, physics-agent, packages, docs, scripts)
  • WScript.Shell 反射生成桌面与开始菜单 .lnk 快捷方式
  • 写入 Windows 注册表 Uninstall 键值
  • 部署独立的 Uninstall.exe
       │
       ▼
【第 4 步：安装完成与运行选项】
  • 成功提示：[✓] 立即启动服务并打开浏览器  [ ] 查阅安装使用指南
  • 点击“完成”优雅退出或拉起应用
```

---

## 三、 快捷方式与 Windows 注册表规范

### 1. 快捷方式生成机制（免外部 COM 依赖）
利用 Windows Script Host 内部反射机制创建标准快捷方式，绑定项目专属高分辨率科学图标（`app.ico`）：
- **桌面快捷方式**：`AI 物理科研工作站.lnk`（指向主目录下的 `一键启动.bat`，指定工作目录为安装路径）；
- **开始菜单程序组**：`%APPDATA%\Microsoft\Windows\Start Menu\Programs\AI 物理科研工作站\`
  - `AI 物理科研工作站.lnk`（主启动项）
  - `运行环境健康自检.lnk`（指向 `环境自检.bat`）
  - `卸载 AI 物理科研工作站.lnk`（指向 `Uninstall.exe`）

### 2. Windows 注册表项写入规范
在当前用户注册表根键下创建规范项：
- **注册表路径**：`HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\AIPhysicsAgent`
- **规范键值列表**：
  - `DisplayName` (REG_SZ): `AI 物理科研工作站 (Physics Research Agent)`
  - `DisplayVersion` (REG_SZ): `1.0.0`
  - `Publisher` (REG_SZ): `AI Physics Research Team`
  - `InstallLocation` (REG_SZ): 目标安装绝对路径
  - `UninstallString` (REG_SZ): `"<目标路径>\Uninstall.exe"`
  - `DisplayIcon` (REG_SZ): `"<目标路径>\app.ico"`
  - `HelpLink` (REG_SZ): `https://github.com/VirtuwiseZ/agnes-harness`
  - `EstimatedSize` (REG_DWORD): `260000` (KB)
  - `NoModify` (REG_DWORD): `1`
  - `NoRepair` (REG_DWORD): `1`
  - `InstallDate` (REG_SZ): 当前日期（`yyyyMMdd`）

---

## 四、 卸载程序架构与生命周期（`UninstallProgram.cs`）

`Uninstall.exe` 作为独立可执行程序放置在主安装根目录中，其执行生命周期如下：

1. **界面交互与确认**：
   - 弹出独立的卸载确认窗口；
   - 核心选项：`[✓] 保留工作区中用户自建的物理研究成果与历史报告 (agh-workspace/)`（默认开启）；
2. **停止后台守护服务**：
   - 自动调用 `node.exe packages/cli/dist/local/agnes.mjs daemon stop` 释放端口与进程锁；
3. **清理桌面与开始菜单快捷方式**：
   - 安全删除桌面 `.lnk` 文件；
   - 递归删除开始菜单中的 `AI 物理科研工作站` 程序组目录；
4. **注销 Windows 注册表项**：
   - 调用 `RegistryKey.DeleteSubKeyTree("AIPhysicsAgent")` 彻底从系统中抹除软件登记；
5. **清理安装目录与延迟自删除**：
   - 若用户勾选保留成果，保留 `agh-workspace/` 目录，清理其余程序文件与库目录；
   - Windows 运行中的 exe 无法自我删除，程序在退出前启动轻量延迟命令行：
     `cmd.exe /c ping 127.0.0.1 -n 2 > nul & rmdir /s /q "<installDir>"`
   - 优雅退出自身，实现完全干净的无残留卸载。

---

## 五、 双轨构建体系：原生编译与 Inno Setup CI 脚本

为了兼顾本地极速构建与 GitHub CI 自动化流水线，项目提供双轨构建方案：

1. **轨道 A：本地原生极速构建（`installer/build_installer.ps1`）**：
   - 本地任意 Windows 机器直接执行；
   - 自动探测 `csc.exe` 路径，分别编译 `Uninstall.exe` 与 `AI_Physics_Agent_Setup.exe`，并内嵌 `app.ico` 图标；
   - 编译耗时仅约 1 秒，产物纯净无臃肿运行时。
2. **轨道 B：标准 Inno Setup CI 构建脚本（`installer/setup.iss`）**：
   - 符合工业级标准的 Inno Setup 6 脚本；
   - 内置基于 Pascal 语法的 `IsNodeInstalled()` 与 `IsPythonInstalled()` 注册表与路径探测逻辑；
   - 可在 GitHub Actions 中通过 `iscc installer/setup.iss` 直接打包生成单文件打包安装包（`AI_Physics_Agent_Setup_Inno.exe`）。
