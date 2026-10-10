p = r"E:\agh-test\program-design\runtime\report_2013A_jupiter_flyby_run2.md"
raw = open(p, encoding="utf-8").read()

anchor = "（图文件：`program-design/runtime/figures_2013A_jupiter_flyby_run2/F1_delta_vs_perigee_head_on.png`、`F2a_saving_surface_head_on.png`、`F2b_saving_surface_overtaking.png`、`F3_chained_staircase.png`。）"
assert anchor in raw, "figure-listing anchor not found"
replacement = anchor + """

（以下 4 张图内联在报告中，供直接查看，不再需要去文件目录翻找：）

{{figure: F1_delta_vs_perigee_head_on}}

{{figure: F2a_saving_surface_head_on}}

{{figure: F2b_saving_surface_overtaking}}

{{figure: F3_chained_staircase}}
"""
raw = raw.replace(anchor, replacement, 1)
open(p, "w", encoding="utf-8").write(raw)
print("inserted 4 {{figure: ...}} placeholders after the plain-text figure listing in section 6")
