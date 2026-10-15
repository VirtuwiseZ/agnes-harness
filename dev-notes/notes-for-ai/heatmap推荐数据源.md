

==================================================
1. UCI Wine Quality —— 首选：变量相关性热图
==================================================

【内容介绍】
UCI Wine Quality 数据集包含葡萄牙 Vinho Verde 红葡萄酒和白葡萄酒的理化检测指标及质量评分。
常用字段包括：
- fixed acidity：固定酸度
- volatile acidity：挥发性酸度
- citric acid：柠檬酸
- residual sugar：残留糖分
- chlorides：氯化物
- free sulfur dioxide：游离二氧化硫
- total sulfur dioxide：总二氧化硫
- density：密度
- pH：pH 值
- sulphates：硫酸盐
- alcohol：酒精含量
- quality：质量评分

它非常适合测试 heatmap 的“变量 × 变量”相关系数矩阵，能验证：
- pandas 相关矩阵计算
- seaborn/matplotlib heatmap 基础绘制
- annot=True 数值标注
- fmt=".2f" 格式化
- 发散型 colormap，例如 "vlag"、"RdBu_r"、"coolwarm"
- center=0 的对称色标
- 坐标轴标签旋转
- 标注重叠、色条、 tight_layout 等细节

【推荐下载方法】
直接下载官方 UCI CSV：

红酒数据：
https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv

白酒数据：
https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv

注意：
- 文件使用分号 ";" 作为分隔符，不是逗号。
- 读取时应使用：
  pd.read_csv(url_or_path, sep=";")


【测试建议】
请实现一个测试脚本，完成以下内容：
1. 从 URL 或本地 CSV 读取两种酒数据。
2. 检查列名、数据类型、缺失值和样本数量。
3. 计算所有数值列的 Pearson 相关系数矩阵。
4. 绘制相关性热图。
5. 使用 annot=True、fmt=".2f"、cmap="vlag"、center=0。
6. 额外做一个“理化指标 × quality 评分”的相关性条形图或热图，验证非方阵 heatmap 的行为。

参考代码思路：
```
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

url = "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"
df = pd.read_csv(url, sep=";")

corr = df.corr(numeric_only=True)

plt.figure(figsize=(10, 8))
sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="vlag",
    center=0,
    cbar_kws={"label": "Pearson correlation coefficient"}
)
plt.title("UCI Wine Quality: Feature Correlation Heatmap")
plt.tight_layout()
plt.savefig("wine_quality_correlation_heatmap.png", dpi=200)
plt.show()
```

==================================================
2. NASA POWER —— 次选：经纬度空间场热图
==================================================

【内容介绍】
NASA POWER（Prediction of Worldwide Energy Resources）提供全球范围的太阳辐射、气象和气候相关数据。
它适合替代原本计划使用的 NOAA 海温网格数据，用于测试“经度 × 纬度”的规则空间网格热图。

推荐使用 2 米气温参数：
- T2M：2 米高度气温，单位通常为摄氏度。

NASA POWER 的区域数据 API 可按以下条件请求：
- latitude-min / latitude-max：纬度范围
- longitude-min / longitude-max：经度范围
- parameters：请求的变量，例如 T2M
- start / end：日期范围，格式为 YYYYMMDD
- format=CSV：返回 CSV
- community=SB：可持续建筑/气象社区参数集

该数据是卫星与模式同化生成的再分析产品，并非逐站点实测数据。
NASA POWER 官方文档说明其 Daily API 可提供按日统计的平均、最高、最低值等时间序列分析数据。其气象格点分辨率约为 0.5° × 0.625°。

【推荐下载方法】
推荐请求一个较小区域和较短时间范围，例如东京周边 2024 年 7 月：

https://power.larc.nasa.gov/api/temporal/daily/regional?latitude-min=34&latitude-max=38&longitude-min=138&longitude-max=142&parameters=T2M&community=SB&start=20240701&end=20240731&format=CSV

也可以换成其他区域，例如：
- 中国长三角：latitude-min=29, latitude-max=33, longitude-min=118, longitude-max=123
- 日本本州东部：latitude-min=34, latitude-max=38, longitude-min=138, longitude-max=142

