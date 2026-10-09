# AGH 协作测试上手指南（ability-test4）

> 本分支 = AGH 官方基座（`packages/` 等，来自 upstream main）+ 物理 Agent
> 测试项目内容（`.agh/`、`program-design/`、仓库根目录下的 node1*/node2b* 等
> 题目运行脚本），**不含任何正在开发中的工作文件**。拿到的人只需跑通下面
> 4 步，不需要了解本仓库任何开发历史。

## 1. 确认分支

```powershell
git clone -b ability-test4 https://github.com/VirtuwiseZ/agnes-harness.git
cd agnes-harness
git branch --show-current
# 应输出：ability-test4
git log -1 --format="%H %s"
```

如果 `git branch --show-current` 显示的不是 `ability-test4`（比如显示
`physics-agent` 或 `main`），先执行 `git checkout ability-test4` 再往下走。

## 2. 环境前提（只需满足一次，跟分支无关）

| 项 | 要求 |
| --- | --- |
| Node.js | `>= 24.10`（`node --version` 确认） |
| pnpm | 仓库根 `package.json` 写死 `pnpm@10.34.5`，直接用 Corepack：
  `corepack pnpm --version`，不用单独装 |
| Windows 额外 | Visual Studio C++ Build Tools + Windows SDK +
  对应 Node 版本的 headers（下面第 3 步第一步会自动准备 headers） |

## 3. 构建 AGH 本体（PowerShell，仓库根目录下执行）

```powershell
# 第一步：拉 Node headers + 装依赖
& .\.github\scripts\prepare-windows-native.ps1 -CacheRoot "$env:LOCALAPPDATA\node-gyp\Cache"
corepack pnpm install --frozen-lockfile

# 第二步：构建出可运行的本地分发（产物在 packages/cli/dist/local/）
corepack pnpm --filter @agnes/cli build:local

# 第三步：自检，能打出帮助说明构建成功
node packages/cli/dist/local/agnes.mjs --help
```

## 4. 启动

```powershell
# 建议用独立 home，避免碰到你机器上已有的 AGH 实例
$env:AGH_HOME = Join-Path ([IO.Path]::GetTempPath()) ('agh-ability-test4-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $env:AGH_HOME | Out-Null
$env:AGNES_PROFILE = 'ability-test4'

node packages/cli/dist/local/agnes.mjs serve
```

- 默认地址 `http://127.0.0.1:4177`，以终端实际输出为准。
- 首次打开会进 Provider 设置页，选一个模型账号、填 API key、点"测试连接"、
  选模型、保存，之后就可以新建任务了。
- 停服务：另开一个终端执行
  `node packages/cli/dist/local/agnes.mjs daemon stop`。

## 5. 跑测试任务时应该看到什么

新建任务时，工作目录选**你 clone 下来的这个仓库根目录**。先随便发一条
"请只读取当前项目，说明主要目录及用途"，看到正常回答 + 轨迹记录，就说明
AGH 本体跑通了。之后发给你的测试题目（PDF/docx/纯文本），照同样的方式
发进去即可；`physics-agent-governance` 这条 SKILL 会在 agent 判断到"这是
一道物理分析/数值求解类题目"时自动加载，不需要手动指定。
