# AI 物理科研工作站核心资产模块 (Physics Agent Module)

本项目模块为基于 Agnes Harness 智能体框架构建的物理科研与工程计算资产套件。模块采用完全解耦的目录架构，通过外部确定性计算工具、科学参考数据集与自动化质量门禁，辅助完成物理问题的推导建模、数值求解与结果验证。

---

## 一、 目录结构一览

```
physics-agent/
├── hooks/                        # 确定性计算与验证工具链（Python）
│   ├── dimensional_gate.py       # 符号量纲齐次性检验门禁（基于 SymPy 与 Pint）
│   ├── boundary_gate.py          # 物理极端退化极限与单调性扫描门禁
│   ├── make_report_figures.py    # 科学矢量图表生成程序（外置图例、防遮挡）
│   ├── report_quality_check.py   # 报告排版与出厂质量自动化检测程序
│   ├── trace_visualizer.py       # 双栏离线交互报告编译引擎（内联 KaTeX 与甘特图）
│   ├── audit_log.py              # 执行动作与计算结果不可篡改留痕工具
│   ├── runlog.py                 # 源码与控制台原始回显资产归档工具
│   ├── skill_bom_check.py        # 技能文件 UTF-8 编码合规检测工具
│   └── requirements.txt          # Python 核心依赖清单
├── knowledge/                    # 物理研究方法论与权威数据源知识库
│   ├── data_source_catalog.md    # 权威公开物理数据源检索与准入指引
│   ├── data-source-routing.md    # 四级数据源分层路由决策树
│   ├── physics_research_methodology.md # 经典力学、天体动力学与光学推导规范
│   ├── boundary-verification.md  # 物理边界条件与极值构造方法
│   ├── parameter-sensitivity.md  # 参数灵敏度与微扰分析指南
│   ├── report_structure_guide.md # 科技研究报告八章行文与排版规范
│   └── reference_data/           # 内置公开发表物理与天文参考数据集（离线 Level 2）
│       ├── nist_codata2022_constants.txt     # CODATA 2022 基础物理常数表
│       ├── hydrogen_emission_lines.csv       # 氢原子特征发射光谱数据
│       ├── gistemp_global_anomaly_1880-2026.csv # NASA GISS 全球地表温度长期序列
│       ├── nasa_exoplanets_mass_radius.csv   # NASA 系外行星质量-半径巡天数据
│       ├── sidc_sunspot_monthly_1749-2026.csv # 太阳黑子长时间序列观测数据
│       └── README.md                         # 数据集来源、版权与调用说明
├── plugins/                      # Agnes Harness 原生宿主插件
│   └── physics-agent-orchestrator/ # 流程路由插件（按解题阶段引导加载子技能）
│       ├── package.json          # 插件清单规范
│       └── index.mjs             # 插件入口与技能注册逻辑
├── runtime/                      # 运行时隔离任务目录与模板
│   ├── problem_state_template.json # 物理状态机基础结构模板
│   └── task_params_template.json   # 任务物理常数表模板
├── third_party/                  # 外部运行时规范与便携环境说明
│   └── portable-runtime/         # 免安装便携式 Python 3.13 运行环境配置
└── problem_state_schema.md       # 物理状态机字段定义与读写契约规范
```

---

## 二、 核心组件分工与运行原理

### 1. 确定性计算与验证工具（`hooks/`）
- **符号量纲检验（`dimensional_gate.py`）**：在执行计算前，通过符号计算解析方程语法树，检验等式两侧物理单位是否一致（如速度方程两侧是否同为 $[length]/[time]$），杜绝量纲失配错误；
- **物理极限门禁（`boundary_gate.py`）**：依据任务配置的边界探针，测试在极端参数下（如外场引力趋零、距离无穷大）计算结果是否自洽趋于物理公理，并检查全域参数扫描是否单调平滑；
- **出厂质量门禁（`report_quality_check.py`）**：在交付报告前执行程序化质检，检查公式是否 100% 本地内联、链接是否存在死链、图例是否压盖数据曲线，确保交付质量；
- **双栏交互排版引擎（`trace_visualizer.py`）**：将生成的 Markdown 文本、矢量图表以及底层的执行记录，编译为单个自包含的离线 HTML 网页，支持正文蓝链与底层执行记录的毫秒级热跳转与脉冲高亮。

### 2. 物理方法论与权威数据源（`knowledge/`）
- **方法论体系**：为模型提供任务解构、费米数量级先行估算、物理机制匹配与报告撰写规范，确保推导有章可循；
- **内置基准数据集（`reference_data/`）**：提供来自 NIST、NASA、WDC-SILSO 等官方科研机构发布的标准物理常数与天文观测数据，脱网环境下可直接读取，避免凭空猜测数据。

### 3. 宿主路由插件（`plugins/`）
- 遵循 Agnes Harness 官方扩展规范，通过插件机制在宿主启动时自动注册路由技能（`physics-agent-orchestrator`），负责识别物理命题并分步引导大模型加载对应的专业子技能，避免单次提示词过长导致注意力分散。

---

## 三、 环境依赖说明

本模块依赖 Python 3.10+ 及以下基础科学计算库：
- `sympy>=1.12`（符号代数与量纲解析）
- `pint>=0.23`（物理单位制核验）
- `numpy>=1.26`（数组与矩阵计算）
- `scipy>=1.12`（变步长数值积分与特殊函数）
- `matplotlib>=3.8`（科学矢量图表输出）

*注：在无外部 Python 或网络受限的环境中，系统可无缝切换调度 `third_party/portable-runtime/` 下预置的免安装嵌入式 Python 3.13 运行环境。*
