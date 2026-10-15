"""E2 — Deterministic pre-delivery quality gate for physics-agent reports.

Validates both the Node 3 Markdown report (--report) and the Node 4 rendered
HTML report (--html) against all 7 quality dimensions required by
test6-1修正清单.md (B1, A1-A4, C1-C3, E1-E6):
  1. [B1/E5] Zero inline meta-commentary or self-praise phrases
  2. [E5]    Zero leaked internal JSON field names or pipeline jargon
  3. [E3]    Full Markdown block rendering (no raw ###, >, |, or {{figure:}} left unrendered)
  4. [A3/E1] Self-contained offline math rendering (no external/local fetch, no raw $...$ left)
  5. [A1/A2/E4] Two-column sticky preview pane & zero dead links (all artifact keys valid)
  6. [E5-1/5] Per-section filtered file blocks & 3-layer '程序' structure (作用 + 迭代记录)
  7. [A4/C3/E6] Pure Simplified Chinese descriptions in file blocks (no raw English audit notes)

Usage:
    python physics-agent/hooks/report_quality_check.py \
        --report physics-agent/runtime/<task-slug>/report.md \
        --html   physics-agent/runtime/<task-slug>/research_report_<task-slug>.html \
        [--state physics-agent/runtime/<task-slug>/problem_state.json]
"""
import argparse
import json
import os
import re
import sys


META_BLACKLIST = [
    (r"（原样引用）|\(原样引用\)", "行内元括注 '（原样引用）'"),
    (r"不再临时引入新假设", "复述规则的元导语 '不再临时引入新假设'"),
    (r"正文里用编号引用", "复述规则的元导语 '正文里用编号引用'"),
    (r"本轮执行说明", "自我标榜章节 '本轮执行说明'"),
    (r"本报告是[^\n。]*正式产物", "自我标榜语句 '本报告是…正式产物'"),
    (r"集中放在报告开头", "元说明语句 '集中放在报告开头'"),
]

JARGON_BLACKLIST = [
    (r"problem_state\.json", "内部状态文件名 'problem_state.json'"),
    (r"data_source_decision", "内部 JSON 字段名 'data_source_decision'"),
    (r"independent_of", "内部 JSON 字段名 'independent_of'"),
    (r"numerical_artifacts", "内部 JSON 字段名 'numerical_artifacts'"),
    (r"internal_prior", "内部 JSON 字段名 'internal_prior'"),
    (r"audit_logs", "内部 JSON 字段名 'audit_logs'"),
    (r"\bNode\s*(?:0|1\.5|1a|1|2a|2b|2\.7|3|4)\b", "内部流水线节点代号 'Node X'"),
    (r"\bLevel\s*[0-2]\b", "内部数据源分级代号 'Level 0/1/2'"),
    (r"A4\s*6-key", "内部开发黑话 'A4 6-key'"),
    (r"数据源\s*data-source\s*:", "中英混杂模板标签 '数据源 data-source:'"),
]


def _strip_scripts_and_styles(html_text):
    """Remove <script>...</script> and <style>...</style> blocks so text checks
    only inspect user-visible HTML markup."""
    s = re.sub(r"<script[\s\S]*?</script>", "", html_text, flags=re.IGNORECASE)
    s = re.sub(r"<style[\s\S]*?</style>", "", s, flags=re.IGNORECASE)
    return s


def _strip_tags(html_fragment):
    return re.sub(r"<[^>]+>", " ", html_fragment)


