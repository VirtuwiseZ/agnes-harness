import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))

st["stage"] = "node_3_report"
st["report"]["conclusion"] = (
    "NOT feasible as a significant fuel-saving strategy - and run #2 STRENGTHENS "
    "run #1's 'no' answer along two genuinely new dimensions, both quantified, not asserted: "
    "(1) the single head-on (closing) encounter is proven IMPOSSIBLE to decelerate the "
    "spacecraft by an EXACT algebraic identity (v_out^2 - v_inf^2 = v_moon^2 + 2*v_inf*v_moon + "
    "2*v_moon(v_inf+v_moon)(1-cos(delta)) > 0 for all delta in (0,pi), v_moon>0), verified "
    "symbolically with sympy, not just numerically over 4 data points; computed max deflection "
    "is only 0.02-0.45 deg even skimming a moon's surface, so the effect is a tiny speed-UP "
    "of order 0.0001-0.001%, giving a NEGATIVE propellant saving (-0.00002% to -0.00029%). "
    "(2) A two-encounter CHAINED construction - the one mechanism that could plausibly have "
    "turned a single-encounter 'no' into a meaningful 'yes' - is exhaustively enumerated over "
    "all 12 ordered moon pairs (A!=B), and the SAME invariant applied recursively to each "
    "encounter shows it ALSO cannot decelerate: every one of the 12 pairs gives v_out_2 > v_inf "
    "by +0.0003 to +0.0009 km/s, i.e. a tiny net speed-UP, not a deceleration, so the chained "
    "construction's 'saving' is likewise negative (-0.0002% to -0.0005%). (3) A NEW this run, "
    "an overtaking-geometry CONTROL case (parallel incoming vectors, not anti-parallel), "
    "computed for all 4 moons after an independent exact-vector re-derivation caught and "
    "corrected a sign error in the initial closed-form formula: at v_inf=20 km/s all 4 Galilean "
    "moons are SLOWER than the spacecraft (Sub-case D), giving a modest net speed LOSS of only "
    "0.0002-0.46 km/s (Io the largest, since its v_moon~17.33 km/s is closest to 20 km/s), "
    "translating to a propellant saving of at most +0.27% - still 37x short of the 10% "
    "'significant saving' threshold, and 2.2x short of the 1 km/s delta-v threshold. "
    "VERDICT: no single-encounter arrangement (head-on OR overtaking) AND no two-encounter "
    "chained construction produces a significant fuel saving at the given 20 km/s approach speed; "
    "the closest-approaching case (Io, overtaking geometry) is the least-bad option by a wide "
    "margin but still fails both acceptance thresholds."
)
st["report"]["traceability"] = {
    "head-on invariant (exact algebraic identity + sympy check)": "jovian_flyby_model_run2.head_on_invariant_check / symbolic_invariant_proof; dimensional gate GATE1-GATE3 all PASS (audit: run2_node2b_dimensional_gate)",
    "all main-case head-on numbers (v_out, delta, per-moon)": "problem_state_2013A_jupiter_flyby_run2.json numerical_artifacts.head_on_tightest_flyby_all_moons (audit: run2_node2b_model_run)",
    "overtaking control case (v_out, per-moon, Sub-case D)": "jovian_flyby_model_run2.v_out_closed_form head_on=False branch, verified against verify_overtake_vectors.py independent exact-vector simulation before being trusted; numbers in numerical_artifacts.overtaking_control_tightest_flyby_all_moons",
    "chained two-encounter construction (all 12 ordered pairs)": "jovian_flyby_model_run2.chained_two_encounter / best_chained_pair; numbers in numerical_artifacts.chained_all_12_pairs",
    "direct-capture delta-v baseline + Tsiolkovsky propellant fraction": "jovian_flyby_model_run2.direct_capture_delta_v / propellant_fraction; numbers in numerical_artifacts.capture_baseline_io_scale / capture_baseline_ganymede_scale",
    "boundary/degenerate-limit verdict": "boundary_gate_run2_result.json, verdict PASS, 3 cases + monotonic mu_m sweep (audit: run2_node2b_boundary_gate)",
    "mu_jupiter independent cross-check vs. published periods": "jovian_flyby_model_run2.kepler_period_check; numbers in numerical_artifacts.kepler_period_cross_check (rel.err < 0.04% for all 4 moons) (audit: run2_node2b_kepler_cross_check)",
    "figure set (F1-F3, redesigned against run #1's near-blank failure mode)": "numerical_artifacts.figures_run2 + run2_node27_figures audit record",
    "constant provenance (mu_j, G, moon a/M/R, Isp)": "jupiter_flyby_params_run2.json + Node 1.5 audit record (Level-3 IAU/JPL standard values, re-confirmed this run, no live source reachable in this environment)"
}

audit_log.append_record(state, "run2_node3_report_written", {
    "file": "program-design/runtime/report_2013A_jupiter_flyby_run2.md",
    "note": "full independent re-analysis, conclusion-first structure, per report_structure_guide.md; sections: abstract/intro/assumptions/model-invariant/control-case/chained-case/figures/verification/results/strengths-weaknesses/discussion"
})

# internal_prior divergence check (Node 1a sketch vs. verified run-#2 result)
prior_expected = "prior sketched a possible 3-6 km/s net velocity change for the CHAINED construction, enough to matter against a ~14 km/s capture burn"
actual = "chained_all_12_pairs: max net speed change = +0.000872 km/s (a speed-UP, not a deceleration); overtaking control max = -0.46 km/s (Io, a mild speed loss, not a 3-6 km/s gain)"
divergence = True  # prior's hoped-for 'yes' outcome did not materialize; verified result is a clean, stronger 'no' than even the single-encounter-only analysis suggested
audit_log.append_record(state, "run2_internal_prior_divergence_check", {
    "prior_expected": prior_expected,
    "actual_verified": actual,
    "divergence_found": divergence,
    "note": "Divergence CONFIRMED and this is the expected, healthy outcome of the prior-then-verify protocol: the Node 1a sketch HOPED the chained construction might reach 3-6 km/s net velocity change (a 'maybe-yes'), but the rigorous computation (invariant applied recursively per encounter) shows it reaches at most +0.0009 km/s in the WRONG direction (a speed-up, not a speed-down). The prior was a genuine hypothesis, not a smuggled answer; the verified result falsifies it, which is exactly what the protocol's internal_prior field is for. Logged here per protocol; NOT to be quoted as a result anywhere in the report/HTML, only as this divergence-check record."
})

json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("node 3 (report) recorded; stage:", st["stage"])
