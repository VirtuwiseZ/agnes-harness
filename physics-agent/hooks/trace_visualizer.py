"""Node 4 — trace visualizer / research-report HTML generator.

Rendering architecture (repositioned 2026-10-05, per project owner's explicit
feedback: the page's audience is the *user of the physics study*, not the
project's developer; the process log is secondary, on-demand verification
material, not the headline):

  Primary narrative source:
    --report  the incremental markdown research report written by the agent
              during the run (physics-agent/runtime/report_<task-slug>.md,
              appended node-by-node per protocol Node 3). Rendered as the
              main body of the page, section by section, in the agent's own
              words — not paraphrased by this script.

  Supporting / verification layers (collapsed by default, expandable):
    --state   problem_state.json — shown only as structured data (anomalies,
              audit_logs, verification) attached to the relevant report
              section, for on-demand check.
    --trace   AGH raw trace export (JSONL, e.g. from `agh export <id> --raw`)
              — used only to compute per-section "files used in this section"
              provenance blocks (③第 4 条 4d, 10/12): which AGH SKILL/plugin
              invocations, project scripts, data sources, and third-party tools
              actually contributed to each report section, read from the 4a/4c
              audit-log fields (script execution) — NOT a general "did this
              claim happen" cross-check of every artifact_id the report
              mentions (that old per-section verify block + page-level
              summary table was removed in this same revision, per Q4
              定论; see the "removed UI blocks" note below in this docstring).

  Fallback (no --report given, e.g. legacy runs such as walkthrough-1 whose
  protocol predates the incremental-report requirement): the generator falls
  back to building the narrative from --state + --trace alone (the old
  "process-log-first" layout). This path is kept only for compatibility
  with already-finished runs; new runs are expected to always have a
  --report file, since the protocol now mandates it.

  KaTeX (③第 2 条, 10/12): the report markdown's inline ($...$) and display
  ($$...$$) math, plus any formulas the 6 style rules (see
  physics-agent/knowledge/report_structure_guide.md) require written as
  LaTeX, are rendered via a self-contained, no-external-CDN hook — the
  page's own inline <script> attempts to load a local KaTeX build shipped
  alongside this task's assets (<task-dir>/vendor/katex/, same per-task
  directory the 4c runlog asset files land in);  when that local build is
  present, every [data-katex] element is upgraded from raw-LaTeX-text to
  real rendered math;  when it is not (offline open, or the vendor/ dir
  was never populated for this task), nothing crashes — the raw LaTeX
  source simply stays visible as-is, never a blank box.

  Markdown pipe tables (③第 2 条, 10/12): consecutive lines starting with
  `|` in the report markdown are rendered as a real <table> (a real
  <thead> + <tbody>, not plain-text lines) — the Node 4-side counterpart
  of the 5th of the 6 style rules (data tables must use real markdown pipe
  syntax, not plain-text lines that merely resemble a table).

  Removed UI blocks (③第 2 条, 10/12, per Q4 定论 — no fallback kept):
    * the per-section <details class='verify-block'> "核验附证 — 这段内容
      对应的实际工具调用" block (the old claim-by-claim trace cross-check
      rendered inside each section);
    * the per-section <details class='state-block'> "数据快照 —
      problem_state.json 中本节写入/更新的内容" block;
    * the page-level "核验附证（汇总）" <section class='cross-check'>
      summary table at the bottom of the page.
  Replaced by, per section: a single collapsible "本节所使用文件" block
  (③第 4 条 4d) whose contents come from the 4a/4c audit-log fields
  (script_path/stdin_or_argv/stdout_tail/stderr/exit_code/iteration_index)
  plus the 4c per-run asset-file path — i.e. "what this section actually
  used to produce its numbers", not "did every claim the report makes
  have a matching trace event" (a broader, separate audit question that
  is not this block's job; the 4a design note in 网页重新设计1011-共识.md
  marks that boundary as open, to be decided when ③第 4 条 4a is fully
  implemented, not retro-fitted onto the removed UI).
  A section with no script-execution audit records at all still renders
  this block, showing the placeholder line "本节无脚本运行记录" — that
  placeholder is ③第 4 条 4d's own design, not a fallback for the removed
  blocks above (they are gone, not hidden behind a "no data" case).

  Visual layout:
    - Main spine: the markdown report's own section headings, in order, as
      the page's top-level structure (no imposed "5 layers" — the agent's
      report IS the structure; if the agent structured its work as N
      sections, the page has N sections).
    - Each report section: heading + agent's prose, expanded by default.
    - Under each section, a collapsed-by-default <details> block:
        * "核验附证（trace 对照）": which trace tool calls back up this
          section's specific claims, ✅/⚠ per claim.
        * "数据快照（problem_state.json）": the structured fields this
          section wrote (anomaly entries, verification numbers, etc.).
    - Anomaly / rollback indicators (orange = retriable, red = human
      decision needed, e.g. annealing rollback / permission stop) are
      visually flagged inside the section that mentions them, collapsed by
      default; a right-side "loop channel" draws return-arcs (e.g. a
      rollback to an earlier section) as SVG paths computed at generation
      time; a tiny inline JS re-measures endpoint positions when the user
      expands/collapses default-collapsed blocks, so loop lines never draw
      to the wrong place.
    - Self-contained single file: no external assets, no CDN, no network.

Usage:
    python physics-agent/hooks/trace_visualizer.py \
        --trace dev-notes/self-tests/trace_walkthrough1_raw.json \
        --report physics-agent/runtime/report_<task-slug>.md \
        --state  physics-agent/runtime/problem_state_<task-slug>.json \
        --out    dev-notes/self-tests/trace_<task>_report.html
"""
import argparse
import base64
import html
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_trace(path):
    """Load an AGH raw trace export (JSONL). Returns a list of events sorted by seq.

    Lines without a top-level "seq" field are ignored (not an error): the
    official `agh export --raw` format guarantees every line has one, but the
    automatic Node 4 capture tool (physics-agent/hooks/trace_capture.cjs)
    prepends a single `_capture_meta` audit line (sessionId + timestamp,
    useful for the HTML's provenance display but not a trace event) which has
    no seq — skipping such lines keeps this loader robust to both sources
    without callers having to pre-filter the file."""
    with open(path, "rb") as f:
        raw = f.read()
    lines = [l for l in raw.splitlines() if l.strip()]
    events = []
    for l in lines:
        obj = json.loads(l)
        if "seq" in obj:
            events.append(obj)
    events.sort(key=lambda e: e["seq"])
    return events


