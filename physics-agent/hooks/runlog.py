"""runlog.py
=========
One-shot asset-file writer for ③第 4 条 4c (10/12): the per-run "full
source + verbatim stdout/stderr" archive that lives OUTSIDE
`problem_state.json` and OUTSIDE the Node 4 HTML body (Q3 定论: not
inlined into the HTML itself, but available as a plain-text file the
browser can link to directly, no JS lazy-loading needed).

File written:
    physics-agent/runtime/<task-slug>/runlogs/<artifact_id>.txt

Layout (source code and run log share ONE file, not two — see ③第 4 条
4c's rationale: "点开看代码与调用运行记录" in the original A4 spec is
the same single click action, one file carrying "this call's complete
record" (code + input + output + errors) fits that intent better than
two separately-named files, and avoids maintaining two path-naming
rules that could drift apart — the same "write it in two places"
disease 1009 §2.5 repeatedly flags):

    # script_path: <relative path of the script actually invoked>
    # stdin_or_argv: <verbatim command line / input>
    # exit_code: <n>
    # iteration_index: <n>
    # artifact_id: <the audit record's content-addressed id>

    # ---- source (only when script_path points at a file created for
    #      THIS task, i.e. not one of physics-agent/hooks/'s existing
    #      general-purpose hooks — see module-level docstring above) ----
    <full source, or the literal text "(inline command, no named file)"
     when script_path is "inline">

    # ---- stdout ----
    <full, verbatim stdout captured for this call>

    # ---- stderr ----
    <full, verbatim stderr captured for this call>

This module deliberately does NOT call `audit_log.append_record` or
touch `problem_state.json` in any way — it is a separate, one-shot
write to a separate, per-task asset directory.  Callers decide, at
the moment a script-execution audit record (4b's 6-key record) has
just been written, whether this task's `script_path` is a
problem-specific new file (vs. a pre-existing general hook in
`physics-agent/hooks/`), and only call `write_runlog()` in the former
case — it is an opt-in follow-up write, not something `audit_log.py`
does on your behalf for every record.
"""

import os

_RUNLOG_DIR_NAME = "runlogs"


def write_runlog(task_slug: str, script_path: str, stdin_or_argv: str,
                 stdout_full: str, stderr_full: str, exit_code,
                 iteration_index, artifact_id: str,
                 source_code: str | None = None,
                 base_runtime_dir: str = "physics-agent/runtime") -> str:
    """Write one runlog asset file.  `base_runtime_dir` is a relative
    (or absolute) path to the `runtime/` directory so tests /
    other machines can point it anywhere; the default matches this
    project's current layout.  `source_code` is the full text of the
    script when `script_path` is a file created for this task (None
    means "inline command, no source to archive", in which case the
    literal marker text is written instead).  Returns the absolute
    path of the file just written."""
    runlog_dir = os.path.join(base_runtime_dir, task_slug, _RUNLOG_DIR_NAME)
    os.makedirs(runlog_dir, exist_ok=True)
    out_path = os.path.join(runlog_dir, f"{artifact_id}.txt")

    source_block = source_code if source_code is not None else \
        "(inline command, no named file)"
    lines = [
        f"# script_path: {script_path}",
        f"# stdin_or_argv: {stdin_or_argv}",
        f"# exit_code: {exit_code}",
        f"# iteration_index: {iteration_index}",
        f"# artifact_id: {artifact_id}",
        "",
        "# ---- source ----",
        source_block,
        "",
        "# ---- stdout ----",
        stdout_full,
        "",
        "# ---- stderr ----",
        stderr_full,
    ]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return os.path.abspath(out_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 1:
        print(__doc__)
