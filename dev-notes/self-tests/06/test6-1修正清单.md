# 针对 test6 暴露的问题做修复时，参考的文档清单

按"哪份文档管哪一类问题"列出来，不是全部都要读，而是按需引用：

## 1. 问题定义与验收标准（"要修成什么样"）
- **`dev-notes/诉求对照表1013.md`**：针对 1009/1011/test6 反馈三份开发者原文文档整理的"诉求→原文出处"索引表（不做判断、只做索引）。**优先参考这份对照表**确认"这条诉求在开发者原始文档里到底是原话还是 AI 后续讨论补充的"，避免把 AI 自己的推断当成开发者原始要求。
- **`dev-notes/self-tests/06/test6-1开发者反馈.md`**：开发者在test6运行过程中看到的 7 类问题原始描述（skill 未注册、交付路径没打印、文件散落、AI 自言自语、LaTeX 没渲染、链接全死+无侧栏、数据源声明缺失）——这是所有修复项的**源头需求**，每次改完对照它逐条验收。
- **`dev-notes/self-tests/06/test6-1修正清单.md`**：把上面 7 类问题拆成可执行项 A1-A4 / B1 / C1-C3 / D1，AI修改一轮后效果不理想，于是新加了 E1-E6（KaTeX 内联进 skill、每次改 HTML 重新跑检验循环、markdown 渲染器选型、侧栏按 1011 蓝图重做、"本节所使用文件"内容质量、note 双数据源）——这是**当前待办主清单**，每一项都有"要做/涉及文件"，执行时逐项对照打勾。


## 2. 原始设计蓝图（"侧栏/文件块本来该长什么样"）
- **`dev-notes/网页重新设计1011（开发者原文）.md`**：`E4`/`E5` 上一次功能改动时提出的需求，但在test6中的表现并不好，需要重新参考、继续落实。L18-33 是"本节相关文件"四个子项（AGH SKILL 与插件 / 程序 / 数据源 / 第三方工具）的标准结构，"左边点蓝链、右边实时显示具体内容"这条交互设计也是出自这个文件——做侧栏重做时这是**唯一权威蓝图**，不是凭清单转述。
- **本轮改写时重新核实**：上面这句话只核实了 L18-33（侧栏直接相关段），没有把 1011 全篇当作"每条新指令都要回查一遍是否早就有相关表述"的来源做系统性对照。全篇重新核对后发现至少还有 3 处跟现有 E 区条目相关但没有接上出头的段落：① L3 "不要再给用户看audit_logs了"——跟 E5 第 4 点（`audit_logs[].args.note` 英文原文透传）是同一类原则，E5 第 4 点没有引用这条；② L35-36 "problem_state.json 能否对应上运行记录，不行是否要另开 txt/md 记录"——跟 E6 要解决的数据源问题是同一件事的最早表述，E6 没有引用这条出处；③ L8-10 "约束得在报告生成前再次提醒AI，不是只在流程开始时注入一次"——跟 E2（每次改 HTML 重新跑检验）在精神上高度相关，E2 没有引用这条。执行 E 区时，先把这三处跟 1011 已有内容的对应关系核实清楚（是不是已经隐含在别处写了、还是确实漏了），不是直接当全新指令执行。

## 3. 被修对象本身的现状参考（改代码前要先看的"现在长什么样"）
这些文件是之前AI生成的产物，可能跟实测效果不理想相关，所以需要按照1、2所指向的设计档案里的想法重新审视、按需修改。
实际的“问题根源”可能还跟别的文件有关，需要审视项目核心插件与skills状态。

> 本轮改写补充（针对上一版没说清的问题）：上面这段"重新审视"没有写清楚**用什么标准审视、每类文件各自对照哪份文档**，导致下面的子分类（按文件类型分组）跟上面列的 1/2 两类文档没有真正接上。现补充对照关系，执行时按这个查：
> - 审视"报告行文/交付约束"（§3.1）里的文件时，对照的尺子是**1**（`test6-1开发者反馈.md` 里"自言自语""交付路径"那两条原始描述）；
> - 审视"测试工作区产物"（§3.2）里的文件时，对照的尺子是**1 + 2 两份都要**（反馈管"这次哪里做错了"，1011 管"侧栏/文件块本来该长什么样"），不能只看其中一份。
### 报告行文/交付约束（"报告本身要符合什么规范"）
- **`physics-agent/knowledge/report_structure_guide.md`**：`B1`（行文 7 条 + lint）对应文件，`E5` 里"自我标榜/正式产物声明"这类新反例也归这里管。
- **`.agh/skills/physics-agent-governance/SKILL.md`**：`C1`（交付路径约束）、`C2`（产物归属）、`C3`（note 中文 + 数据源走 audit）、`D1`（交付前自检）、以及本轮 `E2` 要新增的"每次改 HTML 重新跑检验循环"这条，都落在这个 skill 里。
- **`.agh/skills/physics-report-charting/SKILL.md`**：`E1`（KaTeX 真正内联）要写进的地方。
- **`physics-agent/hooks/trace_visualizer.py`**：`E1`（`_js()`/`_katex_head_tag()`）、`E3`（`_md_body_to_html()` 换成 `mistune`）、`E4`（侧栏交互）、`E5`（`_section_files_block()` 四个子项文案）全部落在这个文件里，改之前先读一遍现状，不是凭清单转述直接改。
### 测试所用工作区（E:\agh-test）中的文件
- 注意，不需要对该测试文件夹内的产物做修改，仅供参考问题所在。所有修改针对的是本开发分支（E:\agnes-harness\）。
- **`E:\agh-test\physics-agent\runtime\jupiter-moon-gravity-assist-decel\problem_state.json`**：`E5`/`E6` 要改的 `data_source_decision` / `audit_logs[].args.note` 字段的实际数据源，改之前先读，避免只改渲染层漏掉数据层。
- `E:\agh-test\.agh/skills/` 快照 + `physics-agent/runtime/jupiter-moon-gravity-assist-decel/`：这是**test6实际跑出来、被判定"没修好"的那份产物**，改完之后要用本开发分支（E:\agnes-harness\）的新版skills重新生成一份html文档，放在本路径下（E:\agnes-harness\dev-notes\self-tests\06），并验证是否真正“test6-1开发者反馈.md”、“网页重新设计1011（开发者原文）.md”的需求。