def load_state(path):
    if not path or not os.path.exists(path):
        return None
    # utf-8-sig transparently strips a BOM if present and is identical to plain
    # utf-8 if not — matters because state files produced via PowerShell's
    # Out-File pipeline (a documented way this project has pulled files down,
    # see dev-notes convention) carry a UTF-8 BOM, and json.load() on a BOM
    # would otherwise raise before any of this script's own logic runs.
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_report_md(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Trace interpretation
# ---------------------------------------------------------------------------

def extract_tool_calls(events):
    """Return a list of tool/call + tool/result pairs, in seq order."""
    calls = {}
    for e in events:
        if e["type"] == "tool/call":
            d = e["data"]
            calls[d["toolUseId"]] = {
                "toolUseId": d["toolUseId"],
                "seq": e["seq"],
                "ts": e["ts"],
                "name": d.get("name"),
                "args": d.get("args") or {},
                "result": None,
                "approval": None,
            }
    for e in events:
        if e["type"] == "tool/result":
            d = e["data"]
            tu = d.get("toolUseId")
            if tu in calls:
                calls[tu]["result"] = {
                    "seq": e["seq"],
                    "text": _first_text(d.get("content")),
                    "isError": bool(d.get("isError")),
                    "enforcement": d.get("enforcement"),
                }
    for e in events:
        if e["type"] == "approval/decided":
            d = e.get("data") or {}
            tu = d.get("toolUseId") or (d.get("meta") or {}).get("toolUseId")
            if tu in calls:
                calls[tu]["approval"] = {
                    "decision": d.get("decision"),
                    "reason": d.get("reason"),
                    "seq": e["seq"],
                }
    return [calls[k] for k in sorted(calls, key=lambda k: calls[k]["seq"])]


def _first_text(content):
    if not content:
        return ""
    parts = []
    for b in content:
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(b.get("text", ""))
    return "\n".join(parts)


def classify_approval(call):
    """Per §4 Kind 1 / Kind 2."""
    a = call.get("approval")
    r = call.get("result") or {}
    if a and a.get("decision") == "rejected":
        reason = a.get("reason") or ""
        kind1 = {"user_rejected", "policy_denied"}
        kind2 = {"timeout", "no_approver"}
        if reason in kind1:
            return "kind1_rejected", reason
        if reason in kind2:
            return "kind2_unanswered", reason
        return "rejected_other", reason
    if r.get("isError"):
        return "tool_error", None
    return "ok", None


# ---------------------------------------------------------------------------
# Markdown report → HTML (primary narrative path)
# ---------------------------------------------------------------------------

def md_to_html_blocks(md_text, katex=False):
    """Split the markdown report into top-level sections (## headings, falling
    back to ### if no ## exists) and render each section's body as minimal
    HTML (paragraphs, - lists, and — ③第 2 条, 10/12 — consecutive pipe-table
    lines; no full markdown renderer on purpose — the protocol specifies a
    constrained, predictable subset so the page stays zero-dependency)."""
    lines = md_text.splitlines()
    level = 2 if any(l.startswith("## ") for l in lines) else 3
    prefix = "## " if level == 2 else "### "

    sections = []
    current = None
    for line in lines:
        if line.startswith(prefix):
            if current:
                sections.append(current)
            current = {"title": line[len(prefix):].strip(), "body_lines": []}
        elif current is not None:
            current["body_lines"].append(line)
    if current:
        sections.append(current)

    blocks = []
    for sec in sections:
        body_html = _md_body_to_html(sec["body_lines"], katex)
        blocks.append({"title": sec["title"], "html": body_html,
                       "raw": "\n".join(sec["body_lines"]).strip()})
    return blocks


FIGURE_RE = re.compile(r"^\{\{figure:\s*([A-Za-z0-9_\-]+)\}\}\s*$")


def _md_body_to_html(body_lines, katex=False):
    """Render the constrained markdown subset (paragraphs, - lists, **bold**,
    `code`, $$-fenced math, and — ③第 2 条, 10/12 — consecutive pipe-table
    lines) into safe HTML.  A single line of the form
    `{{figure: <id>}}` is rendered as a <figure> placeholder carrying the
    figure id in a data attribute; the actual image is inlined into that
    placeholder later, in _figure_tag(), once --figures-dir is known.

    Pipe tables:  a run of consecutive lines whose first non-whitespace
    character is `|` (or a `|---|`-style header-separator line) is
    collected into a real <table><thead>/<tbody> — the Node 4-side
    counterpart of the 5th of the 6 style rules in
    physics-agent/knowledge/report_structure_guide.md.  The first such
    line is the header row;  a following line made only of `|` + `-`/`
    :` characters is consumed as the header/body divider, not data.
    No column-alignment parsing beyond that:  every remaining pipe line in
    the run is a data row, split on `|` into cells, cell text run through
    _inline() for the same **bold**/`code` handling as paragraphs.

    KaTeX:  when `katex` is True, $...$ and $$...$$ segments in the
    plain-text parts of paragraphs/table cells are wrapped in
    [data-katex='true'] markers carrying the raw LaTeX source;  the
    page-level <script> (see _js()) upgrades these into real rendered
    formulas when a local KaTeX build is available, or leaves the raw
    source visible when not (offline-safe, never a crash — ③第 2 条).
    """
    out = []
    in_list = False
    table_rows = []

    def _flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        def _cells(line):
            s = line.strip()
            if s.startswith("|"):
                s = s[1:]
            if s.endswith("|"):
                s = s[:-1]
            return [c.strip() for c in s.split("|")]
        header_cells = _cells(table_rows[0])
        body_start = 1
        if len(table_rows) > 1 and all(
            set(c.replace(" ", "")) <= set("-:") for c in _cells(table_rows[1])
        ):
            body_start = 2  # markdown header-separator row, not data
        thead = "<thead><tr>" + "".join(
            f"<th>{_inline(c, katex)}</th>" for c in header_cells) + "</tr></thead>"
        tbody_rows = ["".join(f"<td>{_inline(c, katex)}</td>" for c in _cells(r))
                      for r in table_rows[body_start:]]
        tbody = ("<tbody>" + "".join(f"<tr>{r}</tr>" for r in tbody_rows) + "</tbody>")
        out.append(f"<table class='md-table'>{thead}{tbody}</table>")
        table_rows = []

    for raw in body_lines:
        line = raw.rstrip()
        if line.lstrip().startswith("|"):
            table_rows.append(line)
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        _flush_table()
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        m = FIGURE_RE.match(line.strip())
        if m:
            if in_list:
                out.append("</ul>")
                in_list = False
            fid = m.group(1)
            out.append(f"<figure class='report-figure' data-figure-id='{html.escape(fid)}'></figure>")
            continue
        if line.lstrip().startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + _inline(line.lstrip()[2:], katex) + "</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<p>" + _inline(line, katex) + "</p>")
    _flush_table()
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _inline(text, katex=False):
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    if katex:
        # $$...$$ (display) first, then $...$ (inline) — both against the
        # already-html-escaped string, so only LaTeX that survived escaping
        # (i.e. not inside a <tag>) gets wrapped in a data-katex marker;
        # the actual render-or-degrade-to-raw-source step happens in the
        # page's inline <script> (see _js()), not here — this function just
        # marks which stretches of text are meant to be math.
        text = re.sub(r"\$\$([^$]+)\$\$",
                      lambda m: f"<div class='math display' data-katex='true'>{m.group(1)}</div>",
                      text)
        text = re.sub(r"\$([^$]+)\$",
                      lambda m: f"<span class='math' data-katex='true'>{m.group(1)}</span>",
                      text)
    return text


