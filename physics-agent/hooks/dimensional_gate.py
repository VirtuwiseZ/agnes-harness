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

    ODE / derivative-form equations: write each derivative term explicitly as
    SymPy's Derivative(function, variable, *count) — do NOT use hand-written
    differential notation like "du/dx" or "dv/dt". That notation is not
    parseable by the SymPy layer (it resolves to two undeclared bare symbols
    and the gate aborts with "symbols without declared dimensions", NOT a
    real PASS/FAIL verdict, as confirmed by an actual run against the 02
    walkthrough's space-diving equation). Correct form for the same 02-run
    equation:

    python dimensional_gate.py \
        --equation "Derivative(u, x) = g - rho*CD*A/(2*m)*u" \
        --dims '{"u": "specific_energy", "x": "length", "g": "acceleration",
                 "rho": "density", "CD": "dimensionless", "A": "area", "m": "mass"}'

    (Declare the differentiated function's own symbol, e.g. "u", with its own
    dimension; the derivative's independent variable, e.g. "x", is credited
    automatically from the Derivative form and also needs a declaration in
    --dims. A higher-order derivative such as D2(u, x, x) is written
    Derivative(u, x, x).)

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
    # --- SI base / fundamental ---
    "dimensionless": "",
    "mass": "kg",
    "length": "m",
    "time": "s",
    "temperature": "K",
    "current": "A",
    "amount": "mol",
    "luminous_intensity": "cd",
    # --- common derived quantities ---
    "force": "N",
    "energy": "J",
    "power": "W",
    "pressure": "Pa",
    "velocity": "m/s",
    "acceleration": "m/s^2",
    "frequency": "Hz",
    "charge": "C",
    # --- extended: geometry / kinematics / dynamics (all verified on Pint 0.26.1) ---
    "area": "m**2",
    "volume": "m**3",
    "specific_energy": "J / kg",
    "momentum": "kg * m / s",
    "angular_momentum": "kg * m**2 / s",
    "torque": "N * m",
    "moment_of_inertia": "kg * m**2",
    "spring_constant": "N / m",
    "stiffness": "N / m",
    "linear_mass_density": "kg / m",
    "surface_density": "kg / m**2",
    "density": "kg / m**3",
    "action": "J * s",
    # --- extended: fluid / transport ---
    "viscosity": "Pa * s",
    "dynamic_viscosity": "Pa * s",
    "kinematic_viscosity": "m**2 / s",
    "volumetric_flow_rate": "m**3 / s",
    "mass_flow_rate": "kg / s",
    "surface_tension": "N / m",
    "diffusivity": "m**2 / s",
    # --- extended: thermodynamics ---
    "specific_heat": "J / (kg * K)",
    "specific_heat_capacity": "J / (kg * K)",
    "heat_capacity": "J / K",
    "entropy": "J / K",
    "specific_entropy": "J / (kg * K)",
    "thermal_conductivity": "W / (m * K)",
    "heat_flux": "W / m**2",
    "heat_transfer_coefficient": "W / (m**2 * K)",
    "thermal_expansion_coefficient": "1 / K",
    "energy_density": "J / m**3",
    # --- extended: electromagnetism ---
    "voltage": "V",
    "electric_potential": "V",
    "electric_field": "V / m",
    "resistance": "ohm",
    "resistivity": "ohm * m",
    "electrical_conductivity": "S / m",
    "capacitance": "F",
    "inductance": "H",
    "magnetic_flux": "Wb",
    "magnetic_field": "T",
    "magnetic_flux_density": "T",
    "permittivity": "F / m",
    "permeability": "H / m",
}


def build_registry(dims_map_input):
    """Create a Pint registry that understands exactly the dimensions the
    caller declared.
    """
    ureg = UnitRegistry()
    for dim in dims_map_input.values():
        if dim in DIM_ALIAS:
            alias = DIM_ALIAS[dim]
        else:
            # Fallback: caller may pass a concrete unit expression directly
            # (e.g. "J/kg", "N*m") rather than a registered alias name.
            # This lets the table stay lean while still accepting arbitrary
            # composite-unit declarations without a round-trip through
            # DIM_ALIAS maintenance.
            try:
                ureg.parse_units(dim)
                continue
            except Exception:
                raise KeyError(f"Unknown dimension alias '{dim}'. "
                               f"Known: {sorted(DIM_ALIAS)}")
        if alias:  # empty string means dimensionless, nothing to parse
            ureg.parse_units(alias)
    return ureg


