请先暂停继续扩大 DIM_ALIAS 表。我们重新审视一下 dimensional_gate.py 的量纲处理设计。

我已经核查过目前的方案，发现一个重要问题：我们现在把“物理量语义名称”“Pint 的 dimension”“Pint 的具体 unit”混在了同一层里，因此才会不断遇到 area、momentum、torque、viscosity 等名称缺失后需要手工补表的问题。

核心结论：

1. 不要把 Pint 已经内置的 dimension 体系重新抄一遍。

Pint 0.26.x 本身已经维护了大量物理 dimension，例如：

- area
- force
- energy
- power
- momentum
- pressure
- torque
- density
- viscosity
- kinematic_viscosity
- electric_potential
- electric_field
- electric_displacement_field
- resistance
- resistivity
- conductance
- conductivity
- capacitance
- magnetic_flux
- inductance
- magnetic_field
- magnetic_field_strength

等等。

因此，我们不应该继续设计这种越来越大的表：

DIM_ALIAS = {
    "force": "N",
    "energy": "J",
    "momentum": "kg*m/s",
    "torque": "N*m",
    "viscosity": "Pa*s",
    ...
}

因为这实际上是在重复维护 Pint 已经拥有的 dimension 定义。

2. 请先在“当前项目实际使用的 Pint 版本”环境中做最小实验，确认 Pint 0.26.x 的行为，不要凭记忆猜。

尤其验证以下区别：

- ureg.parse_units("force")
- ureg.parse_units("area")
- ureg.parse_units("momentum")

这些调用到底是否把“force / area / momentum”当作 unit 解析。

同时验证 Pint 原生 dimension API，例如：

- 如何获取 [force]
- 如何获取 [area]
- 如何获取 [momentum]
- 如何获取 [viscosity]
- 如何获取 [electric_field]

请直接运行代码确认，不要只看文档或根据经验判断。

可以使用类似下面的最小测试，但具体 API 形式由你根据当前安装的 Pint 版本确认：

from pint import UnitRegistry

ureg = UnitRegistry()

tests = [
    "force",
    "area",
    "momentum",
    "torque",
    "viscosity",
]

for x in tests:
    try:
        print(x, "parse_units ->", ureg.parse_units(x))
    except Exception as e:
        print(x, "parse_units ERROR:", type(e).__name__, e)

然后针对 Pint 原生 dimension 再做对应测试。

3. 我们真正需要保留的是“语义别名层”，而不是完整的 Pint dimension 数据库。

例如：

specific_energy
specific_heat
thermal_conductivity
surface_tension
spring_constant
linear_mass_density
surface_density
energy_density
volumetric_flow_rate
moment_of_inertia
heat_flux
charge_density
current_density
permittivity
permeability

这些名字是工程物理建模中常见的“人类语义名称”，但不一定都是 Pint 独立注册的 dimension。

因此建议把架构改成：

人类物理量名称
        ↓
先尝试 Pint 原生 dimension
        ↓
如果 Pint 原生存在 → 直接使用 Pint
        ↓
如果不存在 → 查 CUSTOM_SEMANTIC_ALIASES
        ↓
使用一个具体 SI unit expression 转换为 dimensionality
        ↓
最终只比较 dimensionality

也就是说：

Pint 原生能力优先
+
少量我们自己的工程语义 alias fallback

不要再反过来由我们维护一个庞大的 DIM_ALIAS 数据库。

4. 量纲齐次性检查真正关心的是 dimensionality，不是具体单位。

例如：

momentum -> kg*m/s
specific_energy -> J/kg
specific_heat -> J/(kg*K)
thermal_conductivity -> W/(m*K)

这些具体单位表达式最终都只是为了得到正确的 dimensionality。

因此请尽可能让核心检查逻辑围绕：

“输入名称 → dimensionality”

来设计，而不要让核心逻辑依赖：

“输入名称 → 我们自己维护的完整单位字符串表”。

5. 请重点考虑下面这种结构是否更合理。

示意结构：

CUSTOM_SEMANTIC_ALIASES = {
    "specific_energy": "J/kg",
    "specific_enthalpy": "J/kg",
    "specific_internal_energy": "J/kg",
    "specific_heat": "J/(kg*K)",
    "specific_entropy": "J/(kg*K)",
    "thermal_conductivity": "W/(m*K)",
    "thermal_diffusivity": "m^2/s",
    "diffusivity": "m^2/s",
    "surface_tension": "N/m",
    "spring_constant": "N/m",
    "linear_mass_density": "kg/m",
    "surface_density": "kg/m^2",
    "mass_density": "kg/m^3",
    "energy_density": "J/m^3",
    "mass_flow_rate": "kg/s",
    "volumetric_flow_rate": "m^3/s",
    "moment_of_inertia": "kg*m^2",
    "heat_flux": "W/m^2",
    "stress": "Pa",
    "youngs_modulus": "Pa",
    "bulk_modulus": "Pa",
    "shear_modulus": "Pa",
    "compressibility": "1/Pa",
    "strain_rate": "1/s",
    "shear_rate": "1/s",
    "vorticity": "1/s",
    "charge_density": "C/m^3",
    "current_density": "A/m^2",
    "permittivity": "F/m",
    "permeability": "H/m",
}