# ---------------------------------------------------------------------------
# Legacy fallback (no --report): old trace/state-driven 5-layer layout
# ---------------------------------------------------------------------------

def build_steps_legacy(calls, state):
    """Old behavior, kept only for pre-Node3-incremental-report runs.
    See build_steps() docstring in the previous revision of this file; same
    shape: 5 layers x step-blocks.  (The former third parameter, `cross`,
    removed in ③第 2 条 / Q4 定论:  the cross-check data was only ever fed
    into the now-deleted UI blocks, not into this legacy layer layout.)"""
    layers = []

    task = (state or {}).get("task") or {}
    spec_calls = [c for c in calls if c["name"] == "write" and "problem_id" in json.dumps(c.get("args") or {})]
    layers.append(_legacy_layer(1, "读题解构", [_legacy_step(
        "任务规格写入 problem_state.json",
        (task.get("description") or "")[:300],
        "trace: write tool/call, seq=" + (str(spec_calls[0]["seq"]) if spec_calls else "n/a"),
        "Node 1",
        None,
        detail=json.dumps(task, ensure_ascii=False, indent=2)[:1500],
        seqs=[c["seq"] for c in spec_calls],
    )]))

    hyp = (state or {}).get("hypothesis_layer") or {}
    kr = (state or {}).get("knowledge_routing") or {}
    kr = kr if isinstance(kr, dict) else {"note": str(kr)}
    adapt_calls = [c for c in calls if c["name"] in ("read", "ls") and
                   any(k in json.dumps(c.get("args") or {}) for k in ("knowledge", "template", "ode"))]
    layers.append(_legacy_layer(2, "提出模型假设", [_legacy_step(
        "知识路由与方法论适配判断",
        "匹配模板 " + str(kr.get("matched_template")) + "；模板数值假设需按本题条件重新核对",
        "trace: " + str(len(adapt_calls)) + " file-read/inspect calls to knowledge/ dirs",
        "Node 2a",
        None,
        detail=json.dumps(hyp.get("assumptions") or {}, ensure_ascii=False, indent=2)[:1500],
        seqs=[c["seq"] for c in adapt_calls],
    )]))

    dsd = (state or {}).get("data_source_decision") or {}
    if not isinstance(dsd, dict):
        dsd = {"note": str(dsd)}
    # "modeling_input_source" is the current, domain-neutral field name;
    # "atmosphere_source" is the name an earlier revision of the template
    # used for the same concept (before it was generalized) — try the new
    # name first, fall back to the old one so already-produced state files
    # still render correctly instead of showing a blank "selected source".
    atmo = dsd.get("modeling_input_source", dsd.get("atmosphere_source"))
    atmo = atmo if isinstance(atmo, dict) else {"name": str(atmo) if atmo else ""}
    ws_calls = [c for c in calls if c["name"] == "web_fetch"]
    shell_level0 = [c for c in calls if c["name"] == "shell" and "import " in json.dumps(c.get("args") or {})]
    anomaly3 = "minor" if ws_calls and any((c.get("result") or {}).get("isError") for c in ws_calls) else None
    layers.append(_legacy_layer(3, "数据源判断", [_legacy_step(
        "数据源判断与降级",
        "选定数据源: " + str(atmo.get("name")),
        "trace: shell " + str(len(shell_level0)) + " call(s), web_fetch " + str(len(ws_calls)) + " call(s)",
        "Node 1.5",
        anomaly3,
        detail=json.dumps(dsd, ensure_ascii=False, indent=2)[:1500],
        seqs=[c["seq"] for c in (ws_calls + shell_level0)],
    )]))

    shell_calls = [c for c in calls if c["name"] == "shell"]
    edit_calls = [c for c in calls if c["name"] == "edit"]
    shell_rejected = [c for c in shell_calls if classify_approval(c)[0].startswith("kind")]
    edit_rejected = [c for c in edit_calls if classify_approval(c)[0].startswith("kind")]
    anomalies = (state or {}).get("anomalies") or []
    anomaly_major = [a for a in anomalies if a.get("type") == "annealing_triggered"]
    anomaly_minor = [a for a in anomalies if a.get("type") != "annealing_triggered"]
    layer4 = [_legacy_step(
        "数值执行与迭代",
        str(len(shell_calls)) + " 次 shell 调用，" +
        (str(len(shell_rejected)) + " 次因权限被拒" if shell_rejected else "全部获批执行") + "。",
        "trace: shell tool/call + approval/decided 配对",
        "Node 2b",
        "minor" if shell_rejected else None,
        detail="\n".join((c.get("args") or {}).get("command", "")[:120] for c in shell_calls[:6]),
        seqs=[c["seq"] for c in shell_calls],
    ), _legacy_step(
        "problem_state.json 增量写入 + 写回验证",
        str(len(edit_calls)) + " 次 edit 调用，" +
        (str(len(edit_rejected)) + " 次因权限被拒（§3 写回验证规则针对性修复此漏洞）" if edit_rejected else "全部成功落盘"),
        "trace: edit tool/call + 后续 read 回读验证配对",
        "§3 Write-back verification",
        "minor" if edit_rejected else None,
        seqs=[c["seq"] for c in edit_calls],
    )]
    for a in anomaly_minor:
        layer4.append(_legacy_step("⚠ " + str(a.get("type")), str(a.get("note"))[:300],
                                   "problem_state.json → anomalies[]", "§1", "minor",
                                   detail=json.dumps(a, ensure_ascii=False, indent=2)[:1500]))
    for a in anomaly_major:
        layer4.append(_legacy_step("⛔ 退火回滚触发", str(a.get("note"))[:300],
                                   "problem_state.json → anomalies[]", "§1 配额退火回滚 (N≤3)", "major",
                                   detail=json.dumps(a, ensure_ascii=False, indent=2)[:1500]))
    layers.append(_legacy_layer(4, "测验与迭代", layer4))

    report = (state or {}).get("report") or {}
    verification = (state or {}).get("verification") or {}
    layers.append(_legacy_layer(5, "得出结论", [_legacy_step(
        "结论与可追溯性",
        (report.get("conclusion") or "（未完成 Node 3 完整数值落地）")[:300],
        "problem_state.json → report.conclusion", "Node 3", None,
        detail=json.dumps(verification, ensure_ascii=False, indent=2)[:1500]
        if verification.get("comparison_result") is not None else "",
    )]))
    return layers


