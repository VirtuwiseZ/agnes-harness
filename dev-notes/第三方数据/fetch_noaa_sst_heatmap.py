"""
下载 NOAA OISST v2.1 日均海温（SST）小区域网格数据，用于 heatmap 图表测试。

数据源：NOAA ERDDAP / ncdcOisst21Agg_LonPM180
  - 机构：NOAA National Centers for Environmental Information (NCEI)
  - 数据集：NOAA 0.25° Daily Optimum Interpolation Sea Surface Temperature (OISST) v2.1
  - 许可：Public domain (US government data)
  - 官方页面：https://www.ncei.noaa.gov/products/optimum-interpolation-sst
  - ERDDAP 入口：https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.html

区域：西太平洋热带（0°–20°N，120°E–140°E），时间：2024-01-15，步长 1°
预期输出：~441 行（21×21 格子），约 20 KB，保存为 noaa_sst_pacific_20240115.csv

运行方式：
    python fetch_noaa_sst_heatmap.py

依赖：只用标准库 urllib，无需 requests/xarray。
"""

import urllib.request
import urllib.parse
import os
import sys

# ─── 参数 ────────────────────────────────────────────────────────────────────
DATE       = "2024-01-15T00:00:00Z"
LAT_MIN    =  0.0
LAT_MAX    = 20.0
LON_MIN    = 120.0
LON_MAX    = 140.0
STEP       = 1       # 1° 步长（0.25° 原始分辨率，取整数步以减小数据量）
OUT_FILE   = os.path.join(os.path.dirname(__file__), "noaa_sst_pacific_20240115.csv")

BASE_URL = (
    "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv"
    "?sst[({date}):1:({date})][({lat_min}):{step}:({lat_max})][({lon_min}):{step}:({lon_max})]"
)

url = BASE_URL.format(
    date    = DATE,
    lat_min = LAT_MIN,
    lat_max = LAT_MAX,
    lon_min = LON_MIN,
    lon_max = LON_MAX,
    step    = STEP,
)

print(f"Downloading from NOAA ERDDAP...")
print(f"URL: {url}")
print()

try:
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = resp.read().decode("utf-8")
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    print("If the above URL fails, open it in a browser and save the response as noaa_sst_pacific_20240115.csv", file=sys.stderr)
    sys.exit(1)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(data)

lines = data.strip().splitlines()
print(f"Downloaded {len(lines)} lines ({os.path.getsize(OUT_FILE)} bytes)")
print(f"Saved to: {OUT_FILE}")
print()
print("First 5 data lines:")
for line in lines[:7]:
    print(" ", line)