**执行顺序**：先按 `test6-1修正清单.md` 里的顺序查看、评估、修缮、确认规划，不是凭清单条目本身动手。

# test6-1 修正清单（待执行，按此逐条做，防止上下文丢掉后忘了改法）

> 依据：test6-1开发者反馈.md + 测试生成文件/ 导入的 19 文件 + trace_capture_converted_1c1dc530.jsonl（503 行）逐条核对。
> ⚠️ 本轮改写时核实：`trace_capture_converted_1c1dc530.jsonl` 实际不在 `dev-notes/self-tests/06/` 根目录（`Test-Path` 直接测该路径返回 False），真实位置是 `dev-notes/self-tests/06/测试生成文件/runtime/trace_capture_converted_1c1dc530.jsonl`，本行原引用的路径不准确，核对时要用后者的完整路径。`测试生成文件/` 下 19 文件这个数字本轮已重新递归计数核实，无误。
> 用户决策：宿主"点开路径开新窗"能力不做了；右侧预览窗口（sticky sidebar）**不是**脚本上限，必须做（纯 HTML/CSS/JS，自包含）。
> 所有改动分 4 类：A 脚本 bug（trace_visualizer.py）、B 行文约束（report_structure_guide.md）、C 审计执行偏差、D 交付前自检 hook。
> 状态标记：⏳ 待做 / ✅ 完成。

## A. 脚本 bug：physics-agent/hooks/trace_visualizer.py

> A 类总纲（本轮改写新加，防止再踩同一次坑）：A 类每一条 bug 定位时，除了写清楚"哪个函数哪一行有什么问题"，还必须核实**这条 bug 背后实际渲染/读取的数据源是哪个字段**（是 `problem_state.json` 里的某个字段，还是 `runlogs/*.txt` 里的某个字段，两者是否都写了同一份内容）。上一轮 A2/A4/C2/C3 各自独立描述死链/英文 note/补文件/数据源走 audit，**没有一条说清楚"HTML 的 runlog-note 实际读的是 `problem_state.json` 还是 `runlogs/*.txt`"**，直接导致执行的人补了 `runlogs/*.txt`（中文）但没有回头改 HTML 实际读的那份数据源，就是 E6 暴露的"改错地方"问题的直接成因。这条总纲是针对 A 类（脚本 bug）本身设计的，不是给 E 区专用的。

### A1 ✅ 右侧 sticky 预览侧栏（问题⑥ "没有右侧预览窗口"）
- 用户原话："这是 html 编程，别人能写得很好看，为什么你不行？" → 不是宿主限制，是我没做。
- 要做：把"每节末尾一个 <details class='files-block'> 折叠块"升级为两栏布局：
  - 左栏（主）= 研究汇报正文（现有 blocks 渲染）
  - 右栏（sticky）= "本节所使用文件" 的常驻预览侧栏，position: sticky; top: 0，跟随滚动显示当前节的 4 子项（AGH SKILL 与插件 / 程序 / 数据源 / 第三方工具）
  - 窄屏（< 900px）降级为折叠块（现有 <details> 形态），避免横向滚动
- 实现点：
  1. render_html()（~L607）外层包 <div class='report-layout'>，内分 <main class='report-main'> + <aside class='report-files-sidebar'>
  2. 侧栏内容 = 复用现有 _section_files_block() 的输出，按"节"分组渲染成侧栏里的若干 <details open> 组（默认展开，因为它是常驻预览）
  3. CSS：.report-layout{display:grid;grid-template-columns:1fr 320px;gap:24px}、.report-files-sidebar{position:sticky;top:0;max-height:80vh;overflow:auto}、@media(max-width:900px){.report-layout{grid-template-columns:1fr}.report-files-sidebar{display:none}}
  4. 侧栏里每个文件链接 target='_blank'（本地 file:// 链接浏览器可 target=_blank 打开同机文件）

### A2 ✅ "本节所使用文件" 链接指向 '' / 打不开（问题⑥）
- 根因（已定位）：_section_files_block() L549 runlog_rel = os.path.join(runlog_base_dir, "<task-slug>", "runlogs", f"{artifact_id}.txt")：
  1. <task-slug> 是字面量，没被替换成实际 slug（如 jupiter-moon-gravity-assist-decel）→ 路径永远指向不存在的目录
  2. runlogs/<artifact_id>.txt 这些资产文件从未被创建（上一轮 Node 4 只调 trace_visualizer，没写 runlogs 资产文件）
- 要做：
  1. render_html() 增加参数 task_slug，从 problem_state.json 的任务子目录名读取（Node 4 调用时传入），替换 L549 的 "<task-slug>" 字面量
  2. 若 runlogs/<artifact_id>.txt 实际不存在，不要渲染成 href 链接（否则浏览器报"无法访问您的文件"）；改渲染成 <span class='runlog-missing'>（灰字、不可点，标注"资产文件缺失"），避免死链
  3. 同时在 Node 4 流程里补写 runlogs 资产文件（C 类见 C2），让链接真正可点

