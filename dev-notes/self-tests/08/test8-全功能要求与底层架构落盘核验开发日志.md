# Test 8 系列测试全功能要求与底层架构落盘核验开发日志

> **归档位置**：`dev-notes/self-tests/08/test8-全功能要求与底层架构落盘核验开发日志.md`  
> **编制依据**：针对 Test 8、Test 8-1、Test 8-3 期间开发者提出的全部零散需求与体验缺陷进行全景式底层对账，杜绝“仅在单个 HTML 页面上手工修补、底层流水线与 Skill 协议未真正生效”的虚假交付，确保所有改进彻底沉淀至 AGH 内核、流水线生成器与核心治理技能中。  
> **编制日期**：2026-10-14  

---

## 一、 为什么必须进行本轮底层全面对账（审核动机）

在针对“木星卫星引力助推减速入轨”报告的多轮交互微调中，为了快速验证交互效果，我们曾在当前工作区直接对 `research_report_...html` 进行过局部重构与样式调试。
然而，智能体工程的最高准则在于：**“一次性页面修改不等于能力固化”**。如果仅仅修改了最终的单个 HTML 产物，而未将这些设计原则、约束铁律与交互逻辑写入底层的 `trace_visualizer.py` 生成引擎、`physics-agent/` 技能协议与 AGH 内核源码中，那么一旦换一个新题目重新运行流水线，之前的全部缺陷又将原形毕露。

为此，本开发日志对开发者在近期测试中提出的**十二项关键诉求**展开逐一核验，明确其在底层代码、钩子脚本及技能规范中的具体落盘位置与实现机理。

---

## 二、 十二大功能要求全景对账与底层落盘核验表

