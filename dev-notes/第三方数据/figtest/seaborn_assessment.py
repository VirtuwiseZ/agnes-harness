"""Fact-check what seaborn actually offers on top of the 5 figure kinds we already
support in make_report_figures.py, to answer 'is seaborn more convenient/generic
for OUR use case than our current matplotlib-only setup'. Output is a plain
factual inventory, not a verdict — the verdict is for the user.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("""
== 事实清单：seaborn 相对 make_report_figures.py 当前 5 种 kind 的能力差异 ==

【make_report_figures.py 当前已支持（纯 matplotlib，无 seaborn）】
1. curve / scatter / error_bar / interval_highlight / heatmap(pcolormesh 或
   contourf)，数值型 + 类别型坐标轴
2. 自动 CJK 字体检测 + 脚注/标题/坐标轴自动换行防溢出（上一轮刚修好）
3. NaN/Inf 脚注、维度不匹配硬报错、单张图失败不拖垮整批（render_all 隔离）
4. 所有判断写死在代码里，是"确定性呈现层"，不做任何物理判断

【seaborn 额外提供的（make_report_figures.py 目前没有的能力）】
- 高层统计图：箱线图、小提琴图、点图(hedged)、直方图+KDE、成对散点图
  (pairplot)、regplot（散点+线性拟合线+置信区间，一行代码）
- 这些在"科研报告的探索性数据分析"场景里，比手写 matplotlib 省事很多
  （比如要画 12 个变量两两相关的 pairplot，matplotlib 要写几十行，
  seaborn 一行搞定）

【seaborn 没有、我们当前脚本自己做了的事】
- CJK 字体自动检测/降级（seaborn 不管字体，中文标题它会直接渲染成方框，
  除非你自己配好 matplotlib rcParams）
- NaN/Inf 脚注记录、维度不匹配硬报错这些"数据完整性门禁"逻辑
  （seaborn 不管这些，缺多少数据它就直接跳过多少，没有脚注记录）
- 单张图失败不拖垮整批的隔离渲染逻辑（seaborn 是逐个画图函数，没有
  这个概念，本来也不适用）

【关键结论（基于上面清单，不是印象）】
seaborn 跟我们的 make_report_figures.py 不是"谁替代谁"的关系，是不同层的东西：
- 它擅长的是"高层统计图"（箱线图/regplot/pairplot 等），这些我们当前 5 种
  kind 完全没覆盖，确实是空白
- 但它不擅长（也不管）我们当前脚本里"刻意做对"的几件事：CJK 字体、
  NaN/Inf 脚注、维度门禁、批次隔离——这些是项目"确定性防御层"的核心，
  不会因为装了 seaborn 就自动消失或需要重新实现
- 所以"加 seaborn"= 给项目多一个"高层统计图"的可选后端，成本是：
  一个新的依赖项（纯 Python，pip install 即可，没有编译步骤，没有
  GPU/网络需求）+ 需要在 make_report_figures.py 里新增 1 个可选
  "高层统计 kind"（比如 kind="boxplot" 或 kind="regplot"），复用现有
  CJK 字体/脚注/隔离机制，而不是让 seaborn 绕过这套机制独立出图
  （如果让 seaborn 独立出图，等于绕开了项目的确定性门禁层，违背整个
  架构初衷——这点必须避免，不管加不加都要保证新 kind 走同样的
  门禁/脚注/隔离路径）
""")
