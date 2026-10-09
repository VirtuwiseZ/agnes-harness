# 交付体量评估：项目交付给外部组员/比赛方时，能做多小？（2026-10-09）

> 状态：思考稿，不是实施方案。本次没有创建 `ability-test4` 分支，没有写任何
> 插件代码，只做了三件事：(1) 实测仓库各顶层目录的真实体量；(2) 查清楚 AGH
> 插件机制实际能承载什么（对着仓库里已有的 `skill-helper`/`plugin-helper`
> 插件源码，不是凭印象）；(3) 对照 AGH 自己文档里"如何安装 AGH 本体"的
> 流程，判断"把下载链接塞进插件"这条路走不走得通。

## 1. 仓库本体各部分实测体量（`git ls-files` + `git cat-file -s`，不是看文件
系统大小，排除本地 `node_modules`/构建产物这类不属于仓库内容东西）

| 顶层目录 | 文件数 | 体量 | 是否属于"我们的项目"内容 |
| --- | ---: | ---: | --- |
| `packages/` | 3339 | 28.43 MiB | **否**——这是 AGH 框架本体（CLI/daemon/web 等运行时），是别人
  需要跑的"宿主"，不是我们这次要交付的"物理 Agent 项目" |
| `docs/` | 81 | 16.79 MiB | 否——AGH 自己的文档（含二进制图片/动画素材） |
| `dev-notes/` | 115 | 9.69 MiB | 半——里面有本项目自己的自测/第三方数据
  （`第三轮数据/`），也有 AGH 开发记录，不都是"交付物" |
| `tools/` | 72 | 0.76 MiB | 否 |
| `examples/` | 210 | 0.48 MiB | 否 |
| `third-party/` | 3 | 0.02 MiB | 否 |
| **`program-design/`** | **17** | **0.16 MiB** | **是**——全部核心：
  `hooks/`（6 个 .py + `requirements.txt` + `trace_capture.cjs`）、
  `knowledge/`（4 篇 .md + 1 个 .json）、`problem_state_schema.md`、
  `parser_requirements.md`、`runtime/` 模板 |
| **`.agh/skills/physics-agent-governance/SKILL.md`** | **1** | **0.04 MiB** |
  **是**——项目唯一的 SKILL 文件 |

**"我们的项目"真正交付相关的两部分（`program-design/` + `.agh/`）合计
18 个文件、约 0.20 MiB（≈ 200 KB）**——这已经是"极小"了，比 AGH 框架
本体（`packages/`，28.43 MiB）小两个数量级。

## 2. 但要跑起来，还需要什么（不是我们交付的，是"宿主侧"要自备的）

`docs/guide/install.zh-CN.md` 写得很清楚：AGH 目前是**源码构建**，"尚无
正式公共安装包"，组员/比赛方拿到仓库后要自己走一遍：
- `git clone`（或按分支）→ `pnpm install --frozen-lockfile` →
  `pnpm --filter @agnes/cli build:local`（Windows 还要先跑
  `prepare-windows-native.ps1` 拉 Node headers，需要 .NET/Visual Studio
  C++ Build Tools/Windows SDK）→ 才能 `serve`。
- 也就是说：**"交付项目"实际分两层**——(a) 我们自己的
  `program-design/` + `.agh/` 内容层（≈200 KB，真正要"分享"的东西）；
  (b) 承载它的 AGH 框架层（`packages/` 28.43 MiB，组员自己
  `git clone` 上游/本仓库都要重新构建一遍，这一层不需要我们"交付"，
  他们本来就要跑起来整个 AGH）。

结论：**项目内容层本身已经小到不能再小了（0.2 MiB，18 个文件）**，再
"精简"只会漏掉某个真正被 `SKILL.md`/`problem_state_schema.md` 引用的
知识文件或 hook 脚本，得不偿失；真正会让人觉得"体积大"的不是这一层，
而是(b)层——但(b)层跟"交付哪个分支"无关，组员无论切哪个分支，只要
要真的跑起来 AGH，都得重新构建一次 `packages/`，跟分支里有没有放
`program-design/` 没有关系。

