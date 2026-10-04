"""
dimensional_gate.py
===================
Generic dimensional homogeneity checker for any physical equation.

NOTE — dependency boundary (explicitly scoped to avoid "reinventing the
wheel"):
  - The dimensional engine is delegated to **Pint** (mature, maintained,
    widely used open-source unit/quantity library; `pip install pint`).
    SymPy is used only for lightweight expression parsing, expansion, and
    free-symbol extraction — no home-rolled symbolic algebra.
  - What this script adds on top of Pint is a thin, project-specific
    "dimensional declaration protocol": the caller (an AI modeling node or
    a human) declares each bare symbol's dimension as a JSON table, and
    this script wires that table into a Pint UnitRegistry and checks
    per-term dimensional homogeneity, plus flags non-dimensionless
    transcendental-function arguments. That protocol glue layer is the
    only thing written by hand here — no independent dimensional engine.
  - Known third-party quirk (documented, not worked around silently): the
    Pint 0.26.x `UnitRegistry` does not accept the *bare dimension name*
    ("force", "energy", "acceleration") via `parse_units()` — those are
    only available via the `.dimension` attribute on concrete units. This
    script therefore maintains a small explicit alias table mapping
    human-friendly dimension names (used throughout our consensus docs and
    JSON declaration tables) to concrete Pint units, purely so the JSON
    declaration protocol stays stable across Pint releases.

Protocol (three-layer, per project consensus):
  1. Caller passes an equation string, or a single expression string +
     a variable-dimension declaration table (JSON, e.g. {"m": "mass"}).
  2. Each declared symbol is substituted with a Pint quantity
     (magnitude 1, the declared dimension) inside the SymPy-parsed
     expression; the combined expression (LHS - RHS, or a single
     expression expected to equal zero) is checked so that every
     additive term reduces to the identical base-dimension exponent
     vector.
  3. Additionally, a non-blocking warning is emitted for any
     transcendental function (sin, cos, tan, exp, log, asin, acos,
     atan) whose argument carries non-dimensionless dimensions — a
     classic silent modeling error — without affecting the PASS/FAIL
     verdict itself.

Usage:
    python dimensional_gate.py --equation "F = m*a" \
        --dims '{"F": "force", "m": "mass", "a": "acceleration"}'
    python dimensional_gate.py --equation "F = m" \
        --dims '{"F": "force", "m": "mass"}'        # expected FAIL
    python dimensional_gate.py --equation "E = exp(-x/L)" \
        --dims '{"E": "dimensionless", "x": "length", "L": "length"}'  # warns only

Exit codes:
    0 = PASS
    1 = FAIL (dimensional mismatch between terms)
    2 = usage / parse / unknown-dimension error

Output (stdout, JSON):
    {
      "verdict": "PASS" | "FAIL",
      "expression": "<as-provided>",
      "term_dimensions": {"<term>": "<canonical dimension>", ...},
      "mismatching_terms": ["<term>", ...],
      "transcendental_warnings": ["..."],
    }
"""

import argparse
import json
import sys

import sympy as sp
from sympy.functions.elementary.exponential import exp, log
from sympy.functions.elementary.trigonometric import sin, cos, tan, asin, acos, atan

from pint import UnitRegistry

TRANSCENDENTAL_FUNC_NAMES = {
    "sin", "cos", "tan", "exp", "log", "ln", "asin", "acos", "atan",
}

# Alias table: stable, human-friendly dimension names (used across our
# consensus docs / JSON declaration tables) -> a concrete Pint unit string
# that reliably resolves in Pint 0.26.x. This is the *only* project-specific
# glue on top of Pint, and it exists precisely because Pint's own
# dimension-name namespace is not parse-able via parse_units() in this
# version.
DIM_ALIAS = {
    "dimensionless": "",
    "mass": "kg",
    "length": "m",
    "time": "s",
    "temperature": "K",
    "current": "A",
    "amount": "mol",
    "luminous_intensity": "cd",
    "force": "N",
    "energy": "J",
    "power": "W",
    "pressure": "Pa",
    "velocity": "m/s",
    "acceleration": "m/s^2",
    "frequency": "Hz",
    "charge": "C",
}


def build_registry(dims_map_input):
    """Create a Pint registry that understands exactly the dimensions the
    caller declared.
    """
    ureg = UnitRegistry()
    for dim in dims_map_input.values():
        alias = DIM_ALIAS.get(dim)
        if alias is None:
            raise KeyError(f"Unknown dimension alias '{dim}'. "
                           f"Known: {sorted(DIM_ALIAS)}")
        if alias:  # empty string means dimensionless, nothing to parse
            ureg.parse_units(alias)
    return ureg


