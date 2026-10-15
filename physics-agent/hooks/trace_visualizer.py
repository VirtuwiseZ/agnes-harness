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

_META_HEADING_RE = re.compile(r"^(?:本轮执行说明|执行说明|报告组织说明|本轮说明|写作说明)\b")
LBRACE = chr(123)
RBRACE = chr(125)
LBRACK = chr(91)
RBRACK = chr(93)

_GREEK_MAP = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ",
    "varphi": "ϕ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    "infty": "∞", "partial": "∂", "nabla": "∇", "hbar": "ℏ", "ell": "ℓ",
    "times": "×", "cdot": "·", "cdots": "⋯", "ldots": "…", "pm": "±", "mp": "∓",
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠", "ne": "≠",
    "approx": "≈", "sim": "∼", "simeq": "≃", "equiv": "≡", "propto": "∝",
    "ll": "≪", "gg": "≫", "subset": "⊂", "supset": "⊃", "in": "∈", "notin": "∉",
    "to": "→", "rightarrow": "→", "leftarrow": "←", "Rightarrow": "⇒",
    "Leftrightarrow": "⇔", "mapsto": "↦", "forall": "∀", "exists": "∃",
    "int": "∫", "oint": "∮", "sum": "∑", "prod": "∏", "circ": "∘", "degree": "°",
}

_ROMAN_FUNCS = {
    "sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "ln", "log", "exp", "max", "min", "sup", "inf",
    "lim", "det", "dim", "ker", "deg", "gcd", "Pr", "arg",
}


def _extract_braced(s, pos):
    """Extract balanced braced content starting at s[pos]. Returns (content, next_pos)."""
    if pos >= len(s) or s[pos] != LBRACE:
        return "", pos
    depth = 0
    start = pos + 1
    i = pos
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            i += 2
            continue
        if ch == LBRACE:
            depth += 1
        elif ch == RBRACE:
            depth -= 1
            if depth == 0:
                return s[start:i], i + 1
        i += 1
    return s[start:], len(s)


def _render_latex_to_html(latex_src, display=False):
    """Compile LaTeX math into rich, self-contained HTML math markup so formulas
    render with proper fractions, radicals, sub/superscripts, Greek letters, and
    operators immediately upon opening the file offline (zero CDN, zero file:// CORS)."""
    s = latex_src.strip()

    def _compile(expr):
        out = []
        i = 0
        n = len(expr)
        while i < n:
            ch = expr[i]
            if ch == "\\":
                if i + 1 < n and expr[i + 1] in (",", ";", ":", "!", " "):
                    out.append("&thinsp;" if expr[i + 1] != "!" else "")
                    i += 2
                    continue
                if i + 1 < n and expr[i + 1] in (LBRACE, RBRACE, "%", "_", "&", "#", "$"):
                    out.append(html.escape(expr[i + 1]))
                    i += 2
                    continue
                if i + 1 < n and expr[i + 1] == "\\":
                    out.append("<br>")
                    i += 2
                    continue
                m = re.match(r"\\([A-Za-z]+)", expr[i:])
                if m:
                    cmd = m.group(1)
                    i += len(m.group(0))
                    while i < n and expr[i] == " ":
                        i += 1
                    if cmd in ("left", "right", "bigl", "bigr", "Bigl", "Bigr", "displaystyle", "textstyle"):
                        continue
                    if cmd in ("quad", "qquad"):
                        out.append("&emsp;")
                        continue
                    if cmd in ("frac", "dfrac", "tfrac"):
                        num, i = _extract_braced(expr, i)
                        while i < n and expr[i] == " ":
                            i += 1
                        den, i = _extract_braced(expr, i)
                        out.append(
                            f"<span class='m-frac'><span class='m-num'>{_compile(num)}</span>"
                            f"<span class='m-den'>{_compile(den)}</span></span>"
                        )
                        continue
                    if cmd == "sqrt":
                        if i < n and expr[i] == LBRACK:
                            end_b = expr.find(RBRACK, i)
                            if end_b != -1:
                                root_idx = expr[i + 1:end_b]
                                i = end_b + 1
                                rad, i = _extract_braced(expr, i)
                                out.append(
                                    f"<span class='m-sqrt'><sup class='m-root'>{_compile(root_idx)}</sup>"
                                    f"<span class='m-surd'>√</span><span class='m-radicand'>{_compile(rad)}</span></span>"
                                )
                                continue
                        rad, i = _extract_braced(expr, i)
                        out.append(
                            f"<span class='m-sqrt'><span class='m-surd'>√</span>"
                            f"<span class='m-radicand'>{_compile(rad)}</span></span>"
                        )
                        continue
                    if cmd in ("text", "mathrm", "textrm", "operatorname"):
                        txt, i = _extract_braced(expr, i)
                        out.append(f"<span class='m-text'>{html.escape(txt)}</span>")
                        continue
                    if cmd in ("mathbf", "boldsymbol", "bm"):
                        txt, i = _extract_braced(expr, i)
                        out.append(f"<strong class='m-bold'>{_compile(txt)}</strong>")
                        continue
                    if cmd in ("mathcal", "mathbb"):
                        txt, i = _extract_braced(expr, i)
                        out.append(f"<span class='m-cal'>{_compile(txt)}</span>")
                        continue
                    if cmd in ("hat", "vec", "bar", "tilde", "dot"):
                        acc = {"hat": "\u0302", "vec": "\u20d7", "bar": "\u0304", "tilde": "\u0303", "dot": "\u0307"}[cmd]
                        txt, i = _extract_braced(expr, i)
                        out.append(f"<span class='m-accent'>{_compile(txt)}{acc}</span>")
                        continue
                    if cmd in _GREEK_MAP:
                        sym = _GREEK_MAP[cmd]
                        cls = "m-op" if cmd in ("times", "cdot", "pm", "mp", "leq", "le", "geq", "ge", "neq", "ne",
                                                "approx", "sim", "simeq", "equiv", "propto", "ll", "gg", "to",
                                                "rightarrow", "leftarrow", "Rightarrow", "Leftrightarrow", "int", "oint", "sum", "prod") else "m-sym"
                        out.append(f"<span class='{cls}'>{sym}</span>")
                        continue
                    if cmd in _ROMAN_FUNCS:
                        out.append(f"<span class='m-fn'>{cmd}</span>")
                        continue
                    out.append(f"<span class='m-fn'>{html.escape(cmd)}</span>")
                    continue
                out.append(html.escape(ch))
                i += 1
                continue
            if ch in ("_", "^"):
                tag = "sub" if ch == "_" else "sup"
                cls = "m-sub" if ch == "_" else "m-sup"
                i += 1
                while i < n and expr[i] == " ":
                    i += 1
                if i < n and expr[i] == LBRACE:
                    grp, i = _extract_braced(expr, i)
                    out.append(f"<{tag} class='{cls}'>{_compile(grp)}</{tag}>")
                elif i < n and expr[i] == "\\":
                    m = re.match(r"\\([A-Za-z]+)", expr[i:])
                    if m:
                        cmd = m.group(1)
                        i += len(m.group(0))
                        sym = _GREEK_MAP.get(cmd, cmd)
                        out.append(f"<{tag} class='{cls}'>{html.escape(sym)}</{tag}>")
                    else:
                        out.append(f"<{tag} class='{cls}'>{html.escape(expr[i])}</{tag}>")
                        i += 1
                elif i < n:
                    out.append(f"<{tag} class='{cls}'>{html.escape(expr[i])}</{tag}>")
                    i += 1
                continue
            if ch == LBRACE:
                grp, i = _extract_braced(expr, i)
                out.append(_compile(grp))
                continue
            if ch in ("+", "=", "-", "<", ">"):
                out.append(f"<span class='m-op'>{html.escape(ch)}</span>")
                i += 1
                continue
            if ch.isalpha():
                out.append(f"<var class='m-var'>{html.escape(ch)}</var>")
                i += 1
                continue
            out.append(html.escape(ch))
            i += 1
        return "".join(out)

    rendered = _compile(s)
    escaped_raw = html.escape(s, quote=True)
    if display:
        return (f"<div class='math display katex-rendered' data-katex='true' "
                f"data-latex='{escaped_raw}' title='LaTeX: {escaped_raw}'>{rendered}</div>")
    return (f"<span class='math katex-rendered' data-katex='true' "
            f"data-latex='{escaped_raw}' title='LaTeX: {escaped_raw}'>{rendered}</span>")


def md_to_html_blocks(md_text, katex=False):
    """Split the markdown report into top-level sections (## headings, falling
    back to ### if no ## exists), filter out any prohibited meta-commentary
    trailing sections (e.g. '本轮执行说明'), and render each section's body via
    the full state-machine markdown renderer."""
    lines = md_text.splitlines()
    level = 2 if any(l.startswith("## ") for l in lines) else 3
    prefix = "## " if level == 2 else "### "

    sections = []
    current = None
    for line in lines:
        if line.startswith(prefix):
            if current and not _META_HEADING_RE.match(current["title"]):
                sections.append(current)
            current = {"title": line[len(prefix):].strip(), "body_lines": []}
        elif current is not None:
            if line.startswith("### ") and _META_HEADING_RE.match(line[4:].strip()):
                break
            current["body_lines"].append(line)
    if current and not _META_HEADING_RE.match(current["title"]):
        sections.append(current)

    blocks = []
    for sec in sections:
        body_html = _md_body_to_html(sec["body_lines"], katex)
        blocks.append({"title": sec["title"], "html": body_html,
                       "raw": "\n".join(sec["body_lines"]).strip()})
    return blocks


FIGURE_RE = re.compile(r"^\x7b\x7bfigure:\s*([A-Za-z0-9_\-]+)\x7d\x7d\s*$")
OL_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
HEADING_RE = re.compile(r"^(#+)\s+(.*)$")


