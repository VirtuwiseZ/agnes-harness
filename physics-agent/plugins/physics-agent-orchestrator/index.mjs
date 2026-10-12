/**
 * Physics Agent Orchestrator — 流程路由器（AGH 插件，`inject: ['skills']`）
 *
 * 职责：当会话收到"物理分析/物理建模/数值求解"类题目时，主动提醒 Agent 该按
 * 6 节点 pipeline 执行、且第一步必须先读哪份 skill；把"该用哪个 skill 推进
 * 到哪一步"这层调度逻辑从纯文字说明（`.agh/skills/physics-agent-governance/SKILL.md`
 * 正文里已经写过一遍）升级成由本插件注册进宿主 skill 目录的独立条目。
 *
 * 当前阶段（①第 2 点，"不删改现有 skill"）：
 * - 本插件贡献的这份 skill 条目只承载"路由/提醒"本身，不承载任何节点的具体做法。
 * - 唯一指向的目标 = 现有的完整 `.agh/skills/physics-agent-governance/SKILL.md`
 *   （一份 `SKILL.md`，不拆分）；等①第 4 点（确认点 B）定稿拆分方案后，
 *   再回来把这里的"先读 governance 主 skill"一句改成"按节点依次读对应子 skill"。
 * - 跟"不删改现有 skill"完全兼容：本条目是运行时贡献（Cordis service，
 *   `packages/resource-control-runtime/src/skills-cordis.ts`），跟磁盘上
 *   `.agh/skills/physics-agent-governance/` 是并存的两个不同来源，互不影响。
 */

export const physicsAgentOrchestrator = {
  inject: ['skills'],
  apply(ctx) {
    ctx.skills.register({
      name: 'physics-agent-orchestrator',
      description:
        '物理题的 6 节点 pipeline 路由器：题目属于物理分析/建模/数值求解类、且需要按结构化流水线执行（而非凭直觉自由建模）时，先读这份 skill 判断当前该进入哪个节点、以及该节点该读哪份具体 skill。触发信号 = 题目性质，不是用户是否点名。',
      body: [
        '# 路由规则（只定"哪一步该读哪份 skill"，不写任何节点的具体做法）',
        '',
        '当前拆分方案未定稿前（①第 4 点确认点 B 之前），唯一可读目标是一份完整的：',
        '',
        '- `.agh/skills/physics-agent-governance/SKILL.md`（6 节点流水线全文，',
        '  含 §0 State Check、§1 三条确定性防线、§2 执行 pipeline、§3 可审计性、',
        '  §4/§4a 权限/环境缺口、§5 参考答案隔离、§6 用户指定文档解析）',
        '',
        '到达任一新节点（Node 0 / 1 / 1.5 / 2a / 2b / 3 / 4，或 §4/§4a/§6 的',
        '触发条件命中）时，如果当前上下文里还没有该节点对应的完整说明，',
        '用 `skill_read` 主动读 `physics-agent-governance` 里对应章节；',
        '不要凭记忆复述节点规则，也不要假设"上次读到过所以这次不用重读"。',
        '',
        '本条目的 description 字段本身（1024 字符上限内）就是宿主暴露给模型的',
        '"目录"条目——模型在没被显式点名的情况下，看到这份 description，',
        '自己判断"这道题该不该按 6 节点 pipeline 走"，再决定是否 `skill_read`',
        '对应 skill（机制依据：`docs/guide/skills.zh-CN.md` 第 36 行"模糊描述',
        '不是确定性的激活语法"+ 第 9 行"发现候选、审核版本、选择同名胜出项，',
        '再向会话暴露可用内容"，跟 `physics-agent-governance` 自己',
        '`description` 里那句"应主动检查并加载本 Skill"是同一套机制，',
        '不是新发明；本条目只是把"先读哪份"这个路由判断独立成一份可被宿主',
        '目录直接检索到的条目，跟主 `SKILL.md` 里内嵌的路由文字解耦，',
        '为①第 4 点定稿后的"按节点读对应子 skill"预留改动点，现在只改这一份，',
        '不动 `SKILL.md` 正文一个字。',
      ].join('\n'),
    })
  },
}