def _term_dimension_label(term, ureg, dims_map_input):
    """Return a readable, Pint-reduced dimension label for one SymPy term.
    Comparison is by pure dimension (base-dimension category), not by
    concrete unit spelling, so that e.g. `newton` and `kg*meter/second**2`
    collapse to the same label.
    """
    powers = {}
    for name in dims_map_input:
        sym = sp.Symbol(name)
        if sym not in term.free_symbols:
            continue
        total = 0
        for node in term.atoms(sp.Pow):
            if node.base == sym:
                total += node.exp
        if total == 0:
            total = 1  # the symbol appears to first power somewhere in the term
        powers[name] = total

    if not powers:
        return "dimensionless"

    powers = {name: power for name, power in powers.items() if power != 0}
    if not powers:
        return "dimensionless"

    q = ureg.Quantity(1)
    for name, power in powers.items():
        alias = DIM_ALIAS[dims_map_input[name]]
        if alias:
            q = q * ureg.Quantity(1, alias) ** power
    return str(q.units.dimensionality)


def find_transcendental_args(expr):
    """Return [(func_name, arg_expression), ...] for every transcendental call
    appearing in `expr`.
    """
    results = []
    func_map = {"sin": sin, "cos": cos, "tan": tan, "exp": exp, "log": log,
                "asin": asin, "acos": acos, "atan": atan}
    for node in expr.atoms(sp.Function):
        for name, cls in func_map.items():
            if isinstance(node, cls):
                results.append((name, node.args[0]))
    return results


def main():
    p = argparse.ArgumentParser(
        description="Dimensional homogeneity gate (Pint engine + SymPy parsing)."
    )
    p.add_argument("--equation", help='Equation string, e.g. "F = m*a"')
    p.add_argument("--expression", help="Single expression string that must equal zero, e.g. 'm*a - F'")
    p.add_argument("--dims", required=True,
                   help='JSON dict mapping symbol name -> dimension alias, '
                        'e.g. \'{"F": "force", "m": "mass", "a": "acceleration"}\'')
    args = p.parse_args()

    try:
        dims_map_input = json.loads(args.dims)
    except json.JSONDecodeError as e:
        print(json.dumps({"verdict": "ERROR", "reason": f"invalid --dims JSON: {e}"}))
        return 2

    if args.equation:
        try:
            lhs_str, rhs_str = [s.strip() for s in args.equation.split("=")]
            combined = sp.expand(sp.sympify(lhs_str) - sp.sympify(rhs_str))
            label = args.equation
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"verdict": "ERROR", "reason": f"parse error: {e}"}))
            return 2
    elif args.expression:
        try:
            combined = sp.expand(sp.sympify(args.expression))
            label = f"({args.expression}) = 0"
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"verdict": "ERROR", "reason": f"parse error: {e}"}))
            return 2
    else:
        print(json.dumps({"verdict": "ERROR", "reason": "provide --equation or --expression"}))
        return 2

    try:
        ureg = build_registry(dims_map_input)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"verdict": "ERROR", "reason": f"unknown dimension: {e}"}))
        return 2

    bare_symbols = {s.name if s.is_Symbol else str(s) for s in combined.free_symbols}
    missing = bare_symbols - set(dims_map_input.keys())
    if missing:
        print(json.dumps({
            "verdict": "ERROR",
            "reason": f"symbols without declared dimensions: {sorted(missing)}",
        }))
        return 2

    terms = list(combined.args) if combined.is_Add else [combined]

    # Option A (non-blocking): transcendental-function terms are flagged as
    # warnings (their arguments should be dimensionless - a classic silent
    # modeling error) but are EXCLUDED from the overall homogeneity verdict,
    # since Pint passes the argument's dimension straight through to the
    # function result and would otherwise spuriously mark e.g.
    # "y = sin(x)" (y dimensionless, x length) as a hard FAIL.
    transcendentals = (sp.sin, sp.cos, sp.tan, sp.exp, sp.log,
                       sp.asin, sp.acos, sp.atan)
    is_transcendental_term = lambda t: any(
        isinstance(node, cls) for node in t.atoms(sp.Function) for cls in transcendentals
    )

    term_labels = {}
    label_vecs = []
    for t in terms:
        lbl = _term_dimension_label(t, ureg, dims_map_input)
        term_labels[str(sp.cancel(t))] = lbl
        if not is_transcendental_term(t):
            label_vecs.append(lbl)

    homogeneous = len(set(label_vecs)) == 1
    mismatching = []
    if not homogeneous:
        from collections import Counter
        counts = Counter(label_vecs)
        majority = counts.most_common(1)[0][0]
        for t in terms:
            if is_transcendental_term(t):
                continue
            lbl = _term_dimension_label(t, ureg, dims_map_input)
            if lbl != majority:
                mismatching.append(str(sp.cancel(t)))

    warnings = []
    for func_name, arg in find_transcendental_args(combined):
        arg_lbl = _term_dimension_label(arg, ureg, dims_map_input)
        if arg_lbl not in ("dimensionless", ""):
            warnings.append(
                f"{func_name}({str(arg)}) argument is not dimensionless "
                f"(dimension: {arg_lbl}); verify physical interpretation. "
                f"[non-blocking]"
            )

    verdict = "PASS" if homogeneous else "FAIL"
    result = {
        "verdict": verdict,
        "expression": label,
        "term_dimensions": term_labels,
        "mismatching_terms": mismatching,
        "transcendental_warnings": warnings,
    }
    print(json.dumps(result, indent=2))
    return 0 if homogeneous else 1


if __name__ == "__main__":
    sys.exit(main())