但不要直接照抄这张表作为最终结果。

先检查：
- 哪些名称 Pint 自己已经能作为 dimension 处理
- 哪些名称确实需要进入我们的自定义语义 alias
- 哪些条目实际上语义重复，可以删掉
- 哪些 Pint 原生 dimension 名称应该直接透传

最终目标是让 CUSTOM_SEMANTIC_ALIASES 尽可能小。

6. 请特别处理以下本次实际踩到的问题：

area
specific_energy

以及下一批高概率出现的：

momentum
angular_momentum
torque
viscosity
volumetric_flow_rate
specific_heat

其中：

- area：优先判断是否属于 Pint 原生 dimension
- momentum：优先判断是否属于 Pint 原生 dimension
- torque：优先判断是否属于 Pint 原生 dimension
- viscosity：优先判断是否属于 Pint 原生 dimension
- specific_energy：重点确认是否需要 semantic alias
- specific_heat：重点确认是否需要 semantic alias
- volumetric_flow_rate：重点确认是否需要 semantic alias
- angular_momentum：重点确认 Pint 是否存在对应独立 dimension；如果没有，就用组合单位表达式得到正确 dimensionality

7. 无量纲量不需要为了名字建立一堆 alias。

例如：

- Reynolds number
- Mach number
- drag coefficient
- lift coefficient
- strain
- Poisson ratio

这些本质上都是 dimensionless。

我们的工具只需要正确处理 dimensionless，不需要维护：

"reynolds_number": ...
"mach_number": ...
"drag_coefficient": ...

这样的表。

但请检查代码中是否存在“把角度、弧度、应变率、无量纲系数”等混在一起处理的问题，避免产生错误判断。

8. 最终请把“语义名称”和“量纲本身”分离。

理想结构应该类似：

physical_quantity_name
        ↓
resolve_dimension()
        ↓
Pint native dimension
        OR
custom semantic alias → Pint unit → dimensionality
        ↓
dimensionality
        ↓
equation homogeneity check

而不是：

physical_quantity_name
        ↓
巨大 DIM_ALIAS
        ↓
全部人工映射到 SI unit
        ↓
Pint

9. 请不要为了修这个问题引入新的大型物理单位库。

我们现在已经使用：

- Pint：单位与量纲
- SymPy：符号表达式和方程解析

这个技术路线本身没有必要替换。

除非你实际验证发现 Pint 的设计无法满足当前需求，否则优先在现有 Pint + SymPy 架构内解决。

10. 请给这个改动补测试。

至少要覆盖：

A. Pint 原生 dimension

area
force
energy
power
momentum
pressure
torque
viscosity
density
electric_field
magnetic_flux

B. 我们自己的 semantic aliases

specific_energy
specific_heat
thermal_conductivity
surface_tension
spring_constant
linear_mass_density
surface_density
energy_density
volumetric_flow_rate
moment_of_inertia
heat_flux

C. dimensionless

Reynolds number
Mach number
drag coefficient
strain

D. 本次真实 bug

area
specific_energy

必须确保原来导致 KeyError 的情况不会再发生。

11. 测试不要只测试“名称存在”。

要真正验证：

“这个名字最终得到的 dimensionality 是正确的”。

例如：

specific_energy
应该等价于 J/kg

specific_heat
应该等价于 J/(kg*K)

momentum
应该等价于 kg*m/s

torque
应该等价于 N*m

volumetric_flow_rate
应该等价于 m^3/s

thermal_conductivity
应该等价于 W/(m*K)

并且最好让测试同时验证不同但等价的单位表达式确实得到相同 dimensionality。

12. 最重要的一点：

请不要因为原来的需求说“补全 DIM_ALIAS”，就机械地继续往 DIM_ALIAS 里添加几十上百项。

先从架构上确认：

“这个能力 Pint 已经提供了吗？”

如果已经提供，就调用 Pint。

只有 Pint 没有提供、但我们的 Agent 又确实需要人类友好语义名称时，才增加一个很小的 semantic alias。

我们的目标不是建立一个新的物理单位数据库，而是建立一个可靠的“物理量语义 → Pint dimensionality”适配层。

完成后请向我汇报：

1. Pint 0.26.x 实际测试结果
2. 哪些原 DIM_ALIAS 可以删除
3. 哪些 alias 必须保留
4. 最终建议的数据结构
5. 修改了哪些代码文件
6. 新增了哪些测试
7. 用实际测试证明 area / specific_energy / momentum 等已经不会再触发 KeyError