## 3. "用插件挂下载链接、安装时自动拉取配置"这条路，走不走得通

查了 `packages/package-manager/bundled-plugins/skill-helper/src/github.mjs`
（**现存的、已经在用**的先例）和 `plugin_helper_guide` 返回的官方模板，
结论分两层：

- **走得通的部分**：AGH 插件（ Cordis 对象 + `ctx.fs`/`ctx.net`/
  `ctx.shell`）确实可以在 `apply()` 里做"拉取远端内容 + 写入本地 + 触发
  安装"这类事——`skill-helper` 插件现在就在干一模一样的事（`github.mjs`
  走 GitHub REST API 拉某个 repo/分支的某个子目录，校验 SHA/字节数/条数，
  再走 `skill_helper_install` 的提案-审批流程装进 `.agh/skills/`）。所以
  "写一个 `physics-agent-bootstrap` 插件，`apply()` 里用 `ctx.net` 拉
  本仓库 `ability-test4` 分支的 `program-design/` + `.agh/` 两个目录、
  校验、落盘、提示用户已就绪"——**机制上是成立的，有现成先例可以抄
  （`skill-helper` 的 `github.mjs` 几乎就是这个需求的现成模板，只是它
  拉的是"一个 Skill 目录"，我们要改成拉两个顶层目录）**。
- **走不通/不建议的部分**：如果目标是"让组员/比赛方从零开始跑通整个
  AGH"，插件**替代不了** `packages/` 那 28 MiB 的本体构建（Node 版本、
  pnpm、Windows 原生 helper 这些环境依赖，没有任何"插件安装"动作能
  绕过——它们是要组员机器自己满足的前提条件，不是可以打包进一个
  `.mjs` 文件里带走的）；如果目标只是"把我们的项目内容（program-design/
  + .agh/，≈200 KB）送到一个**已经装好 AGH 本体**的组员机器上"，那
  插件这条路和"直接给一个 GitHub 分支链接 + 一句 `git checkout
  ability-test4 && 把 program-design/ .agh/ 复制到你 AGH home 里`"
  相比，**收益几乎为零**：这 200 KB / 18 个文件，复制一条命令就能完成，
  用一整个插件（要写 manifest、要走 `plugin_helper_create`/
  `plugin_helper_install` 的提案-审批流程、要组员再装一遍这个插件本身
  才能触发拉取）去包一层，反而比"直接给链接+复制"更重、更难用。

## 4. 建议（供建 `ability-test4` 分支时参考，本次未实施）

1. `ability-test4` 分支内容 = `main`（或当前 `physics-agent`）+ 把
   `program-design/` + `.agh/` 这两块"真·交付物"原样带上，**不需要**为了
   "更小"把 `dev-notes/`/`docs/`/`packages/` 从分支里删掉——那三个目录
   是 AGH 框架/开发留痕，删了组员反而没法构建/跑起来 AGH 本体；
   "交付体量"这件事靠**跟组员说清楚'你们只需要关注 program-design/ 和
   .agh/ 这两个目录，其余不用动'**来达成，而不是靠物理删文件。
2. **不做**"插件挂下载链接"这条路：如上第 3 节，200 KB 的内容用一条
   复制命令/一个 README 说明就能送达，为一个这个体量的东西专门造一个
   插件（含审批流）是负收益。如果将来"交付物"膨胀到几百个文件/几十
   MB，且组员反复要重装，再考虑把 `skill-helper` 的 `github.mjs`
   模板改成"拉整个目录"的通用版本，现在不提前做。
3. 唯一真正值得做的一件小事：在 `ability-test4` 分支根目录放一份
   **一页纸的"组员上手指南"**（clone 哪个 remote/分支、要满足什么
   环境前提（Node/pnpm/Windows 原生工具链）、只需关注哪两个目录、怎么
   验证跑通）——这份指南本身也是 18 个交付文件之外的"最小必要说明"，
   比"再写一个插件"更贴合"小而简洁交付"这个目标。