注意事项：
- NASA POWER 返回的 CSV 文件前部包含元数据，不能直接当作普通 CSV 读取。
- 应先下载文件到本地，检查表头所在行，再确定 skiprows 参数。
- 不要硬编码 skiprows；应实现自动定位表头，或至少在文档/注释中标明当前版本的实际表头行号。
- 建议在图注中标明数据来源和分辨率，例如：
  “Data: NASA POWER T2M, 0.5° × 0.625° grid”

【测试建议】
请实现一个测试脚本，完成以下内容：
1. 通过 requests 下载上述 NASA POWER CSV。
2. 保存到本地，例如 data/nasa_power_t2m_tokyo_202407.csv。
3. 解析 CSV，自动跳过前部元数据。
4. 检查纬度、经度、日期和 T2M 字段。
5. 将数据透视成“纬度 × 经度”矩阵。
6. 绘制空间热图，横轴为经度，纵轴为纬度。
7. 使用连续型 colormap，例如 "turbo"、"viridis"、"magma" 或 "RdYlBu_r"。
8. 添加 colorbar，并标注单位为摄氏度。
9. 保存为 PNG，例如 output/nasa_power_t2m_heatmap.png。
10. 测试缺失值处理：确认 NaN 会被正确显示为空白，而不是被错误地填为 0。

参考代码思路：
```
import os
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

url = (
    "https://power.larc.nasa.gov/api/temporal/daily/regional?"
    "latitude-min=34&latitude-max=38&longitude-min=138&longitude-max=142&"
    "parameters=T2M&community=SB&start=20240701&end=20240731&format=CSV"
)

os.makedirs("data", exist_ok=True)
csv_path = "data/nasa_power_t2m_tokyo_202407.csv"

response = requests.get(url, timeout=60)
response.raise_for_status()
with open(csv_path, "wb") as f:
    f.write(response.content)

# NASA POWER CSV 前部有元数据。
# 实际实现时应先检查文件，确定表头所在行，而不是盲目硬编码 skiprows。
df = pd.read_csv(csv_path, skiprows=13)

# 实际列名必须根据下载到的 CSV 确认。
# 常见目标是将数据整理为：LAT, LON, YEAR/MO/DY 或 DATE, T2M
pivot = df.pivot_table(
    index="LAT",
    columns="LON",
    values="T2M",
    aggfunc="mean"
)

plt.figure(figsize=(10, 7))
sns.heatmap(
    pivot,
    cmap="turbo",
    cbar_kws={"label": "2 m air temperature (°C)"}
)
plt.title("NASA POWER T2M: Tokyo Region, July 2024")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("nasa_power_t2m_heatmap.png", dpi=200)
plt.show()
```

==================================================
3. Our World in Data CO2 —— 备选：国家 × 年份热图
==================================================

【内容介绍】
Our World in Data（OWID）的 Annual CO2 emissions per country 数据集记录各国和地区的年度二氧化碳排放量，单位为吨。
数据来源为 Global Carbon Budget，并由 Our World in Data 整理与维护。

数据通常包含：
- Country / Entity：国家或地区
- Code：ISO 国家代码
- Year：年份
- Annual CO2 emissions：年度 CO2 排放量

它适合测试“类别 × 时间”的 heatmap，例如：
- 国家 × 年份
- 行业 × 月份
- 城市 × 月份
- 产品 × 参数

能验证：
- 长表转宽表，即 pivot_table
- 时间轴列排序
- 类别轴排序
- 缺失值显示
- 对数色标或非线性色标
- 大数值下的 colormap 表现
- 热图过密时的降采样或筛选策略

【推荐下载方法】
直接下载 OWID 图表页提供的完整 CSV：

https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv?v=1&csvType=full&useColumnShortNames=false

该数据集为公开、可程序化下载的 CSV。
完整 OWID CO2 数据集较大，约 19 MB、50,000 多行；因此测试时不要直接把所有国家和所有年份画进一张热图。

建议先筛选：
- 20 到 40 个主要国家或地区
- 2000 年至 2024 年
- 只保留年度 CO2 排放量字段

