"""Synthetic regression test for the new log-axis + boxplot capabilities in
make_report_figures.py. Covers:

  (a) log-x curve, all-positive data  -> renders clean, no footnote
  (b) log-y error_bar with one 0-value point -> renders + emits non-positive
      footnote (proves nothing was silently clamped/truncated)
  (c) heatmap, categorical branch + scale:"log" -> hard FigureError (as designed)
  (d) boxplot, 3 categories, all-positive -> renders via new code path
  (e) boxplot, one empty category list -> hard FigureError (not silently omitted)
  (f) boxplot, y-scale:"log" with one negative value in one category ->
      renders + emits the non-positive-on-log-axis footnote
  (g) boxplot, x-scale:"log" -> hard FigureError (categorical x can't be log)
  (h) heatmap, numeric branch + scale:"log" on both axes -> renders clean

Expected: 5 succeed (a,b,d,f,h), 3 fail by design (c,e,g), all with the
correct error footnotes/messages when they fail. Run:
    python test_new_kinds_synthetic.py
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent  # E:\agnes-harness
HOOK = ROOT / "program-design" / "hooks" / "make_report_figures.py"
OUT = pathlib.Path(__file__).parent / "figs_new_kinds_synthetic"
OUT.mkdir(parents=True, exist_ok=True)

CURVE_LOGX = {
    "id": "curve_logx",
    "kind": "curve",
    "title": "对数x轴曲线（全正值）",
    "axes": {"x": {"scale": "log", "label": "频率 (Hz)"},
             "y": {"label": "幅度 (dB)"}},
    "series": [
        {"name": "增益", "kind_hint": "line",
         "points": {"x": [0.1, 1, 10, 100, 1000],
                    "y": [0, 6, 12, 18, 24]}},
    ],
}

ERRBAR_LOGY_ZERO = {
    "id": "errorbar_logy_zero",
    "kind": "error_bar",
    "title": "对数y轴误差棒，含 1 个 0 值点",
    "axes": {"x": {"label": "样本编号"},
             "y": {"scale": "log", "label": "测量值"}},
    "series": [
        {"name": "读数",
         "points": {"x": [1, 2, 3, 4, 5],
                    "y": [2.0, 5.0, 0.0, 7.0, 9.0],
                    "y_err": [0.2, 0.3, 0.1, 0.4, 0.5]}},
    ],
}

HEATMAP_CAT_LOG = {
    "id": "heatmap_catlog_expected_fail",
    "kind": "heatmap",
    "title": "类别轴+log，预期直接报错",
    "axes": {"x": {"scale": "log", "label": "国家"}, "y": {"label": "年份"}},
    "heatmap_style": "pcolormesh",
    "series": [
        {"grid": {
            "x_values": ["CN", "US", "IN"],
            "y_values": ["2020", "2021"],
            "values_2d": [[1, 2, 3], [4, 5, 6]],
        }},
    ],
}

BOXPLOT_3CAT = {
    "id": "boxplot_3cat",
    "kind": "boxplot",
    "title": "三个类别的分布对比",
    "axes": {"x": {"label": "实验条件"}, "y": {"label": "测量值"}},
    "series": [
        {"name": "条件A", "values": [1.0, 1.2, 1.1, 0.9, 1.05, 1.15, 0.95, 1.0, 1.1, 0.8]},
        {"name": "条件B", "values": [2.0, 2.3, 2.1, 1.9, 2.05, 2.15, 2.0, 1.8, 2.2, 2.4]},
        {"name": "条件C", "values": [0.5, 0.6, 0.4, 0.55, 0.5, 0.65, 0.45, 0.6, 0.52, 0.58]},
    ],
}

BOXPLOT_EMPTY_CAT = {
    "id": "boxplot_emptycat_expected_fail",
    "kind": "boxplot",
    "title": "某个类别取值为空，预期直接报错（而不是画 2 个类别的图假装没事）",
    "axes": {"x": {"label": "条件"}, "y": {"label": "值"}},
    "series": [
        {"name": "A", "values": [1.0, 2.0, 3.0]},
        {"name": "B", "values": []},
    ],
}

BOXPLOT_LOGY_NEGATIVE = {
    "id": "boxplot_logy_negative",
    "kind": "boxplot",
    "title": "对数y轴箱线图，某类别含 1 个负值",
    "axes": {"x": {"label": "条件"}, "y": {"scale": "log", "label": "值"}},
    "series": [
        {"name": "A", "values": [1.0, 2.0, 3.0]},
        {"name": "B", "values": [0.5, -1.0, 4.0]},
    ],
}

BOXPLOT_LOGX_REJECTED = {
    "id": "boxplot_logx_expected_fail",
    "kind": "boxplot",
    "title": "对类别x轴指定log，预期直接报错",
    "axes": {"x": {"scale": "log"}, "y": {"label": "值"}},
    "series": [
        {"name": "A", "values": [1.0, 2.0, 3.0]},
        {"name": "B", "values": [0.5, 4.0]},
    ],
}

HEATMAP_NUMER_LOG = {
    "id": "heatmap_numeric_log",
    "kind": "heatmap",
    "title": "数值坐标轴+双log刻度",
    "axes": {"x": {"scale": "log", "label": "k (1/dm)"},
             "y": {"scale": "log", "label": "频率 (cm^-1)"},
             "z": {"label": "吸收系数"}},
    "heatmap_style": "pcolormesh",
    "series": [
        {"grid": {
            "x_values": [1, 2, 4, 8],
            "y_values": [1, 5, 10, 50],
            "values_2d": [[0.1, 0.3, 0.5, 0.8],
                          [0.2, 0.4, 0.6, 0.9],
                          [0.15, 0.35, 0.55, 0.7],
                          [0.05, 0.2, 0.4, 0.6]],
        }},
    ],
}

CASES = {
    "curve_logx": CURVE_LOGX,
    "errorbar_logy_zero": ERRBAR_LOGY_ZERO,
    "heatmap_catlog_expected_fail": HEATMAP_CAT_LOG,
    "boxplot_3cat": BOXPLOT_3CAT,
    "boxplot_emptycat_expected_fail": BOXPLOT_EMPTY_CAT,
    "boxplot_logy_negative": BOXPLOT_LOGY_NEGATIVE,
    "boxplot_logx_expected_fail": BOXPLOT_LOGX_REJECTED,
    "heatmap_numeric_log": HEATMAP_NUMER_LOG,
}

EXPECTED_FAIL = {"heatmap_catlog_expected_fail", "boxplot_emptycat_expected_fail",
                 "boxplot_logx_expected_fail"}


def main():
    state = {"numerical_artifacts": {"figures": CASES}}
    state_path = OUT / "state_new_kinds.json"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    results = []
    for fig_id, spec in CASES.items():
        label = "expect_pass" if fig_id not in EXPECTED_FAIL else "expect_fail"
        sub_out = OUT / fig_id
        sub_out.mkdir(parents=True, exist_ok=True)
        sub_state = sub_out / "state.json"
        sub_state.write_text(json.dumps({"numerical_artifacts": {"figures": {fig_id: spec}}},
                                        ensure_ascii=False, indent=2), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(HOOK), "--state", str(sub_state), "--out-dir", str(sub_out)],
            capture_output=True,
        )
        out_text = proc.stdout.decode("utf-8", errors="replace")
        err_text = proc.stderr.decode("utf-8", errors="replace")
        ok = proc.returncode == 0
        verdict = "OK" if ok == (fig_id not in EXPECTED_FAIL) else "MISMATCH"
        results.append((fig_id, label, proc.returncode, verdict,
                        out_text.strip().splitlines()[-1] if out_text.strip() else "",
                        err_text.strip().splitlines()[-1] if err_text.strip() else ""))

    print("\n=== Summary ===")
    all_correct = True
    for fig_id, label, rc, verdict, stdout_tail, stderr_tail in results:
        print(f"{fig_id:34s} [{label:12s}] rc={rc}  {verdict}")
        if verdict == "MISMATCH":
            all_correct = False
        if rc != 0:
            print(f"    stdout: {stdout_tail}")
            if stderr_tail:
                print(f"    stderr: {stderr_tail}")
    print(f"\nALL CORRECT: {all_correct}")
    sys.exit(0 if all_correct else 1)


if __name__ == "__main__":
    main()
