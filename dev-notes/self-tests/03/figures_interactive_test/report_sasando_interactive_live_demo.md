# 2025A 竹响器（Sasando）— 拖动 zeta 实时看曲线变化（interactive_live 演示）

## 说明

这张图用第 8 种 figure kind（`interactive_live`）：拖动下方的 zeta（阻尼比）滑块时，浏览器端会对这条 H(f) 闭式表达式（4 个阻尼洛伦兹峰的求和，跟 `problem_state.json` 里已算好的 `headline_eigenfrequencies` 同一套数学）重新求一遍 y 值，实时改变曲线形态 —— 这就是 GeoGebra 式"调参数实时看图"的效果，全程不需要服务器，不需要重新解任何方程（因为这里要调的 zeta 只影响峰的宽度/高度，不影响特征频率本身，是一个便宜的闭式重算，不是数值模型重解）。

## 图（拖动滑块试试）

{{figure: fig_sasando_live}}