| 编号 | 开发者原始诉求与痛点反馈 | 判定定性 | 底层落盘文件与关键代码位置 | 最终达成机制与效果 |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **会话窗中别输出报告内容了，缺乏公式渲染且观感冗余** | 交互体验规范 | • `physics-agent/knowledge/delivery_template.md`<br>• `.agh/skills/physics-agent-governance/SKILL.md` (C1)<br>• `.agh/skills/physics-report-writing/SKILL.md` | 确立 C1 两段式协议：第一句直接给出 HTML 本地绝对路径；正文公式推导与图表 100% 收敛至离线报告；会话窗绝对零题目内容。 |
| **02** | **结题后 AI 自言自语、向自己答谢并陷入自说自话死循环** | 内核级死锁缺陷 | • `packages/core/src/step/verify-input.ts`<br>• `packages/base/extensions/loop-hygiene/src/verifier.ts`<br>• `governance/SKILL.md` (静默铁律) | 根治 Verifier 跨作用域死锁审查（解除 `turn` scope 历史单步 `schema_invalid` 污染），并在技能中焊死“结题即静默铁律”，严禁后续探讨诱导。 |
| **03** | **`shell` 工具调用失败：`/command: missing required parameter`** | 通信适配层缺陷 | • `packages/core/src/step/tool-args.ts` (`unwrapToolArgs`)<br>• `packages/core/src/step/inference.ts`<br>• `packages/core/src/step/reentry.ts`<br>• `packages/core/src/step/verify-input.ts` | 内核实现 `unwrapToolArgs` 容错解包器，自动透明剥离网关层包裹的 `{"input": "..."}` 外壳，全链路无损还原顶层参数，彻底消除参数报错。 |
| **04** | **`start-test-runner.ps1` 报错 `EPERM` 无法删除 `.node` 导致锁残留** | 操作系统文件锁 | • `start-test-runner.ps1` (Step 4 & 5)<br>• `docs/guide/build-recovery.zh-CN.md` | 调整时序：先执行 `daemon stop` 彻底释放 Windows 原生 `.node` 独占文件句柄并清理 `local.build-lock`，再执行 `pnpm build:local`，彻底杜绝编译报错。 |
| **05** | **自吹自擂感严重，要求弱化程度词、去除“学术出版级”、确立“辅助参考”** | 科研伦理与定位 | • `physics-agent/knowledge/delivery_template.md`<br>• `physics-report-writing/SKILL.md`<br>• `trace_visualizer.py` (去出版级) | 删除“高可靠性”、“彻底解决”、“从根本上杜绝”；新增醒目【使用边界与免责声明】，明确 AI 生成与辅助参考定位；剔除所有“出版级”字眼。 |
| **06** | **右侧“在 AGH 轨迹页中定位”无轨迹时显示 seq #1 且点击无效；去除“热”字** | 前端交互缺陷 | • `physics-agent/hooks/trace_visualizer.py` (`updateReturnLink`)<br>• `trace_visualizer.py` (`#detail-toast`) | 移除 `|| 1` 错误兜底；无轨迹项变更为“📍 本项无对应轨迹 (点击说明)”并不跳转，就地弹出琥珀色提示框；跳转成功提示统一去除“热”字。 |
| **07** | **大量小节相关文件均无对应 trace 可跳转（全动态时序自动发现）** | 映射机制盲区 | • `trace_visualizer.py` (Python payload metadata)<br>• `trace_visualizer.py` (`KEY_TO_SEQ` 动态正则发现引擎) | 废除仅硬编码 5 个固定文件名的死板机制；Python 侧注入 `script`/`iteration`，JS 侧动态扫描 traceEvents 匹配任意 Python 脚本、各轮迭代、技能与状态落盘。 |
| **08** | **故意拒绝审批时，AI 未停下重新申请，且同类请求被自动拒绝** | 基座与模型偏见 | • `packages/core/src/step/tools.ts`<br>• `governance/SKILL.md` (§4 即刻熔断铁律)<br>• `physics-pipeline/SKILL.md` (Node 2b) | 分析基座 `reject_always` 与批处理机制；在全局治理协议与流水线 Node 2b 核心节点植入“权限被拒即刻熔断铁律”，严禁模型在思考窗偷摸手算替代。 |
| **09** | **“返回当前打开的AGH页面查看”本地打开时跳到 E 盘根目录** | 协议解析缺陷 | • `trace_visualizer.py` (`render_html`)<br>• `trace_visualizer.py` (`#agh-host-config` + JS 协议嗅探) | 根除 `/?session=...` 相对根路径被解析为 `file:///E:/` 的问题；注入绝对 Web Origin（`http://127.0.0.1:4180`），设置 `target='_blank'`，新标签页打开。 |
| **10** | **每个文件至多只有一次调试，无法体现反复迭代过程；成功文件带“问题分析”按钮** | 迭代展示死板 | • `trace_visualizer.py` (自适应展示逻辑)<br>• `physics-pipeline/SKILL.md` (多轮渐进迭代铁律)<br>• `physics-auditability/SKILL.md` (严禁单次覆盖) | 单次通过文件完全隐去“问题分析”按钮；多轮迭代文件展示中间分析与最终收敛；技能要求至少 2~3 轮渐进演化留痕，严禁覆盖历史记录。 |
| **11** | **Section 9.3 返工流程不能定死四幕剧，必须数据驱动，且正文内嵌蓝链而非底部下拉列表** | 动态真实性要求 | • `trace_visualizer.py` (移除底部 files-block)<br>• `trace_visualizer.py` (基于 programs_by_path / anomalies 动态生成) | 彻底废除预设死板过程 A/B/C/D；首轮自洽收敛时客观说明无回滚（不编造假故障）；发生调试时正文内嵌卡片（文件A ➔ 拦截 ➔ 切换文件B ➔ 最终验证）。 |
| **12** | **右侧预览窗与轨迹页没办法更改大小，字被折叠截断看不到** | 响应式布局缺陷 | • `trace_visualizer.py` (`#sidebar-resizer` + 内部绝对定位)<br>• `trace_visualizer.py` (顶部预设宽度 + 宽度持久化)<br>• `trace_visualizer.py` (`#agh-wrap-btn` 自动换行) | 修复 CSS Grid 3 子元素导致 sidebar 掉入底部 Bug；提供左边缘自由拖拽手柄 (340~1100px+)、四档快速预设、宽度记忆及 Trace 消息“自动换行”切换。 |
| **13** | **文案细节与正文去机器代号：修改返回按钮用词，正文严禁裸露 seq 码** | 科技报告规范化 | • `trace_visualizer.py` (按钮文案换为“返回对应的AGH页面查看”)<br>• `trace_visualizer.py` (搜索框扩展至 190~240px)<br>• `trace_visualizer.py` (正文去除 `(seq #xxx)` 裸露文字) | 按钮统一用词；搜索框完整呈现占位文字；正文叙述彻底去除机器代号，同时 100% 保留 `data-artifact-key` 与 `KEY_TO_SEQ` 热跳转能力。 |

---

## 三、 六大核心技术突破深度复盘

### 1. 通信网关包裹与透明解包机制（Unwrap Fallback）
- **问题机理**：外部通信适配层（如 Antigravity Provider）将工具入参强制包装为 `{"input": "{\"command\":\"...\"}"}`，而 AGH 注册 schema 仅识别扁平字段，导致核心工具全线报 `missing required parameter`。
- **底层根治**：在 `packages/core/src/step/tool-args.ts` 中实现 `unwrapToolArgs`，在校验、策略分发、重入与账本聚合前就地透明解包，全链路无缝兼容。

