# -*- coding: utf-8 -*-
"""
test_dns_and_fetch.py — 针对当前网络环境的真实 DNS 解析与数据库直连连通性探测
"""
import socket
import urllib.request
import urllib.error
import ssl
import time

TARGETS = [
    ("NASA JPL SBDB API (小行星)", "https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=Apophis", "ssd-api.jpl.nasa.gov"),
    ("NASA 行星常数表", "https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html", "nssdc.gsfc.nasa.gov"),
    ("OpenAlex 开放学术 API", "https://api.openalex.org/works?search=physics&per-page=1", "api.openalex.org"),
    ("arXiv 预印本 API", "https://export.arxiv.org/api/query?search_query=all:physics&max_results=1", "export.arxiv.org"),
    ("中科院科学数据银行 (ScienceDB)", "https://www.sciencedb.cn/", "www.sciencedb.cn"),
    ("国家天文科学数据中心 (NADC)", "https://nadc.china-vo.org/", "nadc.china-vo.org"),
    ("国家气象科学数据中心 (CMA)", "https://data.cma.cn/", "data.cma.cn"),
    ("国家对地观测中心 (NODA)", "https://chinageoss.org/", "chinageoss.org"),
]

def main():
    print("=" * 70)
    print("本地网络环境真实 DNS 解析与数据库可连接性探测")
    print("=" * 70)
    
    # 忽略 SSL 证书严格校验以便测试物理链路
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    results = []

    for name, url, host in TARGETS:
        # 1. 探测底层系统 DNS 解析出来的真实 IP
        try:
            ips = socket.gethostbyname_ex(host)[2]
            ip_str = ", ".join(ips)
        except Exception as e:
            ip_str = f"DNS解析失败: {e}"

        # 2. 探测直连 HTTP(S) 请求状态
        status_str = ""
        elapsed = 0.0
        t0 = time.time()
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PhysicsAgent/1.0"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                elapsed = time.time() - t0
                status_str = f"HTTP {resp.status} 成功 ({elapsed:.2f}s)"
        except urllib.error.HTTPError as he:
            elapsed = time.time() - t0
            status_str = f"HTTP {he.code} (服务端响应, {elapsed:.2f}s)"
        except urllib.error.URLError as ue:
            elapsed = time.time() - t0
            status_str = f"连接失败: {ue.reason} ({elapsed:.2f}s)"
        except Exception as e:
            elapsed = time.time() - t0
            status_str = f"异常: {e} ({elapsed:.2f}s)"

        print(f"\n【{name}】")
        print(f"  目标域名 : {host}")
        print(f"  系统DNS解析 IP: {ip_str}")
        print(f"  直连访问结果  : {status_str}")
        
        results.append({
            "name": name,
            "url": url,
            "host": host,
            "ips": ip_str,
            "status": status_str
        })

    print("\n" + "=" * 70)
    print("探测完成。")

if __name__ == "__main__":
    main()
