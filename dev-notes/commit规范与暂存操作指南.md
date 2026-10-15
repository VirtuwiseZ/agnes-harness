# 项目 Git Commit 规范与暂存操作指南

> 本文档是本项目所有代码与文档提交（Git Commit）的唯一主控指南。
> 整合出处：`dev-notes/architecture/project_consensus.md` §6（更新说明 / commit message 规范）与开发者 2026-10-13 核心操作指令。
> 目标：规范提交节奏、分类处理文件价值、统一 Commit Message 风格，确保任何协作者或接手 AI 均能清晰追溯代码演进历史。

---

## 一、工作流程与提交节奏（边做清单边记录，最后才上传）

1. **任务全流程闭环前不随意 Commit**：
   - 在执行完毕整个阶段或任务闭环之前，不需要频繁进行碎片化 commit；
   - 必须以对 AI 便捷的方式在 **`dev-notes/执行备忘录1013.md`**（或对应任务的共识/任务清单文档）中实时记录执行状态、完成的工作与技术发现，以免流程太长导致 AI 遗忘上下文、偏离目标或写不好 commit messages。
2. **阶段完成后的收尾顺序**：
   - ① 核查所有任务项均已落盘并通过验证；
   - ② 对工作区内所有新增与修改文件进行 **三类价值判断（A / B / C 分流）**；
   - ③ 清理 B 类文件，将 C 类文件写入 `.gitignore`；
   - ④ 严格对照 Message 规范起草分批次 Commit 文本并自检；
   - ⑤ 分批次执行 `git add` 和 `git commit`；
   - ⑥ **严禁执行 `git push`**（所有提交必须保留在本地，待开发者亲自验收后再上传）。

---

## 二、文件价值判断标准（A / B / C 三类分流处理）

对工作区内产生的所有新增、修改或未跟踪文件，必须逐一按以下三类进行处置，严禁“未经甄别全部 `git add .`”：

| 分类 | 判定标准 | 处置动作 | 本项目典型示例 |
|---|---|---|---|
| **A 类：交付价值** | 对项目实际运行、长期交付、正式报告展现或核心测试回归真正有用的成果代码、Skill 协议、规范文档与最终展示文件。 | **分批暂存并 Commit** | `physics-agent/hooks/*.py`、`.agh/skills/*/SKILL.md`、`packages/web*` 修改、`report_structure_guide.md`、正式报告 `research_report_...html`、重绘图表 `redraw...html` |
| **B 类：一次性废弃** | 仅在调试单次过程中临时生成的中间副本、探针脚本、已迁移废弃的文件、碎片日志。 | **物理删除（Delete）** | 迁移到子目录后残留于根目录的旧报告副本、探针脚本 `probe_*.py`、临时 txt 草稿 |
| **C 类：开发参考保留** | 对接下来的开发有参考价值、排查历史问题还可能用到，但体积过大、含个人环境信息、或不属于向最终用户交付内容的文件。 | **加入 `.gitignore` 忽略** | 历史测试大体积诊断包 `dev-notes/self-tests/06/测试6-1agh-diagnostics-*/`、离线 wheel 运行时二进制目录、本地临时数据库 |

---

## 三、Commit Message 语言与格式风格硬约束

在执行任何 `git commit` 之前，必须先对照本节规范完成 Message 自检。合格后方可提交：

### 1. 标题行结构（Conventional Commits 规范）

```text
<type>(<scope>): <简明中文概要>
```

- **常用 Type 标识**：
  - `feat`: 新增功能、新图表能力、新门禁机制、新 UI 交互
  - `fix`: 修复脚本 bug、修正死链、修复语法/排版未渲染缺陷、修正路径冲突
  - `docs`: 文档增补、备忘录更新、行文规范指南订正
  - `refactor`: 代码重构、Markdown 状态机重写（不改变对外接口的功能重写）
  - `test`: 测试用例增补、重绘图表回归产物
  - `chore`: `.gitignore` 规则更新、临时文件清理、依赖配置调整
- **Scope 范围**：明确指示改动的核心模块，如 `(hooks)`、`(skills)`、`(web)`、`(gates)`、`(reports)`、`(docs)`。

### 2. 语言与措辞约束（严禁对话腔与 AI 自言自语）

- **全中文叙述**：Message 正文主要使用严谨、规范的中文编写；代码标识符、文件名与专有名词（如 `KaTeX`、`Plotly`、`BroadcastChannel`、`BOM`）保留英文原名。
- **去除面向开发者的对话喊话**：绝对禁止出现“我已完成步骤③，有两点需要你确认”“请你查看”“等你点头”等把 Git 历史当聊天界面的语句。Git 提交历史是面向所有协作者的工程日志，不是对话窗口。
- **杜绝 AI 自言自语与自我标榜**：绝对禁止出现“我刚刚完成了……接下来需要……”或“（完全遵照开发者指令，没有使用对话口吻）”等元说明。
- **指代必须完全自包含（禁止代号）**：绝对禁止出现“①已完成”、“对应方案 B”、“按上面第 3 条修改”等脱离上下文无法理解的编号与代词。必须清楚写出**改动了什么组件、解决了什么问题、引入了什么变化**。

### 3. 正文结构模板