注意事项：
- OWID 的列名可能随版本更新变化。
- 不要硬编码列名；应先打印 df.columns，确认国家、年份和排放量列的实际名称。
- 排放量跨度极大，直接使用线性色标时，少数大国会压扁其他国家的颜色差异。
- 可比较线性色标、LogNorm 对数色标、按国家归一化后的相对排放三种效果。

【测试建议】
请实现一个测试脚本，完成以下内容：
1. 下载 OWID CSV，或允许用户传入本地 CSV 路径。
2. 自动识别国家、年份和 CO2 排放量列。
3. 筛选以下国家：
   China, United States, India, Japan, Germany, Russia, Brazil,
   Indonesia, Canada, South Korea
4. 筛选 2000–2024 年。
5. 使用 pivot_table 将长表转换为“国家 × 年份”矩阵。
6. 绘制 heatmap。
7. 分别测试：
   - 线性色标
   - 对数色标
   - 按国家行归一化后的相对排放热图
8. 保存三张 PNG，便于比较色标策略。
9. 检查 NaN 是否正确留白，而不是被当作 0。

参考代码思路：
```
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

url = (
    "https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv"
    "?v=1&csvType=full&useColumnShortNames=false"
)

df = pd.read_csv(url)

# OWID 列名可能变化，实际实现时必须先检查：
# print(df.columns.tolist())

countries = [
    "China", "United States", "India", "Japan", "Germany",
    "Russia", "Brazil", "Indonesia", "Canada", "South Korea"
]

# 下面字段名需要根据实际 CSV 的列名调整
country_col = "Country"
year_col = "Year"
value_col = "Annual CO₂ emissions"

sub = df[
    df[country_col].isin(countries)
    & df[year_col].between(2000, 2024)
]

pivot = sub.pivot_table(
    index=country_col,
    columns=year_col,
    values=value_col,
    aggfunc="first"
)

# 线性色标
plt.figure(figsize=(14, 6))
sns.heatmap(
    pivot,
    cmap="magma",
    cbar_kws={"label": "Annual CO2 emissions (tonnes)"}
)
plt.title("Annual CO2 Emissions: Selected Countries, 2000-2024")
plt.tight_layout()
plt.savefig("owid_co2_linear_heatmap.png", dpi=200)
plt.show()

# 对数色标
plt.figure(figsize=(14, 6))
sns.heatmap(
    pivot,
    cmap="magma",
    norm=LogNorm(),
    cbar_kws={"label": "Annual CO2 emissions (tonnes, log scale)"}
)
plt.title("Annual CO2 Emissions: Log Color Scale")
plt.tight_layout()
plt.savefig("owid_co2_log_heatmap.png", dpi=200)
plt.show()

# 按国家归一化：观察每个国家自身的时间变化
normalized = pivot.div(pivot.max(axis=1), axis=0)

plt.figure(figsize=(14, 6))
sns.heatmap(
    normalized,
    cmap="viridis",
    cbar_kws={"label": "Emissions relative to country maximum"}
)
plt.title("Annual CO2 Emissions: Row-normalized Heatmap")
plt.tight_layout()
plt.savefig("owid_co2_row_normalized_heatmap.png", dpi=200)
plt.show()
```

==================================================
整体测试顺序建议
==================================================

请按以下顺序实现和验证：

1. 先实现 UCI Wine Quality 测试。
   - 目标：验证 heatmap 的基础功能、相关矩阵、annot、fmt、发散色图。
   - 这是最小、最稳定、最容易复现的测试。

2. 再实现 NASA POWER 测试。
   - 目标：验证真实地理网格数据、CSV 元数据解析、经纬度透视、空间热图和缺失值处理。
   - 这最接近原本计划使用 NOAA 海温网格数据的场景。

3. 最后实现 OWID CO2 测试。
   - 目标：验证长表转宽表、类别 × 时间热图、色标策略、缺失值和大数据量筛选。
   - 这能补充非地理网格场景下的 heatmap 能力。

请为每个数据集分别输出：
- 完整可运行 Python 脚本
- 依赖安装命令
- 数据下载/缓存逻辑
- 列名自动检查或明确说明
- 异常处理：网络失败、文件不存在、列名不匹配、缺失值
- 生成的 PNG 文件路径
- 简短的测试结果说明：数据形状、缺失值数量、绘图是否成功、图中应重点检查的视觉特征