def _legacy_step(title, summary, evidence, clause, anomaly_level, detail="", seqs=None):
    return {"title": title, "summary": summary, "evidence": evidence, "clause": clause,
            "anomaly_level": anomaly_level, "detail": detail, "seqs": seqs or []}


def _legacy_layer(num, title, steps):
    return {"num": num, "title": title, "steps": steps, "legacy": True}


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def _section_files_block(section_index, blocks, state, runlog_base_dir="physics-agent/runtime"):
    """③第 4 条 4d (10/12): the per-section collapsible "本节所使用文件"
    block, replacing the removed verify_block/state_block/cross-check UI
    (③第 2 条 / Q4 定论).  Reads the 4a 6-key audit records (when present)
    + the 4c asset-file path; renders the original A4 four-sub-item layout
    (AGH SKILL 与插件 / 程序 / 数据源 / 第三方工具) with the "无则不加这项"
    rule — an entire sub-item row is omitted when it has zero entries, not
    rendered as an empty sub-heading.  If this section has no associated
    script-execution audit records at all, the block still renders, showing
    the single placeholder line "本节无脚本运行记录" (③第 4 条 4d's own
    design, not a fallback for the removed blocks — those are gone, not
    hidden behind a "no data" case).

    Association heuristic (not a hard key — older state files predate 4a's
    6 keys entirely, so this is best-effort): the section's own title is
    matched against the `source` tag's node hint (the existing
    `run2_node1_task_spec` convention, Node 1/1.5/2a/2b naming) to decide
    which audit records "belong" to this section;  records whose `source`
    tag doesn't match this section's node are not listed under it.
    """
    audit = (state or {}).get("audit_logs") or []
    related = [r for r in audit if "script_path" in r]  # 4a script-execution records only
    if not related:
        return ("<details class='files-block'><summary>本节所使用文件</summary>"
                "<p class='runlog-empty'>本节无脚本运行记录</p></details>")

    title_key = (blocks[section_index]["title"] if blocks else "").lower()
    def _node_of(rec):
        src = str(rec.get("source", "")).lower()
        for tag, name in (("node1.5", "数据源"), ("node2b", "数值"),
                          ("node2a", "建模"), ("node1", "建模")):
            if tag in src:
                return name
        return None
    related = [r for r in related if _node_of(r) in (None, "建模", "数值", "数据源")]
    # Keep only records plausibly tied to *this* section's node when detectable
    if "node1.5" in title_key or "数据源" in title_key:
        related = [r for r in related if _node_of(r) == "数据源"] or related
    elif "node2b" in title_key or "建模" in title_key or "数值" in title_key:
        related = [r for r in related if _node_of(r) in ("数值", "建模")] or related

    program_rows, datasource_rows, thirdparty_rows = [], [], []
    for r in related:
        sp = r.get("script_path", "")
        note = (r.get("args") or {}).get("note") or ""
        iter_i = r.get("iteration_index")
        exit_code = r.get("exit_code")
        artifact_id = r.get("artifact_id", "")
        runlog_rel = os.path.join(runlog_base_dir, "<task-slug>", "runlogs", f"{artifact_id}.txt")
        src_kind = _node_of(r)
        if sp and not sp.startswith("physics-agent/hooks/"):
            label = (f"{html.escape(sp)}（第 {iter_i} 次调试，exit {exit_code}）" if iter_i
                     else html.escape(sp))
            program_rows.append(
                f"<li><a class='runlog-link' href='{html.escape(runlog_rel)}'>{label}</a>"
                f"<p class='runlog-note'>{html.escape(note)}</p></li>")
        elif src_kind == "数据源":
            datasource_rows.append(f"<li>{html.escape(sp or str(r.get('source', '')))} — {html.escape(note)}</li>")
        elif src_kind in ("数值", "建模"):
            thirdparty_rows.append(f"<li>{html.escape(sp or str(r.get('source', '')))} — {html.escape(note)}</li>")

    parts = ["<details class='files-block'><summary>本节所使用文件</summary><ul class='files-list'>"]
    # AGH SKILL 与插件 sub-item: 原文 A4 结构固定保留位置（A6-Q2 判断：先保留在信息结构里，
    # 当前实际只有 1 条——physics-agent-governance——不需要为此专门设计展示机制），
    # 无则不加这项。
    parts.append("<li class='files-subitem'><strong>AGH SKILL 与插件</strong><ul>"
                 "<li>physics-agent-governance（AGH 主 skill，路由 + 节点级子 skill 清单；"
                 "完整规则见各子 skill 触发时按需读取，不在本节重复正文）</li>"
                 "</ul></li>")
    if program_rows:
        parts.append("<li class='files-subitem'><strong>程序</strong><ul>" + "".join(program_rows) + "</ul></li>")
    if datasource_rows:
        parts.append("<li class='files-subitem'><strong>数据源</strong><ul>" + "".join(datasource_rows) + "</ul></li>")
    if thirdparty_rows:
        parts.append("<li class='files-subitem'><strong>第三方工具</strong><ul>" + "".join(thirdparty_rows) + "</ul></li>")
    parts.append("</ul></details>")
    return "".join(parts)


