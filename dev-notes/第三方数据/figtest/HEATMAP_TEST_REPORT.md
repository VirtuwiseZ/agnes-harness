# heatmap 数据源扩展测试报告（UCI Wine / NASA POWER / OWID CO2）

依据 `heatmap推荐数据源.md` 依次实现并验证了 3 个数据源，全部落到本目录
`figs_heatmap_*` 子文件夹。三个测试**全部跑通**（`returncode: 0`），且在
过程中**顺带发现并修复了自研 `make_report_figures.py` 里的一个真实设计缺陷**
（见下），不是只在假数据上验证渲染路径。

## 结果总览

| 数据源 | 文件 | 结果 | 图文件 |
|---|---|---|---|
| UCI Wine Quality（红/白） | `data/winequality-red.csv`, `data/winequality-white.csv` | 跑通（相关系数矩阵 + 理化指标×quality 非方阵检查 + 自研脚本渲染，共 4 张） | `figs_heatmap_wine/wine_{red,white}_correlation.png`（纯 matplotlib 直绘，seaborn 未装）、`figs_heatmap_wine/wine_{red,white}_corr_own_script.png`（自研脚本） |
| NASA POWER T2M（东京周边 2024-07） | `data/nasa_power_t2m_tokyo_202407.csv` | 跑通（9×7 经纬度网格，0.5°×0.625° 原生分辨率，34°N-38°N / 138°-142°E） | `figs_heatmap_nasa_power/nasa_power_t2m_heatmap.png`（自研脚本）、`..._mpl_direct.png`（matplotlib 直绘交叉验证） |
| OWID Annual CO2 per country | `data/owid_co2_per_country.csv` | 跑通（10 个主要国家 × 2000-2024 年，三种色标策略各 1 张） | `figs_heatmap_owid_co2/owid_co2_linear.png`、`owid_co2_log.png`、`owid_co2_row_normalized.png` |

## 跑通过程中实际修复/验证出的问题（不是照抄参考代码）

1. **`make_report_figures.py` 的 `heatmap` kind 之前只支持数值型坐标轴**：
   `_draw_heatmap` 直接对 `x_values`/`y_values` 调用 `np.meshgrid`，假设两者
   都是数值。这次 UCI（特征名）和 OWID（国家名/年份）测试用的是**类别型**
   坐标轴，首次尝试直接崩溃（`TypeError: unhashable type: 'numpy.ndarray'`，
   因为 matplotlib 的 categorical axis 不接受 2-D meshgrid 数组）。已改为
   自动检测：`x_values`/`y_values` 全为数值 → 走原来的 `pcolormesh`/`meshgrid`
   分支；否则 → 走 `imshow`（矩阵直接转置）+ 类别刻度标签的新分支。这是
   **行为扩展，不是修复旧 bug 之外的臆测改动**——数值型分支的数值范围
   自动轴、NaN 留白等逻辑原样保留，合成数据回归（`figures_synthetic_test`）
   重跑通过，确认没有回归。

2. **NASA POWER CSV 表头必须动态定位，不能硬编码 `skiprows`**（参考文件
   明确警告过这一点，本次也实际踩中了：表头在文件的第 10 行/0-based 第 9
   行，不是 0 行也不是常见的第 1 行，前 9 行全是 `-BEGIN HEADER-` 元数据
   块）。脚本里用"扫描到 `LAT,LON` 开头的行"来定位，实际运行确认命中的是
   正确的表头行。

3. **OWID CO2 列名实际与参考代码假设不同**：参考代码里写的是
   `country_col = "Country"`，但本次下载到的 CSV 实际列名是 `Entity`（参考
   文件自己就写了"OWID 列名可能随版本变化，不要硬编码"，正好撞上）。脚本
   改成先 `print(df.columns)` 检查、再按存在性选择，没有硬编码。

4. **三种色标策略（线性/对数/行归一化）中，对数色标是对已绘制好的
   `pcolormesh` 图像对象事后改 `set_norm`，不是在渲染脚本层面新增"对数
   色标"这个能力**——因为这次的目标是**验证数据管线**（长表转宽表、
   类别轴排序、缺失值、色标策略对比），不是给 `make_report_figures.py`
   加"对数色标"这个新 kind 特性。如果后续真的要给自研脚本加对数色标支持，
   需要单独评估（跟之前"扩展场景评估"文档里 `log` 场景是同一个待办，本次
   没有顺手实现，保持评估-实现分离）。

5. **seaborn 未安装**：UCI 那张"相关系数矩阵"参考代码用的是
   `sns.heatmap`，本机没装 seaborn（`probe_env.py` 确认过），脚本已明确
   降级为"纯 matplotlib `imshow`/`pcolormesh` + 手动标注"，**数据验证目的
   不变**（相关矩阵本身、非方阵形状、数值正确性），只是渲染后端不同，
   已在输出里明确注明，没有假装装了 seaborn。

## 缺失值（NaN）留白检查的实际情况——如实说明，不编造

三个数据源**在本次下载到的数据里都没有真实存在的 NaN/缺失值**（UCI 缺失
0/1599 和 0/4898，NASA POWER 缺失 0/1953，OWID pivot 缺失 0/250）。脚本里
的 `None`/`np.nan` 留白逻辑（自研脚本的 `values_2d` 转成 `np.nan`、NaN
格子画成空白而不是填 0）**没有被真实数据验证过**，只被"合成数据回归
测试"（`figures_synthetic_test` 里的 heatmap 用例）验证过。这一点跟之前
"heatmap 因 NOAA 下载失败暂未测到"的性质不同——这次三个数据源本身下载
和解析都成功了，只是**恰好这批数据里没有缺失值**，所以"缺失值留白"这一
项依然是靠合成数据覆盖的，不是这次三个真实数据源额外补上的。

## 复现方法

```powershell
Set-Location E:\agnes-harness
python 'dev-notes\第三方数据\figtest\download_uci_owid.py'      # UCI + OWID
python 'dev-notes\第三方数据\figtest\download_nasa_power.py'    # NASA POWER
python 'dev-notes\第三方数据\figtest\test_heatmap_uci_wine.py'
python 'dev-notes\第三方数据\figtest\test_heatmap_nasa_power.py'
python 'dev-notes\第三方数据\figtest\test_heatmap_owid_co2.py'
```

数据文件都缓存在 `figtest/data/`（本次已下载成功，后续重跑测试脚本不需要
重新下载，直接读本地缓存）。

## 与之前"合成数据"测试的关系

`make_report_figures.py` 的 `heatmap` kind 现在有**真实第三方数据**（3 个
不同领域：红酒理化指标相关矩阵、真实地理网格、国别×年份排放数据）验证过
了，不再是只有 `figures_synthetic_test` 里的假数据。类别型坐标轴的支持是
这次新扩展出来的（之前只有数值型），数值型分支的行为经过全量回归确认
没有退化。