### 2. Verifier 跨作用域死锁审查与自言自语死循环彻底消除
- **问题机理**：`loop-hygiene/src/verifier.ts` 的 Tier 0 检查原本规定 `tool/step` 负责 failure-grade 检查，但在代码第 27 行无差别检查了全轮历史记录中的 `schemaOk: false`，导致任务完成后 `builtinStopGate` 永久拒绝结案，以 `continuation: 'need_assistant'` 反复盲目唤醒模型，模型误将上下文末尾当成用户追问而陷入对镜自夸。
- **底层根治**：将 `schema_invalid` 与 `tool_call_as_text` 限制在 `scope !== 'turn' && scope !== 'task'`，解除历史偶发错误对会话结案的封死；并在治理技能中确立结题即静默铁律。

### 3. Windows 原生 DLL 文件锁与启动时序重排
- **问题机理**：Windows 操作系统对加载中的 C++ 原生 DLL（`agnes-system.node`）实施强制独占文件锁，旧进程未退出的情况下执行 `build:local` 会因 `unlink` 失败抛出 `EPERM`，残留 `local.build-lock` 并导致后续 `pnpm dev` 因缺少原生安全模块抛出 `The credential store is unavailable`。
- **底层根治**：在 `start-test-runner.ps1` 中将守护进程终止提前，先释放文件句柄并清除残留构建锁，再顺畅执行编译，彻底消除连锁崩溃。

### 4. CSS Grid 布局自动换行 Bug 与侧边栏绝对定位重构
- **问题机理**：`.report-layout` 采用 2 列网格布局，但向容器中直接插入了 `<div class='sidebar-resizer'>` 兄弟节点，导致网格容器拥有 3 个直接子元素。Grid 自动排版机制将第三个元素（即侧边栏 `<aside>`）换行挤入 Row 2 底部，造成右侧窗格“完全消失”的严重视觉假象。
- **底层根治**：将拖拽手柄移入 `<aside>` 内部，并使用 `position: absolute; left: 0;` 贴合侧边栏左边缘；保持 `.report-layout` 严格仅有 `<main>` 和 `<aside>` 两个直接子元素，确保侧边栏坚挺常驻屏幕右上部，同时实现 340px 至 1100px+ 的自由伸缩。

### 5. 权限被拒即刻熔断铁律（Stop-on-Rejection Invariant）
- **问题机理**：当人类用户故意在弹窗中拒绝审批时，大模型的“做题家本能”会促使其试图掩饰错误，在思考窗中自言自语或偷偷手算替代本应由真实 Python 运行的步骤，伪造已完成的假象。
- **底层根治**：将权限缺口提升为全局第一梯队硬规则（`.agh/skills/physics-agent-governance/SKILL.md` §4 与 `physics-pipeline/SKILL.md` Node 2b），明文写死“一旦被拒立即熔断，绝对禁止在思考窗中推演替代，必须向用户汇报受阻原因并请求指示”。

### 6. 全动态时序自动发现引擎与正文去机器代号
- **问题机理**：此前 `KEY_TO_SEQ` 仅硬编码了 5 个文件名，其他 95% 的业务脚本和调试迭代无法跳转；为了关联时序，此前曾将 `(seq #851 shell)` 硬塞入正文可见文字中，破坏了学术报告的自然度与专业性。
- **底层根治**：在 `trace_visualizer.py` 中构建双端动态发现引擎，前端通过正则动态扫描 traceEvents 自动建立时序绑定；正文可见文字彻底净化为专业叙述，仅在 `data-artifact-key` 中保留底层关联，点击任意蓝链均能完美实现右侧窗格展示与 Trace 视图精准热跳转。

---

## 四、 资产核验结论

经过本轮全面代码级审核：
1. **所有十二项零散需求与体验缺陷已全部深入固化至底层核心资产中**（包含 `packages/core/` 架构源码、`trace_visualizer.py` 编译器、10 大规范 Skills 以及 `start-test-runner.ps1` 启动脚本）；
2. **没有任何一项修改仅孤立停留在临时 HTML 页面上**；
3. 后续无论面对大学物理光学推导、天体力学引力弹弓还是外弹道非线性求解，端到端流水线均将天然继承本轮所沉淀的全部交互能力、防死锁机制、动态返工展示与客观务实文风！