def _resolve_dim_label(alias, ureg, dims_map_input):
    """Return the Pint dimensionality label for a given alias, whether it is
    a registered DIM_ALIAS key or a raw unit expression passed by the caller.
    """
    if alias in DIM_ALIAS:
        concrete = DIM_ALIAS[alias]
    else:
        concrete = alias  # raw unit expression, parse it directly
    if not concrete:
        return "dimensionless"
    return str(ureg.parse_units(concrete).dimensionality)


def _collect_symbol_powers(term, dims_map_input):
    """Walk a SymPy term and return {symbol_name: net_power} for every
    declared bare symbol appearing in it, accounting for Derivative nodes
    (which contribute -n for the differentiation variable and +1 for the
    differentiated function's argument) in addition to ordinary Pow factors.
    """
    powers = {}

    def _add(sym_name, delta):
        powers[sym_name] = powers.get(sym_name, 0) + delta

    # Derivative nodes contribute -n*dim(differentiation variable) +
    # dim(the symbol whose value is being differentiated). Collect these
    # first so that the subsequent generic scans below know which
    # symbols were already accounted for and must not be double-counted
    # (e.g. a plain-Symbol `u` inside `Derivative(u, x)` would otherwise be
    # picked up a second time by the generic bare-Symbol scan below, since
    # atoms(sp.Symbol) on a term containing an unevaluated Derivative still
    # exposes `u` as a leaf symbol of the *undifferentiated* subexpression —
    # SymPy does not automatically flatten Derivative into its own power).
    derivative_symbol_names = set()
    for deriv in term.atoms(sp.Derivative):
        differentiated = deriv.expr
        if isinstance(differentiated, sp.Function):
            # differentiated is a function *application* (e.g. u(x)); the
            # symbol whose value is being differentiated is the function's
            # *name* (u), not its argument (x). Its declared dimension (if
            # any) comes from dims_map_input keyed by that function name.
            func_name = differentiated.func.__name__
            if func_name in dims_map_input:
                _add(func_name, 1)
                derivative_symbol_names.add(func_name)
        elif isinstance(differentiated, sp.Symbol):
            _add(differentiated.name, 1)
            derivative_symbol_names.add(differentiated.name)
        # SymPy's .variable_count is a tuple of (variable, count) pairs, not a
        # dict; normalize to a per-variable count dict here.
        var_counts = {}
        for var, cnt in getattr(deriv, "variable_count", ()):
            var_counts[var] = var_counts.get(var, 0) + cnt
        if not var_counts:
            for v in deriv.variables:
                var_counts[v] = var_counts.get(v, 0) + 1
        for var_sym, count in var_counts.items():
            if isinstance(var_sym, sp.Symbol) and var_sym.name in dims_map_input:
                _add(var_sym.name, -count)

    # Ordinary Pow factors (non-Derivative) — skip symbols already accounted
    # for above as the differentiated value of a Derivative node.
    for node in term.atoms(sp.Pow):
        if isinstance(node.base, sp.Symbol) and node.base.name in dims_map_input \
                and node.base.name not in derivative_symbol_names:
            _add(node.base.name, node.exp)

    # Bare Symbol factors (first power) that are not already captured above,
    # and not the differentiated value of a Derivative node either.
    for sym in term.atoms(sp.Symbol):
        if sym.name not in dims_map_input or sym.name in derivative_symbol_names:
            continue
        if sym.name in powers:
            continue
        if not any(node.base == sym for node in term.atoms(sp.Pow)):
            _add(sym.name, 1)

    # Drop zero-power entries
    return {k: v for k, v in powers.items() if v != 0}


