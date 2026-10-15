# dev-selftest-log.md — 自测索引（开发侧留档，运行 agent 不需要看这个）

记录各确定性钩子/脚本"何时、以何种输入、得出过什么结果"，供后续开发者复查或复跑，
**不需要**被运行 agent 看见或引用。

| 被测对象 | 测试文件 | 最近一次实测结果 | 备注 |
|---|---|---|---|
| `dimensional_gate.py` | `test_dimensional_gate.py`（已迁入本目录） | 4 用例全 PASS（含 Option A 超越函数非阻断告警） | Pint 引擎版 |
| `boundary_gate.py` | `example_boundary_spec.json` + `example_boundary_spec_fail.json`（已迁入本目录） | 正向全 PASS；反向构造用例正确 FAIL 且退出码 1 | 用简单能量模型样例验证钩子本身有效 |
| `audit_log.py` | `test_audit_log.py`（已迁入本目录） | 追加 3 条 + 篡改 1 条后 `verify_chain` 判 FAIL，精确定位到被改条目 | 逐条独立重哈希，非哈希链 |
| `ode_model.py` | 无独立测试文件（`__main__` 自带 39 km 冒烟用例） | 跑出 max_v≈563 m/s / 3.42 g（中间态结果，非最终答案，见下方说明） | 单段 CD=1.0，未实现分段切换 |
| 2023 题的完整运行记录 | `problem_state_2023_worked_example.json`（已迁入本目录） | Node 1.5 数据源决策（ambiance+pymsis 混合）+ Node 2b 首次冒烟结果 | **这是 2023 题的一次运行素材/示例，不是通用协议文档，也不作为任何新题的"标准答案"对照依据** |

## 重要说明：2023 题那份运行记录里的数值不能当作"验证 ODE 写对"的判据

`problem_state_2023_worked_example.json` 里 `numerical_artifacts.node2b_smoke_test_ambiance_39km`
的 `max_v=563.16 m/s` / `max_abs_accel=33.58 m/s²`，以及该记录里"跟 2023 范文的 467.7 m/s、
9.68 m/s² 差多少"这类对照性 caveat，**都是开发过程中顺带算出来的中间结果，不代表这是本项目
"正确答案"或"验证判据"。** 项目真正的验证判据必须是：量纲门禁、边界极限行为、参数敏感
趋势这些**不依赖任何范文数值**的自检项。这份记录仅作为"跑通过一次真实数据链路"的开发留档，
不应被任何新题的分析流程当成"对得上的目标值"。
