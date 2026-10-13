/**
 * Physics Agent Orchestrator — 流程路由器（AGH 插件，`inject: ['skills']`）
 *
 * 职责：当会话收到"物理分析/物理建模/数值求解"类题目时，主动提醒 Agent 按
 * 6 节点 pipeline 执行，并给出"1 主 Skill + 8 子 Skill"的分步按需加载路由表。
 */

export const physicsAgentOrchestrator = {
  inject: ['skills'],
  apply(ctx) {
    ctx.skills.register({
      name: 'physics-agent-orchestrator',
      description:
        '物理题的 6 节点 pipeline 路由器：题目属于物理分析/建模/数值求解类、且需要按结构化流水线执行（而非凭直觉自由建模）时，先读这份 skill 判断当前该进入哪个节点、以及该节点必须按需调用 skill_read 读取哪份具体子 skill。触发信号 = 题目性质，不是用户是否点名。',
      body: [
        '# Physics Agent 节点级 Skill 路由表（1 主 Skill + 8 子 Skill）',
        '',
        '收到任何物理分析、物理建模或数值求解任务时，严禁凭直觉自由跳步。请先通过 `skill_read` 加载主控协议，并在进入对应阶段前按需调用 `skill_read` 读取对应子 Skill：',
        '',
        '1. **全局主控与 Node 4 渲染/交付闭环**：`physics-agent-governance`',
        '   - 收到任务时首先读取，掌握全局 6 节点流水线、参考答案隔离（§5，严禁读取 `dev-notes/` 作为答案来源）及 Node 4 交付前强制自检循环（`skill_bom_check.py` + `report_quality_check.py`）。',
        '2. **Node 0 状态检查与任务专属目录初始化**：`physics-state-check`',
        '   - 创建 `physics-agent/runtime/<task-slug>/problem_state.json` 并写入 `session_key`；所有任务产物统一放进 `<task-slug>/` 子目录（详见 `physics-agent/knowledge/path_convention.md`）。',
        '3. **三条确定性防线（量纲门 / 边界门 / 配额退火）**：`physics-defense-lines`',
        '   - 进入数值求解前必读，确保 `dimensional_gate.py` 与 `boundary_gate.py` 真实跑通。',
        '4. **Node 1 / 1.5 / 2a / 2b 核心建模与验证流水线**：`physics-pipeline`',
        '   - 涵盖任务规范与私密预判（Node 1/1a）、数据源路由（Node 1.5，按《物理竞赛与仿真数据源权威指引》三档规则决策，若遇 `web_fetch` 非公网 IP 报错可按 `notes-for-ai/network_and_vpn_guidelines.md` 走 Python OS 底层网络栈自适应直连）、知识模板机制匹配检查（Node 2a，防"张冠李戴"）、独立建模求解与交叉验证（Node 2b）。',
        '5. **审计留痕与中文运行记录资产**：`physics-auditability`',
        '   - 每次修改状态或运行脚本后必读：执行写回读回校验、调用 `audit_log.py`（`args.note` 必须为面向用户的简体中文，严禁英文或开发黑话）及 `runlog.py` 生成 `<task-slug>/runlogs/<artifact_id>.txt`。',
        '6. **Node 2.7 数值结果绘图与 Node 4 公式/图表自包含内联**：`physics-report-charting`',
        '   - 决定是否绘制静态/交互图表（`make_report_figures.py`），并确保 Node 4 渲染单文件 HTML 时 100% 离线内联数学公式与图表。',
        '7. **Node 3 增量研究汇报写作与七条行文铁律**：`physics-report-writing`',
        '   - 在每个节点结束时向 `physics-agent/runtime/<task-slug>/report.md` 增量追加章节，严格遵守 `report_structure_guide.md` 八章结构与七条约束（严禁任何行内元导语、自我标榜与内部字段名透传）。',
        '8. **权限缺口与便携运行时快路径（§4 / §4a）**：`physics-permission-shortfall`',
        '   - 遇到写权限受阻或 Python 依赖缺失时必读，优先使用 `physics-agent/third_party/portable-runtime/`。',
        '9. **外部文档按需解析（§6，PDF/扫描件/DOCX）**：`physics-doc-parsing`',
        '   - 仅当用户明确要求解析外部文档时按需读取。',
      ].join('\n'),
    })
  },
}
