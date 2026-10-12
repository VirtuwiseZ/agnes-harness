# 物理 Agent 项目路径约定（Path Convention，写入端 + 检索端合并一份）

本文档承载 ③第 3 条（C4/C5）"写入端 + 检索端合并一份"的路径约定全文，以及
③第 5 条（C1）`runtime/<task-slug>/` 命名规则的具体细则。主 `SKILL.md`
（①拆分后的各节点子 skill）只在相关位置留一句指针指向本文档，不在主
`SKILL.md` 正文里重复本文档的目录地图内容（跟 1009 §2.5 修 §7 时"正文
留指针、细节文档承载全文"的处理方式一致；跟 ③第 1 条"不往已经拆出去
的主 SKILL.md 里再堆跟单一节点职责无关的内容"的原则一致）。

读者（未来的 AI 会话）拿到本文档后，按"我要做什么"直接定位到对应小节，
不需要通读全文：

| 我要做什么 | 看哪一节 |
|---|---|
| 要给这道题新建/写入任何运行时文件（`problem_state.json`、增量研究汇报 md、资产文件等） | §1 写入端 |
| 要读/引用一份外部文档（用户上传的 PDF/DOC、本地磁盘路径），走哪个解析层 | §3 检索端：外部文档解析 |
| 要判断"某个文件该落在哪个目录、叫什么名字"，拿不准 | §1 写入端 + §4 命名规则（C1） |

---

## 1. 写入端：项目里"由 pipeline 运行产出的文件"都落在哪里

**根目录**：所有**运行时（非代码、非 git 跟踪模板）产出物**统一落在
`physics-agent/runtime/` 下，**每个任务一个子文件夹**，子文件夹名即
"<task-slug>"（命名规则见 §4，不是任务编号、不是题目编号，是 AI 根据
题干总结的主题短语，kebab-case）。

```
physics-agent/runtime/
  <task-slug>/                      # 例如 "space-diving-drag" 或 "atmosphere-density-profiling"
    problem_state.json              # 该任务自己的增量 state（模板见
                                    # physics-agent/runtime/problem_state_template.json）
    task_params.json                # 该任务自己的参数（模板见
                                    # physics-agent/runtime/task_params_template.json）
    report.md                       # Node 3 增量研究汇报（markdown 原文）
    runlogs/                        # ③第 4 条 4c：脚本运行资产文件目录
      <artifact_id>.txt             # 一个文件 = 源码 + 完整 stdin/argv +
                                    # 完整 stdout + 完整 stderr + 退出码，
                                    # 不拆成两个文件（见 §2）
```

- **`physics-agent/runtime/` 下现有两个文件是"模板"，不是任何具体任务的
  数据**：`problem_state_template.json` 和 `task_params_template.json`
  是填空骨架（跟 ③第 5 条 C1 定论里"test5 分支现存带 `2013A` 编号的历史
  文件不需要回头重命名"是同一类"历史产物不追溯"的处理——模板文件本身
  不属于任何具体 `<task-slug>` 子目录，永远放在 `physics-agent/runtime/`
  根层，不进子文件夹）。
- **每个具体任务必须有自己独立的 `<task-slug>/` 子文件夹**，不允许多个
  不同任务共用/覆盖同一个子文件夹里的 `problem_state.json`；同一道题
  被"再次提出/被要求重做"时，按 §4 的 `_runN` 后缀规则新开一个子文件夹，
  不覆盖旧的那份。

### 2. `runlogs/` 资产文件（③第 4 条 4c 的具体路径约定，跟本文档其余部分
一起作为"写入端"的完整目录地图）

- 一条 `audit_logs` 记录里如果带 4a 的 6 个新键（`script_path` 等），且
  这条调用对应的是一个**任务现场新建的 `.py` 文件**（不是
  `physics-agent/hooks/` 下已有的通用 hook），调用方应调用
  `physics-agent/hooks/runlog.py` 的 `write_runlog()`，把这份"完整记录"
  （源码 + 完整 stdin/argv + 完整 stdout + 完整 stderr + 退出码，**写进
  同一个 `.txt` 文件，不拆两个文件**——理由：原文 A4 里"点开看代码与
  调用运行记录"本来就是同一个点击动作，一个文件承载比两个文件更贴合原
  文意图，且避免"两个文件的路径命名规则要各自维护"这类 1009 §2.5 反复
  强调要避免的"两处各写一遍"病根）落到
  `physics-agent/runtime/<task-slug>/runlogs/<artifact_id>.txt`。
- 对应 4a 记录里如果 `script_path` 指向的是 `physics-agent/hooks/` 下
  **已有的通用 hook**（`audit_log.py`/`ode_model.py`/`make_report_figures.py`
  等），**不需要**为这次调用额外写一份 `runlogs/` 资产文件（这些文件的
  "源码"已经在 git 里、路径固定、不需要"这次调用的现场快照"来定位）；
  只有"任务现场新建、用完即弃或跨题不通用"的脚本才触发 4c 的落盘动作。
- 4d（`trace_visualizer.py` 的"本节所使用文件"块）里"运行记录"这个链接
  直接指向上面这个相对路径（浏览器点开即纯文本，不需要 JS 懒加载机制，
  跟 ③第 4 条 4d 的定论一致，此处只补充"路径本身长什么样"这一层，
  不重复 4d 的 UI 渲染细节）。

## 3. 检索端：外部文档解析（`document_read` 的两条实测确认，10/12）

