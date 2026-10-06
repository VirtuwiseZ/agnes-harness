# 泛用性审视笔记 — 走查发现（非结论）

聚焦问题：项目设计里"过度绑定 2023 高空跳伞单题、缺乏泛用性"的具体位置，按严重程度排序。
所有条目都是"发现了 + 具体在哪 + 建议方向"，记录时点没有实际动手改任何协议/模板/代码。

## 1. 最明显的问题：`problem_state_template.json` 的 `data_source_decision` 字段命名，把"大气数据源"焊死进了通用模板

`program-design/runtime/problem_state_template.json` 第26-34行：
```json
"data_source_decision": {
    "atmosphere_source": null,
    "verification_baseline": null,
    ...
}
```
这份模板文件开头自己写着"Generic blank template for a NEW physics problem"，但字段名 `atmosphere_source` 是**大气物理专属**的命名——换一个非大气问题（比如"悬臂梁最大挠度"、"RLC 电路谐振频率"），这个字段名就会跟问题本身完全脱节，agent 或者填 null（合规但信息量为0）、或者硬塞一个跟"大气"无关的值进 `atmosphere_source`（语义错误）。

**建议方向**（记录时点未动手，只是记下）：字段名应该抽象成 `modeling_input_source`（或类似的中性命名），"大气"是 2023 题的具体答案，不该是通用模板的字段名。这条跟 `dev-notes/self-tests/02/boundary_spec_space_diving.json` 里同样写死 `"model_module": "descent_model"`（一个具体某次走查落盘的文件名，不是任何可复用模块的通用路径）是同一个病根——通用协议模板里混进了单题的具体值。

（后已落实：`atmosphere_source` 已改名为 `modeling_input_source`，`trace_visualizer.py` 保留旧名回退以兼容历史记录文件。）

## 2. `ode_model.py` 里 `run_single_descent` 只处理"从某高度向地面自由下落"这一个特定几何，且 `__main__` 演示段落直接写死ambiance-only 0-39km

- 第52-59行的 `descent_ode_rhs`/`run_single_descent` 假设的是"从 z0_m 垂直落到 1m 高度"，`g_eff` 用 `GM_EARTH/(R_EARTH_M+alt)**2` 硬编码了地球引力——这是针对"跳伞/再入大气层"这类问题的专属建模，不是通用的"一维 ODE 数值求解器"。
- 但这份文件放在 `program-design/hooks/` 里，按项目"确定性防线必须独立脚本运行"的定位，容易被误读成"Node 2b 的通用 ODE 引擎"。实际上它只是 2023 题这一道题的参考实现/烟雾测试，跟 `descent_model.py`（02 走查里 agent 自己写的、真正被边界门调用的模块）是两个东西，但**记录时点没有任何注释说明这一点**——`ode_model.py` 只说自己是"first version...for now"，没说清楚它跟"这次走查实际跑起来的那个模块"是什么关系。
- 第104-128行 `__main__` 里 `z0_m=39_000.0`、`m_kg=190.0`、`cd=1.0`、`a_m2=0.18` 全是 2023 题的具体数值（虽然注释里标注了来源是 `space_diving_params.json`，这点是好的），但如果这份脚本被当作"通用示例"复用到下一道题，这些数字是需要 agent 主动重写的，没有任何机制（比如参数化入口、CLI 覆盖）提示它们"这是默认值、可以/需要覆盖"。

**建议方向**：要么把 `ode_model.py` 明确标注为"2023 题的参考实现，不是通用引擎"（跟 `descent_model.py` 区分清楚），要么给它加一层"参数可覆盖"的入口（CLI 参数或一个 JSON 参数文件），让"数值"和"逻辑"真正解耦。

（后已落实：`ode_model.py` 的 docstring 已明确标注为"仅参考示例、非通用引擎"，SKILL.md Node 2b 对应更新为"应该写一个全新模块，不要改这个文件"。）

## 3. `space_diving_params.json` 这份文件本身没问题（它就该是题目专属的），但它的存在方式暴露了一个缺口：没有"通用题目参数文件"的模板

目前只有 `space_diving/` 一个题目专属目录，里面只有一份 2023 题的参数。如果下一道题是"2010 题（摆锤抛射）"，agent 需要自己现写一份新的参数 JSON，没有现成的"题目参数文件该长什么样"的模板参照（`problem_state_template.json` 是运行时状态模板，不是"题目输入参数"模板）。这是一个小缺口，不影响记录时点这一轮，但做第二道题测试时会撞到。

（后已落实：新增 `program-design/runtime/task_params_template.json` 作为通用题目参数文件空模板，SKILL.md Node 1 加了"每个任务必须从这份模板起一份任务专属参数表"的指引。）

## 4. 记录时点实测确认的一个独立小发现（跟上面单题绑定问题无关，但顺手记一下）：`boundary_gate.py` 认的 `model_module` 目前是"必须是一个可 import 的模块名"

02 走查里 agent 实际跑的是 `descent_model.py`，但 `boundary_spec_space_diving.json` 里写的 `"model_module": "descent_model"` 意味着 agent 必须保证这个文件名在 Python 的 import path 上（这次走查里应该是临时 `cd` 到那个目录或者手动加了 path，这一点记录时点没有专门核查 agent 具体是怎么让 import 成功的——是个小悬而未决的细节，不影响结论，但如果下次复用到新题时要留意 `boundary_gate.py` 能不能直接拿到这个模块名）。

（后已落实：`program-design/knowledge/boundary-verification.md` 第3步补全了 `model_module` 的 `importlib` 解析机制说明，明确了"模块名必须在钩子启动目录下可 import"这个前提。）

## 结论

泛用性问题集中在两处：(a) 通用模板/schema 文件里混进了"大气""跳伞"这类单题专属词汇（问题1），(b) 参考实现脚本（`ode_model.py`）没有做"数值与逻辑解耦"，容易被误当通用引擎（问题2）。问题3/4是次要的、可以等下一道题测试时再处理的缺口。

**记录时点没有动手改任何一条**，因为改协议模板/字段命名这类东西（尤其是 `problem_state_template.json` 的字段名一旦改了，`problem_state_schema.md` 和 `trace_visualizer.py`/`report` 里引用这些字段的地方都得跟着动，是牵连面比较广的一刀切）需要明确确认后再动手，不宜在未获确认时单方面执行。后续 4 条已全部落实，见上各条"（后已落实）"备注与对应 commit。
