# 环境准备与下载指导（Python / Node / pnpm）

> 本文件是"别人拿到本项目（AGH 宿主仓库 + 本项目 physics-agent-governance skill）要在自己电脑上跑起来"的最小环境清单和安装指引。
> 跟 `check-env.mjs`（同目录）配套用：先按下面装好，再跑一次 `node dev-notes/env-check/check-env.mjs` 确认全绿。

## 需要的三样东西

| 组件 | 为什么需要 | 本项目实际验证过的版本（不是最低版本） |
|---|---|---|
| Node.js | AGH 宿主本身跑在 Node 上，`pnpm install` 也靠它 | 24.21.0（LTS） |
| pnpm | AGH 宿主仓库的包管理器，`pnpm install` 装宿主依赖 | 10.34.5 |
| Python | 本项目 `program-design/hooks/` 下所有确定性 hook 脚本（量纲门禁、边界检查、ODE 建模、报告图表等）的运行环境，`dev-notes/self-tests/` 验收脚本也是 Python | 3.13.9 |

这三个版本的对应关系，跟 `dev-notes/self-tests/00-meta/self-test-index.md` §3"固定事实块"记录的"这份清单在哪个 Node/pnpm/Python 版本组合上实际跑通过"一致——`check-env.mjs` 里检查的下限就是这份清单，不是拍脑袋定的"最低版本号"。

## 安装（Windows）

### 1. Node.js
1. 打开 https://nodejs.org/zh-cn ，下载 **LTS** 版本的 Windows 安装包（`.msi`）。
2. 安装时保持默认选项（会自动加入系统 `PATH`），不要手动改安装路径。
3. 装完**新开一个终端**（老终端不会自动刷新 `PATH`），运行 `node --version`，能打印出版本号就算装好。

### 2. pnpm
- Node 装好后，在终端里跑一次：`npm install -g pnpm`
- 装完运行 `pnpm --version` 确认能打印版本号。

### 3. Python
1. 打开 https://www.python.org/downloads/ ，下载最新的 Windows 安装包（`.exe`，`64-bit`）。
2. **安装第一步界面最下面有一个 "Add python.exe to PATH" 的勾选项，一定要勾上再点 "Install Now"**（默认是勾选状态，别手滑取消）。
3. 装完**新开一个终端**，运行 `python --version`，能打印版本号就算装好。

> 如果 `python` 命令没反应但 `python3` 有反应（少数 Windows 环境下会出现），说明安装时 PATH 加的是 `python3` 而不是 `python`；`check-env.mjs` 会同时探测这两个命令名，不影响使用。

## 验证

装好三样东西后，在**仓库根目录**（不是 `dev-notes/env-check/` 子目录）运行：

```
node dev-notes/env-check/check-env.mjs
```

三行都打印 `✓`、末尾显示"全部通过"才算环境就绪。任何一行是 `✗`，按该行下面的安装提示补装，再跑一次。

## 常见问题

- **装了 Node 但 `pnpm install` 报权限错误**：不是 Node 版本问题，是终端没有以足够权限运行，重新用"以管理员身份运行"的终端再试一次即可，不需要重装。
- **Python 装好了但 `python` 命令找不到**：99% 是安装时漏勾了 "Add python.exe to PATH"，重装一次、勾上这一项即可，不需要卸载旧的。
- **换电脑 / 重装系统后要重新确认一遍**：`check-env.mjs` 是纯检查工具，不做任何自动修复；它只负责告诉你"现在齐没齐"，装的动作还是要按上面步骤手动做（或者用你熟悉的包管理方式装，只要版本对得上 `dev-notes/self-tests/00-meta/self-test-index.md` §3 那份清单就行）。
