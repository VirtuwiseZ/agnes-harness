import json
import os

task_slug = "wave-optics-diffraction-resolution"
base_dir = os.path.join("physics-agent", "runtime", task_slug)
os.makedirs(base_dir, exist_ok=True)

# 1. problem_state.json
problem_state = {
  "schema_version": 1,
  "task": {
    "problem_id": task_slug,
    "description": "大学物理波动光学核心推导与分析：白光单缝衍射机理与色散、圆孔衍射艾里斑与瑞利分辨判据、近地轨道航天员肉眼分辨能力与‘太空看长城’传言定量物理分析、普通光学显微镜阿贝极限与浸油物镜极限分辨能力。",
    "target_quantity": "单缝衍射光强分布 I(θ)、各色光条纹角宽度 Δθ(λ)、艾里斑角半宽度 θ_0=1.22λ/D、人眼最小分辨角 θ_min 与轨道地面分辨距离 Δx(h)、阿贝极限分辨率 d_min=λ/(2NA)",
    "safety_constraints_ref": "N/A（标准大学物理理论推导与定量教学分析题）",
    "sub_tasks": [
      "1. 白光单缝衍射机理与色散规律解析推导、角宽度公式与多波长光强对比曲线族",
      "2. 圆孔衍射与第一类贝塞尔函数极值推导、艾里斑角半宽度与瑞利分辨判据模型",
      "3. 人眼极限分辨角推导、200~400 km 轨道高度地面分辨距离 Δx(h) 模型与太空看长城物理判据",
      "4. 普通光学显微镜阿贝极限推导、浸油物镜 NA≈1.4 下可见光最高空间分辨率评估"
    ],
    "core_objective": "基于波动光学第一性原理系统推导单缝与圆孔衍射光强分布与色散规律，严格确立光学仪器角分辨率判据，定量解析人眼宏观轨道观测极限与光学显微镜微观空间分辨极限。"
  },
  "session_key": "afe4b613-d573-41c7-84cb-362e37d1946b",
  "stage": "node_1_spec",
  "quota": {
    "downstream_retries_remaining": 3,
    "note": "Decrement once per code-edit + re-run cycle inside node_2b_modeling; at 0 with no convergence, trigger annealing rollback to hypothesis_layer."
  },
  "hypothesis_layer": {
    "model_form": "波动光学夫琅禾费远场衍射积分、第一类一阶贝塞尔函数极值分析、瑞利分辨判据、几何角距投影模型与阿贝相干成像空间频率截止模型",
    "assumptions": {
      "assumption_1_fraunhofer": "夫琅禾费远场衍射近似：光源与观察屏距离缝/孔径足够远，满足菲涅耳数 N_F = a^2/(λL) << 1，入射波与衍射波视为平面波。",
      "assumption_2_paraxial": "小角（傍轴）近似：因宏观光阑或单缝尺寸远大于光波长（a, D >> λ），衍射偏折主要集中在微小角域，满足 sin(θ) ≈ tan(θ) ≈ θ。",
      "assumption_3_eye_parameters": "人眼静态明视觉公称物理参数：瞳孔孔径直径取 D = 2.5 mm（典型明视觉瞳孔尺寸），可见光中心有效波长取 λ = 550 nm（人眼视觉最敏感的黄绿光波段）。暂忽略人眼晶状体像差与微眼颤生理微扰，视网膜成像由衍射与感光细胞尺度共同决定。",
      "assumption_4_orbit_geometry": "近地轨道星下点垂直观测几何模型：航天员在离地高度 h (200~400 km) 垂直俯瞰地面，忽略地表微小曲率修正，地面极限分辨线间距采用小角三角几何模型 Δx = h * θ_min。",
      "assumption_5_abbe_illumination": "显微成像阿贝理论与极限数值孔径：采用斜入射全孔径照明条件，物方介质为浸油（折射率 n ≈ 1.515），物镜最大孔径半角 α ≈ 68°~70°，对应极限数值孔径 NA = n sin(α) ≈ 1.4。"
    },
    "last_known_good_version": None
  },
  "dimensional_table": {
    "single_slit_intensity": "I(theta) = I_0 * (sin(pi * a * sin(theta) / lambda) / (pi * a * sin(theta) / lambda))**2 [无量纲归一化光强]",
    "angular_half_width": "theta_0 = lambda / a [rad, 角度量纲为无量纲 1]",
    "airy_disk_radius": "theta_0 = 1.21966989 * lambda / D [rad, 角度量纲为无量纲 1]",
    "ground_resolution": "Delta_x = h * theta_min = 1.22 * h * lambda / D [m, 长度量纲 L]",
    "abbe_limit": "d_min = lambda / (2 * NA) [m, 长度量纲 L]"
  },
  "internal_prior": "理论预判与物理尺度感：(1) 单缝衍射中白光中央条纹由全部连续光谱叠加，零级极大在 θ=0 处全部同相重合，表现为明亮的白光；各级极小与次极大位置与波长成正比（θ ∝ λ），红光偏折角大于紫光，使得第一级及更高级次展现出明显的内紫（蓝）外红彩条，高级次谱线发生重叠；(2) 圆孔衍射第一暗环对应一阶贝塞尔函数 J1(v)=0 的第一非零零点 v1 ≈ 3.8317，对应艾里斑角半宽度 θ0 ≈ 1.22 λ/D；(3) 人眼在 D=2.5mm, λ=550nm 下瑞利极限分辨角约为 2.684e-4 rad (~0.923' ≈ 1 弧分)，在 200~400 km 轨道高度对应的地面肉眼极限分辨尺寸为 53.7~107.4 m，而长城实测宽度仅 5~8 m，相差 7~20 倍，肉眼在太空中绝无可能分辨出长城；(4) 显微镜在 NA=1.4 和可见光波段（400~550nm）下，阿贝极限分辨率理论值为 143~196 nm（约 0.15~0.20 μm），构成了普通光学显微镜不可逾越的经典物理极限。",
  "knowledge_routing": {
    "matched_template": "physics-agent/knowledge/physics_research_methodology.md (板块⑤ 波动学与光学物理分析范式)",
    "param_json": f"physics-agent/runtime/{task_slug}/task_params.json",
    "routing_decision_audit": "本题属于大学物理经典的波动光学推导与光学仪器分辨本领分析，涵盖傅里叶衍射理论、贝塞尔函数极值、瑞利判据与阿贝显微成像理论，直接基于波动光学第一性原理与标准科学常数展开推导与数值仿真。"
  },
  "data_source_decision": {
    "modeling_input_source": "标准物理常数（CODATA）与经典大学物理理论公称参数：可见光标准特征波长（蓝光450nm、绿光532nm、红光633nm、中心波长550nm）、人眼公称瞳孔直径D=2.5mm、近地轨道高度200~400km、长城典型几何宽度5~8m、显微镜极限浸油物镜NA=1.4。",
    "verification_baseline": {
      "name": "贝塞尔函数精确数值零点与解析极限退化、瑞利准则与道威斯/斯帕罗准则交叉核验、菲涅耳-基尔霍夫波阵面数值积分检验",
      "independent_of": True
    },
    "rationale": "基础理论推导与公称光学系统计算优先采用物理学公认标准常数与数学解析严密解，无需外部网络爬虫。",
    "availability_check": "本地 scipy.special (jv, jn_zeros) 与 scipy.constants 离线可用。",
    "manual_fetch_guide": None,
    "user_choice": None,
    "note": "采用标准大学物理教材公称参数与 SciPy 科学计算库数学物理函数，数据完全离线可用且具备权威可溯源性。"
  },
  "numerical_artifacts": {},
  "audit_logs": [],
  "anomalies": [],
  "verification": {
    "benchmark_source": "SciPy 精密特异函数数值求解（jn_zeros）与经典理论退化极限",
    "comparison_result": "待数值仿真与理论验证执行后填入",
    "max_relative_error": None
  },
  "report": {
    "conclusion": None,
    "traceability": {}
  }
}

