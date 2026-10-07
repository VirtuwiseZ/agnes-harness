"""Fact-based inventory: which seaborn high-level plots are actually worth
adding as new `kind`s to make_report_figures.py, judged against what a
physics-agent report (Node 3) actually needs to present, NOT against
'seanbon can do X'. For each candidate, state:
  - what data structure it consumes (must fit our general schema, no
    physics-specific field)
  - which common physics-report situation it covers that our current 5
    kinds (curve/scatter/error_bar/interval_highlight/heatmap) genuinely
    cannot cover
  - whether it can be drawn with pure matplotlib (i.e. is seaborn strictly
    required, or just convenient) — this determines the dependency's
    nature in requirements.txt
  - verdict: add / hold / skip, with one-line reason
"""

print("""
== 候选 seaborn kind 逐一判断（以"物理题报告常见呈现需求"为基准，不是"seaborn能画啥"） ==

--- 候选 A: 箱线图/小提琴图（分布对比） ---
典型场景：同一物理量在 N 个"条件"（不同材料、不同工况、不同时间点取样）下的
分布对比，不是一条"量 vs 量"的曲线，而是"每个条件一组采样值"。
物理例：不同发射角下多次实验的落点分布、不同阻尼比下响应的统计分布。
当前 5 种 kind 覆盖不了：我们只有"一条条 x-y 序列"（scatter 是散点，
不是分箱统计），没有"类别 x 分布"这种二维结构（类别轴=条件名，值轴=
该条件下的采样值列表）。
纯 matplotlib 能否画：可以（matplotlib 自带 boxplot()，功能上够用，
只是默认样式比 seaborn 丑一点、少几个统计层如 outlier 高亮/置信区间）。
判断：值得加，且**不强依赖 seaborn**——用 matplotlib 原生 boxplot 画，
seaborn 装了的话可以选更好看的样式，不装也能画。数据 schema 要新加
"每个 category 对应一组 y 值"的结构（跟现有 series 的 x/y 对偶不同，
是"category -> list of values"），这是本次要设计的新 schema 形态，
不牵扯现有 5 种 kind 的字段。

--- 候选 B: regplot（散点 + 线性/多项式拟合线 + 置信区间带） ---
典型场景：一组（x, y）数据点，想同时展示"原始散点 + 拟合的线性/多项式
关系 + 95% 置信区间阴影带"，一条命令出图。物理例：验证某物理量是否
满足线性关系（斜率=某常数）、验证 Hooke 定律（F vs x 线性拟合斜率=k）。
当前 5 种 kind 覆盖不了：我们有 scatter（只是点）和 curve（任意函数值
序列），但没有"散点+自动拟合+统计置信区间"这个三合一的呈现——拟合线
本身其实可以用 curve kind 画（如果上游把拟合参数算好填进 series），
但**置信区间带**这个"统计不确定性"呈现目前没有对应 kind（error_bar
是逐点的测量误差，不是"拟合线本身的置信带"，两者统计含义不同，
不能混用）。
纯 matplotlib 能否画：拟合线本身可以用 curve kind 画（上游算好 y=kx+b
的采样值）；但置信区间带（regplot 里自动算的 95% 置信区间）需要
上游 agent 自己算好上下界序列再喂进来（跟 error_bar 的 y_err 是同一
类数据形态，只是画成"两条曲线夹住的阴影带"而不是逐点误差棒），
**不需要** seaborn 本身——seaborn 的 regplot 价值主要在"一条命令自动
拟合+自动算置信区间"，如果我们坚持"脚本不做物理判断"的原则（拟合
参数/置信区间由上游算好、脚本只负责画），那 seaborn 在这个场景里
其实是多余的——matplotlib 画"曲线+置信带"完全够用，且更可控
（置信区间的计算口径由上游定死，脚本不猜）。
判断：**跳过 regplot 作为独立 kind**。理由是它 90% 的能力（画拟合线、
画置信带）用现有 curve + y_err 风格的置信带数据就能表达，剩下 10%
（自动拟合）恰恰是我们原则里"上游算好、脚本不判断"明确不该脚本做的
事。硬加一个"自动拟合"的 kind 会打破这条原则。

--- 候选 C: 小提琴图（violinplot，分布的形状对比，比箱线图多一层密度信息） ---
跟候选 A 是同一类需求（类别 x 分布），只是呈现细节不同（小提琴图多画
了核密度估计的形状）。物理例：两个不同条件下某物理量的分布形状对比。
纯 matplotlib：matplotlib 3.8+ 自带 violinplot()，能用，但默认样式
一般。
判断：跟候选 A 二选一即可，不两个都加——**箱线图（A）更常见于
"多条件对比"的科研报告**（6 个以上条件时小提琴图会画到糊掉，
箱线图仍然清晰），小提琴图留给"只有 2-4 个条件、想强调分布形状"
的场景，属于偏小众。本次加 A（箱线图），C 暂不加，撞到需要强调
分布形状的题再说。

--- 候选 D: pairplot（多变量两两散点矩阵） ---
典型场景：一次性看 N 个变量之间的两两相关关系（比如 12 个理化指标
两两之间的相关散点）。物理例：多参数扫描后的多变量关系探索。
当前 5 种 kind 覆盖不了：我们的 series 是"一条条序列"，没有
"N x N 散点矩阵"这种结构。
纯 matplotlib：可以手画（grid 布局 + 每格一个 scatter），但 pairplot
的真正价值是"自动把 N 个变量两两组合、自动排 N x N 网格"，这个
布局逻辑用 matplotlib 要写几十行，seaborn 一行。
判断：**价值真实但不紧迫**——本次 5 种 kind + log-scale 已经覆盖
了"单图/多图"的主线需求，pairplot 属于"探索性数据分析"的辅助工具，
不是"报告里必须呈现的关键结论图"（报告正文的图一般是"验证了某个
具体结论"，不是"探索所有变量两两关系"）。暂不加，撞到明确的
多变量探索需求再说（跟评估文档里④⑥的"撞到再评估"原则一致）。

--- 最终决定：本次只加 1 个 kind：boxplot（候选 A）---
理由：
1. 泛用性：多条件分布对比在物理报告里是真实存在的需求（不同材料/
   工况/取样点），且当前 5 种 kind 完全没有覆盖（不是"seaborn 有
   就有"的问题，是"我们需要这个呈现但 5 种 kind 画不出来"的问题）。
2. 不强依赖 seaborn：matplotlib 原生 boxplot 够用，seaborn 是
   "可选的美化后端"（装了画更好看的样式，不装画朴素但正确的图），
   这样 requirements.txt 里 seaborn 是 optional 依赖，不装也不影响
   项目其它任何功能——跟项目"克制"原则一致，不因为加一个 kind 就
   把整个项目的依赖面拉大。
3. 不破坏"脚本不做物理判断"原则：箱线图本身是纯统计呈现（分位数
   计算是确定性规则，不是物理判断），符合现有 5 种 kind 的定位。
4. 排除 B/C/D：B 违反"脚本不判断"原则（自动拟合），C 偏小众先
   不挤进来，D 是探索工具不是报告主线图。
"""
)
