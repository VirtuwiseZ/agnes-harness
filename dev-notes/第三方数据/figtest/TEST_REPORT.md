# 第三方数据逐类测试报告（make_report_figures.py 当前 5 种 kind）

数据来源：`E:\agnes-harness\dev-notes\第三方数据\`（详见其 README.md）。
测试脚本：`figtest\run_third_party_figures_test.py`（本目录内），生成结果
`figs_<label>/*.png` + 对应 `_state_<label>.json`（可直接检查喂给脚本的完整
`numerical_artifacts.figures` 内容，用于人工核对"图画出来的是不是数据里
本该有的东西"）。

## 结果总览

| kind | 数据源 | 结果 | 图文件 |
|---|---|---|---|
| `curve` | `gistemp_global_anomaly_1880-2026.csv`（全球年气温距平，J-D 列） | 成功，146 年数据点 | `figs_curve_gistemp\gistemp_annual_anomaly.png` |
| `scatter` | `nasa_exoplanets_mass_radius.csv`（~780 颗系外行星，质量–半径） | 成功 | `figs_scatter_exoplanets\exoplanet_mass_radius.png` |
| `error_bar` | `nist_codata2022_constants.txt`（kg 量纲子集 8 个常数，误差棒=标准不确定度） | 成功 | `figs_errorbar_codata\codata_kg_errorbar.png` |
| `interval_highlight` | `hydrogen_emission_lines.csv`（H I 谱线 + 380–780 nm 可见光区间高亮） | 成功 | `figs_interval_hydrogen\hydrogen_lines_visible_band.png` |
| `interval_highlight` | `sidc_sunspot_monthly_1749-2026.csv`（太阳黑子数，降采样为年尺度） | 成功 | `figs_interval_sunspot\sunspot_yearly_mean.png` |
| `heatmap` | `noaa_sst_pacific_20240115.csv`（未下载成功，见下） | **未测试** | 无 |

## 逐类测试过程中撞出/修复的问题

1. **CODATA 文件并非"按 README 描述"的 `|` 分隔列**。README 写"列为
   `Quantity | Value | Uncertainty | Unit`"，但实际文件里**没有任何 `|`
   字符**，是固定宽度 + 可变长度空格填充的格式。第一版解析器按 `|` 分割
   自然一行都解析不到（触发"整张图无数据点"硬报错，行为本身是符合设计的
   ——坏输入就报错，不静默糊过去）。定位到真实格式后（数值内部千分位是
   单个空格、字段间分隔符是 5+ 连续空格、极精密数值用 `...` 截断、
   `(exact)` 表示无不确定度），重写为独立的 `figtest\codata_parser.py`
   （单独验证过、能解析出全部 11 条 kg 常数、明确统计并打印"跳过了
   103 行"而不是静默丢弃）。**这个坑以后任何要解析这个文件的人都可能再
   撞一次，建议把 `codata_parser.py` 保留在 figtest/ 里而不是删掉。**

2. **`interval_highlight` 现在合法支持"零 series、纯背景色带"的图**（之前
   这一轮打磨已经修好），所以氢谱线这张图即使只有 `highlights` 没有
   数据点也能画出来；但本次测试里氢谱线其实**有** 4 条 series（Lyman /
   Balmer / Paschen / Brackett 四个系各自一条折线），`highlights` 是叠加在
   上面的可见光区间——这是"series + highlights"的正常组合，不是极端用法。

3. **太阳黑子时间序列太密**（1749–2026，月尺度），直接画 3300+ 个点的
   折线没有信息量，测试里按"每年取该年最后一期的月均值"降采样到年尺度
   再画——这个降采样是**呈现层判断**（画图的人可以选画什么粒度），
   不是物理判断（没有改动黑子数本身）。

4. **heatmap 没能测到**：`fetch_noaa_sst_heatmap.py` 在本机跑失败
   （`SSL: UNEXPECTED_EOF_WHILE_READING`），`web_fetch` 工具也报该域名
   解析到非公开 IP。没有替代数据源就绪，**没有**拿假数据/其他数据源
   冒充 NOA 海温网格做 heatmap 测试（那样测出来的图跟"真实海温场"无关，
   不算有效测试）。这一块是**明确未完成的**，不是漏了没提。

## 复现方法

```powershell
Set-Location E:\agnes-harness
python 'dev-notes\第三方数据\figtest\run_third_party_figures_test.py'
```

每类结果同时落在 `dev-notes\第三方数据\figtest\_state_<label>.json`
（喂给 `make_report_figures.py` 的完整 `numerical_artifacts.figures`）和
`figs_<label>\*.png`（渲染结果）两处，两边可以对照检查。

## 与之前"合成数据"测试的关系

`error_bar`/`heatmap` 之前只有 `dev-notes/self-tests/03/figures_synthetic_test/`
里的假数据验证过渲染路径。本次 `error_bar` 补上了**真实数据**（CODATA），
是这次逐类测试里最有价值的一项。`heatmap` 仍只有合成数据验证过，真实数据
验证要等 NOAA 下载问题（或替代数据源）解决。