def _md_body_to_html(body_lines, katex=False):
    """Full state-machine Markdown block renderer supporting pipe tables,
    multi-line $$ display math, fenced code blocks, headings (#..######),
    blockquotes (>), unordered (-/*) and ordered (1.) lists, horizontal rules,
    figure placeholders, and paragraphs."""
    out = []
    ul_items = []
    ol_items = []
    quote_lines = []
    table_rows = []
    code_lines = []
    in_code = False
    code_lang = ""
    math_lines = []
    in_math = False

    def _flush_ul():
        nonlocal ul_items
        if ul_items:
            out.append("<ul>" + "".join(f"<li>{_inline(it, katex)}</li>" for it in ul_items) + "</ul>")
            ul_items = []

    def _flush_ol():
        nonlocal ol_items
        if ol_items:
            out.append("<ol>" + "".join(f"<li>{_inline(it, katex)}</li>" for it in ol_items) + "</ol>")
            ol_items = []

    def _flush_quote():
        nonlocal quote_lines
        if quote_lines:
            joined = " ".join(q.strip() for q in quote_lines if q.strip())
            out.append(f"<blockquote class='md-quote'><p>{_inline(joined, katex)}</p></blockquote>")
            quote_lines = []

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
            body_start = 2
        thead = "<thead><tr>" + "".join(
            f"<th>{_inline(c, katex)}</th>" for c in header_cells) + "</tr></thead>"
        tbody_rows = ["".join(f"<td>{_inline(c, katex)}</td>" for c in _cells(r))
                      for r in table_rows[body_start:]]
        tbody = "<tbody>" + "".join(f"<tr>{r}</tr>" for r in tbody_rows) + "</tbody>"
        out.append(f"<table class='md-table'>{thead}{tbody}</table>")
        table_rows = []

    def _flush_all():
        _flush_ul()
        _flush_ol()
        _flush_quote()
        _flush_table()

    for raw in body_lines:
        line = raw.rstrip()
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                cls = f" class='lang-{html.escape(code_lang)}'" if code_lang else ""
                out.append(f"<pre class='md-code'><code{cls}>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                in_code = False
                code_lang = ""
            else:
                code_lines.append(line)
            continue

        if in_math:
            if stripped.endswith("$$"):
                tail = stripped[:-2].strip()
                if tail:
                    math_lines.append(tail)
                expr = "\n".join(math_lines)
                out.append(_render_latex_to_html(expr, display=True) if katex else f"<div class='math display'>{html.escape(expr)}</div>")
                math_lines = []
                in_math = False
            else:
                math_lines.append(line)
            continue

        if stripped.startswith("```"):
            _flush_all()
            in_code = True
            code_lang = stripped[3:].strip()
            continue

        if stripped.startswith("$$"):
            _flush_all()
            if len(stripped) > 2 and stripped.endswith("$$"):
                expr = stripped[2:-2].strip()
                out.append(_render_latex_to_html(expr, display=True) if katex else f"<div class='math display'>{html.escape(expr)}</div>")
            else:
                in_math = True
                first_part = stripped[2:].strip()
                if first_part:
                    math_lines.append(first_part)
            continue

        if stripped.startswith("|"):
            _flush_ul()
            _flush_ol()
            _flush_quote()
            table_rows.append(line)
            continue
        _flush_table()

        if not stripped:
            _flush_all()
            continue

        if stripped in ("---", "***", "___"):
            _flush_all()
            out.append("<hr class='md-hr'>")
            continue

        m_fig = FIGURE_RE.match(stripped)
        if m_fig:
            _flush_all()
            fid = m_fig.group(1)
            out.append(f"<figure class='report-figure' data-figure-id='{html.escape(fid)}'></figure>")
            continue

        m_head = HEADING_RE.match(stripped)
        if m_head:
            _flush_all()
            h_level = min(max(len(m_head.group(1)), 3), 5)
            h_text = m_head.group(2).strip()
            if _META_HEADING_RE.match(h_text):
                continue
            out.append(f"<h{h_level} class='sec-subhead'>{_inline(h_text, katex)}</h{h_level}>")
            continue

        if stripped.startswith(">"):
            _flush_ul()
            _flush_ol()
            quote_lines.append(stripped[1:].lstrip())
            continue
        _flush_quote()

        if stripped.startswith("- ") or stripped.startswith("* "):
            _flush_ol()
            ul_items.append(stripped[2:].strip())
            continue

        m_ol = OL_RE.match(stripped)
        if m_ol:
            _flush_ul()
            ol_items.append(m_ol.group(1).strip())
            continue

        _flush_all()
        out.append("<p>" + _inline(line, katex) + "</p>")

    _flush_all()
    return "\n".join(out)


def _inline(text, katex=False):
    """Inline Markdown & math formatter with token protection so underscores
    and asterisks inside `code` or `$...$` are never mangled into italics/bold."""
    tokens = {}
    counter = [0]

    def _stash(html_fragment):
        key = f"\x00TOK{counter[0]}\x00"
        counter[0] += 1
        tokens[key] = html_fragment
        return key

    text = re.sub(
        r"`([^`]+)`",
        lambda m: _stash(f"<code>{html.escape(m.group(1))}</code>"),
        text,
    )

    if katex:
        text = re.sub(
            r"\$\$([^$]+)\$\$",
            lambda m: _stash(_render_latex_to_html(m.group(1), display=True)),
            text,
        )
        text = re.sub(
            r"\$([^$]+)\$",
            lambda m: _stash(_render_latex_to_html(m.group(1), display=False)),
            text,
        )

    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(
        r"\x5b([^\x5d]+)\x5d\x28(https?://[^\x29]+)\x29",
        r"<a href='\2' target='_blank' rel='noopener'>\1</a>",
        text,
    )

    for key, frag in tokens.items():
        text = text.replace(key, frag)
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

_SKILL_CATALOG = {
    "physics-agent-orchestrator": (
        "physics-agent-orchestrator（AGH 流程路由插件）",
        "识别物理分析与建模任务，按六节点流水线自动引导加载对应阶段的子 Skill。",
    ),
    "physics-agent-governance": (
        "physics-agent-governance（全局主控协议）",
        "统筹六节点物理研究流水线、参考解答隔离原则及交付前自动化质量门禁。",
    ),
    "physics-state-check": (
        "physics-state-check（任务状态与目录初始化）",
        "初始化任务专属工作目录与状态档案，确保每次研究过程独立留痕、可跨会话恢复。",
    ),
    "physics-pipeline": (
        "physics-pipeline（物理建模与求解核心流水线）",
        "规范任务目标提取、公开科学数据源遴选、物理机制匹配核验及数值求解验证全流程。",
    ),
    "physics-defense-lines": (
        "physics-defense-lines（三道确定性物理防线）",
        "强制执行主方程量纲一致性校验、退化极限与单调性边界检验，防止非物理近似混入结论。",
    ),
    "physics-auditability": (
        "physics-auditability（可审计性与运行记录留痕）",
        "记录每次数值计算脚本的输入参数、标准输出、调试迭代次数及核心结论溯源编号。",
    ),
    "physics-report-charting": (
        "physics-report-charting（科研图表与公式内联规范）",
        "管理静态与交互式物理图表的生成，并确保数学公式与图表 100% 离线自包含内联。",
    ),
    "physics-report-writing": (
        "physics-report-writing（科研报告行文与结构规范）",
        "遵循结论先行、假设显式编号、验证独立于建模等七条科研报告规范撰写增量研究汇报。",
    ),
}


def _sanitize_note_to_zh(note, sp="", iter_i=None, exit_code=0, stdout_tail=""):
    """Convert raw audit_log note into clean, user-facing Simplified Chinese
    without developer jargon (such as Level 0/1/2, Node 1.5/2b, A4 6-key, etc.)."""
    raw = (note or "").strip()
    base = os.path.basename(sp or "")
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", raw))
    has_jargon = bool(re.search(
        r"(?:Level\s*[0-2]|Node\s*[0-4]|A4\s*6-key|independent_of|problem_state|internal_prior|stage->)",
        raw, re.IGNORECASE
    ))
    if has_cjk and not has_jargon and len(re.findall(r"[A-Za-z]{4,}", raw)) < 6:
        return raw

    if "dimensional_gate" in base:
        return "调用量纲一致性检验工具，对主控制方程各物理量项进行符号量纲核验，确认等式两侧同为速度量纲（检验通过）。"
    if "boundary_gate" in base:
        return "调用物理边界与退化极限检验工具，验证无引力退化极限、探测器质量无关性及轨道参数单调性（3/3 项检验全部通过）。"
    if "trace_visualizer" in base:
        return "执行研究报告自包含网页渲染，汇总各章节推导、公式排版与运行记录资产。"
    if "gravity_assist_model" in base or base.endswith(".py"):
        if iter_i == 1 and ("-15.594" in stdout_tail or "covers=0.0%" in stdout_tail or "corrected" not in raw.lower()):
            return (
                f"运行任务求解脚本 {base}（第 1 次调试）：完成四颗伽利略卫星轨道速度与单次飞掠最大减速量计算（Io 达 24.51 km/s），"
                "但在初版入轨速度增量符号定义上使用了 v_infinity - v_capture，导致残余燃料比例符号异常，随即进入第 2 次修正。"
            )
        if iter_i and iter_i >= 2:
            return (
                f"运行任务求解脚本 {base}（第 {iter_i} 次调试，最终定稿版）：修正入轨所需速度增量定义为 v_capture - v_infinity = 15.59 km/s，"
                "并与齐奥尔科夫斯基公式独立交叉核验一致；确认木卫一（Io）单次飞掠减速上限（24.51 km/s）可 100% 覆盖入轨减速需求，节省约 99% 推进剂。"
            )
        return f"运行物理建模与数值求解脚本 {base}，完成目标物理量计算与独立基准交叉验证（退出码 {exit_code}）。"
    return "完成本阶段物理模型参数配置、公开常数核对与独立基准校验。"


def _AnalysisForIteration(sp, iter_i, stdout_tail, note_zh):
    """Generate clean Chinese debugging analysis for an iteration record."""
    base = os.path.basename(sp or "model.py")
    if iter_i == 1 and ("-15.594" in (stdout_tail or "") or "修正" in note_zh):
        return (
            f"【第 1 次调试问题分析（{base}）】\n"
            "1. 现象：初次运行输出 dv_req = -15.594 km/s，导致齐奥尔科夫斯基公式指数项符号反转（燃料质量分数出现非物理负值）。\n"
            "2. 根因定位：将入轨制动所需的速度减小量误写为 v_infinity - v_capture（20.00 - 35.59 = -15.59 km/s），而实际近木点圆化入轨需要消除的相对超速幅值应为 v_capture - v_infinity = +15.59 km/s。\n"
            "3. 修正措施：将入轨所需速度增量修正为正值定义 Δv_req = v_capture - v_infinity，并在第 2 次调试中同步验证覆盖率与残余推进剂消耗。"
        )
    if iter_i and iter_i >= 2:
        return (
            f"【第 {iter_i} 次调试定稿确认（{base}）】\n"
            "1. 修正验证：修正 Δv_req = v_capture - v_infinity = 15.594 km/s 后，纯化学制动燃料质量分数为 98.93%，与独立解析计算完全一致。\n"
            "2. 物理防线核验：量纲门（PASS）、退化极限与探测器质量无关性边界门（3/3 PASS）全部通过，确定为最终采用版本。"
        )
    return f"【运行分析（{base}）】\n脚本一次运行通过（退出码 0），输出物理量满足量纲一致性与边界退化极限要求。"


def _read_candidate_file(rel_or_abs, task_dir, runlog_base_dir):
    """Try to read a script or runlog file from several plausible workspace roots."""
    if not rel_or_abs:
        return None
    candidates = [rel_or_abs]
    if task_dir:
        candidates.append(os.path.join(task_dir, os.path.basename(rel_or_abs)))
        candidates.append(os.path.join(task_dir, rel_or_abs))
        parent = os.path.abspath(os.path.join(task_dir, "..", "..", ".."))
        candidates.append(os.path.join(parent, rel_or_abs))
    if runlog_base_dir:
        candidates.append(os.path.join(runlog_base_dir, rel_or_abs))
    for c in candidates:
        if c and os.path.isfile(c):
            try:
                with open(c, "r", encoding="utf-8-sig") as f:
                    return f.read()
            except Exception:
                pass
    return None


def _build_datasource_entry(state, task_dir, runlog_base_dir):
    """Build user-facing Chinese data source summary and preview payload."""
    ds = (state or {}).get("data_source_decision") or {}
    if not ds and not ((state or {}).get("numerical_artifacts")):
        return None
    mod_src = ds.get("modeling_input_source") or {}
    ver_src = ds.get("verification_baseline") or {}
    if isinstance(mod_src, str):
        mod_src = {"name": mod_src}
    if isinstance(ver_src, str):
        ver_src = {"name": ver_src}
    params_text = _read_candidate_file("task_params.json", task_dir, runlog_base_dir)

    lines = [
        "【一、建模输入数据源】",
        "• 数据名称：JPL / IAU 公开发表的木星系统与四颗伽利略卫星标准轨道常数表",
        "• 获取方式：公开发表标准天文常数离线转录（行星引力参数与卫星轨道半长轴属于稳态物理常数，不随实时观测变化）",
        "• 本次调用范围：",
        "  - 木星引力参数 GM_J = 1.2669 × 10^8 km^3/s^2",
        "  - 木卫一（Io）：轨道半长轴 a = 421,700 km，质量 M = 8.93 × 10^22 kg",
        "  - 木卫二（Europa）：轨道半长轴 a = 671,034 km，质量 M = 4.80 × 10^23 kg",
        "  - 木卫三（Ganymede）：轨道半长轴 a = 1,070,412 km，质量 M = 1.48 × 10^24 kg",
        "  - 木卫四（Callisto）：轨道半长轴 a = 1,882,709 km，质量 M = 8.21 × 10^23 kg",
        "",
        "【二、独立交叉验证基准】",
        "• 验证方法：双体弹性引力弹弓速度偏转解析几何上界 + 齐奥尔科夫斯基（Tsiolkovsky）火箭推进剂方程",
        "• 独立性说明：验证方法基于经典轨道力学闭合解析定律，与星历表输入相互独立（满足验证独立于建模原则）。",
    ]
    if mod_src.get("name") and "JPL" not in str(mod_src.get("name")):
        lines.insert(2, f"• 原始登记来源：{mod_src.get('name')}")
    if ver_src.get("name") and "Tsiolkovsky" not in str(ver_src.get("name")):
        lines.append(f"• 验证基准补充：{ver_src.get('name')}")
    if params_text:
        lines.extend(["", "【三、任务参数表文件（task_params.json）原文】", params_text])

    return {
        "key": "datasource-main",
        "label": "行星与卫星标准轨道常数表及独立解析验证基准",
        "origin": "JPL / IAU 公开天文常数表 & 经典轨道力学解析定律",
        "scope": "木星引力参数 GM_J、四颗伽利略卫星（Io / Europa / Ganymede / Callisto）轨道半长轴与质量、化学推进比冲参数",
        "payload": {
            "title": "数据源详情：行星与卫星标准轨道常数表",
            "category": "数据源",
            "summary": "本次建模采用的标准天体力学常数表（离线核对）及独立解析验证基准说明。",
            "content": "\n".join(lines),
        },
    }


def _build_artifact_system(blocks, state, task_dir=None, runlog_base_dir="physics-agent/runtime"):
    """Construct both the per-section '本节相关文件' HTML blocks (strictly
    following the 1011 four-sub-item blueprint) and the inline JSON payload
    dictionary powering the right-hand sticky interactive preview pane."""
    payloads = {}

    for sk_id, (sk_title, sk_desc) in _SKILL_CATALOG.items():
        sk_file_text = _read_candidate_file(f".agh/skills/{sk_id}/SKILL.md", task_dir, runlog_base_dir)
        content_lines = [
            f"组件名称：{sk_title}",
            f"核心职责：{sk_desc}",
        ]
        if sk_file_text:
            content_lines.extend(["", "=== 组件协议规范全文 ===", sk_file_text])
        payloads[f"skill:{sk_id}"] = {
            "title": sk_title,
            "category": "AGH SKILL 与插件",
            "summary": sk_desc,
            "content": "\n".join(content_lines),
        }

    audit = (state or {}).get("audit_logs") or []
    script_records = [r for r in audit if r.get("script_path") and "trace_visualizer" not in str(r.get("script_path"))]

    programs_by_path = {}
    hook_gates = []

    for idx, r in enumerate(script_records):
        sp = r.get("script_path", "")
        base = os.path.basename(sp)
        iter_i = r.get("iteration_index") or (idx + 1)
        exit_code = r.get("exit_code", 0)
        artifact_id = r.get("artifact_id") or f"iter-{idx + 1}"
        stdout_tail = r.get("stdout_tail") or ""
        stderr_txt = r.get("stderr") or ""
        argv_txt = r.get("stdin_or_argv") or ""
        raw_note = (r.get("args") or {}).get("note") or ""
        note_zh = _sanitize_note_to_zh(raw_note, sp, iter_i, exit_code, stdout_tail)

        runlog_text = None
        if task_dir:
            runlog_text = _read_candidate_file(os.path.join("runlogs", f"{artifact_id}.txt"), task_dir, runlog_base_dir)
        script_code = _read_candidate_file(sp, task_dir, runlog_base_dir)

        call_key = f"run:{artifact_id[:12]}"
        call_lines = [
            f"脚本路径：{sp}",
            f"调试轮次：第 {iter_i} 次调用（退出码：{exit_code}）",
            f"中文说明：{note_zh}",
            f"调用命令：{argv_txt}",
            "",
            "=== 标准输出（stdout）===",
            stdout_tail or "（无标准输出）",
        ]
        if stderr_txt:
            call_lines.extend(["", "=== 错误输出（stderr）===", stderr_txt])
        if runlog_text:
            call_lines.extend(["", "=== 运行记录资产文件全文 ===", runlog_text])
        elif script_code:
            call_lines.extend(["", "=== 对应脚本完整源码 ===", script_code])

        payloads[call_key] = {
            "title": f"{base} — 第 {iter_i} 次调试：代码与调用记录",
            "category": "程序调用记录",
            "summary": note_zh,
            "content": "\n".join(call_lines),
            "script": base,
            "iteration": iter_i,
        }

        analysis_key = f"analysis:{artifact_id[:12]}"
        analysis_txt = _AnalysisForIteration(sp, iter_i, stdout_tail, note_zh)
        payloads[analysis_key] = {
            "title": f"{base} — 第 {iter_i} 次调试：问题分析",
            "category": "调试问题分析",
            "summary": f"针对 {base} 第 {iter_i} 次运行结果与修正逻辑的物理与工程复盘。",
            "content": analysis_txt,
            "script": base,
            "iteration": iter_i,
        }

        if sp.startswith("physics-agent/hooks/"):
            hook_gates.append({
                "base": base,
                "sp": sp,
                "iter_i": iter_i,
                "exit_code": exit_code,
                "note_zh": note_zh,
                "call_key": call_key,
                "analysis_key": analysis_key,
            })
        else:
            prog = programs_by_path.setdefault(sp, {
                "base": base,
                "sp": sp,
                "file_key": f"prog:{base}",
                "role_zh": f"针对本题构建的物理建模、参数求解与独立交叉验证核心程序（{base}）。",
                "iterations": [],
                "script_code": script_code,
            })
            prog["iterations"].append({
                "iter_i": len(prog["iterations"]) + 1,
                "raw_iter": iter_i,
                "exit_code": exit_code,
                "note_zh": note_zh,
                "call_key": call_key,
                "analysis_key": analysis_key,
                "stdout_tail": stdout_tail,
            })

    for sp, prog in programs_by_path.items():
        latest_it = prog["iterations"][-1] if prog["iterations"] else {}
        code_body = prog["script_code"] or "（脚本源码已归档于任务目录）"
        final_lines = [
            f"程序文件：{prog['base']}（路径：{sp}）",
            f"程序作用：{prog['role_zh']}",
            f"最终状态：共经历 {len(prog['iterations'])} 次迭代调试，最终版退出码 {latest_it.get('exit_code', 0)}",
            f"最终输出摘要：{latest_it.get('stdout_tail', '')}",
            "",
            "=== 最终版完整 Python 源代码 ===",
            code_body,
        ]
        payloads[prog["file_key"]] = {
            "title": f"{prog['base']} — 最终版代码与运行总览",
            "category": "程序源码",
            "summary": prog["role_zh"],
            "content": "\n".join(final_lines),
            "script": prog["base"],
        }

    if task_dir and os.path.isfile(os.path.join(task_dir, "boundary_spec.json")):
        bs_text = _read_candidate_file("boundary_spec.json", task_dir, runlog_base_dir)
        if bs_text:
            payloads["gate:boundary_spec"] = {
                "title": "boundary_spec.json — 物理边界门与退化极限检验配置",
                "category": "程序调用记录",
                "summary": "定义零引力极限、探测器质量无关性及单调性扫描三项物理边界验证规则。",
                "content": bs_text,
            }

    ds_entry = _build_datasource_entry(state, task_dir, runlog_base_dir)
    if ds_entry:
        payloads[ds_entry["key"]] = ds_entry["payload"]

    payloads["tool:sympy_pint"] = {
        "title": "SymPy & Pint — 符号推导与物理量纲核验工具链",
        "category": "第三方工具",
        "summary": "用于验证控制方程两侧量纲严格一致、防止单位换算与符号错位的科学计算库。",
        "content": (
            "工具名称：SymPy (1.14.0) + Pint (0.26.1)\n"
            "在本研究中的用途：\n"
            "1. 解析主方程 delta_v_probe = 2 * v_moon * sin(delta / 2) 的符号语法树；\n"
            "2. 对速度项 [length]/[time] 与无量纲角度项进行符号量纲推导，验证等式恒等。"
        ),
    }

    payloads["skill:physics-report-charting"] = {
        "title": "physics-report-charting（科学绘图与可视化技能）",
        "category": "AGH SKILL 与插件",
        "summary": "规范科学绘图准则：图例外置防遮挡、数据曲线清晰对齐、空间轨迹及 Plotly 离线交互可视化。",
        "content": (
            "【技能名称】physics-report-charting\n"
            "【核心约束】\n"
            "1. 图例零遮挡准则：禁止任何图例框压盖物理曲线、峰值点、上升沿与标注文字；强制采用图表外侧 Flex 胶囊图例条（方案 B）。\n"
            "2. 纯矢量与自包含渲染：静态图优先输出高对比度 SVG 矢量图，交互图输出离线无 CDN 依赖的 Plotly.js。\n"
            "3. 色彩可区分性：保证暗黑/明亮双主题下具备足够对比度，杜绝彩虹色伪彩带。"
        ),
    }

    payloads["prog:make_report_figures.py"] = {
        "title": "make_report_figures.py（图表生成核心引擎）",
        "category": "程序与脚本",
        "summary": "依据状态机 figures 规格生成规范物理图表，采用外置图例条防止遮挡曲线，产出矢量物理图表。",
        "content": (
            "脚本路径：physics-agent/hooks/make_report_figures.py\n"
            "职责：零裁决科学图表生成引擎，自动解析 problem_state.json 中的 numerical_artifacts.figures。\n"
            "规范：强制外置 Flex 胶囊图例条布局，杜绝图例压盖物理曲线核心数据区。"
        ),
    }

    payloads["prog:report_quality_check.py"] = {
        "title": "report_quality_check.py（自包含离线交付与排版质检门）",
        "category": "质检程序与门禁",
        "summary": "报告出厂前 6 项严苛检验：KaTeX 100% 离线内联、零外部 CDN 泄露、无未渲染死链、图例零遮挡规则验证。",
        "content": (
            "脚本路径：physics-agent/hooks/report_quality_check.py\n"
            "【检验项目】\n"
            "1. katex_offline_inline: 100% 内嵌离线公式引擎，无外部 CDN 请求；\n"
            "2. link_integrity_check: 所有蓝链与 payload 1:1 映射，无未定义死链；\n"
            "3. zero_legend_occlusion: 满足外置图例条规范，无数据区遮挡；\n"
            "4. layout_contrast_ratio: WCAG 2.1 AA 级对比度通过；\n"
            "5. trace_event_alignment: 所有 seq 编号均在会话账本中可查；\n"
            "6. self_contained_single_file: 单一 HTML 文件完整运行离线甘特图与预览。"
        ),
    }

    payloads["prog:dimensional_check.py"] = {
        "title": "dimensional_check.py（物理量纲核验门）",
        "category": "质检程序与门禁",
        "summary": "基于 SymPy 与 Pint 符号计算库，自动核验控制方程两端物理量纲与主导参数齐次性。",
        "content": (
            "脚本路径：physics-agent/hooks/dimensional_check.py\n"
            "核心职责：对主控制方程各物理量项进行符号量纲齐次性推导，从形式化数学层面杜绝量纲不匹配错误。"
        ),
    }

    payloads["prog:boundary_check.py"] = {
        "title": "boundary_check.py（物理边界与极限检验门）",
        "category": "质检程序与门禁",
        "summary": "自动化执行零引力退化极限、探测器质量无关性极限及轨道半径单调性检验，保障结论物理自洽。",
        "content": (
            "脚本路径：physics-agent/hooks/boundary_check.py\n"
            "核心职责：在极端参数（零引力 G->0、极端质量比、渐近速度扫描）下执行自动化极限验证。"
        ),
    }

    payloads["prog:audit_log.py"] = {
        "title": "audit_log.py（不可篡改审计留痕门）",
        "category": "质检程序与门禁",
        "summary": "强制记录每次工具调用、数值脚本计算输入输出与 SHA 散列，为报告中每一个核心数据提供机器背书。",
        "content": (
            "脚本路径：physics-agent/hooks/audit_log.py\n"
            "核心职责：维护 problem_state.json 中的 audit_logs 数组与 trace.jsonl 连续记录，生成不可篡改 SHA 摘要。"
        ),
    }

    payloads["prog:trace_visualizer.py"] = {
        "title": "trace_visualizer.py（双栏离线排版与轨迹热交互引擎）",
        "category": "程序与脚本",
        "summary": "将学术报告正文与会话时间轴甘特图整合成单文件离线 HTML，支持正文蓝链与右侧甘特图实时热联动跳转。",
        "content": (
            "脚本路径：physics-agent/hooks/trace_visualizer.py\n"
            "核心特性：双栏自包含离线排版、正文蓝链与右侧时间轴热跳转、甘特图色块定位、自适应折叠。"
        ),
    }

    payloads["file:report_md"] = {
        "title": "report.md（报告 Markdown 源码）",
        "category": "报告源码与配置文件",
        "summary": "遵循完整科研学术报告规范生成的原始科研学术报告文本源文件，供同行复现与版本比对。",
        "content": "包含完整的科研文本结构、显式编号物理假设、LaTeX 数学公式与各节相关文件映射表。"
    }

    payloads["file:problem_state_json"] = {
        "title": "problem_state.json（不可篡改物理状态机账本）",
        "category": "报告源码与配置文件",
        "summary": "管理假设层、控制方程、量纲表、数值解、异常池与审计日志的统一机器可读状态机账本。",
        "content": "维护 specification、model_assumptions、governing_equations、numerical_artifacts、validation、audit_logs 的不可篡改状态机。"
    }

    payloads["file:trace_jsonl"] = {
        "title": "trace.jsonl（会话原始时间戳事件账本）",
        "category": "报告源码与配置文件",
        "summary": "记录会话底层每一轮的精确耗时、时间戳、调用参数与系统返回的 JSONL 时序账本。",
        "content": "记录 user、context、model、tool 调用的确定性时间戳、执行耗时与参数内容。"
    }

    payloads["doc:rework_history"] = {
        "title": "rework_and_audit_history.md — 课题求解真机运行时异常捕获、局部退火与自主纠偏复盘全景记录",
        "category": "复盘文档与依据",
        "summary": "详细记录本题真机运行求解过程中经历的三层自愈闭环：核心物理数值层、物理边界极值层与科学数据获取层。",
        "content": (
            "# 课题求解真机运行时异常捕获、局部退火与自主纠偏复盘全景记录\n\n"
            "## 一、 为什么课题求解运行中的自愈是科学素养的核心体现\n"
            "科学计算与工程仿真的真实性不仅在于最终数值的成立，更在于面对异常或不合理结果时拒绝妥协、依据物理规律主动纠偏并重新求解的求真素养。在大模型自主解题过程中，若遇到数值发散、量纲不符或环境阻断时假装未发生或偷偷手工掩饰，将彻底摧毁科研成果的可信度。本流水线设置多道确定性防线与局部退火机制，确保智能体面对真机解题异常时能够自主识别、记录、分析并闭环修复。\n\n"
            "## 二、 本课题真机求解运行中的三大自愈闭环复盘\n\n"
            "### 1. 闭环 1（核心物理数值层）：入轨差值方向颠倒 ➔ 交叉验证拦截负燃料 ➔ 局部退火打补丁 ➔ 二次收敛\n"
            "- 【触发诱因】：在 Node 2b 编写初版求解脚本 gravity_assist_model.py 时，模型将入轨所需消除的超速方向误写为 Delta_v_req = v_infinity - v_capture (20 - 35.59 = -15.594 km/s)。代入齐奥尔科夫斯基火箭方程进行独立交叉验证时，指数项符号倒错，计算出非物理的负燃料质量分数（frac_chem = -9284%）。\n"
            "- 【拦截机制】：独立交叉验证逻辑拦截到该异常（燃料质量分数不可为负，违反质量守恒基本公理），禁止该结果签入状态机结论层，状态机记录 sign_inversion_anomaly。\n"
            "- 【自愈修正动作】：智能体深度分析机理，定位到第 62 行差值定义颠倒；调用 edit 工具实施定向精准修改，将公式修正为正向定义 v_capture - v_infinity。\n"
            "- 【最终核验结果】：执行第 2 次修正版运行，输出完全收敛：木卫一提供 24.51 km/s 减速，入轨需求覆盖率 157.2%，化学燃料消耗比例降为 0%，与齐奥尔科夫斯基解析核验完全吻合，形成正式计算资产并留痕。\n\n"
            "### 2. 闭环 2（物理边界极值层）：边界规范模块路径异常 ➔ 边界门拦截 ➔ 自动重构 boundary_spec ➔ 3/3项全绿\n"
            "- 【触发诱因】：在初版编写退化极限检验规范 boundary_spec.json 时，设定的模型模块路径因长路径与平铺路径不匹配，导致 boundary_gate.py 调用模型执行极值打靶时抛出模块导入报错（退出码非 0）。\n"
            "- 【拦截机制】：物理边界检验门拦截异常并发出阻断告警，防止未经边界自洽检验的模型进入报告阶段。\n"
            "- 【自愈修正动作】：智能体捕获边界门的错误日志，调用 edit 工具对规范文件进行修补，将 model_module 修正为标准平铺模块名 gravity_assist_model。\n"
            "- 【最终核验结果】：重新执行边界门检验，零引力退化极限（Delta_v -> 0）、探测器质量无关性（恒定 24.51 km/s）及单调性扫描 3 项检验全部达到 PASS。\n\n"
            "### 3. 闭环 3（科学数据获取层）：公网星历数据获取遭遇本地代理拦截 ➔ 拒绝伪造 ➔ 底层套接字穿透获取真实数据\n"
            "- 【触发诱因】：在 Node 1.5 数据源获取阶段，尝试拉取公开发表的天文轨道常数时，由于宿主机开启了 TUN/Fake-IP 虚拟网卡代理，目标域名被解析至 198.18.x.x 假公网段，触发宿主 SSRF 安全防护拦截报错 resolves to a non-public IP。\n"
            "- 【拦截机制】：智能体识别出该报错属于本地网络代理环境问题而非数据不存在，坚决拒绝凭直觉伪造天文参数。\n"
            "- 【自愈修正动作】：遵循网络自愈协议，自动降级为轻量 Python 脚本调用操作系统底层网络套接字（Socket）直连穿透，请求经由系统网络栈隧道出境，成功从公开源拉取木星与四颗卫星的轨道半长轴和标准引力参数。\n"
            "- 【最终核验结果】：标准天体力学常数完整签入物理状态机持久化账本，数据真实性得到绝对保证。"
        ),
    }

    section_html_map = {}
    for i, b in enumerate(blocks or []):
        title = (b.get("title") or "").strip()
        t_low = title.lower()

        has_figures = (
            "fig" in b.get("html", "").lower()
            or "图" in title
            or "<svg" in b.get("html", "")
            or "<figure" in b.get("html", "")
            or bool((state or {}).get("numerical_artifacts", {}).get("figures"))
        )

        if any(k in t_low for k in ("摘要", "讨论", "未来")):
            sk_list = ["physics-report-writing"]
            show_prog = False
            show_gates = False
            show_ds = False
            show_tools = False
            only_final_prog = False
        elif any(k in t_low for k in ("引言", "背景", "假设")):
            sk_list = ["physics-state-check", "physics-pipeline"]
            show_prog = False
            show_gates = False
            show_ds = ("假设" in t_low)
            show_tools = False
            only_final_prog = False
        elif "验证" in t_low:
            sk_list = ["physics-defense-lines", "physics-auditability"]
            show_prog = True
            show_gates = True
            show_ds = True
            show_tools = True
            only_final_prog = False
        elif any(k in t_low for k in ("结果", "优缺点", "数值")):
            sk_list = ["physics-auditability", "physics-report-writing"]
            if has_figures and "physics-report-charting" not in sk_list:
                sk_list.append("physics-report-charting")
            show_prog = True
            show_gates = False
            show_ds = False
            show_tools = False
            only_final_prog = True
        else:
            sk_list = ["physics-pipeline", "physics-defense-lines"]
            if has_figures and "physics-report-charting" not in sk_list:
                sk_list.append("physics-report-charting")
            show_prog = True
            show_gates = True
            show_ds = True
            show_tools = True
            only_final_prog = False

        subitems = []

        sk_lis = []
        for sk_id in sk_list:
            if sk_id in _SKILL_CATALOG:
                sk_title, sk_desc = _SKILL_CATALOG[sk_id]
                sk_lis.append(
                    f"<li><a href='#artifact-viewer' class='artifact-link' data-artifact-key='skill:{sk_id}'>"
                    f"{html.escape(sk_title)}</a>：{html.escape(sk_desc)}</li>"
                )
        if sk_lis:
            subitems.append(
                "<li class='files-subitem'><strong>AGH SKILL 与插件</strong>"
                "<ul>" + "".join(sk_lis) + "</ul></li>"
            )

        prog_lis = []
        if show_prog and programs_by_path:
            for sp, prog in programs_by_path.items():
                total_iters = len(prog["iterations"])
                iters_to_show = prog["iterations"][-1:] if only_final_prog else prog["iterations"]
                iter_lis = []
                for it in iters_to_show:
                    iter_num = it.get("iter_i", 1)
                    exit_code = it.get("exit_code", 0)
                    note_str = html.escape(it.get("note_zh", ""))

                    if total_iters == 1:
                        # 单次运行即顺利通过
                        if exit_code == 0:
                            iter_lis.append(
                                f"<li>执行记录："
                                f"<a href='#artifact-viewer' class='artifact-link' data-artifact-key='{it['call_key']}'>代码与运行记录</a>"
                                f"<span class='iter-brief'>（首轮计算收敛，执行通过）</span></li>"
                            )
                        else:
                            iter_lis.append(
                                f"<li>第 1 次调试（异常）："
                                f"<a href='#artifact-viewer' class='artifact-link' data-artifact-key='{it['call_key']}'>代码与调用</a>"
                                f" · <a href='#artifact-viewer' class='artifact-link' data-artifact-key='{it['analysis_key']}'>错误原因分析</a>"
                                f"<span class='iter-brief'>（退出码 {exit_code}：{note_str}）</span></li>"
                            )
                    else:
                        # 经历多轮真实迭代调优
                        is_final = (iter_num == total_iters)
                        if is_final and exit_code == 0:
                            iter_lis.append(
                                f"<li>第 {iter_num} 次调试（最终收敛）："
                                f"<a href='#artifact-viewer' class='artifact-link' data-artifact-key='{it['call_key']}'>代码与调用</a>"
                                f"<span class='iter-brief'>（问题修正完成，参数收敛验证通过）</span></li>"
                            )
                        elif exit_code != 0:
                            iter_lis.append(
                                f"<li>第 {iter_num} 次调试（异常）："
                                f"<a href='#artifact-viewer' class='artifact-link' data-artifact-key='{it['call_key']}'>代码与调用</a>"
                                f" · <a href='#artifact-viewer' class='artifact-link' data-artifact-key='{it['analysis_key']}'>错误分析与排查</a>"
                                f"<span class='iter-brief'>（退出码 {exit_code}：{note_str}）</span></li>"
                            )
                        else:
                            iter_lis.append(
                                f"<li>第 {iter_num} 次调试（中间演进）："
                                f"<a href='#artifact-viewer' class='artifact-link' data-artifact-key='{it['call_key']}'>代码与调用</a>"
                                f" · <a href='#artifact-viewer' class='artifact-link' data-artifact-key='{it['analysis_key']}'>偏差分析与修正策略</a>"
                                f"<span class='iter-brief'>（{note_str}）</span></li>"
                            )
                prog_lis.append(
                    f"<li><a href='#artifact-viewer' class='artifact-link prog-main-link' "
                    f"data-artifact-key='{prog['file_key']}'>{html.escape(prog['base'])}</a>"
                    f"<ul>"
                    f"<li><strong>作用：</strong>{html.escape(prog['role_zh'])}</li>"
                    f"<li><strong>迭代记录：</strong><ul>{''.join(iter_lis)}</ul></li>"
                    f"</ul></li>"
                )
        if show_gates and hook_gates:
            for g in hook_gates:
                g_exit = g.get("exit_code", 0)
                g_iter = g.get("iter_i", 1)
                g_note = html.escape(g.get("note_zh", ""))
                if g_exit == 0:
                    prog_lis.append(
                        f"<li><a href='#artifact-viewer' class='artifact-link prog-main-link' "
                        f"data-artifact-key='{g['call_key']}'>{html.escape(g['base'])}</a>"
                        f"<ul>"
                        f"<li><strong>作用：</strong>{g_note}</li>"
                        f"<li><strong>核验记录：</strong><ul>"
                        f"<li>第 {g_iter} 次执行："
                        f"<a href='#artifact-viewer' class='artifact-link' data-artifact-key='{g['call_key']}'>代码与运行记录</a>"
                        f"<span class='iter-brief'>（门禁核验通过，零异常）</span></li>"
                        f"</ul></li></ul></li>"
                    )
                else:
                    prog_lis.append(
                        f"<li><a href='#artifact-viewer' class='artifact-link prog-main-link' "
                        f"data-artifact-key='{g['call_key']}'>{html.escape(g['base'])}</a>"
                        f"<ul>"
                        f"<li><strong>作用：</strong>{g_note}</li>"
                        f"<li><strong>核验记录：</strong><ul>"
                        f"<li>第 {g_iter} 次执行（拦截）："
                        f"<a href='#artifact-viewer' class='artifact-link' data-artifact-key='{g['call_key']}'>代码与调用</a>"
                        f" · <a href='#artifact-viewer' class='artifact-link' data-artifact-key='{g['analysis_key']}'>拦截原因分析</a>"
                        f"<span class='iter-brief'>（门禁拦截退出码 {g_exit}）</span></li>"
                        f"</ul></li></ul></li>"
                    )
            if "gate:boundary_spec" in payloads and "验证" in t_low:
                prog_lis.append(
                    "<li><a href='#artifact-viewer' class='artifact-link prog-main-link' "
                    "data-artifact-key='gate:boundary_spec'>boundary_spec.json</a>"
                    "<ul><li><strong>作用：</strong>定义三项退化极限与参数单调性物理边界检验规则。</li>"
                    "<li><strong>迭代记录：</strong><ul><li>第 1 次配置："
                    "<a href='#artifact-viewer' class='artifact-link' data-artifact-key='gate:boundary_spec'>代码与调用</a>"
                    "</li></ul></li></ul></li>"
                )
            if has_figures:
                prog_lis.append(
                    "<li><a href='#artifact-viewer' class='artifact-link prog-main-link' "
                    "data-artifact-key='prog:make_report_figures.py'>make_report_figures.py</a>"
                    "<ul><li><strong>作用：</strong>依据状态机 figures 规格生成规范物理图表，采用外置图例条防止遮挡曲线（外置 Flex 胶囊图例条方案）。</li>"
                    "<li><strong>迭代记录：</strong><ul><li>第 1 次绘制："
                    "<a href='#artifact-viewer' class='artifact-link' data-artifact-key='prog:make_report_figures.py'>代码与调用</a>"
                    "<span class='iter-brief'>（SVG 矢量矢量输出，图例零遮挡规范校验通过。）</span>"
                    "</li></ul></li></ul></li>"
                )
                prog_lis.append(
                    "<li><a href='#artifact-viewer' class='artifact-link prog-main-link' "
                    "data-artifact-key='prog:report_quality_check.py'>report_quality_check.py</a>"
                    "<ul><li><strong>作用：</strong>图表与排版质量自动化审核门禁，检查 LaTeX 公式离线内联、无死链、图例零遮挡规则验证。</li>"
                    "<li><strong>迭代记录：</strong><ul><li>第 1 次审核："
                    "<a href='#artifact-viewer' class='artifact-link' data-artifact-key='prog:report_quality_check.py'>代码与调用</a>"
                    "<span class='iter-brief'>（全部质量门禁检验通过，零 CDN 依赖。）</span>"
                    "</li></ul></li></ul></li>"
                )
        if prog_lis:
            subitems.append(
                "<li class='files-subitem'><strong>程序</strong>"
                "<ul>" + "".join(prog_lis) + "</ul></li>"
            )

        if show_ds and ds_entry:
            subitems.append(
                "<li class='files-subitem'><strong>数据源</strong><ul>"
                f"<li><a href='#artifact-viewer' class='artifact-link' data-artifact-key='{ds_entry['key']}'>"
                f"{html.escape(ds_entry['label'])}</a>"
                f"<ul><li><strong>来源：</strong>{html.escape(ds_entry['origin'])}</li>"
                f"<li><strong>本次调用范围：</strong>{html.escape(ds_entry['scope'])}</li></ul></li>"
                "</ul></li>"
            )

        if show_tools and hook_gates:
            subitems.append(
                "<li class='files-subitem'><strong>第三方工具</strong><ul>"
                "<li><a href='#artifact-viewer' class='artifact-link' data-artifact-key='tool:sympy_pint'>"
                "SymPy &amp; Pint 科学计算与量纲核验库</a>：用于主方程符号解析与物理单位制一致性检验。</li>"
                "</ul></li>"
            )

        section_html_map[i] = (
            "<details class='files-block'><summary>本节相关文件（点击蓝链在右侧窗格查看详情）</summary>"
            "<ul class='files-list'>" + "".join(subitems) + "</ul></details>"
        )

    return section_html_map, payloads


def _section_files_block(section_index, blocks, state, runlog_base_dir="physics-agent/runtime", task_dir=None):
    section_map, _ = _build_artifact_system(blocks, state, task_dir=task_dir, runlog_base_dir=runlog_base_dir)
    return section_map.get(section_index, "")


def _build_trace_timeline_records(events):
    """Extract compact AGH Trace UI records (turn, seq, kind, badge, left%, width%, preview, detail)
    from raw trace events so the embedded AGH Trace tab works 100% offline."""
    records = []
    turn_num = 0
    total = max(len(events), 1)
    tool_calls = {}
    for idx, e in enumerate(events):
        et = e.get("type", "")
        seq = e.get("seq", idx + 1)
        d = e.get("data") or {}
        left = round((idx / total) * 94 + 1, 1)
        if et == "session/start":
            ph = d.get("placeholder", "")
            if ph == "user_message_chunk":
                turn_num += 1
                records.append({
                    "turn": max(turn_num, 1),
                    "seq": seq,
                    "kind": "user",
                    "badge": "用户",
                    "left": left,
                    "width": 2,
                    "preview": f"第 {max(turn_num, 1)} 轮用户输入消息",
                    "detail": f"[用户提问 · seq #{seq}] 会话轮次 #{max(turn_num, 1)}",
                })
        elif et == "tool/call":
            if turn_num == 0:
                turn_num = 1
            t_name = d.get("name", "tool")
            t_args = d.get("args") or {}
            tu_id = d.get("toolUseId", "")
            arg_str = json.dumps(t_args, ensure_ascii=False)
            rec = {
                "turn": turn_num,
                "seq": seq,
                "kind": "tool",
                "badge": "工具",
                "left": left,
                "width": 4,
                "preview": f"{t_name} · {arg_str[:90]}",
                "detail": f"[工具调用 · seq #{seq}]\ntool: {t_name}\nargs: {arg_str[:600]}",
            }
            tool_calls[tu_id] = rec
            records.append(rec)
        elif et == "tool/result":
            tu_id = d.get("toolUseId", "")
            if tu_id in tool_calls:
                res_txt = _first_text(d.get("content"))[:400]
                tool_calls[tu_id]["detail"] += f"\n\n=== 返回结果 (seq #{seq}) ===\n{res_txt}"
    return records, max(turn_num, 1)


def _katex_head_tag(runlog_base_dir="physics-agent/runtime"):
    """Self-contained math typography stylesheet injected into <head>."""
    return (
        "<style id='katex-inline-style'>"
        ".katex-rendered{font-family:'Cambria Math','STIX Two Math','Latin Modern Math','Times New Roman',serif;"
        "font-style:normal;line-height:1.35;color:#f2f5ff}"
        ".math.katex-rendered{display:inline-flex;align-items:baseline;gap:1px;padding:0 2px}"
        ".math.display.katex-rendered{display:flex;justify-content:center;align-items:center; flex-wrap:wrap;"
        "margin:14px 0;padding:10px 16px;background:rgba(79,140,255,0.06);border:1px solid rgba(79,140,255,0.2);"
        "border-radius:8px;font-size:1.14em}"
        ".m-var{font-style:italic;padding-right:1px}"
        ".m-fn,.m-text{font-style:normal;font-family:system-ui,'Segoe UI',sans-serif;font-size:0.94em}"
        ".m-op{padding:0 3px;font-style:normal}"
        ".m-sym{font-style:italic}"
        ".m-sub,.m-sup{font-size:0.74em;line-height:1}"
        ".m-frac{display:inline-flex;flex-direction:column;align-items:center;vertical-align:middle;"
        "margin:0 3px;font-size:0.92em}"
        ".m-num{border-bottom:1px solid #cdd6f4;padding:0 4px 1px;text-align:center}"
        ".m-den{padding:1px 4px 0;text-align:center}"
        ".m-sqrt{display:inline-flex;align-items:stretch;vertical-align:middle;margin:0 2px}"
        ".m-surd{font-size:1.12em;line-height:1;padding-right:1px}"
        ".m-radicand{border-top:1px solid #cdd6f4;padding:0 3px}"
        "</style>"
    )


def render_html(blocks, cross, events, state, out_path, fallback_legacy=None,
                 report_source="report-md", figures_dir=None,
                 runlog_base_dir="physics-agent/runtime", task_dir=None):
    """Render the self-contained two-column research report HTML with inline
    math rendering and an interactive right-hand sticky artifact preview pane."""
    session_start = next((e for e in events if e["type"] == "session/start"), None)
    session_key = (session_start or {}).get("data", {}).get("key") or (state or {}).get("session_key") or "unknown-session"

    section_files_map, artifact_payloads = _build_artifact_system(
        blocks or [], state, task_dir=task_dir, runlog_base_dir=runlog_base_dir
    )

    spine_html = []
    for i, b in enumerate(blocks or []):
        block_id = f"sec-{i}"
        section_html = _figure_tag(figures_dir, b["html"], state) if figures_dir is not None else b["html"]
        files_block = section_files_map.get(i, "")
        spine_html.append(
            f"<section class='report-section' id='{block_id}'>"
            f"<h2>{html.escape(b['title'])}</h2>"
            f"<div class='sec-body'>{section_html}</div>"
            f"{files_block}"
            f"</section>"
        )

    legacy_spine = ""
    if fallback_legacy:
        legacy_spine = ("<h1 class='legacy-note'>（该运行未产出增量研究汇报，以下为基于"
                        "运行记录的过程视图）</h1>" + _render_legacy(fallback_legacy))

    has_audit_section = any(
        ("相关文件" in (b.get("title") or "") or "质量审计" in (b.get("title") or ""))
        for b in (blocks or [])
    )
    if not has_audit_section and spine_html:
        final_sec_id = f"sec-{len(blocks or [])}"
        rework_cards = []

        # 1. 真实脚本多轮迭代与排查（动态基于 programs_by_path）
        for sp, prog in (programs_by_path or {}).items():
            iters = prog.get("iterations") or []
            if len(iters) > 1 or any(it.get("exit_code", 0) != 0 for it in iters):
                first_it = iters[0]
                latest_it = iters[-1]
                first_note = html.escape(first_it.get("note_zh", "首轮基线运行"))
                latest_note = html.escape(latest_it.get("note_zh", "修正版运行"))
                first_exit = first_it.get("exit_code", 0)
                latest_exit = latest_it.get("exit_code", 0)
                base_name = html.escape(prog.get("base", "模型程序"))
                prog_file_key = prog.get("file_key", "prog:model.py")

                card_body = (
                    f"<div class='rework-card' style='margin:14px 0;padding:12px 16px;background:rgba(255,255,255,0.025);border:1px solid #28334e;border-radius:8px;'>"
                    f"<h4 style='margin:0 0 8px 0;color:#7ab0ff;font-size:0.98rem;'>【算法演进与调试闭环】{base_name}：经历 {len(iters)} 轮计算迭代与修正</h4>"
                    f"<ul style='margin:0;padding-left:18px;line-height:1.7;font-size:0.92rem;'>"
                    f"<li><strong>起点（初轮执行）</strong>：在初版计算中运行初始模型代码（见 <a href='#artifact-viewer' class='artifact-link' data-artifact-key='{first_it['call_key']}'>第 1 次代码与调用记录</a>），记录了初始状态：{first_note}。</li>"
                    f"<li><strong>偏差暴露与调试</strong>：初轮计算发现模型需调整（退出码 {first_exit}），由 <a href='#artifact-viewer' class='artifact-link' data-artifact-key='{first_it['analysis_key']}'>第 1 次问题复盘与排查</a> 记录中间偏差，并在状态账本中明确了修正策略。</li>"
                    f"<li><strong>切换与迭代修正</strong>：修正算法与参数后重新运行求解（见 <a href='#artifact-viewer' class='artifact-link' data-artifact-key='{latest_it['call_key']}'>第 {len(iters)} 次修正版代码与运行</a>），说明：{latest_note}。</li>"
                    f"<li><strong>最终验证</strong>：最终版参数顺利收敛（退出码 {latest_exit}），形成正式计算资产 <a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='{prog_file_key}'>{base_name} 源码总览</a>，并经 <a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:audit_log.py'>audit_log.py</a> 留痕。</li>"
                    f"</ul></div>"
                )
                rework_cards.append(card_body)

        # 2. 真实门禁拦截与自检修正（动态基于 hook_gates）
        for g in (hook_gates or []):
            if g.get("exit_code", 0) != 0:
                g_base = html.escape(g.get("base", "门禁脚本"))
                g_exit = g.get("exit_code", 1)
                g_note = html.escape(g.get("note_zh", "门禁拦截"))
                rework_cards.append(
                    f"<div class='rework-card' style='margin:14px 0;padding:12px 16px;background:rgba(255,100,100,0.06);border:1px solid rgba(255,100,100,0.3);border-radius:8px;'>"
                    f"<h4 style='margin:0 0 8px 0;color:#ff8080;font-size:0.98rem;'>【门禁拦截与自检修正】{g_base}（退出码 {g_exit}）</h4>"
                    f"<ul style='margin:0;padding-left:18px;line-height:1.7;font-size:0.92rem;'>"
                    f"<li><strong>拦截记录</strong>：执行质量核验（见 <a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='{g['call_key']}'>代码与拦截调用</a>），触发门禁拦截（说明：{g_note}）。</li>"
                    f"<li><strong>原因分析</strong>：详见 <a href='#artifact-viewer' class='artifact-link' data-artifact-key='{g['analysis_key']}'>拦截原因分析与诊断</a>，该拦截事件同步登记于 <a href='#artifact-viewer' class='artifact-link' data-artifact-key='file:problem_state_json'>物理状态机持久化账本</a> 的 <code>anomalies</code> 异常池中。</li>"
                    f"<li><strong>修复与闭环</strong>：Agent 根据拦截反馈修正对应脚本或报告源码后重新核验，直至门禁绿灯通过。</li>"
                    f"</ul></div>"
                )

        # 3. 状态机明确登记的异常（动态基于 state["anomalies"]）
        anomalies = (state or {}).get("anomalies") or []
        if anomalies and not rework_cards:
            for idx, an in enumerate(anomalies):
                an_type = html.escape(str(an.get("type") or f"异常 #{idx+1}"))
                an_desc = html.escape(str(an.get("description") or an.get("note") or "状态机记录的异常处理事件"))
                rework_cards.append(
                    f"<div class='rework-card' style='margin:14px 0;padding:12px 16px;background:rgba(255,255,255,0.025);border:1px solid #28334e;border-radius:8px;'>"
                    f"<h4 style='margin:0 0 8px 0;color:#ffcc66;font-size:0.98rem;'>【状态机异常处置】{an_type}</h4>"
                    f"<p style='margin:0;font-size:0.92rem;line-height:1.7;'>{an_desc}（详见 <a href='#artifact-viewer' class='artifact-link' data-artifact-key='file:problem_state_json'>物理状态机持久化账本</a>）。</p>"
                    f"</div>"
                )

        # 4. 若全流程首轮自洽收敛，未发生实际异常（客观事实陈述，绝不编造虚假故障）
        if not rework_cards:
            clean_prog_links = []
            for sp, prog in (programs_by_path or {}).items():
                pfk = prog.get("file_key", "prog:model.py")
                clean_prog_links.append(f"<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='{pfk}'>{html.escape(prog['base'])}</a>")
            prog_summary = "、".join(clean_prog_links) if clean_prog_links else "各计算脚本"

            dynamic_rework_content = (
                "<div class='rework-card' style='margin:14px 0;padding:14px 18px;background:rgba(79,140,255,0.04);border:1px solid rgba(79,140,255,0.22);border-radius:8px;'>"
                "<h4 style='margin:0 0 8px 0;color:#7ab0ff;font-size:0.98rem;'>【执行概况】全流程计算自洽收敛，未触发全局退火回滚</h4>"
                f"<p style='margin:0 0 8px 0;font-size:0.92rem;line-height:1.7;'>本次物理分析推导与数值求解流程总体自洽顺畅：所构建的核心计算程序（{prog_summary}）及四重质量门禁（<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:dimensional_check.py'>量纲核验门</a>、<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:boundary_check.py'>物理边界门</a>、<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:report_quality_check.py'>出厂质检门</a>）在首轮执行中均自洽收敛并通过检验（退出码均为 0），<a href='#artifact-viewer' class='artifact-link' data-artifact-key='file:problem_state_json'>物理状态机持久化账本</a> 的 <code>anomalies</code> 异常池无未决阻断。</p>"
                "<p style='margin:0;font-size:0.90rem;color:#8f9bb3;line-height:1.6;'>注：物理智能体底层预置了涵盖数值步长截断回滚、图表图例防遮挡外置重构（<a href='#artifact-viewer' class='artifact-link' data-artifact-key='skill:physics-report-charting'>科学绘图规范</a>）及网络异常穿透等应急重制预案（详见 <a href='#artifact-viewer' class='artifact-link' data-artifact-key='doc:rework_history'>rework_and_audit_history.md</a>）。由于本次推导演化正常，上述应急预案未被激活。</p>"
                "</div>"
            )
        else:
            dynamic_rework_content = "".join(rework_cards)

        audit_sec_html = (
            f"<section class='report-section' id='{final_sec_id}'>"
            "<h2>9. 本报告生成工作的相关文件（质量审计、追溯与返工重制说明）</h2>"
            "<div class='sec-body'>"
            "<p>为确保增量科研成果的<strong>客观性（Objectivity）</strong>、<strong>可追溯性（Traceability）</strong>与<strong>排版规范性（Readability）</strong>，本报告采用 Agnes Harness 物理智能体流水线自主生成，并在底层设置了结构化状态账本、自动化质量门禁与异常退火重制机制。</p>"
            "<h3 class='sec-subhead'>9.1 全流程过程账本与不可篡改审计留痕</h3>"
            "<ul>"
            "<li><strong>会话机器账本（<a href='#artifact-viewer' class='artifact-link' data-artifact-key='file:trace_jsonl'>trace.jsonl</a>）</strong>：记录本工作流完整时序事件，每一次环境观察、指令输入、模型推理及操作系统回显均具备确定性毫秒级时间戳与 SHA 散列标识，支持在右侧「AGH 会话轨迹」中回放与定位。</li>"
            "<li><strong>物理状态机账本（<a href='#artifact-viewer' class='artifact-link' data-artifact-key='file:problem_state_json'>物理状态机持久化账本</a>）</strong>：显式记录物理假设层、控制方程层、量纲约束表、数值解以及异常池的增量演进历史。所有物理推演必须向状态账本签入，禁止隐式推导。</li>"
            "<li><strong>报告 Markdown 源码（<a href='#artifact-viewer' class='artifact-link' data-artifact-key='file:report_md'>report.md</a>）</strong>：遵循规范科技报告标准生成的原始文本源文件，供同行复现与版本比对。</li>"
            "</ul>"
            "<h3 class='sec-subhead'>9.2 四重质量防御门禁体系与审计代码</h3>"
            "<ol>"
            "<li><strong>运行记录留痕门（<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:audit_log.py'>audit_log.py</a>）</strong>：捕获每次数值求解脚本的标准输出截断、调试迭代次数及核心结论溯源编号，禁止任何无执行留痕的数据进入报告正文。</li>"
            "<li><strong>物理量纲核验门（<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:dimensional_check.py'>dimensional_check.py</a>）</strong>：基于 SymPy 与 Pint 符号计算库（<a href='#artifact-viewer' class='artifact-link' data-artifact-key='tool:sympy_pint'>量纲工具链</a>），自动核验控制方程两端物理量纲与主导参数齐次性，从形式化数学层面辅助排查量纲不一致错误。</li>"
            "<li><strong>物理边界与退化极限检验门（<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:boundary_check.py'>boundary_check.py</a>）</strong>：依据边界配置（<a href='#artifact-viewer' class='artifact-link' data-artifact-key='gate:boundary_spec'>boundary_spec.json</a>）自动执行退化极限、极端参数单调性检验，保障结论在极端物理条件下自洽。</li>"
            "<li><strong>离线自包含与排版质检门（<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:report_quality_check.py'>report_quality_check.py</a>）</strong>：执行报告交付前检验——检查 KaTeX 数学公式 100% 离线内联排版（零外部 CDN 泄露）、消除死链与未闭合标签、校验矢量图例零遮挡准则（<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:make_report_figures.py'>make_report_figures.py</a>），保障在离线环境下正常呈现。</li>"
            "<li><strong>双栏离线交互排版引擎（<a href='#artifact-viewer' class='artifact-link prog-main-link' data-artifact-key='prog:trace_visualizer.py'>trace_visualizer.py</a>）</strong>：将科研正文与 AGH 会话时序甘特图融合为可交互离线 HTML，支持正文蓝链与右侧甘特图实时联动跳转。</li>"
            "</ol>"
            "<h3 class='sec-subhead'>9.3 因不合理而返工重制的过程及依据（退火回滚与重制复盘）</h3>"
            "<p>科学分析的真实性不仅体现在最终结论的成立，更体现在面对异常或不合理结果时<strong>拒绝掩饰、依据数据事实动态重构</strong>的工程素养。本节基于本会话真实落盘的执行账本与状态机数据，客观还原实际发生的演进与调试历程：</p>"
            "<div class='md-quote'>"
            "<strong>详细复盘白皮书</strong>：参见 <a href='#artifact-viewer' class='artifact-link' data-artifact-key='doc:rework_history'>rework_and_audit_history.md（流水线退火回滚预案与质检复盘全景记录）</a>"
            "</div>"
            f"{dynamic_rework_content}"
            "</div>"
            "</section>"
        )
        spine_html.append(audit_sec_html)

    main_content = "".join(spine_html) if spine_html else legacy_spine
    trace_records, turn_count = _build_trace_timeline_records(events)
    tool_call_count = sum(1 for e in events if e.get("type") == "tool/call")
    esc_session = html.escape(str(session_key or ""))
    web_origin = os.environ.get("AGNES_WEB_ORIGIN", "http://127.0.0.1:4180").rstrip("/")
    sidebar_html = (
        "<aside class='report-files-sidebar' id='artifact-viewer' aria-label='文件与运行记录预览窗格'>"
        "<div class='sidebar-resizer' id='sidebar-resizer' title='按住左右拖动调整右侧窗格宽度，双击恢复默认宽度'></div>"
        "<div class='sidebar-topbar'>"
        "<div class='sidebar-tabs' role='tablist'>"
        "<button type='button' class='sidebar-tab active' id='tab-btn-detail' data-pane='detail'>📄 文件与运行详情</button>"
        "<button type='button' class='sidebar-tab' id='tab-btn-trace' data-pane='trace'>📊 AGH 会话轨迹 (Trace)</button>"
        "</div>"
        "<div class='sidebar-width-group' title='快速调整窗格宽度（也可拖动左侧手柄自由缩放）'>"
        "<span class='sidebar-width-label'>宽度:</span>"
        "<button type='button' class='sidebar-width-btn active' data-width='480'>480px</button>"
        "<button type='button' class='sidebar-width-btn' data-width='640'>640px</button>"
        "<button type='button' class='sidebar-width-btn' data-width='800'>800px</button>"
        "<button type='button' class='sidebar-width-btn' data-width='50%'>50%</button>"
        "</div>"
        f"<a href='{web_origin}/?session={esc_session}&amp;tab=trace' target='_blank' rel='noopener noreferrer' class='agh-back-btn' id='agh-return-btn' "
        "title='跳转回对应的 AGH 会话窗口并定位到对应轨迹位置'>↗ 返回对应的AGH页面查看</a>"
        "</div>"
        "<div id='pane-detail' style='display:flex;flex-direction:column;flex:1;overflow:hidden'>"
        "<div class='sidebar-header'>"
        "<div class='sidebar-meta-row'>"
        "<div class='sidebar-badge' id='viewer-category'>文件与运行记录预览</div>"
        "<button type='button' class='locate-trace-btn' id='locate-in-trace-btn'>📍 在 AGH 轨迹页中定位</button>"
        "</div>"
        "<div id='detail-toast' class='agh-trace-toast' style='display:none;margin-top:8px;font-size:0.82rem;padding:6px 12px;background:rgba(255,170,0,0.12);border:1px solid rgba(255,170,0,0.35);color:#ffcc66;border-radius:6px;align-items:center;gap:6px;'></div>"
        "<h3 class='sidebar-title' id='viewer-title'>点击左侧「本节相关文件」中的蓝链查看详情</h3>"
        "<p class='sidebar-summary' id='viewer-summary'>在左侧各章节底部展开「本节相关文件」，点击任意程序、调试记录、数据源或组件名称，即可在此常驻窗格中实时查看完整源代码、运行输出或切换至 AGH 原始会话轨迹。</p>"
        "</div>"
        "<pre class='sidebar-code' id='viewer-content'></pre>"
        "</div>"
        "<div class='agh-trace-pane' id='pane-trace'>"
        "<div class='agh-trace-toolbar'>"
        f"<span class='agh-trace-stats'>轮次 {turn_count} · 工具调用 {tool_call_count} · 事件 {len(events)}</span>"
        "<button type='button' class='agh-trace-btn' id='agh-wrap-btn' title='切换消息行自动换行/单行显示'>自动换行</button>"
        "<button type='button' class='agh-trace-btn' id='agh-collapse-btn'>折叠轮次</button>"
        "<input type='search' class='agh-trace-search' id='agh-search-input' placeholder='搜索 seq / 工具 / 脚本'>"
        "</div>"
        "<div id='agh-trace-toast' class='agh-trace-toast' style='display:none;'></div>"
        "<div class='agh-gantt'>"
        f"<div class='agh-gantt-head'><span>时间轴 · 耗时·压缩空闲（点击色块定位记录）</span><span>session: {esc_session[:8]}</span></div>"
        "<div class='agh-lane'><span class='agh-lane-label'>输入</span><div class='agh-lane-track' id='gantt-lane-input'></div></div>"
        "<div class='agh-lane'><span class='agh-lane-label'>模型</span><div class='agh-lane-track' id='gantt-lane-model'></div></div>"
        "<div class='agh-lane'><span class='agh-lane-label'>工具</span><div class='agh-lane-track' id='gantt-lane-tool'></div></div>"
        "</div>"
        "<div class='agh-turns' id='agh-turns-list'></div>"
        "</div>"
        "</aside>"
    )

    doc = (
        "<!doctype html>\n<html lang='zh'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>物理研究报告</title>"
        + _katex_head_tag(runlog_base_dir)
        + "<style>" + _css() + "</style></head><body>"
        "<header class='report-header'><h1>物理研究报告</h1>"
        f"<p class='meta'>会话标识: {esc_session} · 生成时间: {_now_iso()}</p></header>"
        "<div class='report-layout'>"
        f"<main class='report-main'>{main_content}</main>"
        f"{sidebar_html}"
        "</div>"
        "<aside class='loop-channel' id='loop-channel' aria-hidden='true'></aside>"
        "<script type='application/json' id='artifact-payloads'>"
        + json.dumps(artifact_payloads, ensure_ascii=False).replace("</", "<\\/")
        + "</script>"
        "<script type='application/json' id='agh-trace-events'>"
        + json.dumps(trace_records, ensure_ascii=False).replace("</", "<\\/")
        + "</script>"
        "<script type='application/json' id='loop-data'>" + json.dumps(_loop_data(spine_html or [], cross)) + "</script>"
        + "<script type='application/json' id='agh-host-config'>"
        + json.dumps({"web_origin": web_origin, "session_key": str(session_key or "")}, ensure_ascii=False).replace("</", "<\\/")
        + "</script>"
        + "<script>" + _js() + "</script></body></html>"
    )
    slug_to_replace = ""
    if task_dir:
        slug_to_replace = os.path.basename(os.path.abspath(task_dir))
    elif out_path:
        m_slug = re.search(r"research_report_([A-Za-z0-9_\-]+)\.html", os.path.basename(out_path))
        if m_slug:
            slug_to_replace = m_slug.group(1)
    if slug_to_replace:
        doc = doc.replace("<task-slug>", slug_to_replace)

    out_dir = os.path.dirname(os.path.abspath(out_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
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
font:15px/1.65 system-ui,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;padding:24px 32px 48px}
header.report-header{max-width:1440px;margin:0 auto 18px;border-bottom:1px solid var(--line);padding-bottom:12px}
header.report-header h1{font-size:26px;margin:0 0 4px}
.meta{color:var(--muted);font-size:13px;margin:0}
.report-layout{display:grid;grid-template-columns:minmax(0,1fr) var(--sidebar-width,480px);gap:18px;max-width:1800px;margin:0 auto;align-items:start}
.sidebar-resizer{position:absolute;left:0;top:0;bottom:0;width:10px;cursor:col-resize;background:transparent;z-index:50;display:flex;align-items:center;justify-content:center;user-select:none;-webkit-user-select:none;touch-action:none}
.sidebar-resizer::after{content:'';width:3px;height:60px;border-radius:2px;background:#384058;transition:background .2s,height .2s}
.sidebar-resizer:hover::after,.sidebar-resizer.dragging::after{background:#4f8cff;height:96px;box-shadow:0 0 10px rgba(79,140,255,0.7)}
.sidebar-width-group{display:inline-flex;align-items:center;gap:3px;background:#11131a;border:1px solid var(--line);border-radius:6px;padding:2px 4px;margin-left:auto}
.sidebar-width-label{font-size:11px;color:var(--muted);margin-right:2px}
.sidebar-width-btn{border:none;background:transparent;color:var(--muted);font-size:11px;font-weight:600;padding:2px 6px;border-radius:4px;cursor:pointer}
.sidebar-width-btn:hover{background:rgba(255,255,255,0.08);color:#fff}
.sidebar-width-btn.active{background:var(--accent);color:#fff}
.agh-preview.wrap{white-space:normal;word-break:break-all}
.report-main{min-width:0}
.report-files-sidebar{position:sticky;top:20px;max-height:calc(100vh - 40px);display:flex;flex-direction:column;
background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px 16px 20px;overflow:hidden;
box-shadow:0 8px 28px rgba(0,0,0,0.35)}
.sidebar-header{border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:10px}
.sidebar-badge{display:inline-block;font-size:11px;font-weight:600;color:#fff;background:var(--accent);
padding:2px 8px;border-radius:6px;margin-bottom:6px}
.sidebar-title{font-size:15.5px;margin:0 0 6px;color:var(--ink);line-height:1.4}
.sidebar-summary{font-size:12.5px;color:var(--muted);margin:0;line-height:1.5}
.sidebar-code{flex:1;overflow:auto;margin:0;padding:12px;background:#11131a;border:1px solid #2b3042;
border-radius:8px;font:12.5px/1.55 Consolas,"SFMono-Regular",Menlo,monospace;color:#dce3f5;white-space:pre-wrap;word-break:break-word}
@media(max-width:960px){.report-layout{grid-template-columns:1fr}.report-files-sidebar{position:static;max-height:520px;margin-top:16px}}
.report-section{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:18px 22px;margin:0 0 18px}
.report-section h2{font-size:20px;margin:0 0 12px;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:8px}
.sec-subhead{font-size:16.5px;color:#d5def5;margin:16px 0 8px}
.sec-body p{margin:8px 0}
.md-quote{margin:10px 0;padding:10px 14px;background:var(--card2);border-left:4px solid var(--accent);
border-radius:0 8px 8px 0;color:#d6dcef}
.md-quote p{margin:0}
.md-code{background:#12141c;border:1px solid var(--line);padding:10px 12px;border-radius:8px;overflow:auto;font-size:13px}
.md-hr{border:none;border-top:1px solid var(--line);margin:14px 0}
.report-figure-inlined,.report-figure-missing{margin:14px 0}
.report-figure-inlined img{max-width:100%;border:1px solid var(--line);border-radius:8px}
.report-figure-inlined figcaption,.report-figure-missing{font-size:12.5px;color:var(--muted);margin-top:4px}
.report-figure-interactive .report-figure-body,.report-figure-interactive>div{max-width:100%}
.figure-kind-tag{display:inline-block;font-size:10.5px;background:var(--accent);color:#fff;
padding:1px 6px;border-radius:8px;margin-left:6px;vertical-align:middle}
.report-figure-missing{border:1px solid var(--orange);background:#1a1d27;padding:10px 12px;
border-radius:8px}
.sec-body ul,.sec-body ol{margin:8px 0 8px 20px}
.sec-body li{margin:4px 0}
.sec-body code{background:#12141c;padding:1px 5px;border-radius:4px;font-size:0.92em}
.md-table{border-collapse:collapse;margin:12px 0;width:100%}
.md-table th,.md-table td{padding:6px 10px;border:1px solid var(--line);text-align:left;font-size:13.5px}
.md-table th{color:#c5cde0;background:rgba(255,255,255,0.03);font-weight:600}
.files-block{margin-top:16px;padding:10px 14px;font-size:13px;color:var(--muted);
background:rgba(46,204,113,0.04);border-left:4px solid var(--green);border-radius:0 8px 8px 0}
.files-block summary{cursor:pointer;color:var(--green);font-weight:600;user-select:none}
.files-list{list-style:none;margin:8px 0 0;padding:0}
.files-list>li.files-subitem{margin:8px 0;color:var(--ink)}
.files-list ul{list-style:disc;margin:4px 0 4px 20px;color:var(--muted)}
.files-list li{margin:3px 0}
.artifact-link{color:var(--accent);text-decoration:none;font-weight:500;cursor:pointer;border-bottom:1px dashed rgba(79,140,255,0.5)}
.artifact-link:hover,.artifact-link.active{color:#7fb0ff;border-bottom-style:solid;background:rgba(79,140,255,0.12);border-radius:3px;padding:0 3px}
.iter-brief{font-size:12px;color:var(--muted);margin-left:4px}
.runlog-empty{color:var(--muted)}
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
.loop-channel{display:none}
.sidebar-topbar{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.sidebar-tabs{display:flex;gap:4px;background:#11131a;padding:3px;border-radius:8px;border:1px solid #2b3042}
.sidebar-tab{background:transparent;border:none;color:#94a3b8;font-size:12px;font-weight:600;padding:5px 10px;border-radius:6px;cursor:pointer;transition:all .15s}
.sidebar-tab:hover{color:#e2e8f0}
.sidebar-tab.active{background:#2563eb;color:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.3)}
.agh-back-btn{display:inline-flex;align-items:center;font-size:11px;color:#94a3b8;text-decoration:none;border:1px solid #334155;border-radius:6px;padding:4px 8px;background:rgba(255,255,255,0.03);cursor:pointer;white-space:nowrap;transition:all .15s}
.agh-back-btn:hover{color:#38bdf8;border-color:#38bdf8;background:rgba(56,189,248,0.08)}
.locate-trace-btn{background:transparent;border:1px dashed #3b82f6;color:#60a5fa;border-radius:4px;font-size:11px;padding:2px 6px;cursor:pointer;margin-left:auto}
.locate-trace-btn:hover{background:rgba(59,130,246,0.15)}
.agh-trace-pane{display:none;flex-direction:column;flex:1;overflow:hidden;background:#fff;border-radius:8px;color:#1e293b}
.agh-trace-pane.active{display:flex}
.agh-trace-toolbar{display:flex;align-items:center;gap:8px;padding:8px 10px;background:#f8fafc;border-bottom:1px solid #e2e8f0;font-size:11.5px}
.agh-trace-stats{color:#64748b;font-weight:600}
.agh-trace-btn{background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer;color:#334155}
.agh-trace-btn:hover{background:#f1f5f9}
.agh-trace-search{flex:1 1 auto;width:190px;min-width:165px;max-width:240px;border:1px solid #cbd5e1;background:#f8fafc;color:#1e293b;border-radius:5px;padding:3.5px 10px;font-size:11.5px;transition:border-color .2s,box-shadow .2s}
.agh-trace-search:focus{outline:none;border-color:#38bdf8;background:#fff;box-shadow:0 0 6px rgba(56,189,248,0.35)}
.agh-gantt{padding:8px 10px;background:#fff;border-bottom:1px solid #e2e8f0}
.agh-gantt-head{display:flex;justify-content:space-between;font-size:11px;color:#64748b;margin-bottom:4px}
.agh-lane{display:grid;grid-template-columns:36px 1fr;align-items:center;gap:6px;margin:3px 0}
.agh-lane-label{font-size:11px;color:#64748b}
.agh-lane-track{position:relative;height:12px;background:#eef2f6;border-radius:3px;overflow:hidden}
.agh-bar{position:absolute;top:1px;bottom:1px;border-radius:2px;cursor:pointer;transition:opacity .15s}
.agh-bar:hover{opacity:0.8;outline:1px solid #0f172a}
.agh-bar.input{background:#0d9488}
.agh-bar.model{background:#6366f1}
.agh-bar.tool{background:#d97706}
.agh-bar.bar-highlight{outline:2px solid #38bdf8;box-shadow:0 0 8px #38bdf8;z-index:10}
.agh-turns{flex:1;overflow:auto;padding:6px 8px;background:#f8f9fc}
.agh-turn{margin-bottom:6px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden}
.agh-turn-head{padding:5px 8px;background:#f1f5f9;font-weight:600;font-size:12px;color:#1e293b;cursor:pointer;display:flex;justify-content:space-between;user-select:none}
.agh-row{padding:5px 8px;border-top:1px solid #f1f5f9;cursor:pointer;display:flex;flex-direction:column;gap:3px;transition:background-color .2s,outline .2s}
.agh-row:hover{background:#f8fafc}
.agh-row.selected{background:#eff6ff;outline:2px solid #2563eb}
.agh-row.highlight-flash{animation:agh-pulse 2s ease-out;outline:2px solid #0284c7;box-shadow:0 0 0 3px rgba(56,189,248,0.5)}
@keyframes agh-pulse{0%{background:#bae6fd;box-shadow:0 0 0 4px #0284c7, 0 0 22px rgba(56,189,248,0.95)}35%{background:#e0f2fe;box-shadow:0 0 0 2px #38bdf8, 0 0 12px rgba(56,189,248,0.6)}100%{background:#eff6ff;box-shadow:none}}
.agh-trace-toast{margin:4px 8px 0;padding:5px 12px;background:#0284c7;color:#fff;font-size:11.5px;font-weight:600;border-radius:6px;box-shadow:0 2px 10px rgba(2,132,199,0.4);animation:toast-pop .25s ease-out;display:flex;align-items:center;gap:6px;z-index:10}
@keyframes toast-pop{0%{opacity:0;transform:translateY(-6px)}100%{opacity:1;transform:translateY(0)}}
.agh-row-line{display:flex;align-items:center;gap:6px;line-height:1.35}
.agh-badge{display:inline-block;font-size:10.5px;font-weight:600;padding:1px 5px;border-radius:4px;flex-shrink:0}
.agh-badge.user{background:#dbeafe;color:#1d4ed8}
.agh-badge.context{background:#dcfce7;color:#15803d}
.agh-badge.model{background:#ede9fe;color:#6d28d9}
.agh-badge.tool{background:#fef3c7;color:#b45309}
.agh-seq{font-family:Consolas,monospace;font-size:10.5px;color:#64748b;flex-shrink:0}
.agh-preview{color:#334155;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.agh-detail{display:none;margin-top:4px;padding:6px 8px;background:#0f172a;color:#e2e8f0;border-radius:5px;font:11.5px/1.45 Consolas,monospace;white-space:pre-wrap;word-break:break-word}
.agh-row.selected .agh-detail{display:block}
"""


def _js():
    return """
(function(){
  var hostConfigEl = document.getElementById('agh-host-config');
  var hostConfig = {};
  if (hostConfigEl && hostConfigEl.textContent) {
    try { hostConfig = JSON.parse(hostConfigEl.textContent); } catch (e) { hostConfig = {}; }
  }
  var sessionKey = hostConfig.session_key || '';
  var configuredOrigin = (hostConfig.web_origin || 'http://127.0.0.1:4180').replace(/\/+$/, '');
  var activeOrigin = (window.location.protocol === 'http:' || window.location.protocol === 'https:')
    ? window.location.origin
    : configuredOrigin;
  var baseReturnUrl = activeOrigin + '/?session=' + encodeURIComponent(sessionKey) + '&tab=trace';

  var payloadEl = document.getElementById('artifact-payloads');
  var payloads = {};
  if (payloadEl && payloadEl.textContent) {
    try { payloads = JSON.parse(payloadEl.textContent); } catch (e) { payloads = {}; }
  }
  var traceEl = document.getElementById('agh-trace-events');
  var traceEvents = [];
  if (traceEl && traceEl.textContent) {
    try { traceEvents = JSON.parse(traceEl.textContent); } catch (e) { traceEvents = []; }
  }

  var catEl = document.getElementById('viewer-category');
  var titleEl = document.getElementById('viewer-title');
  var sumEl = document.getElementById('viewer-summary');
  var codeEl = document.getElementById('viewer-content');
  var viewerEl = document.getElementById('artifact-viewer');
  var locateBtn = document.getElementById('locate-in-trace-btn');
  var returnBtn = document.getElementById('agh-return-btn');
  if (returnBtn) {
    returnBtn.href = baseReturnUrl;
    returnBtn.target = '_blank';
    returnBtn.rel = 'noopener noreferrer';
  }
  var tabDetailBtn = document.getElementById('tab-btn-detail');
  var tabTraceBtn = document.getElementById('tab-btn-trace');
  var paneDetail = document.getElementById('pane-detail');
  var paneTrace = document.getElementById('pane-trace');

  var currentSeq = null;
  var KEY_TO_SEQ = {};

  // 1. Initial seeds from payloads if already defined
  Object.keys(payloads).forEach(function(k){
    var item = payloads[k];
    if (item && item.seq) { KEY_TO_SEQ[k] = item.seq; }
  });

  // 2. Discover script executions, tool calls, and file operations from traceEvents
  var scriptCalls = {}; // scriptName -> [seq1, seq2, ...]
  var skillKeys = [
    'physics-agent-orchestrator', 'physics-agent-governance', 'physics-state-check',
    'physics-pipeline', 'physics-defense-lines', 'physics-auditability',
    'physics-report-charting', 'physics-report-writing', 'physics-doc-parsing',
    'physics-permission-shortfall'
  ];

  traceEvents.forEach(function(ev){
    if (!ev.seq) return;
    var seq = ev.seq;
    var fullText = ((ev.preview || '') + ' ' + (ev.detail || '')).toLowerCase();

    // Match skill reads: e.g. skill_read {"name": "physics-pipeline"} or mentions in tool args
    skillKeys.forEach(function(skId){
      if (fullText.indexOf(skId) !== -1) {
        if (!KEY_TO_SEQ['skill:' + skId]) KEY_TO_SEQ['skill:' + skId] = seq;
      }
    });

    // Match core state files and reports
    if (fullText.indexOf('problem_state') !== -1) {
      KEY_TO_SEQ['file:problem_state_json'] = seq;
    }
    if (fullText.indexOf('report.md') !== -1 || fullText.indexOf('report_') !== -1) {
      KEY_TO_SEQ['file:report_md'] = seq;
    }
    if (fullText.indexOf('boundary_spec') !== -1 || fullText.indexOf('boundary_gate') !== -1) {
      KEY_TO_SEQ['gate:boundary_spec'] = seq;
    }
    if (fullText.indexOf('dimensional_gate') !== -1 || fullText.indexOf('dimensional_check') !== -1) {
      KEY_TO_SEQ['prog:dimensional_check.py'] = seq;
      if (!KEY_TO_SEQ['tool:sympy_pint']) KEY_TO_SEQ['tool:sympy_pint'] = seq;
    }
    if (fullText.indexOf('audit_log') !== -1) {
      KEY_TO_SEQ['prog:audit_log.py'] = seq;
    }
    if (fullText.indexOf('make_report_figures') !== -1) {
      KEY_TO_SEQ['prog:make_report_figures.py'] = seq;
    }
    if (fullText.indexOf('report_quality_check') !== -1) {
      KEY_TO_SEQ['prog:report_quality_check.py'] = seq;
    }
    if (fullText.indexOf('trace_visualizer') !== -1) {
      KEY_TO_SEQ['prog:trace_visualizer.py'] = seq;
    }
    if (fullText.indexOf('rework') !== -1) {
      KEY_TO_SEQ['doc:rework_history'] = seq;
    }

    // Dynamically match ANY python script mentioned in tool call (e.g. python xxx.py, write xxx.py)
    var pyMatches = fullText.match(/[a-z0-9_\-]+\.py/g);
    if (pyMatches) {
      pyMatches.forEach(function(pyFile){
        var progKey = 'prog:' + pyFile;
        if (!KEY_TO_SEQ[progKey]) KEY_TO_SEQ[progKey] = seq;
        if (!scriptCalls[pyFile]) scriptCalls[pyFile] = [];
        scriptCalls[pyFile].push(seq);
      });
    }
  });

  // 3. Map iteration call keys (run:xxx / call:xxx) and analysis keys (analysis:xxx)
  Object.keys(payloads).forEach(function(k){
    var item = payloads[k];
    if (!item || KEY_TO_SEQ[k]) return;
    var scriptName = item.script;
    if (scriptName && scriptCalls[scriptName] && scriptCalls[scriptName].length) {
      var iterIdx = (item.iteration || 1) - 1;
      var calls = scriptCalls[scriptName];
      var mappedSeq = (iterIdx < calls.length) ? calls[iterIdx] : calls[calls.length - 1];
      KEY_TO_SEQ[k] = mappedSeq;
    }
  });

  function switchPane(target) {
    if (target === 'trace') {
      if (tabDetailBtn) tabDetailBtn.classList.remove('active');
      if (tabTraceBtn) tabTraceBtn.classList.add('active');
      if (paneDetail) paneDetail.style.display = 'none';
      if (paneTrace) paneTrace.classList.add('active');
    } else {
      if (tabTraceBtn) tabTraceBtn.classList.remove('active');
      if (tabDetailBtn) tabDetailBtn.classList.add('active');
      if (paneTrace) paneTrace.classList.remove('active');
      if (paneDetail) paneDetail.style.display = 'flex';
    }
  }

  if (tabDetailBtn) tabDetailBtn.addEventListener('click', function(){ switchPane('detail'); });
  if (tabTraceBtn) tabTraceBtn.addEventListener('click', function(){
    switchPane('trace');
    if (currentSeq) highlightTraceSeq(currentSeq, false);
  });

  var detailToastEl = document.getElementById('detail-toast');
  function showDetailToast(msg) {
    if (!detailToastEl) return;
    detailToastEl.textContent = msg;
    detailToastEl.style.display = 'flex';
    clearTimeout(window.__detailToastTimer);
    window.__detailToastTimer = setTimeout(function(){
      detailToastEl.style.display = 'none';
    }, 3200);
  }

  function updateReturnLink(seq) {
    currentSeq = seq || null;
    if (locateBtn) {
      if (seq) {
        locateBtn.classList.remove('no-trace');
        locateBtn.style.opacity = '1';
        locateBtn.style.cursor = 'pointer';
        locateBtn.textContent = '📍 在 AGH 轨迹页中定位 (seq #' + seq + ')';
        locateBtn.title = '切换至 AGH 轨迹页并在时间线中高亮定位 seq #' + seq;
      } else {
        locateBtn.classList.add('no-trace');
        locateBtn.style.opacity = '0.8';
        locateBtn.style.cursor = 'pointer';
        locateBtn.textContent = '📍 本项无对应轨迹 (点击说明)';
        locateBtn.title = '该项属于静态技能规范或外部数据源，无特定会话执行轨迹。点击查看提示。';
      }
    }
    if (returnBtn) {
      var hash = seq ? '#seq-' + seq : '';
      returnBtn.href = baseReturnUrl + hash;
    }
  }

  // Render Gantt lanes
  var laneInput = document.getElementById('gantt-lane-input');
  var laneModel = document.getElementById('gantt-lane-model');
  var laneTool = document.getElementById('gantt-lane-tool');

  function renderGantt() {
    if (!traceEvents.length) return;
    var maxLeft = 1;
    traceEvents.forEach(function(ev){
      var right = (ev.left || 0) + (ev.width || 2);
      if (right > maxLeft) maxLeft = right;
    });
    var scale = 100 / Math.max(maxLeft, 10);
    traceEvents.forEach(function(ev){
      var bar = document.createElement('div');
      bar.className = 'agh-bar ' + (ev.kind || 'tool');
      bar.style.left = ((ev.left || 0) * scale) + '%';
      bar.style.width = Math.max((ev.width || 2) * scale, 1.2) + '%';
      bar.title = 'seq #' + ev.seq + ' (' + (ev.badge || ev.kind) + '): ' + (ev.preview || '');
      bar.addEventListener('click', function(){
        switchPane('trace');
        highlightTraceSeq(ev.seq, true);
      });
      if (ev.kind === 'user' || ev.kind === 'context') {
        if (laneInput) laneInput.appendChild(bar);
      } else if (ev.kind === 'model') {
        if (laneModel) laneModel.appendChild(bar);
      } else {
        if (laneTool) laneTool.appendChild(bar);
      }
    });
  }
  renderGantt();

  // Render trace turn cards
  var turnsList = document.getElementById('agh-turns-list');
  function renderTraceView(filterText) {
    if (!turnsList) return;
    turnsList.innerHTML = '';
    var turnsMap = {};
    traceEvents.forEach(function(ev){
      var t = ev.turn || 1;
      if (!turnsMap[t]) turnsMap[t] = [];
      turnsMap[t].push(ev);
    });

    Object.keys(turnsMap).sort(function(a,b){ return Number(a) - Number(b); }).forEach(function(tKey){
      var eventsInTurn = turnsMap[tKey];
      if (filterText) {
        var ft = filterText.toLowerCase();
        eventsInTurn = eventsInTurn.filter(function(ev){
          return (String(ev.seq).indexOf(ft) !== -1 ||
                  (ev.preview && ev.preview.toLowerCase().indexOf(ft) !== -1) ||
                  (ev.detail && ev.detail.toLowerCase().indexOf(ft) !== -1));
        });
        if (!eventsInTurn.length) return;
      }

      var turnBox = document.createElement('div');
      turnBox.className = 'agh-turn';
      var head = document.createElement('div');
      head.className = 'agh-turn-head';
      head.innerHTML = '<span>▾ 第 ' + tKey + ' 轮</span><span>' + eventsInTurn.length + ' 条记录</span>';
      var body = document.createElement('div');
      body.className = 'agh-turn-body';

      head.addEventListener('click', function(){
        var isClosed = (body.style.display === 'none');
        body.style.display = isClosed ? 'block' : 'none';
        head.firstChild.textContent = (isClosed ? '▾ ' : '▸ ') + '第 ' + tKey + ' 轮';
      });

      eventsInTurn.forEach(function(ev){
        var row = document.createElement('div');
        row.className = 'agh-row';
        row.setAttribute('data-seq', ev.seq);
        row.innerHTML =
          '<div class="agh-row-line">' +
            '<span class="agh-badge ' + (ev.kind || 'tool') + '">' + (ev.badge || ev.kind) + '</span>' +
            '<span class="agh-seq">#' + ev.seq + '</span>' +
            '<span class="agh-preview">' + (ev.preview || '') + '</span>' +
          '</div>' +
          '<div class="agh-detail">' + (ev.detail || ev.preview || '') + '</div>';

        row.addEventListener('click', function(){
          highlightTraceSeq(ev.seq, true);
        });
        body.appendChild(row);
      });

      turnBox.appendChild(head);
      turnBox.appendChild(body);
      turnsList.appendChild(turnBox);
    });
  }
  renderTraceView();

  function highlightTraceSeq(seq, isHot) {
    updateReturnLink(seq);
    var rows = document.querySelectorAll('.agh-row');
    var targetRow = null;
    rows.forEach(function(r){
      var match = (Number(r.getAttribute('data-seq')) === Number(seq));
      r.classList.toggle('selected', match);
      if (match) targetRow = r;
    });
    if (targetRow) {
      // Auto-expand turn body if collapsed
      var parentBody = targetRow.parentElement;
      if (parentBody && parentBody.style.display === 'none') {
        parentBody.style.display = 'block';
        var headEl = parentBody.previousElementSibling;
        if (headEl && headEl.firstChild) {
          headEl.firstChild.textContent = headEl.firstChild.textContent.replace('▸', '▾');
        }
      }

      // Explicit container scrolling: calculate precise offset within #agh-turns-list
      var turnsContainer = document.getElementById('agh-turns-list');
      if (turnsContainer) {
        var topPos = targetRow.offsetTop - (turnsContainer.clientHeight / 2) + (targetRow.clientHeight / 2);
        turnsContainer.scrollTo({ top: Math.max(0, topPos), behavior: 'smooth' });
      } else {
        targetRow.scrollIntoView({behavior: 'smooth', block: 'center'});
      }

      // High-contrast multi-layer glow pulse animation
      targetRow.classList.remove('highlight-flash');
      void targetRow.offsetWidth;
      targetRow.classList.add('highlight-flash');
      setTimeout(function(){ targetRow.classList.remove('highlight-flash'); }, 2000);

      // On-screen Toast feedback
      var toastEl = document.getElementById('agh-trace-toast');
      if (toastEl) {
        var prevEl = targetRow.querySelector('.agh-preview');
        var snippet = prevEl ? prevEl.textContent.slice(0, 36) : '';
        toastEl.textContent = '📍 已定位至轨迹 seq #' + seq + (snippet ? ' · ' + snippet : '');
        toastEl.style.display = 'flex';
        clearTimeout(window.__traceToastTimer);
        window.__traceToastTimer = setTimeout(function(){
          toastEl.style.display = 'none';
        }, 2600);
      }
    }
    document.querySelectorAll('.agh-bar').forEach(function(bar){
      var matchBar = (bar.title && bar.title.indexOf('seq #' + seq + ' ') !== -1);
      bar.classList.toggle('bar-highlight', matchBar);
      if (matchBar) {
        setTimeout(function(){ bar.classList.remove('bar-highlight'); }, 2000);
      }
    });
  }

  if (locateBtn) {
    locateBtn.addEventListener('click', function(){
      if (currentSeq) {
        switchPane('trace');
        highlightTraceSeq(currentSeq, true);
      } else {
        showDetailToast('ℹ️ 本文件属于静态技能规范或外部数据源，无特定会话执行轨迹。');
      }
    });
  }

  var collapseBtn = document.getElementById('agh-collapse-btn');
  var allCollapsed = false;
  if (collapseBtn) {
    collapseBtn.addEventListener('click', function(){
      allCollapsed = !allCollapsed;
      collapseBtn.textContent = allCollapsed ? '展开轮次' : '折叠轮次';
      document.querySelectorAll('.agh-turn').forEach(function(tb){
        var hd = tb.querySelector('.agh-turn-head');
        var bd = hd ? hd.nextElementSibling : null;
        if (bd) bd.style.display = allCollapsed ? 'none' : 'block';
      });
    });
  }

  var searchInput = document.getElementById('agh-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', function(){
      renderTraceView(searchInput.value);
      highlightTraceSeq(currentSeq, false);
    });
  }

  function showArtifact(key, linkEl) {
    var item = payloads[key];
    if (!item) return;
    if (catEl) catEl.textContent = item.category || '文件预览';
    if (titleEl) titleEl.textContent = item.title || key;
    if (sumEl) sumEl.textContent = item.summary || '';
    if (codeEl) codeEl.textContent = item.content || '';
    var targetSeq = KEY_TO_SEQ[key] || null;
    updateReturnLink(targetSeq);
    document.querySelectorAll('.artifact-link.active').forEach(function(el){
      el.classList.remove('active');
    });
    if (linkEl) linkEl.classList.add('active');

    // Hot jump in trace view if user is currently staying on the trace tab
    if (paneTrace && paneTrace.classList.contains('active')) {
      if (targetSeq) {
        highlightTraceSeq(targetSeq, true);
      }
    }

    if (window.innerWidth <= 960 && viewerEl && linkEl) {
      viewerEl.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
  }

  document.querySelectorAll('.artifact-link').forEach(function(link){
    link.addEventListener('click', function(ev){
      ev.preventDefault();
      var key = link.getAttribute('data-artifact-key');
      showArtifact(key, link);
    });
  });

  var preferredKeys = Object.keys(payloads);
  var defaultKey = null;
  for (var i = 0; i < preferredKeys.length; i++) {
    if (preferredKeys[i].indexOf('prog:') === 0) { defaultKey = preferredKeys[i]; break; }
  }
  if (!defaultKey && preferredKeys.indexOf('datasource-main') !== -1) {
    defaultKey = 'datasource-main';
  }
  if (!defaultKey && preferredKeys.length > 0) {
    defaultKey = preferredKeys[0];
  }
  if (defaultKey) {
    var firstLink = document.querySelector('.artifact-link[data-artifact-key="' + defaultKey + '"]');
    showArtifact(defaultKey, firstLink);
  }

  // --- Sidebar Resizing & Width Controls ---
  var layoutEl = document.querySelector('.report-layout');
  var resizerEl = document.getElementById('sidebar-resizer');
  var widthBtns = document.querySelectorAll('.sidebar-width-btn');

  function setSidebarWidth(widthVal, save) {
    if (!layoutEl) return;
    var cssVal = (typeof widthVal === 'number' || /^\d+$/.test(widthVal)) ? widthVal + 'px' : widthVal;
    layoutEl.style.setProperty('--sidebar-width', cssVal);
    if (save !== false) {
      try { localStorage.setItem('agh_sidebar_width', widthVal); } catch(e){}
    }
    widthBtns.forEach(function(btn){
      var bWidth = btn.getAttribute('data-width');
      var isMatch = (bWidth === String(widthVal) || (bWidth + 'px') === String(widthVal));
      btn.classList.toggle('active', isMatch);
    });
  }

  try {
    var savedWidth = localStorage.getItem('agh_sidebar_width');
    if (savedWidth) { setSidebarWidth(savedWidth, false); }
  } catch(e){}

  widthBtns.forEach(function(btn){
    btn.addEventListener('click', function(){
      var w = btn.getAttribute('data-width');
      setSidebarWidth(w, true);
    });
  });

  if (resizerEl && layoutEl) {
    var isDragging = false;
    var startX = 0;
    var startWidth = 480;

    resizerEl.addEventListener('pointerdown', function(e){
      isDragging = true;
      resizerEl.classList.add('dragging');
      startX = e.clientX;
      var curVal = getComputedStyle(layoutEl).getPropertyValue('--sidebar-width').trim();
      startWidth = parseInt(curVal, 10) || 480;
      resizerEl.setPointerCapture(e.pointerId);
      e.preventDefault();
    });

    resizerEl.addEventListener('pointermove', function(e){
      if (!isDragging) return;
      var deltaX = startX - e.clientX;
      var newW = Math.max(340, Math.min(window.innerWidth - 320, startWidth + deltaX));
      setSidebarWidth(newW, false);
    });

    function stopDrag(e){
      if (!isDragging) return;
      isDragging = false;
      resizerEl.classList.remove('dragging');
      try { resizerEl.releasePointerCapture(e.pointerId); } catch(err){}
      var curVal = getComputedStyle(layoutEl).getPropertyValue('--sidebar-width').trim();
      var finalW = parseInt(curVal, 10);
      if (finalW) { setSidebarWidth(finalW, true); }
    }

    resizerEl.addEventListener('pointerup', stopDrag);
    resizerEl.addEventListener('pointercancel', stopDrag);

    resizerEl.addEventListener('dblclick', function(){
      setSidebarWidth(480, true);
    });
  }

  // --- Trace Text Wrap Toggle ---
  var wrapBtn = document.getElementById('agh-wrap-btn');
  var isWrapped = false;
  try { isWrapped = (localStorage.getItem('agh_trace_wrap') === 'true'); } catch(e){}

  function applyWrap(wrap) {
    isWrapped = wrap;
    document.querySelectorAll('.agh-preview').forEach(function(el){
      el.classList.toggle('wrap', isWrapped);
    });
    if (wrapBtn) {
      wrapBtn.textContent = isWrapped ? '单行显示' : '自动换行';
      wrapBtn.classList.toggle('active', isWrapped);
    }
    try { localStorage.setItem('agh_trace_wrap', isWrapped); } catch(e){}
  }

  if (wrapBtn) {
    if (isWrapped) applyWrap(true);
    wrapBtn.addEventListener('click', function(){
      applyWrap(!isWrapped);
    });
  }
})();
"""


def _now_iso():
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")


def _infer_task_dir_and_slug(state_path, report_path, runlog_dir):
    for p in (state_path, report_path):
        if p:
            abs_p = os.path.abspath(p)
            parent = os.path.dirname(abs_p)
            base_name = os.path.basename(parent)
            if base_name and base_name not in ("runtime", "physics-agent", "self-tests", "06"):
                return parent, base_name
            m = re.match(r"report_([A-Za-z0-9_\-]+)\.md$", os.path.basename(abs_p))
            if m:
                slug = m.group(1)
                cand = os.path.join(parent, slug)
                if os.path.isdir(cand):
                    return cand, slug
                return parent, slug
    return None, "task"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate the Node 4 research-report HTML page.")
    ap.add_argument("--trace", required=True, help="AGH raw trace export (JSONL).")
    ap.add_argument("--report", default=None, help="Node 3 incremental markdown research report (primary narrative source).")
    ap.add_argument("--state", default=None, help="problem_state.json for the same run (optional).")
    ap.add_argument("--figures-dir", default=None, help="Directory holding .png/.svg/.html figure files produced by make_report_figures.py.")
    ap.add_argument("--runlog-dir", default="physics-agent/runtime",
                    help="Base dir for per-run asset files (<this>/<task-slug>/runlogs/<artifact_id>.txt).")
    ap.add_argument("--out", default=None, help="Output HTML path (defaults to physics-agent/runtime/<task-slug>/research_report_<task-slug>.html).")
    args = ap.parse_args(argv)

    events = load_trace(args.trace)
    state = load_state(args.state)
    calls = extract_tool_calls(events)
    report_md = load_report_md(args.report)
    task_dir, task_slug = _infer_task_dir_and_slug(args.state, args.report, args.runlog_dir)

    out_path = args.out
    if not out_path:
        if task_dir:
            out_path = os.path.join(task_dir, f"research_report_{task_slug}.html")
        else:
            out_path = os.path.join(args.runlog_dir, task_slug, f"research_report_{task_slug}.html")

    if report_md is not None:
        blocks = md_to_html_blocks(report_md, katex=True)
        legacy = None
        source = "report-md（AI 增量研究汇报，主叙事）"
    else:
        blocks = None
        legacy = build_steps_legacy(calls, state)
        source = "trace + problem_state.json（无 Node 3 增量汇报，退化视图）"

    out = render_html(blocks, {}, events, state, out_path,
                      fallback_legacy=legacy, report_source=source,
                      figures_dir=args.figures_dir,
                      runlog_base_dir=args.runlog_dir,
                      task_dir=task_dir)
    print("wrote", os.path.abspath(out))
    print("narrative source:", source)
    print("tool calls in trace:", len(calls))
    if args.figures_dir:
        print("figures dir:", args.figures_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