def _state_snapshot_block(state):
    # ③第 2 条 / Q4 定论:  此函数及其调用点已随 per-section verify_block/
    # state_block 一起删除；保留函数体（不再被 render_html 调用）仅为旧调用方
    # 兼容期内的 no-op，下一次大版本时整体移除。
    return ""


def _katex_head_tag(runlog_base_dir="physics-agent/runtime"):
    """③第 2 条: self-contained KaTeX hook — NOT an external CDN link.
    Emits nothing into the <head> itself (no <link>, no external
    <script src>);  the actual local-KaTeX-load-or-degrade logic lives in
    the page's own inline <script> (see _js()), which fetches a local
    KaTeX build shipped alongside this task's assets at
    <task-dir>/vendor/katex/ (task-dir = whatever per-task runtime
    subfolder this report was generated under, consistent with the 4c
    asset-file directory convention).  If that local build is present,
    every [data-katex='true'] element is upgraded from raw-LaTeX-text to
    real rendered math;  if not (offline open, or vendor/ never
    populated for this task), nothing crashes — the raw LaTeX source
    simply stays visible as-is (③第 2 条's explicit requirement: “离线打开
    时公式退化为原始 LaTeX 源码显示，不崩溃”).  Genuinely self-contained:
    no external host is ever referenced.  This is the Node 4 rendering
    counterpart of ③第 1 条's style rule that formulas must be written as
    LaTeX (giving this path something to render)."""
    return ""  # no head injection needed; the upgrade attempt is in _js()


