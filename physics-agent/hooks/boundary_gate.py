"""
boundary_gate.py
================
Deterministic boundary / degenerate-limit verification hook.

Purpose (per project consensus, "Boundary Gate" defense line):
    Before a modeling result is trusted, the governing equations or
    numerical model must be probed under physically degenerate limits.
    This script automates that probe: given a callable model function
    (or a callable that itself takes a dict of parameters), a named
    primary result, and a spec file enumerating the boundary cases to
    test, it runs each case, checks the result against a stated
    physical expectation, and reports PASS/FAIL per case + overall.

Design (tool-priority principle, per updated consensus):
    - Numerical evaluation, finiteness checks: NumPy (standard, mature).
    - No home-rolled numerical method; the model callable itself is
      expected to already be a solved/working function (e.g. wrapping
      a SciPy ODE solve), so this hook stays thin: it is a *harness*
      that drives boundary-case probing, not a physics solver.

Protocol:
  1. Caller provides a boundary spec JSON file describing:
     - "model_module": importable Python module path containing `run_model(params: dict) -> float`
     - "primary_result": name of the result key inside `run_model`'s return dict
     - "cases": list of {"name": ..., "params": {...}, "expectation": "finite" | "zero" | "nonnegative" | "monotonic_increase" | "monotonic_decrease" | "bounded_by:<float>", ...}
  2. For each case the hook:
       - calls run_model(params), extracts the primary result value,
       - checks it against the expectation,
       - records the actual value + pass/fail.
  3. If "monotonic_*" is used, the spec must also provide a
     "sweep_param" (name of the parameter to sweep) and "sweep_values"
     (list); the hook evaluates the primary result across the sweep and
     checks the ordering.

Usage:
    python boundary_gate.py --spec boundary_spec.json
    # JSON emitted to stdout:
    # {"verdict": "PASS"|"FAIL", "cases": [...], "sweep": {...}}

Exit codes: 0 = all PASS, 1 = any FAIL, 2 = usage/load error.

NOTE — dependency boundary: NumPy/SciPy usage is delegated; this script
itself only implements the "boundary-probing protocol" glue described in
the boundary-verification method template.
"""

import argparse
import importlib
import json
import math
import sys


def load_model(model_module_name):
    module = importlib.import_module(model_module_name)
    if not hasattr(module, "run_model"):
        raise AttributeError(f"{model_module_name} has no run_model(params) callable")
    return module.run_model


def _check_single(actual, expectation):
    """Return (passed, reason)."""
    if expectation == "finite":
        return math.isfinite(actual), "expected finite value"
    if expectation == "zero":
        return abs(actual) < 1e-12, "expected ~0"
    if expectation == "nonnegative":
        return actual >= -1e-12, "expected >= 0"
    if expectation.startswith("bounded_by:"):
        bound = float(expectation.split(":", 1)[1])
        return abs(actual) <= bound, f"expected |value| <= {bound}"
    return False, f"unknown expectation '{expectation}'"


def check_cases(run_model, spec, cases):
    results = []
    all_passed = True
    for case in cases:
        name = case["name"]
        params = case["params"]
        expectation = case.get("expectation", "finite")
        try:
            out = run_model(params)
            if isinstance(out, dict):
                primary_key = spec.get("primary_result", list(out.keys())[0])
                actual = out[primary_key]
            else:
                actual = out
        except Exception as e:  # noqa: BLE001
            results.append({"name": name, "passed": False, "actual": None,
                           "expectation": expectation, "error": str(e)})
            all_passed = False
            continue

        passed, reason = _check_single(float(actual), expectation)
        results.append({"name": name, "passed": passed, "actual": float(actual),
                        "expectation": expectation, "reason": reason})
        if not passed:
            all_passed = False
    return all_passed, results


def check_sweep(run_model, spec, sweep_cfg):
    """Monotonicity check across a parameter sweep."""
    sweep_param = sweep_cfg["param"]
    sweep_values = sweep_cfg["values"]
    order = sweep_cfg.get("order", "increase")  # "increase" or "decrease"
    base_params = dict(sweep_cfg.get("base_params", {}))
    primary_key = spec.get("primary_result")

    values_seen = []
    ok = True
    for v in sweep_values:
        p = dict(base_params)
        p[sweep_param] = v
        try:
            out = run_model(p)
            actual = out[primary_key] if isinstance(out, dict) else out
            values_seen.append({"param_value": v, "result": float(actual)})
        except Exception as e:  # noqa: BLE001
            return False, {"error": str(e)}, values_seen

    numeric = [d["result"] for d in values_seen]
    if order == "increase":
        ok = all(b >= a - 1e-12 for a, b in zip(numeric, numeric[1:]))
    else:
        ok = all(b <= a + 1e-12 for a, b in zip(numeric, numeric[1:]))
    return ok, {"param": sweep_param, "order": order, "observed": values_seen}, values_seen


def main():
    p = argparse.ArgumentParser(description="Boundary/degenerate-limit verification gate.")
    p.add_argument("--spec", required=True, help="Path to boundary spec JSON file.")
    args = p.parse_args()

    try:
        with open(args.spec, encoding="utf-8") as f:
            spec = json.load(f)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"verdict": "ERROR", "reason": f"cannot load spec: {e}"}))
        return 2

    try:
        run_model = load_model(spec["model_module"])
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"verdict": "ERROR", "reason": f"cannot load model module: {e}"}))
        return 2

    overall_passed = True
    case_results = []

    cases = spec.get("cases", [])
    if cases:
        ok, case_results = check_cases(run_model, spec, cases)
        overall_passed = overall_passed and ok

    sweep_result = None
    if spec.get("sweep"):
        sweep_ok, sweep_detail, _ = check_sweep(run_model, spec, spec["sweep"])
        sweep_result = {"passed": sweep_ok, **sweep_detail}
        overall_passed = overall_passed and sweep_ok

    verdict = "PASS" if overall_passed else "FAIL"
    out = {
        "verdict": verdict,
        "cases": case_results,
        "sweep": sweep_result,
    }
    print(json.dumps(out, indent=2))
    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