def _dimension_key(dimensionality):
    """Return a deterministic, hashable key for a Pint dimensionality, robust
    to however the underlying Quantity was constructed (build order, etc.).
    Comparison must always go through this key, never through the raw
    dimensionality string, which is not guaranteed to be in a canonical
    ordering across different construction paths.
    """
    return tuple(sorted(dimensionality.items()))


def _term_dimension_label(term, ureg, dims_map_input):
    """Return a readable, Pint-reduced dimension label for one SymPy term,
    plus the deterministic comparison key. Comparison (homogeneity checks)
    must use the key, not the string; the string is display-only.
    """
    powers = _collect_symbol_powers(term, dims_map_input)

    if not powers:
        return "dimensionless", _dimension_key(ureg.Quantity(1).units.dimensionality)

    q = ureg.Quantity(1)
    for name, power in powers.items():
        q = q * ureg.parse_units(
            DIM_ALIAS.get(dims_map_input[name], dims_map_input[name])
        ) ** power
    return str(q.units.dimensionality), _dimension_key(q.units.dimensionality)


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

    # Protect declared symbol names that collide with SymPy built-in
    # constants/functions (e.g. "E" -> Exp1, "I" -> ImaginaryUnit,
    # "N"/"O"/"Q"/"S" -> other built-ins) from being silently reinterpreted
    # by sympify: the caller has explicitly declared these as dimensional bare
    # symbols, so they must parse back to sp.Symbol, not to a SymPy built-in.
    # Only override names that sympify would otherwise mis-resolve to a
    # non-Symbol (checked empirically, not assumed); ordinary identifier
    # names (e.g. "u" in an ODE context, usable as u(x)) are left to
    # sympify's default behavior so function-form differentiated symbols
    # like "u" in Derivative(u(x), x) still parse correctly.
    symbol_locals = {}
    for name in dims_map_input:
        if not getattr(sp.sympify(name), "is_Symbol", False):
            symbol_locals[name] = sp.Symbol(name)

    if args.equation:
        try:
            lhs_str, rhs_str = [s.strip() for s in args.equation.split("=")]
            combined = sp.expand(sp.sympify(lhs_str, locals=symbol_locals)
                                 - sp.sympify(rhs_str, locals=symbol_locals))
            label = args.equation
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"verdict": "ERROR", "reason": f"parse error: {e}"}))
            return 2
    elif args.expression:
        try:
            combined = sp.expand(sp.sympify(args.expression, locals=symbol_locals))
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
    # SymPy's free_symbols does NOT include the argument of a Derivative
    # written in function form (e.g. Derivative(u(x), x) -> only {x});
    # walk every Derivative node explicitly and add the differentiated
    # function's argument symbol, if it is a plain Symbol, so it is
    # required to have a declared dimension like any other bare symbol.
    for deriv in combined.atoms(sp.Derivative):
        diff_target = deriv.expr
        if isinstance(diff_target, sp.Function):
            for arg in diff_target.args:
                if isinstance(arg, sp.Symbol):
                    bare_symbols.add(arg.name)
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
    label_keys = []
    key_to_label = {}
    for t in terms:
        lbl, key = _term_dimension_label(t, ureg, dims_map_input)
        term_labels[str(sp.cancel(t))] = lbl
        key_to_label[key] = lbl
        if not is_transcendental_term(t):
            label_keys.append(key)

    homogeneous = len(set(label_keys)) == 1
    mismatching = []
    if not homogeneous:
        from collections import Counter
        counts = Counter(label_keys)
        majority_key, _ = counts.most_common(1)[0]
        majority = key_to_label[majority_key]
        for t in terms:
            if is_transcendental_term(t):
                continue
            _lbl, tkey = _term_dimension_label(t, ureg, dims_map_input)
            if tkey != majority_key:
                mismatching.append(str(sp.cancel(t)))

    warnings = []
    dimless_key = _dimension_key(ureg.Quantity(1).units.dimensionality)
    for func_name, arg in find_transcendental_args(combined):
        _arg_lbl, arg_key = _term_dimension_label(arg, ureg, dims_map_input)
        if arg_key != dimless_key:
            warnings.append(
                f"{func_name}({str(arg)}) argument is not dimensionless "
                f"(dimension: {_arg_lbl}); verify physical interpretation. "
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
