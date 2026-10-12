# Portable Runtime（项目内便携运行时，用户进入 AGH 会话后相关依赖的离线安装方案）

## 这是什么、不是什么

- **这是什么**：进入 AGH 前端会话区之后、跟本项目物理分析流水线（量纲门/边界门/审计日志/图表/文档解析）真正要跑的 Python 依赖，预先准备"快速静默安装版"（无安装器、不写注册表、解压/下载即用的形式），放在 `program-design/third_party/portable-runtime/`，用户拿到仓库就能直接用，不需要现场联网装。
- **不是什么**：AGH 宿主本身（Node/pnpm/仓库构建）的依赖不属于这一层——那是"用户进入 AGH 会话之前"的事，由 `dev-notes/env-check/check-env.mjs` + 给组员的手工准备清单负责，见 `dev-notes/env-check/README.md`。本文件只管"进 AGH 之后、跟项目物理任务相关"的那部分。

## 伦理边界（设计原则，写在这里是为了以后不用反复争论）

1. 自动做的部分：下载到/解压到**项目目录内**（`program-design/third_party/portable-runtime/`），不碰用户系统 PATH、不写注册表、不覆盖用户已装的其他 Python。
2. 需要用户点头的部分（**默认不替用户做**）：把便携运行时加入用户当前 shell 会话的 PATH、覆盖/替换用户系统里已存在的其他 Python 版本。这两件事永远是显式询问，不是默认行为。
3. 版本锁死：本包内的 Python 和第三方库都是"在 `dev-notes/self-tests/` 实际跑通过的那一版"，不是"理论上能装的最早版本"。版本漂移（比如用户自己装了个 3.14）不在这个包的保证范围内。

## Python 便携版（主路径）

- 来源：Python 官方 `python-3.13.9-embed-amd64.zip`（embeddable package，无安装器、不写注册表、解压即用；这是官方专门为"放进自己目录、不碰系统"场景出的发行形式，Windows 上下载自 `https://www.python.org/ftp/python/3.13.9/python-3.13.9-embed-amd64.zip`，Linux/macOS 没有官方 embeddable 包，需要用系统包管理器或源码编译，本文件暂不覆盖这两种平台的便携方案，先只做 Windows，跟本项目当前唯一验证过的环境一致）。
- 需要预烘焙的第三方库（`program-design/hooks/requirements.txt` 里当前真正被 hook 直接 import 的那几个，不是全部候选）：
  - 核心数值栈：`sympy==1.14.0`、`pint==0.26.1`、`numpy==2.5.3`、`scipy==1.18.1`（以上四个是当前开发机上实际安装、跑通全部 `dev-notes/self-tests/` 验收脚本的版本，锁死这些具体版本号，不用 `requirements.txt` 里的 `>=` 范围）
  - 图表（Node 2.7 可选项）：`matplotlib==3.11.2`（静态 6 种 kind 都用它）；`plotly==7.1.0`（仅 `interactive`/`interactive_live` 两个可选分支需要，静态图任务可以不装）
  - 文档解析（§6 按需触发）：`PyMuPDF4LLM`（Tier 1 默认，`pymupdf4llm.to_markdown()`）——**注意**：当前 `requirements.txt` 里没有把 PyMuPDF4LLM 列成 hook 直接依赖，它属于 SKILL.md §6 按需触发时才要装的东西，本便携包是否要默认带上取决于"要不要让 §6 触发时零等待可用"，目前设计为**可选带上**（带，但标注为可选），不占用必须项的地位。
  - CJK 字体：`make_report_figures.py` 在没有任何 CJK 字体的机器上跑会画出来全是豆腐块，目前只能靠"图还是画出来了但中文是方块"这个弱信号提示（脚本 top-of-run 的 warning）。**本便携包应该随包附带一份 CJK 字体文件**（推荐思源黑体子集，或者干脆复用 Windows 自带的"微软雅黑"——Windows 桌面环境默认有，非 Windows 才需要单独带字体文件），打包进 `program-design/third_party/portable-runtime/fonts/`，让 `make_report_figures.py` 的字体探测逻辑（`_configure_cjk_font()`，见该文件 docstring）能在这套便携环境里稳定命中，不再依赖宿主机恰好装了哪款中文字体。
- **未纳入本包**（保持现状，只做文档说明，不自动装）：MinerU（Tier 2，重量级模型依赖，体积大、下载不可控、且只是"备选"路径不是主路径）；`ambiance`/`pymsis`（数据源路由 Level 0 候选包，`requirements.txt` 里明确标注"仅为了运行时可用性检查能真的跑起来才装，当前没有任何 hook import 它们"，不属于便携包必须项，用户真用到需要这两个包时再手动 `pip install`）。

## 安装/使用方式（给"拿到仓库的用户"的说明，将来要写进 SKILL.md 或被用户端 AI 记得引用）

1. 拿到仓库后先跑 `node dev-notes/env-check/check-env.mjs`（这一层检查的是 AGH 宿主本身的 Node/pnpm，跟本便携包无直接关系，但跑一次能确认基础环境没大问题）。
2. 需要跑本项目 Python hooks（量纲门/边界门/审计日志/图表）时：
   - 优先用本便携包：`program-design/third_party/portable-runtime/python/python.exe program-design/hooks/dimensional_gate.py ...`（Windows 路径示例；实际目录名以下面"目录结构"一节为准，这里只是示意调用形式）。
   - 便携包内的第三方库已经烘焙好，不需要再单独 `pip install`；如果用户机器上另有自己的 Python，也不强制要求用系统 Python，便携包就是为了让"没装 Python 的用户"也能零门槛跑通本项目 hooks。
3. 什么时候"必须"用便携包而不是系统 Python：用户机器上 `where.exe python` 第一行落在 `WindowsApps`（`check-env.mjs` 会明确报这个错），或者用户根本没装 Python。

## 目录结构（待实际生成文件后填实，当前是先写清楚规划，文件本体按下面这个结构落盘）

```
program-design/third_party/portable-runtime/
├── PORTABLE_RUNTIME.md        # 本文件
├── python/                   # 解压后的 python-3.13.9-embed-amd64.zip（python.exe + 标准库）
├── wheels/                   # 上面列出的 sympy/pint/numpy/scipy/matplotlib/plotly 的具体版本 wheel
├── fonts/                    # CJK 字体（Windows 可用系统自带微软雅黑兜底，非 Windows 需随包带一份）
└── INSTALL.md                # 给"第一次拿到这套东西的用户"的三步说明：解压/启用 site/指向 portable 里的 python.exe
```

## 跟 SKILL.md 的关系（要让"用户端 AI"记得用）

- `SKILL.md` §4a（环境缺口停止规则）：在"环境里缺 Python/缺 pip 依赖"这类场景下，**先检查 `program-design/third_party/portable-runtime/` 是否已经能直接用**（不需要走"停等用户装"的流程），只有在便携包也不满足（比如用户需要的是 MinerU 这种明确排除在本包外的重依赖）时，才升级到 §4a 的正式停止+等待用户指示流程。
- `SKILL.md` §6（文档解析）：Tier 1（PyMuPDF4LLM）如果本机没装，优先看便携包里 `wheels/` 是否已有，有的话直接用便携包的 `python.exe -m pip install --target` 指过去，不需要现联网下载。
- 这两处修改见本文件同批次提交的 `SKILL.md` diff，不在本文件里重复全文，只做指针。