with open(os.path.join(base_dir, "problem_state.json"), "w", encoding="utf-8") as f:
    json.dump(problem_state, f, indent=2, ensure_ascii=False)

# 2. task_params.json
task_params = {
  "description": "大学物理波动光学核心参数配置表（单缝衍射、圆孔衍射、人眼及航天轨道观测、显微镜极限）",
  "problem_id": task_slug,
  "source_citation": "大学物理学波动光学教材、CODATA 基础物理常数、经典光学与人眼视觉生理学实验测定值",
  "primary_target_quantity": "光强角分布 I(θ)、艾里斑角半宽度 θ_0、地面肉眼极限分辨距离 Δx(h)、显微镜阿贝极限 d_min",
  "safety_or_acceptance_constraints": {
    "values": "N/A",
    "units": "N/A",
    "rationale": "标准理论推导与定量教学分析任务，无工程失效或安全阈值约束。"
  },
  "named_parameters": {
    "visible_wavelength_blue_m": {
      "value": 4.5e-7,
      "units": "m",
      "description": "可见光标准蓝光波长 450 nm",
      "origin": "标准激光谱线/光学教材典型蓝光"
    },
    "visible_wavelength_green_m": {
      "value": 5.32e-7,
      "units": "m",
      "description": "可见光标准绿光波长 532 nm (Nd:YAG倍频激光)",
      "origin": "光学实验室标准波长"
    },
    "visible_wavelength_red_m": {
      "value": 6.33e-7,
      "units": "m",
      "description": "可见光标准红光波长 633 nm (He-Ne激光)",
      "origin": "经典氦氖激光标准波长"
    },
    "visible_wavelength_center_m": {
      "value": 5.5e-7,
      "units": "m",
      "description": "可见光平均/人眼明视觉最敏感波长 550 nm",
      "origin": "CIE 标准明视觉光度函数峰值波长"
    },
    "visible_wavelength_violet_limit_m": {
      "value": 4.0e-7,
      "units": "m",
      "description": "可见光短波极限（紫光） 400 nm",
      "origin": "可见光谱边缘界限"
    },
    "slit_width_a_m": {
      "value": 5.0e-5,
      "units": "m",
      "description": "单缝仿真公称宽度 a = 0.05 mm = 50 μm",
      "origin": "典型大学物理单缝衍射实验装置参数"
    },
    "human_pupil_diameter_D_m": {
      "value": 2.5e-3,
      "units": "m",
      "description": "人眼明视觉瞳孔公称直径 D = 2.5 mm",
      "origin": "题干给定参数，符合生理明适应瞳孔测量统计均值"
    },
    "orbit_altitude_min_m": {
      "value": 2.0e5,
      "units": "m",
      "description": "近地轨道扫描下限高度 h = 200 km",
      "origin": "题干指定近地轨道扫描区间下界"
    },
    "orbit_altitude_max_m": {
      "value": 4.0e5,
      "units": "m",
      "description": "近地轨道扫描上限高度 h = 400 km（国际空间站 ISS 典型轨道）",
      "origin": "题干指定近地轨道扫描区间上界"
    },
    "great_wall_width_min_m": {
      "value": 5.0,
      "units": "m",
      "description": "长城顶宽公称典型值 5 m",
      "origin": "题干给定长城几何尺寸区间下界"
    },
    "great_wall_width_max_m": {
      "value": 8.0,
      "units": "m",
      "description": "长城基底与关隘公称典型宽度 8 m",
      "origin": "题干给定长城几何尺寸区间上界"
    },
    "microscope_max_NA": {
      "value": 1.4,
      "units": "dimensionless",
      "description": "普通光学显微镜浸油物镜极限数值孔径 NA",
      "origin": "题干给定参数，对应折射率 n=1.515 香柏油与最大孔径半角 α≈68°"
    }
  },
  "candidate_verification_baseline": {
    "name": "第一类贝塞尔函数零点解析积分验证、瑞利判据与斯帕罗/道威斯准则理论对照",
    "expected_value": "第一零点 v1 ≈ 3.83170597，艾里斑第一暗环系数 1.21966989",
    "units": "dimensionless",
    "citation_or_source": "Abramowitz and Stegun (Handbook of Mathematical Functions), Born & Wolf (Principles of Optics)"
  }
}

with open(os.path.join(base_dir, "task_params.json"), "w", encoding="utf-8") as f:
    json.dump(task_params, f, indent=2, ensure_ascii=False)

print("problem_state.json and task_params.json written successfully.")
