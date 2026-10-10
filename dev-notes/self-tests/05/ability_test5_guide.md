# AGH 协作测试上手指南（ability-test5）

> 本分支 = AGH 官方基座（`packages/` 等，来自 upstream main）+ 物理 Agent
> 测试项目内容（`.agh/`、`program-design/`，含 2026-10-10 新增的项目内便携
> Python 运行时 `program-design/third_party/portable-runtime/`），**不含任何
> 正在开发中的工作文件**。拿到的人只需跑通下面 5 步，不需要了解本仓库
> 任何开发历史。

跟 ability-test4 相比的两个实质性变化（不用深究原理，按步骤走即可）：
- 本分支的代码基线是 `physics-agent` 分支 2026-10-10 的最新 HEAD
  （`9611ac11`），不再是 test4 那个 10-06 的分叉点；test4 暴露过的
  "报告里还印着一堆看不懂的 64 位哈希码"的呈现层问题，本分支上
  已知的修复/进展会随代码一起带上（是否彻底解决以实际跑通后的报告
  观感为准，不在本指南里替代码下结论）。
- 本分支**自带一份完整的、离线可用的 Python 3.13.9 便携运行时**
  （`program-design/third_party/portable-runtime/`，19 个锁版依赖包 +
  CJK 字体，全部已烘焙、已实测跑通），你的机器**不需要**预先装好
  Python 就能跑通本项目的全部确定性钩子（量纲门/边界门/审计日志/
  图表）——详见下面第 5 步。

## 1. 确认分支

```powershell
git clone -b ability-test5 https://github.com/VirtuwiseZ/agnes-harness.git
cd agnes-harness
git branch --show-current
# 应输出：ability-test5
git log -1 --format="%H %s"
# 应输出：9611ac11 fix(portable-runtime): 补漏 flexcache 锁版条目 + 修 build_wheels.mjs 解析器忽略行尾注释的 bug
```

如果 `git branch --show-current` 显示的不是 `ability-test5`（比如显示
`physics-agent` 或 `main`），先执行 `git checkout ability-test5` 再往下走。

## 2. 环境前提（只需满足一次，跟分支无关）

| 项 | 要求 |
| --- | --- |
| Node.js | `>= 24.10`（`node --version` 确认） |
| pnpm | 仓库根 `package.json` 写死 `pnpm@10.34.5`，直接用 Corepack：
  `corepack pnpm --version`，不用单独装 |
| Windows 额外 | Visual Studio C++ Build Tools + Windows SDK +
  对应 Node 版本的 headers（下面第 3 步第一步会自动准备 headers） |
| Python | **不需要你预先装**。本分支自带便携运行时（见第 5 步），
  即使你机器上完全没有 Python、或者只有一个 Windows 商店占位符
  `python.exe`（点了没反应的那个），都不影响跑通本项目的钩子。 |

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
$env:AGH_HOME = Join-Path ([IO.Path]::GetTempPath()) ('agh-ability-test5-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $env:AGH_HOME | Out-Null
$env:AGNES_PROFILE = 'ability-test5'

node packages/cli/dist/local/agnes.mjs serve
```

- 默认地址 `http://127.0.0.1:4177`，以终端实际输出为准。
- 首次打开会进 Provider 设置页，选一个模型账号、填 API key、点"测试连接"、
  选模型、保存，之后就可以新建任务了。
- 停服务：另开一个终端执行
  `node packages/cli/dist/local/agnes.mjs daemon stop`。

## 5. 跑测试任务时应该看到什么（含"缺 Python"场景的自验证）

新建任务时，工作目录选**你 clone 下来的这个仓库根目录**。

**先做一步自验证，确认便携运行时本身工作正常（可选但建议做，30 秒）：**

```powershell
cd agnes-harness
& "program-design\third_party\portable-runtime\python\python.exe" -c "import sympy, pint, numpy, scipy, matplotlib, plotly; print('portable-python-ok')"
```

只要打出 `portable-python-ok`，说明这套不依赖你系统 Python 的
离线运行时是可用的——之后哪怕你的机器上完全没有 Python，或者只有
Windows 商店那个点了没反应的占位符，项目里的确定性钩子都能照常跑。

然后照 test4 的方式发一条随便的"请只读取当前项目，说明主要目录及用途"，
看到正常回答 + 轨迹记录，就说明 AGH 本体跑通了。之后发给你的测试题目
（PDF/docx/纯文本），照同样的方式发进去即可；
`physics-agent-governance` 这条 SKILL 会在 agent 判断到"这是一道物理
分析/数值求解类题目"时自动加载，不需要手动指定。

如果 agent 在执行过程中真的需要 Python（跑量纲门/边界门/审计日志/
出图），它应该会自动切到这套便携解释器（`program-design/third_party/
portable-runtime/python/python.exe`），**不需要你做任何额外操作、也不需要
你本机有 Python**。如果 agent 反而停下来问你要不要装 Python，那说明
这次的便携运行时 fast-path 没有生效，把这段卡住的具体对话截图/复制出来
回报给开发者，作为下一轮测试的输入。
