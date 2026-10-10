import re
s = open(r"E:\agh-test\program-design\runtime\report_2013A_jupiter_flyby_run2.html", encoding="utf-8").read()
print("data:image inlines:", s.count("data:image"))
for key in ["F1_delta", "F2a_saving", "F2b_saving", "F3_chained"]:
    print(f"{key} refs:", len(re.findall(key, s)))
