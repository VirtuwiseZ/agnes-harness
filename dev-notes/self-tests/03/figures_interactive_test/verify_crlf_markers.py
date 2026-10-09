import sys
p = 'program-design/hooks/make_report_figures.py'
with open(p, 'rb') as f:
    data = f.read()
marker = "    js_div_id = div_id\r\n\r\n    script_template = \"\"\""
print("CRLF marker found:", marker.encode('utf-8') in data)
marker2 = "    controls_block = (\r\n        '<div class=\"interactive-live-controls\""
print("CRLF marker2 found:", marker2.encode('utf-8') in data)