（本小节是 ③第 3 条追加的"跟这份路径约定文档合并核实"的两条
`document_read` 复核结论的实测记录；`physics-doc-parsing` 子 skill 正文
不需要因此改动——两条复核都指向"维持现状"，不是"改"，只是把
"读源码推断"升级成"实际跑一遍验证"。）

### 3.1 复核一：`document_read` 是否仍然只认 `session-file://` 附件、
不认本地磁盘路径 —— **实测确认：确实不认本地磁盘路径（2010-GM-B-210.pdf
实测，10/12）**

- 用本仓库现存的一份**真实本地磁盘 PDF 路径**
  （`E:\agnes-harness\dev-notes\reference-solutions\例题\2010-GM-B-210.pdf`，
  非 session 附件）实际调用一次 `document_read`，**该工具直接拒绝**，
  返回 `tool arguments do not match the registered schema`——不是"能读
  但读出来的内容不对"，是**参数校验层面**直接拒绝，跟"读源码推断
  `read.ts` 没有本地磁盘路径分支"的结论**完全一致**，不是意外/临时故障。
- **结论**：`physics-doc-parsing` 子 skill B 分支（"用户给的是本地磁盘
  路径"→ 直接走 PyMuPDF4LLM/MinerU，不经过 `document_read`）的写法
  **不需要因此改动**，本轮把这个"读源码推断"的结论正式升级为"实测确认"，
  写入本文档作为后续维护者（AI 或人）的权威依据，避免以后有人拿本地
  路径再试探一次 `document_read`、发现"又失败了"就误以为是新的 bug。

### 3.2 复核二：`document_read` 公式提取效果是否仍不如 MinerU ——
**已核实：`document-reader` 插件实现代码在 #370 merge 范围内一个文件没
被改过，实测结论没有改变（10/12）**

- `git log cde816b8..3f48dfff -- packages/package-manager/bundled-plugins/
  document-reader/` 查询结果为空——即这次官方上游 merge 完全没有触碰
  这份实现代码，"公式区域读出来是散乱不可读字符、跟 Tier 1 同一档、
  不如 Tier 2 MinerU"这个之前实测结论**在 #370 之后没有改变**，
  `physics-doc-parsing` 里 Tier 0"不擅长公式、要交给 Tier 2 MinerU"的
  分层判断不需要因此调整。
- 本条**不需要 ③第 3 条再写任何新代码/新机制**，只是把"查过、结论没
  变"这个事实记在这里，避免未来 AI 误以为这次官方更新会让
  `document_read` 的公式提取能力突然变好、于是擅自把"公式密集型文档
  直接交给 Tier 0 试试"当成可以偷懒省掉 Tier 2 的新依据。

## 4. 命名规则（C1，③第 5 条）：`runtime/<task-slug>/` 怎么起这个名字

（细则在 `网页重新设计1011.md` C1 段"命名规则（本轮开发者已拍板）"小节
里已经写明，本节只放指针指回那一节，不复制原文，避免"两处各写一遍"
病根；此处列出的要点是"起名字时逐条对照"的清单，不是规则本身
的重新发明。）

1. 文件夹名 = AI 根据题干总结的**题目主题短语**（例如 `space-diving-drag`
   / `atmosphere-density-profiling`），**不带题目编号**（不是 `2013A` 这类
   原始编号）。
2. 同一题干+参数被**再次提出/被要求重做** → 在原 slug 后面加 `_runN`
   后缀（`space-diving-drag_run2`），不覆盖 `space-diving-drag` 那份；
   N 是"这是第几次针对同一道题的独立运行"，不是题号。
3. test5 分支上现存的带 `2013A` 编号的历史 `runtime/` 子目录**不需要
   回头重命名**——这条规则只对"规则生效之后"新建的任务文件夹起作用，
   不追溯改名已存在的历史目录（跟 ②改名时"历史 commit 里的旧路径不做
   改写、只做'从下一次改动开始'的前瞻性同步"是同一类"不追溯"原则）。
4. `<task-slug>` 全程 kebab-case（小写字母 + 数字 + 连字符），不带下划线
   开头、不带空格，方便直接拼进路径/命令行参数而不用额外转义。

---

## 5. 本文档跟其余 ③ 待办条目的边界（避免重复承载/重复维护）

- §1/§2 的"写入端"目录地图本身不属于任何**具体节点子 skill** 的职责
  （Node 1/2a/2b/3/4 各自关心"这一节该写什么内容"，不关心"写进哪个
  文件/哪个目录"这个横切问题），所以放进本文档、主 `SKILL.md` 各子
  skill 只在真正需要用到某条路径时（例如 Node 2b 要写 `problem_state.json`、
  Node 4 要生成/读 `runlogs/` 链接）加一句"路径约定见
  `physics-agent/knowledge/path_convention.md`"的指针，不在正文里复制
  目录树。
- §3 的两条 `document_read` 复核结论**只属于**"文档解析"这一个子 skill
  （`physics-doc-parsing`）关心的范围，不是通用路径问题；本小节只是
  把 ③第 3 条追加的"合并核实"要求落在这里（因为 ③第 3 条原文要求
  "跟这份路径约定文档合并核实，不另起条目"），不代表这两条结论在
  项目里有任何**其它**位置需要同步维护——`physics-doc-parsing` 正文
  本身不需要因为这两条复核结果改动一个字（两条结论都是"维持现状"，
  不是"改现状"），本文档只是把"维持现状的依据"记实、升级成实测，
  供未来维护者查阅。
