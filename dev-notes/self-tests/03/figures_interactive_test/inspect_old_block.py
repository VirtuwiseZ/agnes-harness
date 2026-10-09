import re
p = 'program-design/hooks/make_report_figures.py'
with open(p, 'r', encoding='utf-8', newline='') as f:
    text = f.read()

start_marker = "    js_div_id = div_id\r\n\r\n    script_template"
end_marker = '        "</div>"\r\n    )\r\n'
i = text.index(start_marker)
j = text.index(end_marker, i) + len(end_marker)
old_block = text[i:j]
print("old_block found, length:", len(old_block))
print("--- first 200 chars ---")
print(old_block[:200])
print("--- last 200 chars ---")
print(old_block[-200:])