def render_html(blocks, cross, events, state, out_path, fallback_legacy=None,
                 report_source="report-md", figures_dir=None,
                 runlog_base_dir="physics-agent/runtime"):
    """blocks: list of {title, html, raw} — the page's main spine, in order.
    fallback_legacy: if set (no --report given), renders the old 5-layer layout
    instead of (not in addition to) the blocks spine — see module docstring.
    figures_dir: if set, every {{figure: <id>}} placeholder produced by
    _md_body_to_html() is inlined here (base64) with its caption looked up
    in problem_state.json's numerical_artifacts.figures[<id>].title when
    state is provided; missing files render as an explicit "missing" box,
    never silently dropped.
    runlog_base_dir: base dir for ③第 4 条 4c's per-run asset files (the
    "本节所使用文件" block's run-record links point at
    <runlog_base_dir>/<task-slug>/runlogs/<artifact_id>.txt)."""
    session_start = next((e for e in events if e["type"] == "session/start"), None)
    session_key = (session_start or {}).get("data", {}).get("key", "unknown-session")

    spine_html = []
    for i, b in enumerate(blocks or []):
        block_id = f"sec-{i}"
        section_html = _figure_tag(figures_dir, b["html"], state) if figures_dir is not None else b["html"]
        files_block = _section_files_block(i, blocks, state, runlog_base_dir) if (blocks or []) else ""
        spine_html.append(
            f"<section class='report-section' id='{block_id}'>"
            f"<h2>{html.escape(b['title'])}</h2>"
            f"<div class='sec-body'>{section_html}</div>"
            f"{files_block}"
            f"</section>"
        )

    legacy_spine = ""
    if fallback_legacy:
        legacy_spine = "<h1 class='legacy-note'>（该运行未产出 Node 3 增量研究汇报 markdown，以下为基于" \
                       "trace + problem_state.json 的过程记录视图，非最终报告形态）</h1>"
        legacy_spine += _render_legacy(fallback_legacy)

    doc = (
        "<!doctype html>\n<html lang='zh'><head><meta charset='utf-8'>"
        "<title>物理研究汇报 — " + html.escape(session_key) + "</title>"
        + _katex_head_tag(runlog_base_dir)
        + "<style>" + _css() + "</style></head><body>"
        "<header class='report-header'><h1>物理研究汇报</h1>"
        f"<p class='meta'>session: {html.escape(session_key)} · 主叙事来源: {report_source}"
        f" · trace 事件数: {len(events)} · tool calls: {sum(1 for e in events if e['type'] == 'tool/call')}"
        f" · 生成于 {_now_iso()}</p></header>"
        + ("".join(spine_html) if spine_html else legacy_spine)
        + "<aside class='loop-channel' id='loop-channel' aria-hidden='true'></aside>"
        + "<script type='application/json' id='loop-data'>" + json.dumps(_loop_data(spine_html or [], cross)) + "</script>"
        + "<script>" + _js() + "</script></body></html>"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_path


def _figure_tag(figures_dir, block_html, state):
    """Fill every <figure class='report-figure' data-figure-id='...'></figure>
    placeholder in a report section with its inlined figure. figures_dir may be
    None (no --figures-dir given), in which case every placeholder becomes an
    explicit "no figure source configured" box — matching this project's
    "never paper over a missing piece of output" principle rather than
    rendering a blank <figure>. State (if provided) is consulted only to look
    up the figure's caption (numerical_artifacts.figures[<id>].title); it is
    not used for anything else, and never for a physics judgment about the
    figure's content.

    Two file types are inlined, never mixed up: raster/vector images
    (.png/.svg/.jpg/.jpeg) go in as a base64 <img> (the static matplotlib
    kinds); an interactive Plotly figure (kind='interactive', see
    dev-notes/interactive_figure_design.md §3) is a self-contained .html
    fragment produced by make_report_figures.py's _render_interactive() and
    is inlined by inlining that fragment's <div>+<script> body directly —
    not wrapped in an <img>, since it is not an image, it is a live
    interactive widget (rotation/zoom/hover/button-switching, all client-
    side, no external CDN dependency thanks to plotly's inline plotly.js).
    """
    def repl(m):
        fid = html.unescape(m.group(1))
        title = ""
        if state:
            figs = (state.get("numerical_artifacts") or {}).get("figures") or {}
            fig = figs.get(fid)
            if isinstance(fig, dict):
                title = fig.get("title") or ""
        if not figures_dir:
            return (f"<figure class='report-figure-missing'>引用了 <code>{html.escape(fid)}</code> 的图，"
                    f"但未提供 --figures-dir，无法内联对应图片/交互片段。</figure>")
        # Image kinds: .png/.svg/.jpg/.jpeg
        path = None
        for ext in (".png", ".svg", ".jpg", ".jpeg"):
            cand = os.path.join(figures_dir, fid + ext)
            if os.path.exists(cand):
                path = cand
                break
        if path is not None:
            ext = os.path.splitext(path)[1].lower()
            mime = {".png": "image/png", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}[ext]
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            caption = f"<figcaption>{html.escape(title) if title else '（无标题）'}</figcaption>"
            return (f"<figure class='report-figure-inlined'>"
                    f"<img src='data:{mime};base64,{b64}' alt='{html.escape(fid)}'>{caption}</figure>")
        # Interactive kind: <fid>.html (a full self-contained Plotly fragment,
        # not an image — extract just its rendered <div>+<script> body, not
        # the fragment's own <!doctype>/<html>/<head> shell, so it composes
        # cleanly inside this report page rather than nest a second document).
        html_path = os.path.join(figures_dir, fid + ".html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                frag = f.read()
            body_m = re.search(r"(<div id='[^']+Plotly[^']*'>[\s\S]*?</div>)\s*(<script>[\s\S]*?</script>)?", frag)
            body = (body_m.group(1) + (body_m.group(2) or "")) if body_m else frag
            caption = f"<figcaption>{html.escape(title) if title else '（无标题）'}" \
                      f"<span class='figure-kind-tag'>交互图</span></figcaption>"
            return (f"<figure class='report-figure-inlined report-figure-interactive'>"
                    f"{body}{caption}</figure>")
        return (f"<figure class='report-figure-missing'>引用了 <code>{html.escape(fid)}</code> 的图，"
                f"但在 --figures-dir 下找不到对应的 <code>{html.escape(fid)}</code>.png/.svg/.jpg/.jpeg/.html。"
                f"（.html 对应 kind='interactive' 的交互图分支，见 dev-notes/interactive_figure_design.md。）</figure>")
    return re.sub(r"<figure class='report-figure' data-figure-id='([^']+)'></figure>", repl, block_html)


def _render_legacy(layers):
    out = []
    for layer in layers:
        steps_html = []
        for i, s in enumerate(layer["steps"]):
            badge = ('<span class="badge badge-major">需人决策</span>' if s["anomaly_level"] == "major"
                     else '<span class="badge badge-minor">可恢复小异常</span>' if s["anomaly_level"] == "minor" else "")
            seqs_text = ("trace seq: " + ", ".join(map(str, s["seqs"]))) if s["seqs"] else "无对应 trace 工具调用"
            steps_html.append(
                f'<div class="step-block anomaly-{s["anomaly_level"] or "normal"}">'
                f'<div class="step-head"><strong>{html.escape(s["title"])}</strong>{badge}</div>'
                f'<div class="step-summary">{html.escape(s["summary"])}</div>'
                f'<div class="step-evidence"><em>依据:</em> {html.escape(s["evidence"])}'
                f' · <em>条款:</em> {html.escape(s["clause"])}</div>'
                f'<div class="step-seqs">{html.escape(seqs_text)}</div>'
                + (f'<details class="step-detail"><summary>展开细节</summary><pre>{html.escape(s["detail"])}</pre></details>'
                   if s["detail"] else "")
                + f'</div>'
            )
        out.append(
            f'<section class="layer-card" id="layer-{layer["num"]}">'
            f'<h2><span class="layer-num">{layer["num"]}</span> {html.escape(layer["title"])}</h2>'
            + "\n".join(steps_html) + "</section>"
        )
    return "\n".join(out)


def _loop_data(spine_html, cross):
    """Return-arc specs: sections whose content explicitly mentions a rollback /
    permission-stop / data-source-stop trigger get an arc back to an earlier
    section (or to section 0 if no earlier section is implicated). Kept very
    conservative — only fired on explicit keywords, not guessed."""
    arcs = []
    markers = {
        "annealing": ("回滚", "annealing", "退火"),
        "permission": ("PERMISSION REQUIRED", "权限受限", "permission_denied", "permission_unanswered"),
        "data_source": ("DATA SOURCE REQUIRED", "数据源受限", "data_source_unavailable"),
    }
    # spine_html here is a list of section html strings only when built in
    # render_html; for the legacy path it is passed as [] and we fall back to
    # scanning the legacy layers' step titles instead — caller passes
    # `spine_html` purely as a positional marker; real detection uses the
    # section *titles/sections* built by the caller, not the joined html.
    return arcs  # v1: no auto-drawn arcs yet; left as a stable hook.


def _css():
    return """
:root{--bg:#0f1117;--card:#1a1d27;--card2:#232733;--ink:#e8eaf2;--muted:#9aa0b4;
--accent:#4f8cff;--orange:#ff9f43;--red:#ff5470;--green:#2ecc71;--line:#3a3f52}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 system-ui,"Segoe UI",sans-serif;padding:24px 200px 40px 24px}
header.report-header h1{font-size:26px;margin:0 0 4px}
.meta{color:var(--muted);font-size:13px}
.report-section{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:18px 20px;margin:18px 0}
.report-section h2{font-size:20px;margin:0 0 12px}
.sec-body p{margin:8px 0}
.report-figure-inlined,.report-figure-missing{margin:14px 0}
.report-figure-inlined img{max-width:100%;border:1px solid var(--line);border-radius:8px}
.report-figure-inlined figcaption,.report-figure-missing{font-size:12.5px;color:var(--muted);margin-top:4px}
.report-figure-interactive .report-figure-body,.report-figure-interactive>div{max-width:100%}
.figure-kind-tag{display:inline-block;font-size:10.5px;background:var(--accent);color:#fff;
padding:1px 6px;border-radius:8px;margin-left:6px;vertical-align:middle}
.report-figure-missing{border:1px solid var(--orange);background:#1a1d27;padding:10px 12px;
border-radius:8px}
.sec-body ul{margin:8px 0 8px 18px}
.sec-body code{background:#12141c;padding:1px 5px;border-radius:4px;font-size:0.92em}
.md-table{border-collapse:collapse;margin:10px 0;width:100%}
.md-table th,.md-table td{padding:5px 9px;border:1px solid var(--line);text-align:left;font-size:13.5px}
.md-table th{color:var(--muted);font-weight:600}
.files-block{margin-top:14px;font-size:13px;color:var(--muted);border-left:4px solid var(--green);padding-left:12px}
.files-block summary{cursor:pointer;color:var(--green);font-weight:600}
.files-list{list-style:none;margin:6px 0;padding:0}
.files-list>li.files-subitem{margin:6px 0}
.files-list ul{list-style:disc;margin:4px 0 4px 18px}
.runlog-link{color:var(--accent)}
.runlog-note{font-size:12px;color:var(--muted);margin:2px 0 0}
.runlog-empty{color:var(--muted)}
.math{font-family:serif;font-style:italic}
.math.display{display:block;text-align:center;margin:10px 0;font-size:1.1em}
.legacy-note{color:var(--muted);font-weight:400;font-size:15px;margin:20px 0}
.layer-card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:18px 20px;margin:18px 0}
.layer-card h2{font-size:20px;margin:0 0 12px;display:flex;align-items:center;gap:10px}
.layer-num{background:var(--accent);color:#fff;border-radius:50%;width:30px;height:30px;
display:inline-flex;align-items:center;justify-content:center;font-size:15px}
.step-block{background:var(--card2);border-radius:8px;padding:12px 14px;margin:10px 0;
border-left:4px solid var(--accent)}
.step-block.anomaly-minor{border-left-color:var(--orange)}
.step-block.anomaly-major{border-left-color:var(--red)}
.badge{font-size:11px;padding:2px 8px;border-radius:10px;margin-left:8px;font-weight:600}
.badge-major{background:var(--red);color:#fff}
.badge-minor{background:var(--orange);color:#1a1d27}
.step-detail{margin-top:8px;font-size:12.5px;color:var(--muted)}
.step-detail pre{white-space:pre-wrap;background:#12141c;
padding:8px;border-radius:6px;max-height:220px;overflow:auto}
.loop-channel{position:fixed;right:16px;top:80px;width:160px}
.loop-arc{fill:none;stroke-width:2;opacity:.85}
.loop-arc.major{stroke:var(--red)}
"""


def _js():
    return """
(function(){
  // ③第 2 条 KaTeX 本地升级：若本任务随附了自己的 KaTeX 构建（自包含、
  // 不走外部 CDN，路径约定见 _katex_head_tag docstring），把每个
  // [data-katex='true'] 元素从“原始 LaTeX 源码”升级为真实渲染的公式；
  // 若本地构建不存在（离线打开、或 vendor 目录未为该任务准备过），
  // 什么都不做——原始 LaTeX 源码原样可见，不崩（③第 2 条明确要求的
  // 离线退化行为）。此处只用相对路径 fetch，绝不引用任何外部域名。
  try{
    fetch('vendor/katex/katex.min.js', {cache: 'no-cache'}).then(function(r){
      if(!r.ok){ throw new Error('local katex build not present'); }
      return r.text();
    }).then(function(code){
      (new Function(code + '\nwindow.katex=window.katex||{};'))();
      if(window.katex && window.katex.render){
        document.querySelectorAll('[data-katex="true"]').forEach(function(el){
          try{ window.katex.render(el.textContent, el, {throwOnError: false}); }
          catch(e){ /* 任何渲染失败都保持原始源码，不崩 */ }
        });
      }
    }).catch(function(){ /* 本地 KaTeX 不可用：原始 LaTeX 原样保留，不崩 */ });
  }catch(e){ /* 这段逻辑本身出任何错都不能影响页面其余 JS */ }

  // Placeholder for future return-arc drawing (see _loop_data docstring: v1
  // does not auto-draw arcs yet; this hook is left in so the mechanism is
  // already wired without needing a second revision of the page).
  var data = JSON.parse(document.getElementById('loop-data').textContent || '[]');
  var channel = document.getElementById('loop-channel');
  function draw(){
    channel.innerHTML = '';
    if(!data.length) return;
    var svgNS = 'http://www.w3.org/2000/svg';
    var H = document.body.scrollHeight;
    var svg = document.createElementNS(svgNS,'svg');
    svg.setAttribute('width','160'); svg.setAttribute('height', H);
    svg.style.position='absolute';
    channel.appendChild(svg);
    data.forEach(function(a){
      var fromEl = document.getElementById(a.from), toEl = document.getElementById(a.to);
      if(!fromEl || !toEl) return;
      var fr = fromEl.getBoundingClientRect(), tr = toEl.getBoundingClientRect(),
          cr = channel.getBoundingClientRect();
      var y1 = fr.top + fr.height/2 - cr.top, y2 = tr.top + tr.height/2 - cr.top, x = 80;
      var p = document.createElementNS(svgNS,'path');
      p.setAttribute('d','M '+x+' '+y1+' C '+(x+70)+' '+y1+', '+(x+70)+' '+y2+', '+x+' '+y2);
      p.setAttribute('class','loop-arc '+(a.sev||'major'));
      svg.appendChild(p);
    });
  }
  document.querySelectorAll('.files-block summary, .step-detail summary')
    .forEach(function(el){ el.addEventListener('click', function(){ setTimeout(draw,60); }); });
  setTimeout(draw, 100);
})();
"""


def _now_iso():
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate the Node 4 research-report HTML page.")
    ap.add_argument("--trace", required=True, help="AGH raw trace export (JSONL).")
    ap.add_argument("--report", default=None, help="Node 3 incremental markdown research report (primary narrative source).")
    ap.add_argument("--state", default=None, help="problem_state.json for the same run (optional).")
    ap.add_argument("--figures-dir", default=None, help="Directory holding .png/.svg figure files produced by make_report_figures.py; every {{figure: <id>}} placeholder in --report is inlined from here.")
    ap.add_argument("--runlog-dir", default="physics-agent/runtime",
                    help="Base dir for ③第 4 条 4c per-run asset files; the per-section 「本节所使用文件」block's run-record links resolve against <this>/<task-slug>/runlogs/<artifact_id>.txt")
    ap.add_argument("--out", default="research_report.html", help="Output HTML path.")
    args = ap.parse_args(argv)

    events = load_trace(args.trace)
    state = load_state(args.state)
    calls = extract_tool_calls(events)
    report_md = load_report_md(args.report)

    if report_md is not None:
        blocks = md_to_html_blocks(report_md, katex=True)
        legacy = None
        source = "report-md（AI 增量研究汇报，主叙事）"
    else:
        blocks = None
        legacy = build_steps_legacy(calls, state)
        source = "trace + problem_state.json（无 Node 3 增量汇报，退化视图）"

    out = render_html(blocks, {}, events, state, args.out,
                      fallback_legacy=legacy, report_source=source,
                      figures_dir=args.figures_dir,
                      runlog_base_dir=args.runlog_dir)
    print("wrote", out)
    print("narrative source:", source)
    print("tool calls in trace:", len(calls))
    if args.figures_dir:
        print("figures dir:", args.figures_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
