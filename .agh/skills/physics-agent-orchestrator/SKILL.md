---
name: physics-agent-orchestrator
description: '物理题的 6 节点 pipeline 路由器：题目属于物理分析、理论推导、大学物理教学阐释、数值建模或竞赛研究类，且需要按结构化流水线执行时，先读这份 skill 判断当前该进入哪个节点、以及该节点必须按需调用 skill_read 读取哪份具体子 skill。无论题目是开放性科研探索还是具备标准解析解的课内多问推导，均适用本流水线。触发信号 = 物理题目性质，不是用户是否点名。'
---

# Physics Agent 节点级 Skill 路由表（1 主 Skill + 8 子 Skill）

收到任何物理分析、理论推导、课内教学阐释或数值求解任务（涵盖开放性科研探索题与经典大学物理标准推导题）时，严禁凭直觉自由跳步。请先通过 `skill_read` 加载主控协议，并在进入对应阶段前按需调用 `skill_read` 读取对应子 Skill：

1. **全局主控与 Node 4 渲染/交付闭环**：`physics-agent-governance`
   - 收到任务时首先读取，掌握全局 6 节点流水线、参考答案隔离（§5，严禁读取 `dev-notes/` 作为答案来源）及 Node 4 交付前强制自检循环（`skill_bom_check.py` + `report_quality_check.py`）。
2. **Node 0 状态检查与任务专属目录初始化**：`physics-state-check`
   - 创建 `physics-agent/runtime/<task-slug>/problem_state.json` 并写入 `session_key`；所有任务产物统一放进 `<task-slug>/` 子目录（详见 `physics-agent/knowledge/path_convention.md`）。
3. **三条确定性防线（量纲门 / 边界门 / 配额退火）**：`physics-defense-lines`
   - 进入数值求解前必读，确保 `dimensional_gate.py` 与 `boundary_gate.py` 真实跑通。
4. **Node 1 / 1.5 / 2a / 2b 核心建模与验证流水线**：`physics-pipeline`
   - 涵盖任务规范（Node 1 提炼一句话核心目标；支持复合多小问解构，课内理论推导题安全约束自然填 N/A）、数据源路由（Node 1.5，基础物理常数优先直接调用标准库或教材公称参数，无需外部网络爬虫；外部复杂数据按权威三档分类与决策树选用并支持 TUN 代理自适应底层穿透）、知识模板与机理核验（Node 2a，防"张冠李戴"；无特定预置模板的基础物理领域直接依据第一性物理定律与 `physics_research_methodology.md` 展开推导）、独立求解与多维验证（Node 2b，支持极限退化检验、解析与数值残差比对、多判据交叉互证等多重严谨理论物理验证范式）。
5. **审计留痕与中文运行记录资产**：`physics-auditability`
   - 每次修改状态或运行脚本后必读：执行写回读回校验、调用 `audit_log.py`（`args.note` 必须为面向用户的简体中文，严禁英文或开发黑话）及 `runlog.py` 生成 `<task-slug>/runlogs/<artifact_id>.txt`。
6. **Node 2.7 数值结果绘图与 Node 4 公式/图表自包含内联**：`physics-report-charting`
   - 决定是否绘制静态/交互图表（`make_report_figures.py`），并确保 Node 4 渲染单文件 HTML 时 100% 离线内联数学公式与图表。
7. **Node 3 增量研究汇报写作与七条行文铁律**：`physics-report-writing`
   - 在每个节点结束时向 `physics-agent/runtime/<task-slug>/report.md` 增量追加章节，严格遵守 `report_structure_guide.md` 八章结构与七条约束（复合多问与教学推导题按二级小节递进组织，优缺点章自适应采用“理论假设与适用局限”，严禁任何行内元导语、自我标榜与内部字段名透传）。
8. **权限缺口与便携运行时快路径（§4 / §4a）**：`physics-permission-shortfall`
   - 遇到写权限受阻或 Python 依赖缺失时必读，优先使用 `physics-agent/third_party/portable-runtime/`。
9. **外部文档按需解析（§6，PDF/扫描件/DOCX）**：`physics-doc-parsing`
   - 仅当用户明确要求解析外部文档时按需读取。