def check_report(report_path=None, html_path=None, state_path=None):
    errors = []

    md_text = ""
    if report_path:
        if not os.path.isfile(report_path):
            errors.append(f"[FILE] 找不到报告 Markdown 文件: {report_path}")
        else:
            with open(report_path, "r", encoding="utf-8-sig") as f:
                md_text = f.read()

    html_text = ""
    if html_path:
        if not os.path.isfile(html_path):
            errors.append(f"[FILE] 找不到报告 HTML 文件: {html_path}")
        else:
            with open(html_path, "r", encoding="utf-8-sig") as f:
                html_text = f.read()

    if errors:
        for e in errors:
            print(e)
        return 1

    visible_html = _strip_scripts_and_styles(html_text) if html_text else ""
    visible_text = _strip_tags(visible_html)

    # Check 1: B1 / E5 Meta-commentary & self-praise
    for pat, desc in META_BLACKLIST:
        if md_text and re.search(pat, md_text):
            errors.append(f"[Check 1 - B1 元导语拦截 (MD)] 命中禁用模式: {desc}")
        if visible_text and re.search(pat, visible_text):
            errors.append(f"[Check 1 - B1 元导语拦截 (HTML)] 命中禁用模式: {desc}")

    # Check 2: E5 Internal field names & developer jargon
    for pat, desc in JARGON_BLACKLIST:
        if md_text and re.search(pat, md_text):
            errors.append(f"[Check 2 - E5 内部黑话拦截 (MD)] 命中禁用模式: {desc}")
        if visible_text and re.search(pat, visible_text):
            errors.append(f"[Check 2 - E5 内部黑话拦截 (HTML)] 命中禁用模式: {desc}")

    if html_text:
        # Check 3: E3 Markdown syntax coverage
        if re.search(r"<p>\s*#{1,6}\s+", visible_html):
            errors.append("[Check 3 - E3 Markdown 渲染] HTML 中存在未渲染为标题标签的 '<p>### ...' 段落")
        if re.search(r"<p>\s*&gt;\s*", visible_html):
            errors.append("[Check 3 - E3 Markdown 渲染] HTML 中存在未渲染为 <blockquote> 的 '<p>&gt; ...' 引用段落")
        if re.search(r"\{\{figure:\s*[A-Za-z0-9_\-]+\}\}", visible_html):
            errors.append("[Check 3 - E3 Markdown 渲染] HTML 中残留未替换的 '{{figure: ...}}' 占位符")
        if md_text:
            if re.search(r"^###\s+", md_text, flags=re.MULTILINE) and "<h3" not in visible_html:
                errors.append("[Check 3 - E3 Markdown 渲染] Markdown 含三级标题 '### '，但 HTML 中未生成 <h3>")
            if re.search(r"^>\s+", md_text, flags=re.MULTILINE) and "<blockquote" not in visible_html:
                errors.append("[Check 3 - E3 Markdown 渲染] Markdown 含引用块 '> '，但 HTML 中未生成 <blockquote>")

        # Check 4: A3 / E1 Self-contained LaTeX math rendering
        if "id='katex-inline-style'" not in html_text and 'id="katex-inline-style"' not in html_text:
            errors.append("[Check 4 - E1 公式内联] HTML <head> 缺少内联数学排版样式表 (#katex-inline-style)")
        if "fetch('vendor/katex" in html_text or 'fetch("vendor/katex' in html_text:
            errors.append("[Check 4 - E1 公式内联] HTML 仍残留旧版必败的 fetch('vendor/katex/...') 逻辑")
        katex_nodes = re.findall(r"<(?:span|div)[^>]*data-katex=['\"]true['\"][^>]*>([\s\S]*?)</(?:span|div)>", visible_html)
        if md_text and "$" in md_text and not katex_nodes:
            errors.append("[Check 4 - E1 公式内联] Markdown 含公式定界符 '$'，但 HTML 中没有任何 [data-katex='true'] 渲染节点")
        for node_inner in katex_nodes:
            if "\\frac{" in node_inner or "\\sqrt{" in node_inner:
                errors.append("[Check 4 - E1 公式内联] [data-katex] 节点内仍残留未编译的 \\frac 或 \\sqrt 原始 LaTeX 源码")
                break
        # Check for unrendered raw $...$ in visible HTML outside math nodes
        html_without_math = re.sub(
            r"<(?:span|div)[^>]*data-katex=['\"]true['\"][^>]*>[\s\S]*?</(?:span|div)>",
            "",
            visible_html,
        )
        if re.search(r"\$\$[^$]+\$\$", html_without_math):
            errors.append("[Check 4 - E1 公式内联] HTML 可见正文中残留未渲染的 $$...$$ 公式块")

        # Check 5: A1 / A2 / E4 Two-column sticky preview pane & zero dead links
        for req_cls in ("report-layout", "report-main", "report-files-sidebar", "artifact-viewer"):
            if req_cls not in html_text:
                errors.append(f"[Check 5 - E4 右侧预览窗格] HTML 缺少双栏预览核心结构标识: {req_cls}")
        if "<task-slug>" in html_text:
            errors.append("[Check 5 - A2 死链拦截] HTML 中仍残留未替换的 '<task-slug>' 字面量路径")
        if re.search(r"href=['\"]['\"]", visible_html):
            errors.append("[Check 5 - A2 死链拦截] HTML 中存在空链接 href=''")

        m_payload = re.search(
            r"<script[^>]*id=['\"]artifact-payloads['\"][^>]*>([\s\S]*?)</script>",
            html_text,
        )
        payloads = {}
        if not m_payload:
            errors.append("[Check 5 - E4 右侧预览窗格] HTML 缺少内联预览数据池 <script id='artifact-payloads'>")
        else:
            try:
                payloads = json.loads(m_payload.group(1))
            except Exception as ex:
                errors.append(f"[Check 5 - E4 右侧预览窗格] artifact-payloads JSON 解析失败: {ex}")
            if not payloads:
                errors.append("[Check 5 - E4 右侧预览窗格] artifact-payloads 数据池为空")

        link_keys = re.findall(r"data-artifact-key=['\"]([^'\"]+)['\"]", visible_html)
        if not link_keys:
            errors.append("[Check 5 - E4 右侧预览窗格] 左侧章节未生成任何带 data-artifact-key 的可点击预览蓝链")
        for k in link_keys:
            if k not in payloads:
                errors.append(f"[Check 5 - E4 右侧预览窗格] 蓝链指向的 data-artifact-key='{k}' 在数据池中不存在")

        # Check 6: E5-1 section filtering & E5-5 '程序' 3-layer structure
        files_blocks = re.findall(r"<details class=['\"]files-block['\"][\s\S]*?</details>", visible_html)
        if len(files_blocks) >= 3 and len(set(files_blocks)) == 1:
            errors.append("[Check 6 - E5-1 按节过滤] 所有章节的 '本节相关文件' 内容完全雷同，未按章节职责过滤")
        for idx, fb in enumerate(files_blocks):
            if "<strong>程序</strong>" in fb:
                if "<strong>作用：</strong>" not in fb or "<strong>迭代记录：</strong>" not in fb:
                    errors.append(
                        f"[Check 6 - E5-5 程序板块结构] 第 {idx + 1} 节的 '程序' 子项缺少 1011 标准三层结构字段 ('作用：' 或 '迭代记录：')"
                    )

        # Check 7: A4 / C3 / E6 Chinese descriptions in file blocks
        for idx, fb in enumerate(files_blocks):
            fb_text = _strip_tags(fb)
            if re.search(r"\b(?:ran\s+gravity_assist|defense-line|verified\s+read-back|ephemeris\s+table)\b", fb_text, re.IGNORECASE):
                errors.append(f"[Check 7 - A4/E6 中文说明] 第 {idx + 1} 节 '本节相关文件' 仍包含未转化的英文审计原文")

        # Check 8: S10 Figure completeness, inlining & anti-flat gate
        if "report-figure-missing" in visible_html:
            errors.append("[Check 8 - 图表内联门禁] HTML 中存在未成功内联的图表占位报错 (report-figure-missing)")
        if state_path and os.path.isfile(state_path):
            try:
                with open(state_path, "r", encoding="utf-8-sig") as sf:
                    st_obj = json.load(sf)
                figs_spec = ((st_obj.get("numerical_artifacts") or {}).get("figures")) or {}
                if figs_spec and "report-figure-inlined" not in html_text:
                    errors.append("[Check 8 - 图表内联门禁] problem_state.json 定义了 figures，但 HTML 中未内联任何图表 (report-figure-inlined)")
                for fid, fspec in figs_spec.items():
                    if not isinstance(fspec, dict):
                        continue
                    f_series = fspec.get("series") or []
                    if fspec.get("kind", "curve") in ("curve", "scatter", "curve_family") and f_series and not fspec.get("allow_constant"):
                        non_flat = 0
                        multi_pt = 0
                        for s_item in f_series:
                            ys = [v for v in ((s_item.get("points") or {}).get("y") or []) if isinstance(v, (int, float))]
                            if len(ys) >= 3:
                                multi_pt += 1
                                if (max(ys) - min(ys)) > 1e-9 * max(abs(sum(ys) / len(ys)), 1.0):
                                    non_flat += 1
                        if multi_pt > 0 and non_flat == 0:
                            errors.append(f"[Check 8 - 防空白死线门禁] 图表 '{fid}' 的所有序列均为零方差水平死线")
            except Exception as ex:
                errors.append(f"[Check 8 - 状态文件图表检查] 读取 state 失败: {ex}")

    if errors:
        print(f"[FAIL] 报告质量门禁发现 {len(errors)} 项问题：")
        for e in errors:
            print("  -", e)
        return 1

    print("[PASS] 报告质量门禁 7 大类检查全部通过（无元导语/黑话、Markdown 与公式已内联渲染、右侧预览窗格与蓝链全部有效、四子项结构完整且全中文）。")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pre-delivery quality check for physics-agent report MD & HTML.")
    ap.add_argument("--report", default=None, help="Path to Node 3 markdown report.")
    ap.add_argument("--html", required=True, help="Path to Node 4 generated HTML report.")
    ap.add_argument("--state", default=None, help="Optional path to problem_state.json.")
    args = ap.parse_args(argv)
    return check_report(args.report, args.html, args.state)


if __name__ == "__main__":
    sys.exit(main())
