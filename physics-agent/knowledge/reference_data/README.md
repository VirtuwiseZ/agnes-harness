# 正式项目内置物理参考基准数据集 (Physics Agent Reference Datasets)

本目录为 `physics-agent` 正式交付包内置的公开发表物理与天体测量基准数据集（Level 2 数据源）。
代码与模型可通过相对路径 `physics-agent/knowledge/reference_data/<文件名>` 直接读取，无需依赖外部网络或 `dev-notes/` 目录。

## 数据集清单

1. **`nist_codata2022_constants.txt`**：
   - **来源**：NIST / CODATA 2022 基础物理常数权威列表。
   - **用途**：基础力学、电磁学、量子与热力学通用常数基准（如阿伏伽德罗常数、玻尔兹曼常数、普朗克常数、真空光速、电子电荷等）。
2. **`hydrogen_emission_lines.csv`**：
   - **来源**：NIST Atomic Spectra Database (ASD), 2024。
   - **用途**：氢原子发射光谱特征线（莱曼系、巴尔末系、帕邢系、布拉开系），波长范围 80–2200 nm，含自发辐射爱因斯坦 A 系数与可见光波段（380–780 nm）标定。
3. **`gistemp_global_anomaly_1880-2026.csv`**（归档于历史测试库，可按需引用）：
   - **来源**：NASA GISS 全球地表温度异常长期监测序列。
   - **用途**：热力学宏观能量平衡、气候系统变温动力学模型基准。
4. **`sidc_sunspot_monthly_1749-2026.csv`**（归档于历史测试库）：
   - **来源**：WDC-SILSO 太阳黑子月平均相对数序列（1749年至今）。
   - **用途**：太阳 11 年活动周期、地磁暴与空间环境阻力扰动模型基准。
5. **`nasa_exoplanets_mass_radius.csv`**（归档于历史测试库）：
   - **来源**：NASA 系外行星档案馆（Exoplanet Archive）。
   - **用途**：行星质量-半径幂律拟合、开普勒轨道与重力场分析基准。
