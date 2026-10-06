# 提示词（直接复制给另一个 AI，比如一个有联网搜索能力的 AI）

---

我需要一个**权威、全面的物理量纲（dimension）类别清单**，用于扩充一个"量纲齐次性检查工具"的维度别名表。背景如下：

## 背景

我写了一个 Python 工具（`dimensional_gate.py`），用于检查物理方程的量纲齐次性（dimensional homogeneity）。它基于两个成熟库：

- **Pint**（单位/量纲库，`pip install pint`，当前版本 0.26.x）作为底层量纲引擎
- **SymPy**（符号代数库）用于解析方程、提取自由符号

已知 Pint 0.26.x 有一个 quirk：`UnitRegistry.parse_units()` **不接受裸量纲名**（比如直接传 `"force"`、`"energy"`、`"acceleration"`），这些名字只在具体单位的 `.dimension` 属性里才能用。所以我在脚本里维护了一张"人类友好量纲名 → Pint 能解析的具体单位字符串"的映射表（`DIM_ALIAS`），目前长这样：

```python
DIM_ALIAS = {
    "dimensionless": "",
    "mass": "kg",
    "length": "m",
    "time": "s",
    "temperature": "K",
    "current": "A",
    "amount": "mol",
    "luminous_intensity": "cd",
    "force": "N",
    "energy": "J",
    "power": "W",
    "pressure": "Pa",
    "velocity": "m/s",
    "acceleration": "m/s^2",
    "frequency": "Hz",
    "charge": "C",
}
```

## 遇到的问题

最近一次实际使用这个工具检查一道高空跳伞（拖曳主导的垂直下降 ODE）题目时，脚本在用到两个新的维度别名时直接报 `KeyError`：

1. **`area`（面积，L²）**——拖曳项里用到的横截面积 A
2. **`specific_energy`（比能，L²T⁻²，即 J/kg）**——我把状态变量选成了 u = v²/2（比动能），它的真实量纲是比能，不是普通能量

这两个别名不在上面那张 15 项的表里，导致量纲检查脚本根本没跑起来。我现在意识到这张表**当初设计时只覆盖了"7 个 SI 基本量 + 8 个最常见的导出量"，没有覆盖"高阶组合导出量"这一整类**——我粗略扫了一遍，至少还有 `momentum`、`angular_momentum`、`torque`、`volumetric_flow_rate`、`viscosity`、`diffusivity`、`conductivity`（thermal/electrical）、`specific_heat`、`spring_constant`、`linear_mass_density`、`surface_density`、`energy_density`、`surface_tension` 等常见量也都没有对应条目，只要下一道题用到其中任何一个，同样的 `KeyError` 会再次发生。

## 需要你帮我查/整理的东西

请你**联网检索**（优先参考权威来源，比如 SI 单位体系官方文档、Pint 官方文档/源码里内置的单位定义、Wikipedia 的 SI derived units / Unit dimensions 条目等），给我一份**比我现在这张 15 项表更全、更通用**的维度类别清单，要求：

1. **覆盖范围**：至少覆盖力学、热学/热力学、流体力学、电磁学这四个方向里**工程物理建模中最常用的导出量纲**（不是要穷举物理史上出现过的所有量，是要"建模时大概率会遇到、且 Pint 有对应内置单位"的那一批）。
2. **每一项给出**：
   - 人类友好的量纲名（英文，比如 `momentum`、`angular_momentum`，跟我现有表里的命名风格一致，全小写加下划线）
   - 它对应的**标准 SI 单位拼写**，且必须是 **Pint 的 `parse_units()` 能直接解析的具体单位字符串**（比如 `momentum` → `kg*m/s`，`viscosity` → `Pa*s`，`specific_heat` → `J/(kg*K)`——**请用 Pint 官方文档/源码里实际存在的单位名来写，不要凭记忆写**，写完之后最好能附一句"这个拼写对应 Pint 里的哪个内置单位定义，我验证过它能被 `parse_units()` 接受"）
   - 如果是**非量纲比值的物理量**（比如 `flow_coefficient`、`drag_coefficient` 这类），也请标注出来，跟"有真实量纲的量"分开列（我这边对"无量纲"这一个类别已经单独处理了，不需要为每一个具体的无量纲系数都建条目，一个 `dimensionless` 就够用了，但请确认我没有漏掉某个"看起来无量纲、其实有量纲"的常见坑，比如雷诺数/马赫数这类确认真正无量纲的量是否真的不需要单独条目）。
3. **优先顺序**：请先把我**已经明确踩到的两个**（`area`、`specific_energy`）和**我有把握的下一批**（`momentum`、`angular_momentum`、`torque`、`viscosity`、`volumetric_flow_rate`、`specific_heat`，共 8 个）**排在最前面、逐个确认 Pint 认哪个具体拼写**；然后再补"我可能漏掉的、但工程建模大概率也会用到"的那一批（热传导系数、扩散系数、表面张力、劲度系数、线/面/体积密度、能量密度、电磁学里的磁通量/磁感应强度/电容/电阻等）。
4. **一个单独的问题需要你先验证清楚再回答**：Pint 0.26.x 的 `UnitRegistry.parse_units()`，**到底认不认 `parse_units("momentum")`、`parse_units("area")` 这种直接用"量纲名/物理量名"（而不是具体单位名）的调用**？
   - 如果你能确认"实际上直接传这些词就能解析成功"（即 Pint 内部其实有这些词对应的默认单位注册，只是文档没写清楚/我测试的方式不对），那结论是**我这张 `DIM_ALIAS` 表本身可能是不必要的中间层**，可以直接删掉，让调用方传 Pint 原生认识的词——这是比"补全这张表"更干净的修法，请帮我确认或否定这一点（最好附一段最小可复现的代码片段，比如 `from pint import UnitRegistry; ureg = UnitRegistry(); ureg.parse_units("momentum")` 在 0.26.x 下到底返回什么/报不报错）。
   - 如果你确认"确实不认、必须传具体单位串"，那结论是**这张表必须保留且必须补全**，请把补全后的完整清单给我。
5. **格式**：请最终给我一张可以直接照抄进 Python 字典的清单（跟我上面 `DIM_ALIAS` 完全同款的 `{"量纲名": "Pint能解析的单位串"}` 格式），不要只给表格/散文描述——我要的是"拿到就能 `DIM_ALIAS.update({...})` 粘进去"的那种。

**最后一步验证要求**：请你把最终清单里**每一个** `parse_units()` 用到的单位串，都用一段最简 Python 代码（比如 `ureg.parse_units("X")` 逐个跑一遍）实际验证过能成功解析，不要只凭"我觉得 Pint 应该有这个单位"来写——我这次踩坑的根源就是"表设计得太保守、没有覆盖到实际会用到的量"，不想再为第二次踩同样的坑（这次是"想当然觉得这些量 Pint 肯定认识"，结果它不认）。