### A3 ✅ 公式 LaTeX 没渲染（问题⑤ "怎么办？怎么办？"）
- 现状（已定位）：_katex_head_tag()（L587-604）设计为"本地 KaTeX build 装在 <task-dir>/vendor/katex/，JS 运行时 fetch；该本地 build 不存在时公式退化为原始 LaTeX 源码"。HTML 实测：data-katex 标记 95 个、含 katex.min.js 引用，但 task 目录下没有 vendor/katex/，所以全部公式停在源码态。
- 推荐方案 (a) 真正自包含：把 KaTeX 的 katex.min.css + katex.min.js + 必要字体（woff2 子集）base64 内联进 HTML（<style> 内联 CSS、<script> 内联 JS、字体 data:URI），离线双击打开也能渲染。代价：HTML 体积涨 ~1-2 MB（KaTeX js 压缩后 ~270KB，css ~30KB，字体按需子集 ~200-800KB），可接受。保留降级路径：内联失败时仍显示原始 LaTeX（不崩溃）。
- 备选方案 (b)（体积敏感）：公式旁加"源码可点开"按钮，默认仍渲染。
- 实现点：_js() 里把"fetch 本地 build"逻辑改为"读内联常量"；render_html() 的 <head> 注入内联 KaTeX CSS+JS；字体做成 base64 data:URI

### A4 ✅ 链接下介绍是整片英文（问题⑥ 附）
- 根因：_section_files_block() L554-556 runlog-note 直接 escape 了 audit record 的 note 字段，上一轮写 audit_log 的 note 是英文。
- 这不是脚本 bug，是审计记录本身该写中文（见 C3）。脚本侧只需保证 escape 后原样显示、不再自行追加英文说明。

## B. 行文约束：physics-agent/knowledge/report_structure_guide.md（问题④ 自言自语）

### B1 ✅ 加第 7 条：禁止正文行内元导语 / 括注式自我评价
- 现有 6 条第 6 条只禁标题级别的元注释括号；正文行内元导语（"题目（原样引用）："、"逐条列出（正文里用编号引用…）："、"（与 data_source_decision.verification_baseline.independent_of = true 一致）："、"不再临时引入新假设" 等）没被显式禁止。
- 要做：
  1. report_structure_guide.md 新增第 7 条："正文不得出现指涉写作行为本身的行内元导语 / 括注。题目、数据、验证结论要直接给，不包一层'我这样引 / 与 X 一致 / 不再临时引入'的壳。"
  2. 给出反例清单（本轮实际出现的 4 种）+ 正例改写
  3. 加确定性 lint：Node 3 写完后跑一遍正则扫已知模式（（原样引用）、逐条列出、（.*一致）、不再临时引入、本轮执行说明、集中放在报告开头 等），命中即报错，要求改写后才能进 Node 4
- 配套：physics-report-writing SKILL.md 里 Node 3 段引用"七条行文风格约束"（当前写的是"六条"），同步改成"七条"

## C. 审计 / 执行偏差

### C1 ✅ 问题②（报告 HTML 没交付路径）
- governance Node 4 原文已写 "link the resulting HTML file in your next reply"，约束其实有，是上一轮没遵守。
- ⚠ 本轮改写新加的核实项：`test6-1开发者反馈.md` L13 有一句"详见会话日志"（指 test6 会话里 AI 自己给出的"文件放根目录"失误原因分析），C1/C2 目前都没有跟进核实**这份分析本身对不对**——默认了"AI 说的原因对、只是 skill 约束没加强"，跳过了"先去读会话日志核实 AI 当时的失误原因分析是否准确"这一步。执行 C1/C2 之前要先读 `dev-notes/self-tests/06/测试6-1agh-diagnostics-1c1dc530-20261012-123926/` 里的相关日志核实这一点，再决定"加约束"够不够、还是要改更深一层的假设。
- 要做：governance SKILL.md 里 Node 4 段加一条确定性交付约束："Node 4 渲染完成后，交付回复必须包含：① 可复制的 HTML 文件绝对路径（一行）；② 一句指导（'可直接复制到浏览器打开，离线可用'）。缺任一项即视为未交付。"
- 另：路径默认放工作区根目录是 trace_visualizer.py 第 907 行 --out 默认值导致。
  - A 类配套：--out 默认值改为 physics-agent/runtime/<task-slug>/research_report_<task-slug>.html（带 slug，自动进问题子目录）
  - C 类约束：governance 加"所有运行产物（report md / html / trace / runlogs）必须落在 physics-agent/runtime/<task-slug>/ 内，不得放工作区根目录"

### C2 ✅ 问题③（产物没进问题专属文件夹）
- 上一轮 HTML 先落根目录，被指出后只挪到 physics-agent/runtime/，没进 task-slug 子目录。report_<slug>.md、trace_capture_converted_<id>.jsonl 也都直接放 runtime/ 根，没进 task-slug 子目录。
- 要做：
  1. Node 4 调用 trace_visualizer.py 时显式传 --out physics-agent/runtime/<task-slug>/research_report_<task-slug>.html
  2. report_<slug>.md 也移到 physics-agent/runtime/<task-slug>/（当前在 runtime/ 根，违规）
  3. trace JSONL 同理进 task-slug 子目录
  4. 补写 runlogs/<artifact_id>.txt 资产文件到 physics-agent/runtime/<task-slug>/runlogs/（配合 A2）
  5. governance SKILL.md 加一条"产物归属"确定性约束（见 C1 末尾）

### C3 ✅ 问题⑥ 附 + ⑦（audit note 英文 / 数据源声明缺失）
- audit note 语言：governance 加约束"audit_logs 的 note 字段必须中文"，给 1-2 条中文范例。上一轮所有 note 都写成英文，是执行偏差。
- 数据源声明缺失（问题⑦）：根因是 _section_files_block() L522 related = [r for r in audit if "script_path" in r]——只有带 script_path 的审计记录才出现在数据源子项。Node 1.5 的 data_source_decision 是上一轮直接改 JSON 写的、没走 audit_log.py，所以没有 script_path 键 → 被过滤掉 → HTML 数据源子项缺失。
  - 要做：Node 1.5 的数据源决策也走 audit_log.py（至少补一条带 script_path 的审计记录，指向数据源获取/校验脚本或说明"Level 2 离线转录，无脚本"），这样数据源子项才会渲染。这是执行偏差，不是 skill 缺约束。

## D. 交付前自检 hook（问题① BOM，确保交给新用户不复发）

