# dev-notes/ — 仅开发过程文档与参考素材（不进入运行 agent 的可见路径）

> **本目录下的内容不是物理问题分析 agent 的组成部件。**
> 新会话/演示版 agent 不应加载、引用、或以此目录下的任何文件作为操作指令。
> 目录仅用于：开发过程记录、赛事合规要求原文、参考范文、自测脚本。

## 目录约定（供开发者自查"该不该放进这里"）

判定规则：
- 如果某个文件是**告诉开发者"我们为什么这样设计 / 我们要满足哪些赛事要求 / 我参考了哪篇范文"** → 放这里。
- 如果某个文件是**告诉运行 agent"拿到物理题后该做什么、该调用哪个钩子、该遵守哪些门禁"** → 不放在这里（应放在 `.agh/skills/` 或 `program-design/` 下对应位置）。

## 当前内容清单

| 文件/目录 | 原位置 | 定性 |
|---|---|---|
| `competition/项目开发要求.md` | 仓库根目录 | 赛事合规要求原文（开发侧对照清单，非 agent 指令） |
| `competition/黑客松参赛指南.md` | 仓库根目录 | 赛事流程/时间线（开发侧参考，非 agent 指令） |
| `reference-solutions/例题/` | 仓库根目录 `例题/` | 2010/2020/2023 三篇参考范文（PDF + 提取文本），仅用于开发时的思路借鉴 |
| `architecture/project_consensus.md` | 原 `program-design/project_consensus.md` | 开发过程达成的架构决策记录（§0 顶层铁律、题目分工、赛事条款映射等）；**其中给运行 agent 的操作规则，已在 `.agh/skills/physics-agent-governance/SKILL.md` 和 `program-design/knowledge/` 各模板里独立成文，本文件本身不需要被 agent 加载** |
| `self-tests/` | 原 `program-design/hooks/` 下的 `example_*` 与 `test_*` 文件 | 开发者自测样例/脚本，用于证明各钩子本身可运行；**不是**运行 agent 解题时需要的东西，打包演示版时应剔除 |
| `dev-selftest-log.md` | 本目录 | 自测索引：记录每个钩子/脚本"测过、何时测、结果如何"，供开发者复查，不需要被 agent 看见 |
