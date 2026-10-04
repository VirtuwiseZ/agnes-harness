# 打包演示版成果：文件清单与排除规则

## 一句话规则

**"打包演示版" = 把 `dev-notes/` 整个目录排除掉，剩下所有本项目自有文件（`.agh/skills/` + `program-design/`）就是完整的、可直接独立演示的成果。**

`dev-notes/` 是本项目唯一承载"开发过程相关内容"（赛事要求原文、参考范文、架构决策记录、自测样例与留档）的位置；除此之外，运行 agent 需要看到的操作规则、方法论模板、钩子脚本、状态机骨架全部集中在 `.agh/skills/physics-agent-governance/` 和 `program-design/` 两处，且这两处内容在排除 `dev-notes/` 后应当是**自包含、可独立运行**的。

## 具体文件清单（按目录）

### 保留（随演示版一起交付）
```
.agh/skills/physics-agent-governance/SKILL.md          项目"宪法"，跨会话自举入口
program-design/knowledge/                               方法论模板层（5 份，含题域参数 JSON）
program-design/knowledge/space_diving/space_diving_params.json
program-design/hooks/dimensional_gate.py                量纲门禁
program-design/hooks/boundary_gate.py                   边界门禁
program-design/hooks/audit_log.py                       审计日志写入/防篡改校验
program-design/hooks/ode_model.py                       Node 2b 数值模型（数据源无关）
program-design/hooks/requirements.txt                    钩子层第三方依赖边界声明
program-design/problem_state_schema.md                   状态机字段规范
program-design/runtime/problem_state_template.json       状态机通用空骨架（新题从这里起步）
```

### 排除（属于开发过程，不进入演示版）
```
dev-notes/                                             （整个目录，包含以下全部子项）
├── competition/项目开发要求.md
├── competition/黑客松参赛指南.md
├── reference-solutions/例题/（2010/2020/2023 三篇范文 PDF + 提取文本）
├── architecture/project_consensus.md
└── self-tests/（example_* / test_* / problem_state_2023_worked_example.json / dev-selftest-log.md）
```

## 排除 `dev-notes/` 后，演示版如何自包含

1. 运行 agent 拿到一道**新的、没有范文的**物理题时，第一步是加载 `.agh/skills/physics-agent-governance/SKILL.md`（跨会话自举协议会要求 agent 检查 `program-design/runtime/problem_state_template.json` 是否存在，并按任务起一份自己的实例文件——不会误触任何 2023 题的旧记录，因为那份记录已经不在运行路径里）。
2. 数据源决策、方法论模板、三道防线钩子，全部只需要 `program-design/knowledge/` + `program-design/hooks/` 里保留的那部分，不需要读 `dev-notes/` 里的任何文件。
3. `dev-notes/self-tests/dev-selftest-log.md` 是**开发者**复查"哪些钩子跑通过、结果如何"用的留档，不进入 agent 的调用路径，可以放心排除。

## 后续新增开发产出时，先问自己一个问题

"这个文件是告诉运行 agent 该怎么做题的，还是告诉开发者我们当时为什么这么设计的？"
- 前者 → 放 `.agh/skills/` 或 `program-design/`（保留进演示版）
- 后者 → 放 `dev-notes/`（演示版直接排除，不用逐个挑）