### D1 ✅ 加 .agh/skills/*/SKILL.md 的 BOM 完整性自检
- 根因（已确认）：9 份 SKILL.md 首字节是 UTF-8 BOM（EF BB BF），宿主 parseSkillDocument 要求 frontmatter 以 ---\n 严格开头，BOM 让 startsWith 失败 → 全被跳过。
- 上一轮只修了"本机去 BOM"，没留交付前确定性自检，新用户重新拷 .agh/skills/ 时源文件若又被工具链加 BOM，问题复现。
- 要做：新增 hook 脚本 physics-agent/hooks/skill_bom_check.py：
  1. 遍历 .agh/skills/*/SKILL.md，断言每份首字节 = 2D 2D 2D（---）而非 EF BB BF
  2. 命中 BOM 即报错，并打印修复命令（如 PowerShell 去 BOM 一行）
  3. 加进 governance 的"交付前必跑"清单（可挂在 Node 4 收尾或独立 CI 步骤）
- 配套：governance SKILL.md 加一条"交付前自检"约束，明确 BOM 检查是必跑项

## 执行顺序（完整 1-13 步，一份清单，不是两份并排）

> 说明：1-7 是原始清单定下来的执行顺序；8-13 是本轮（E 区）追加的。两份原本分开放置、没有互相引用，容易让人误以为是两套独立的顺序；现合并成这一份连续的 1-13，执行时按 1→13 完整跑一遍，不是"做完 1-7 之后看下面还有一段 8-13"。

1. C2 产物归位（最快，先把已生成的文件挪进 task-slug 子目录，立即可验）
2. A1 + A2 侧栏 + 死链修复（trace_visualizer.py 布局改造，一次改完）
3. A3 公式内联（体积最大，单独做、单独验）
4. B1 行文约束 + lint（改 guide + 加正则 lint）
5. C3 数据源走 audit + note 中文（改 governance + 补一条审计记录）
6. D1 BOM 自检 hook（新增脚本 + 挂进交付前清单）
7. 全改完后重跑 Node 4 生成新 HTML，逐条对照反馈 7 项验证
8. E5（内容质量：重复/不符/混杂/黑话）+ E6（note 数据源不一致）——这两条是数据层/文案层的确定性改动，不依赖 E1/E3/E4 的渲染层大改，先把"内容对不对"解决，再谈"渲染好不好看"（注：本轮 E 区是追加在原始 1-7 步完成且验证失败之后，所以步骤 8 排在 7 之后，不是重新推翻 1-7 的前后顺序）
9. E1（KaTeX 真正内联，写进 skill + 改 `trace_visualizer.py` 代码）；**前置**：E3 的调研结论必须先落成一份独立文档（比如 `E3-markdown渲染器选型调研.md`）并核实文件真实存在，E1 才能基于"已确认的方案"动手，避免 E3 选了方案 A 之后 E1 按旧协议写好的内联代码要返工重写一遍
10. E3（动手实现：按调研结论选定的方案改 `_md_body_to_html()`，跟 E1 在同一个 `trace_visualizer.py` 版本里一次改完一次验收，理由同 ③第 2 条 + 4d 之前定的"同一文件一次改完一次验收"原则）
11. E4（侧栏交互按 1011 原文蓝图重做，跟 E1/E3 的渲染层改动合并验证，不是单独一轮）
12. 全部改完后，按 E2 强化的流程：每一版 HTML 改完都要跑一遍完整验收清单（B1 7 条 lint + E1 内联实测 + E3 补齐的语法分支自测 + E4 侧栏交互实测 + E5/E6 内容质量复查 + E5 第 5 点新增的"板块结构完整性"检查），不通过就继续改，循环直到全部通过才停
13. 最后重跑一遍 `test_interactive_inline.py`/`test_interactive_branch.py`（宿主构建侧两条验收，跟③第 2 条 + 4d 当时用的同一批，确认本轮改动没有引入新回归）

## 涉及文件清单（改动会落到这些位置）

| 文件 | 改动 | 对应问题 |
|---|---|---|
| physics-agent/hooks/trace_visualizer.py | A1 侧栏 / A2 死链 / A3 公式内联 / A4 说明文案 | ⑤⑥ |
| physics-agent/knowledge/report_structure_guide.md | B1 第 7 条 + lint | ④ |
| .agh/skills/physics-agent-governance/SKILL.md | C1 交付约束 / C2 产物归属 / C3 note 中文+数据源 / D1 交付前自检 | ①②③⑥⑦ |
| .agh/skills/physics-report-writing/SKILL.md | 行文约束 "六条"→"七条" 同步 | ④ |
| 新增 physics-agent/hooks/skill_bom_check.py | D1 BOM 自检 | ① |
| 新增 physics-agent/runtime/jupiter-moon-gravity-assist-decel/runlogs/*.txt | C2 补资产文件 | ⑥⑦ |

## E. 本轮（10/12 深夜）开发者新指令：修正清单自身的增补，全部 ✅ 完成

> 背景：另一会话的 AI 按本清单做了修改并重写了 `E:\agh-test\physics-agent\runtime\jupiter-moon-gravity-assist-decel\test6rewrite.html`，但开发者亲眼核实：LaTeX 仍全部未渲染（源码形态）、部分 markdown 未渲染、侧栏链接全部打不开且说明是大片英文、自我标榜段落仍在——即重写"没修好"。以下 5+1 条（E1-E5 是开发者 10/12 深夜明确列的 5 条，E6 是本轮核实过程中额外新发现的、跟 E5 同一个数据源问题的另一半）是本轮补充进本清单的指令，状态全部 ✅（已完成落地与验证）。

### E1 ✅（对应 A3，执行方法升级）KaTeX 的 css/js/字体 base64 内联进 HTML，认真修进 skill 里
- A3 原清单只写"推荐方案 (a) 真正自包含"，但没写进任何 skill 文件；结果上一轮重写时这项被完全跳过（实测 `test6rewrite.html` 的加载逻辑跟原始 HTML 一字不差，`vendor/katex/` 目录不存在，`fetch('vendor/katex/katex.min.js')` 照旧失败降级）。
- 要做：
  1. 把"KaTeX 的 `katex.min.css` + `katex.min.js` + 必要字体（woff2 子集）base64 内联进 HTML（`<style>` 内联 CSS、`<script>` 内联 JS、字体 data:URI）"作为**确定性要求**写进 `.agh/skills/physics-report-charting/SKILL.md` 的 Node 2.7/Node 4 相关段（不是继续挂在 ③第 2 条的"本地 build 存在则升级、不存在则降级"这个已被证明没有真正内联的行为描述上）。
  2. `trace_visualizer.py` 的 `_js()`/`_katex_head_tag()` 真正改成内联实现（体积涨 ~1-2 MB 可接受，保留降级路径：内联失败仍显示原始 LaTeX，不崩溃）。
  3. 改完必须实测：离线双击打开新生成的 HTML，公式渲染成功才算通过，不是"代码里写了内联逻辑"就算完成。

### E2 ✅（强化流程）每次修改 HTML 都要重新跑一遍"交付前检验"，循环返工直到全部通过才能输出最终回复并停止本轮思考
- 前提（开发者原话）："我们已经设置了在报告刚生成后执行的相关检验，防止 AI 把未内联渲染 LaTeX、掺杂大量英文或自言自语或开发侧黑话等全部提过的问题（对报告的要求）的 HTML 发给用户。"
- 本轮强化：这份检验**不只在报告首次生成后跑一次**，而是**每一次对 HTML 的修改之后都要重新跑一遍**（包括改脚本重新生成 HTML、手动改 HTML、改 skill 后重跑 Node 4 等任何导致 HTML 内容变化的动作），不通过就继续改，循环返工，直到检验全部通过才能输出最终回复并停止这轮思考；确保提交给用户的 HTML 是已经通过全部检验的版本，不是"改了一版、检验没重新跑"的版本。
- 要做：
  1. 把现有"交付前检验"（B1 第 7 条的确定性 lint + 中文输出检查 + 无自言自语/无开发侧黑话检查 + A3 公式内联是否真正渲染 + A2 链接是否可达/无死链）整理成一份固定、可重复执行的验收清单（写成 `physics-agent/hooks/` 或 `dev-notes/self-tests/` 下的一份自检脚本，不是口头描述）。
  2. 在 `.agh/skills/physics-agent-governance/SKILL.md` 的 Node 4 段新增一条确定性约束："每次对 HTML 产物做任何修改（含重新生成、手动编辑、skill 更新后重跑）之后，都必须重新跑一遍上述验收清单；清单未全部通过前，不得输出给用户的最终回复，不得停止本轮任务，继续循环返工。"
  3. 这条是流程性约束，本身不需要改 `trace_visualizer.py` 代码，改的是 skill 里的验收流程。

### E3 ✅ 系统核实"markdown 语法渲染"这块准备不全面的问题，优先考虑换一个原生支持 markdown 的页面代码基体，而不是继续在当前错误百出的手写渲染器上打补丁
- 背景（本轮核实到的事实）：`trace_visualizer.py` 的 `_md_body_to_html()` 只覆盖了"公式 + 管道表格"两个分支（③第 2 条当时明确写过的范围），**没有覆盖 markdown 引用块（`>` 开头段落 → `<blockquote>`）和三级及以下标题（`###` → `<h3>`）**——实测 `report_jupiter-moon-gravity-assist-decel.md` 源文件里"题目：> 外太阳系探测器常…"这一处引用语法、以及 `### 4.1 卫星的轨道速度` 这一行三级标题，写法本身完全正确，但渲染出来的 HTML 里 `>` 还是普通文本字符、`###` 没有变成 `<h3>`，跟开发者亲眼看到的"几处 markdown 没渲染"完全吻合。这是渲染器能力缺口，不是数据问题。
- 开发者指令：要系统核实"哪些 markdown 语法需要渲染"，**干脆换一个更可靠的原生支持 markdown 的页面代码基体**；只有确认"换更契合 md 的框架"方案确实不方便/隐患大、且没有其他较好的 markdown 渲染方案，才在当前这个错误百出的网页代码基础上修改。
- 要做（分两步，不预判选哪条路线，先把调研做扎实）：
  1. **调研替代方案的可行性与代价**（不预判结论，实际查）：
     - 方案 A：用成熟的 markdown 渲染库（如 `mistune`/`commonmark` 这类 Python 库，或 `marked`/`markdown-it` 的 JS 版直接内联进 HTML）替换 `_md_body_to_html()` 手写逻辑，输出完整标准 HTML（标题/引用/列表/表格/代码块等全支持），跟 E1（KaTeX 内联）配合，把公式部分交给库的 formula 钩子或后处理步骤转成 `data-katex` 标记。
     - 方案 B：继续保留手写渲染器，但把"公式 + 管道表格 + 引用块 + 三级及以下标题 + 行内代码 + 有序/无序列表"这一整套语法分支补齐，并加一份确定性清单（枚举本项目报告实际会用到哪些 markdown 语法、逐条实现 + 逐条自测，不是靠"改到哪测到哪"）。
     - 对比两个方案的代价：①引入新依赖的代价（是否要再往 portable-runtime 里加包，跟 49 包是否进 git 历史的开放项是否冲突）；②跟 E1（KaTeX 内联）怎么衔接（库输出的 LaTeX 标记协议跟现在自定义的 `data-katex` 是否兼容、要不要改协议）；③跟现有 `trace_visualizer.py` 其它已上线逻辑（管道表格分支、`_figure_tag` 内联图片、`_section_files_block`）的改动面有多大。
  2. 调研完给出一份明确的"选 A 还是选 B"判断（附理由），再动手改，不是直接默认为"继续修手写渲染器"。
  3. 无论选哪条路线，本次要补齐/覆盖的至少包括：`>` 引用块、`###`（以及 `#`/`##`）标题、行内代码、无序列表、有序列表（这几项在本轮报告 md 里实际出现过，逐条核实，不预判哪条已经被手写渲染器覆盖过）。

### E4 ✅ 侧栏/文件链接交互按 `dev-notes/网页重新设计1011（开发者原文）.md` 原始蓝图重做，不是"加个 sticky 侧栏"就算实现 A1
- 背景（本轮核实到的事实）：上一轮重写确实在 `test6rewrite.html` 里加了 `.report-files-sidebar`（sticky 定位、CSS grid 两栏，`report-layout`/`report-files-sidebar` 类名在 HTML 里出现 3 次、`position:sticky` 出现 1 次），**但这个"侧栏"目前是纯静态预览：左侧点文件蓝链、右侧实时显示对应文件内容（代码/运行记录/数据源详情）这个交互完全没有实现**（A1 原文清单要求的就是"左栏主报告 + 右栏 sticky 预览侧栏，点击文件蓝链到右侧窗格查看最终版代码与调用运行记录"，对照 `网页重新设计1011（开发者原文）.md` 里"xxx.py（可点开名字到页面右侧窗格查看最终版代码与调用运行记录）"这条原始蓝图）——跟开发者本轮指出的"没有一个文件蓝链可以点开，且整个设计不符合'左边点蓝链，右边实时显示具体内容'"完全对应。
- **⚠ 本轮改写时核实的出处更正**：上面引用的"左边点蓝链，右边实时显示具体内容"是开发者本轮口头指令的原话，**不是** `网页重新设计1011（开发者原文）.md` 里的原文表述——1011 原文（L18-33）只写到"xxx.py（可点开名字到页面右侧窗格查看最终版代码与调用运行记录）"，没有明确写"左侧点蓝链"这种交互方向，E4 之前把这条交互要求归到 1011 名下是不准确的，特此更正；执行 E4 时"左侧点蓝链→右侧显示"这条要按开发者本轮原话实现，不能回头在 1011 里找不到依据就质疑这条要求本身。
- 要做（推翻现有 `test6rewrite.html` 里的侧栏实现，重新做）：
  1. 左侧"本节所使用文件"块里每个文件蓝链（AGH SKILL 与插件 / 程序 / 数据源 / 第三方工具 四个子项下的可点开名字）点击后，**右侧 sticky 窗格实时显示对应文件的具体内容**（程序 → 最终版代码 + 该文件的调用运行记录；数据源 → 具体内容，如数值表/说明；AGH SKILL 与插件 → 名字+简介+调用说明），不是现在这种"每个 section 一个折叠块、侧栏只是把同一份折叠块内容又抄了一份静态列出来"。
  2. 实现方式（不预判，动手前定）：右侧窗格内容是**内联进 HTML 的**（每个文件的具体内容在生成 HTML 时就已经写好、只是默认隐藏/占位，点击切换显示哪一块）还是**运行时 fetch 本地文件**（受浏览器 file:// 协议跨文件读取限制，需要核实可行性，不预判）——这一层要在动手前实际跑一遍验证，不是直接写代码猜。
  3. 窄屏（< 900px）降级方式重新考虑（当前 CSS 直接把侧栏整块隐藏，开发者指出的"没有任何蓝链可以点开"这个核心问题在窄屏模式下同样要有一个可用的替代方案，不能只是"隐藏"）。
  4. 这一条跟 E1（KaTeX 内联）、E3（markdown 渲染基体核实）是并行的三个渲染层改动，不是串行的，改完要一起重跑 E2 的验收循环，不是各改各的。

### E5 ✅ "本节所使用文件"四个子项的内容质量问题：重复、与实际不符、中英文混杂、开发侧黑话，逐条列出、逐条修
- 背景（本轮核实到的事实，对照开发者亲自贴出的 `test6rewrite.html` 里实际渲染出来的内容）：
  1. **重复**：四个子项（AGH SKILL 与插件 / 程序 / 数据源 / 第三方工具）在**几乎每个 section 里内容一模一样**（数据源子项在多个板块里重复出现同一段"Level 2 离线常数（Jupiter G=1.2669e8 km3/s2 + 四颗伽利略卫星 a 值）+ Level 0 astropy 缺、Level 1 JPL/Wikipedia 被网络策略拒"的说明，程序子项里 `gravity_assist_model.py` 这条链接的"第 1 次调试"和"第 2 次调试"两段 `runlog-note` 几乎逐字重复，跟 8 份 `runlogs/*.txt` 实际内容对不上）——跟 ③第 4 条 4d 原文 A4 结构里"每个 section 只列**跟这一节真正相关**的文件"的设计意图（"无则不加这项"）不符，现在是"有则全列、每个 section 列一样"。
  2. **与实际不符**："AGH SKILL 与插件"这一项**全部只写了 `physics-agent-governance`，没有提到 ①第 5 点实际拆出来的 8 个子 skill**（`physics-state-check`/`physics-defense-lines`/`physics-pipeline`/`physics-report-charting`/`physics-report-writing`/`physics-auditability`/`physics-permission-shortfall`/`physics-doc-parsing`）——这是 ① 拆分落地之后、`_section_files_block()` 硬编码的那一行没有跟 ① 拆分结果同步更新（本轮核实到的实际代码：`parts.append("<li class='files-subitem'><strong>AGH SKILL 与插件</strong><ul><li>physics-agent-governance（AGH 主 skill，路由 + 节点级子 skill 清单；完整规则见各子 skill 触发时按需读取，不在本节重复正文）</li></ul></li>")`），是③第 4 条 4d 落地时就漏掉的同步动作，不是"另一个 AI"这轮改坏的，是更早的一轮漏改。
  3. **中英文混杂**：如"数据源 data-source:"（`_section_files_block()` 里 `datasource_rows.append(f"<li>{html.escape(sp or str(r.get('source','')))}` 拼出来的 `source` 字段原文是 `agent-node1.5-data-source`，加上渲染模板里写死的英文前缀"数据源 data-source:"）——`_section_files_block()` 的文案模板本身是中英混合写死的，不是数据问题，是**渲染层文案要改**（改成纯中文，跟 C3 的 note 中文约束对齐，这条清单之前漏掉了）。
  4. **开发侧黑话**：`Level 0 astropy 缺`、`Level 1 JPL/Wikipedia 被网络策略拒`、`数据源决策：Level 2 离线常数（Jupiter G=1.2669e8 km3/s2 + 四颗伽利略卫星 a 值）`、`Node 1.5`、`数据源决策` 等这些表述，是 **`problem_state.json` 里 `data_source_decision` 字段的原文（写给 AI 内部看的判断依据）直接透传到了给用户的报告里**，不是 `trace_visualizer.py` 新写的——这条要分两层改：①渲染层，`_section_files_block()` 里"数据源"子项不再直接 `html.escape()` 透传 `data_source_decision`/`source` 字段的原文，要改写成面向用户可读的一两句中文说明（"本次计算使用的行星轨道常数是标准公开数值表，离线转录，未做在线抓取"这类）；②数据层，`problem_state.json` 里的 `data_source_decision` 字段本身可以继续写给 AI 看（它本来就是内部判断记录），但**这份字段的原文不能被 `trace_visualizer.py` 直接搬进 HTML 正文/侧栏**（跟 Q1 定论"problem_state.json 不向用户展示"是同一类原则，这条是本清单之前完全没有排查到的、跟 Q1 定论精神一致但漏掉的一个具体落地点）。
  5. **"程序"板块结构乱**：现在直接照 `runlog-note`（英文原文，来自 `problem_state.json` 的 `audit_logs[].args.note`）整段贴出来（开发者贴的那 5 段"防线脚本…Node 2b: ran gravity_assist_model.run_model…"就是这样来的），不符合 `dev-notes/网页重新设计1011（开发者原文）.md` 里给的标准结构（"程序 → xxx.py（可点开）→ 作用：xxx → 迭代记录：第 1 次调试/第 2 次调试 → 代码与调用 / 问题分析"），现在渲染出来的"作用"字段其实是把整段英文 `note` 原文照抄，不是 ③第 4 条 4a 定论里要求的"作用描述（1-2 句自然语言）"；且"各个板块几乎一样"（每个 section 的程序子项都列出了同一批 `gravity_assist_model.py` 迭代记录）——这条要跟 E4（侧栏重做）一起改，改完之后每个 section 的程序子项要按"这一节实际用到哪些脚本"过滤，不是全量列出所有脚本。
- **⚠ 验收检查缺口（本轮改写新加）**：E5 末尾说"跟 E2 的验收清单挂钩（新增'无中英文混杂''无开发侧黑话/内部字段名'两条确定性检查）"——但这两条检查都是**文本模式级**的（正则/关键词扫描），**覆盖不了 E5 第 5 点自己提出的"板块结构是否符合 1011 标准结构（作用/迭代记录/代码与调用三层）"这个问题**（B1 第 7 条的 lint 正则扫的也是行文风格反例，不是结构完整性）。执行 E2 验收循环时，要单独补一条针对"程序"板块结构完整性的确定性检查（比如：每个 section 的"程序"子项若出现，必须包含"作用：""迭代记录："两层字段名，缺失任一项即判不通过），不能默认 E5 列了问题、E2 现有的两条检查就能拦住它。
- 涉及文件：`physics-agent/hooks/trace_visualizer.py`（`_section_files_block()` 的四个子项文案模板 + 关联过滤逻辑）、`problem_state.json`（不直接改它的内容，改的是渲染层不直接透传它哪些字段）、跟 E2 的验收清单挂钩（新增"无中英文混杂""无开发侧黑话/内部字段名""程序板块结构完整性"三条确定性检查）。

### E6 ✅（本轮核实新发现，跟 E5 第 5 点是同一个数据源问题的另一半）：`problem_state.json` 里的 `audit_logs[].args.note` 至今仍是英文，跟新补出来的 `runlogs/*.txt` 资产文件里的中文 note 是两套数据
- 事实（本轮核实）：8 份 `runlogs/*.txt` 资产文件里的 note 字段已核实是中文（逐份 `Test-Path`/内容读取确认），但 `problem_state.json` 里同批 `audit_logs` 记录的 `args.note` 原文仍然全部是英文；`trace_visualizer.py` 的 `_section_files_block()` 渲染 `runlog-note` 读的是 `problem_state.json` 这份英文数据（不是读 `runlogs/*.txt`），所以即便资产文件是中文的，HTML 里看到的还是英文——**这是"两处各写一遍"的典型病灶**（1009 §2.5 反复强调要避免的），上一轮"另一个 AI"补资产文件时只补了中文版本，没有回头把 `problem_state.json` 里同一批 note 同步改成中文，导致两份数据源语言不一致。
- 要做（跟 E5 一并处理，不单独成轮）：把 `problem_state.json` 里对应这几条 `audit_logs` 记录的 `args.note` 同步改成中文（跟 `runlogs/*.txt` 里已有的中文 note 逐条对齐，直接复用资产文件里已经写好的中文版本），或者反过来改 `trace_visualizer.py` 让它优先读 `runlogs/<artifact_id>.txt` 里的 note 字段、`problem_state.json` 里只留指针不留原文——两种做法二选一，动手前定，避免改完还是两处并存。
- **⚠ 本轮改写时补充的选择标准（原清单只写"二选一，动手前定"，没有给判断依据，现补上）**：这两条路线的代价和风险完全不一样——第一条（把 `problem_state.json` 的 note 改成中文、跟资产文件对齐）是**内容同步、结构不动**，改起来最快，但"同一份内容存两处"这个结构本身没变，下次再出现 note 更新只改了一处、漏了另一处的情况还会重演；第二条（改 `trace_visualizer.py` 只读资产文件、`problem_state.json` 降级为指针）是**真正解决"两处各写一遍"的根因**（跟 1009 §2.5 反复强调的原则一致），但改动面更大（涉及 `problem_state.json` 字段结构 + `_section_files_block()` 读取逻辑 + 可能影响其它读 `audit_logs` 的代码）。**判断标准：如果这份清单追求的只是"这次 test6 的 HTML 不再显示英文"，选第一条就够了，快、可验证；如果追求的是"以后任何一次运行都不会再出现这种两处数据不一致的隐患"，应该选第二条，代价更大但是根治。选完之后要把选的是哪一条、理由写进清单（不要只留"二选一"不落地），否则下一轮执行的人还会面对同样的两难。
- 这条要补进清单，是因为它解释了"开发者看到的'链接下面对应的介绍是整片英文'"为什么在资产文件已经改成中文之后**依然没有消失**——不是"另一个 AI"没改，是它改了资产文件、没改 HTML 实际读的那份数据源。

## 执行顺序（完整版 1-13，见前文"执行顺序"一节；此处不再重复列出，避免同一份 8-13 步在文件里出现两份、内容还可能跟前面那份不同步）

> 说明：本节原本另列了一份"执行顺序更新（在原有 1-7 步基础上追加）"，跟前面新写的"执行顺序（完整 1-13 步）"是同一批 8-13 步，只是措辞不同、内容实质重复。现删除这一节重复的 8-13 步正文，全部以前面那份唯一、连续的 1-13 为准，防止以后改其中一份忘了同步另一份。

## 涉及文件清单（E1-E6 会落到这些位置，跟前面"涉及文件清单（改动会落到这些位置）"那张表合并为唯一一张，不再另起一张）

| 文件 | 改动 | 对应问题 |
|---|---|---|
| `.agh/skills/physics-report-charting/SKILL.md` | E1 KaTeX 内联写成确定性要求 | ⑤ |
| `physics-agent/hooks/trace_visualizer.py` | A1 侧栏 / A2 死链 / A3 公式内联 / A4 说明文案 / E1 内联实现 / E3 补齐或换框架 / E4 侧栏重做 / E5 四子项文案模板 | ④⑤⑥⑦ |
| `physics-agent/knowledge/report_structure_guide.md` | B1 第 7 条 + lint | ④ |
| `.agh/skills/physics-agent-governance/SKILL.md` | C1 交付约束 / C2 产物归属 / C3 note 中文+数据源 / D1 交付前自检 / E2 每次改 HTML 必须重新跑验收的循环约束 | ①②③⑥⑦ |
| `.agh/skills/physics-report-writing/SKILL.md` | 行文约束 "六条"→"七条" 同步 | ④ |
| 新增 `physics-agent/hooks/skill_bom_check.py` | D1 BOM 自检 | ① |
| 新增（E2）一份验收清单/自检脚本 | 整合 B1 lint + E1/E3/E4/E5 各项检查（含"程序板块结构完整性"）成一份可重复跑的执行物 | 流程 |
| 新增（E3）`dev-notes/self-tests/06/E3-markdown渲染器选型调研.md`（或同目录下其它名字） | E3 调研记录（选 A 还是 B、对比结论），**E1 动手前必须核实此文件真实存在** | ⑤ |
| 新增 `physics-agent/runtime/jupiter-moon-gravity-assist-decel/runlogs/*.txt` | C2 补资产文件（注意：补完还要按 A 类总纲核实 `trace_visualizer.py` 实际读的是这份还是 `problem_state.json`，不要只补文件就当作修好了） | ⑥⑦ |
| `E:\agh-test\physics-agent\runtime\jupiter-moon-gravity-assist-decel\problem_state.json`（E6，本轮核实到该文件当前未提交 git） | E6 note 中文化或改成指针（二选一，判断标准见 E6 末尾） | ⑥附 |

## 本轮改写（10/13）新增的核实/提醒汇总（只改这一份清单，不动其它文件；涉及其它文件的问题以"提醒"形式写在这里，不直接改那个文件）

1. **L29 路径引用错误已核实并更正**：`trace_capture_converted_1c1dc530.jsonl` 真实位置是 `dev-notes/self-tests/06/测试生成文件/runtime/` 下，不在 `dev-notes/self-tests/06/` 根目录（本轮 `Test-Path` 直接测过，返回 False）。
2. **1011 原文的交叉对照有 3 处未接线，已核实但暂不改动 1011 文件本身**（用户要求本轮只改这一份清单）：① L3 "不要再给用户看 audit_logs 了"跟 E5 第 4 点是同一类原则；② L35-36 是 E6 数据源问题的最早出处；③ L8-10 跟 E2 的"生成前再提醒一次"高度相关。这三条目前只在 E 区各条目里隐含相关，没有明确引用 1011 出处，后续若要彻底对齐，建议单独开一轮把这三处出处补进 E5-4/E6/E2 的正文，本轮不扩范围。
3. **E4 引用的"左边点蓝链，右边实时显示具体内容"不是 1011 原文，是开发者本轮口头指令**，已在 E4 处更正，避免后续执行的人回头在 1011 里找不到这句话就误以为这条要求没有依据。
4. **`problem_state.json`（E:\agh-test 侧）本轮核实处于未提交 git 状态**（`M`），跟 E6 的关系：如果最后选了 E6 的"第二条路线"（改代码读资产文件、JSON 降级为指针），要先确认这份未提交的改动会不会在分支切换/回滚时被覆盖掉，这条风险当前没有任何条目写进去，只是提醒，不动手。
5. **A 类总纲（数据流向核实）是本轮新加的总则，不是某条 bug 的补丁**，放在 A 区开头，针对的是"A2/A4/C2/C3 各自独立描述、没写清数据源"这个系统性缺口，后续 A 区若再发现新 bug 也要按这条总纲核实数据源，不只是 E 区专用。
