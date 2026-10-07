# 第三方测试数据说明

本目录包含用于测试 `make_report_figures.py` 五种图表类型（`curve`、`scatter`、`error_bar`、`interval_highlight`、`heatmap`）的真实科学数据集。

---

## 已直接下载的文件（4 个，可立即使用）

### 1. `gistemp_global_anomaly_1880-2026.csv`
**用途**：`curve` — 全球平均气温距平折线图  
**数据源**：NASA Goddard Institute for Space Studies (GISS)  
**描述**：全球陆海合并月均温距平（相对 1951–1980 基准期），1880 年至今，每行一年  
**列**：`Year, Jan, Feb, ..., Dec, J-D（年均）, D-N, DJF, MAM, JJA, SON`  
**单位**：°C（距平），`***` 表示缺测  
**文件大小**：~13 KB  
**版权**：美国政府公开数据，公有领域  
**原始 URL**：`https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv`

---

### 2. `sidc_sunspot_monthly_1749-2026.csv`
**用途**：`interval_highlight` — 月均太阳黑子数时间序列 + 太阳活动极大期区间高亮  
**数据源**：WDC-SILSO，比利时皇家天文台，布鲁塞尔  
**描述**：国际太阳黑子数（ISN v2.0），月均值，1749 年至今  
**格式**：分号分隔（`;`）  
**列**（顺序）：`年, 月, 年分数, 月均黑子数, 月均标准差, 观测站数, 数据标志`  
  - 标准差 = -1.0 表示早期无法估算  
  - 数据标志 = 1 表示已验证数据  
**文件大小**：~127 KB  
**引用要求**：WDC-SILSO, Royal Observatory of Belgium, Brussels  
**原始 URL**：`https://www.sidc.be/SILSO/DATA/SN_m_tot_V2.0.csv`

---

### 3. `nasa_exoplanets_mass_radius.csv`
**用途**：`scatter` — 系外行星质量–半径散点图（Neptune 以内行星）  
**数据源**：NASA Exoplanet Archive，Planetary Systems Composite Parameters (pscomppars) 表  
**描述**：质量 < 20 地球质量且同时有质量和半径测量值的系外行星，约 780 颗  
**列**：`pl_name（行星名）, pl_masse（质量，地球质量单位）, pl_rade（半径，地球半径单位）`  
**文件大小**：~35 KB  
**版权**：美国政府公开数据，公有领域  
**原始 URL**：  
```
https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_masse,pl_rade+from+pscomppars+where+pl_masse+is+not+null+and+pl_rade+is+not+null+and+pl_masse+<+20&format=csv
```

---

### 4. `nist_codata2022_constants.txt`
**用途**：`error_bar` — 基本物理常数精度图（选取一组常数，x 轴为常数编号，y 轴为量纲化值，误差棒为测量不确定度）  
**数据源**：NIST，2022 CODATA 调整值  
**描述**：所有基本物理常数的完整列表，含数值、不确定度和单位  
**格式**：固定宽度文本（非 CSV），列为 `Quantity | Value | Uncertainty | Unit`  
  - 不确定度中 `(exact)` 表示精确定义值（无不确定度）  
  - 数值使用空格分隔的科学计数法，需解析（见下方说明）  
**文件大小**：~40 KB  
**版权**：美国政府公开数据，公有领域  
**原始 URL**：`https://physics.nist.gov/cuu/Constants/Table/allascii.txt`

> **解析提示**：值中的空格是千分位分隔符（如 `6.674 30 e-11` 即 `6.67430e-11`），去掉空格后可直接 `float()` 解析。建议选取同一量纲的常数子集（如"质量"或"能量"类）进行比较，避免混合单位。

---

### 5. `hydrogen_emission_lines.csv`
**用途**：`interval_highlight` — 氢原子发射光谱线 + 可见光区间高亮（380–780 nm）  
**数据源**：NIST Atomic Spectra Database (ASD) 2024 版，人工整理关键谱线  
**描述**：氢 H I 谱线，含 Lyman（紫外）、Balmer（可见/近紫外）、Paschen（近红外）、Brackett（红外）系  
**列**：`wavelength_nm, series, lower_level, upper_level, Aki_s-1, relative_intensity_approximate`  
  - `Aki`：爱因斯坦自发辐射系数，表示谱线强度的物理根据  
  - `relative_intensity_approximate`：相对强度（各系内以最强线为 1000 归一化）  
**文件大小**：~2 KB  
**版权**：美国政府公开数据，公有领域  
**原始来源**：`https://physics.nist.gov/PhysRefData/ASD/lines_form.html`（H I，80–4500 nm）