```text
<type>(<scope>): <简明中文概要（50字以内）>

- 核心变动：清晰列举涉及的核心文件路径及函数/逻辑改动点；
- 解决问题：说明本提交修复的具体缺陷或实现的业务/物理目标；
- 影响范围：说明对上下游节点、宿主运行或用户阅读的具体影响。
```

---

## 四、提交前收尾自检清单（过一遍再提交）

在敲下 `git commit` 之前，必须在心里或备忘录中过一遍这 7 项检查：
- [ ] 1. 是否已剔除所有对话口吻（“我完成了…”）？
- [ ] 2. 是否排除了所有不明指代（“方案 B”、“问题①”）？
- [ ] 3. 标题是否以标准 `fix():` / `feat():` / `docs():` 开头？
- [ ] 4. Message 是否为规范中文且列出了文件路径？
- [ ] 5. 是否已清理 B 类废弃文件、并将 C 类文件配置入 `.gitignore`？
- [ ] 6. 本批次提交的文件是否属于同一逻辑职责（分批暂存，不一锅端）？
- [ ] 7. **【最核心铁律】是否确认未执行 `git push`（仅本地 commit）？**
- [ ] 8. `git add` 路径是否为纯 ASCII 或安全英文通配符（严禁脚本内含中文路径字面量，防范 CP936 乱码）？
- [ ] 9. 多行 Commit Message 是否采用 `git commit -F` 外置文本（严禁直接在 PowerShell 中写 Here-String）？

---

## 五、Windows PowerShell 5.1 环境下提交自动化防坑铁律（防乱码与防崩溃）

在 Windows 平台使用默认 PowerShell 5.1（代码页通常为 CP936 / GBK）执行自动化暂存与提交时，极易因字符集转码缺陷引发连续报错。所有自动化脚本必须严格遵守以下三道防错铁律：

### 1. 铁律一：暂存路径严禁硬编码中文字符串（纯 ASCII + 通配符原则）
- **高发灾难**：在 `.ps1` 脚本中若直接写入包含中文字符的路径或通配符（如 `git add "*启动测试环境*"` 或 `git add "dev-notes/.../test8-全功能要求...md"`），PowerShell 5.1 会将其转码为乱码（Mojibake，如 `*鍚姩娴嬭瘯鐜*` 或 `test8-鍏ㄥ姛...md`），导致 Git 抛出致命错误：  
  `fatal: pathspec '...' did not match any files`。
- **强制约束**：脚本中的 `git add` 路径参数**绝对禁止出现任何中文字符串字面量**！必须全部采用**纯英文字符、后缀通配符或纯英文前缀通配符**进行匹配。
- **典型正反例对照表**：
  | 错误写法（必报 Mojibake 找不到文件） | 正确合规写法（100% 纯 ASCII 安全匹配） | 匹配目标 |
  | :--- | :--- | :--- |
  | `git add "*启动测试环境*"` | `git add *.bat` | 根目录下唯一的批处理启动脚本 |
  | `git add "dev-notes/.../test8-全功能...md"` | `git add dev-notes/self-tests/08/test8-*.md` | 测试 8 开发审计核验日志 |
  | `git add "dev-notes/competition/黑客松...md"` | `git add dev-notes/competition/*.md` | 六篇黑客松参赛与路演材料 |
  | `git add "dev-notes/self-tests/06/测试...html"` | `git add dev-notes/self-tests/06/research_report_*.html` | 历史测试生成报告归档 |

### 2. 铁律二：多行提交信息强制采用 `git commit -F <file>` 外置 UTF-8 文本
- **高发灾难**：在 PowerShell 中直接内嵌 `@"..."@`（Here-String）极易因多字节字符截断换行符、转义闭合引号失败而触发 `TerminatorExpectedAtEndOfString` 语法解析崩溃；
- **强制约束**：
  1. 严禁在脚本中拼接包含中文的多行提交字符串；
  2. 必须由开发工具预先将标准中文 Message 写入独立的 UTF-8 文本文件（如 `dev-notes/commit_msg_batch1.txt`）；
  3. 脚本中统一使用纯 ASCII 命令调用：`git commit -F "dev-notes\commit_msg_batch1.txt"`；
  4. 提交完成后立即通过 `Remove-Item` 清理该临时文本；
  5. 必须仔细核对文件名拼写，杜绝 `commit_net_msg_...` 笔误导致 Git 向 stderr 报错。

### 3. 铁律三：防范原生命令 stderr 触发 PowerShell `$ErrorActionPreference = 'Stop'` 意外终止
- **高发灾难**：在脚本声明了 `$ErrorActionPreference = 'Stop'` 时，Git 的任何非致命 stderr 输出（包括找不到测试文件时的警告）都会被 PowerShell 判定为致命的 `NativeCommandError` 并立刻强行中断脚本执行；
- **强制约束**：
  1. 在调用 `git commit -F` 前，必须使用 `if (Test-Path $msgFile)` 先行确认提交说明文件存在；
  2. 对于已提交过的批次，使用 `if (Test-Path ...)` 优雅识别并跳过，禁止盲目重复执行抛错；
  3. 确保传递给 `git add` 的路径在磁盘上真实存在，杜绝空通配符报警。

