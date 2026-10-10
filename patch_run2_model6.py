p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

old = '''    head_on_all = perigee_sweep_all_moons_all_geometries(r_p_factors)["head_on"]
    overtake_all = perigee_sweep_all_moons_all_geometries(r_p_factors)["overtaking"]

    single_best_dec = {name: rows[0] for name, rows in head_on_all.items()}  # r_p_factor=1.0 row = tightest flyby
    single_worst_dec = {name: rows[-1] for name, rows in head_on_all.items()}  # r_p_factor=10.0 row = most distant
    overtake_shown = {name: single_encounter_all_moons("overtaking", r_p_factor=1.0)[name] for name in _moon_names()}

    orbits = {label: {"a_m": c["a_m"]} for label, c in CAPTURE_ORBITS.items()}
    capture_baseline = {}
    for label, c in orbits.items():
        dv = direct_capture_delta_v(c["a_m"])
        frac = propellant_fraction(dv)
        capture_baseline[label] = {
            "delta_v_direct_m_s": dv,
            "propellant_fraction_direct": frac,
            "delta_v_assisted_headon_m_s": None,  # filled below, per-moon
            "delta_v_assisted_overtaking_m_s": None,
            "delta_v_assisted_chained_best_m_s": None,
        }

    for label, c in orbits.items():
        for name, d in single_best_dec.items():
            v_out_m_s = d["v_out_m_s"]
            v_peri_assisted = math.sqrt(v_out_m_s ** 2 + 2.0 * MU_J / c["a_m"])
            v_circ = math.sqrt(MU_J / c["a_m"])
            dv_assisted = v_peri_assisted - v_circ
            saving_frac = propellant_fraction(capture_baseline[label]["delta_v_direct_m_s"]) - propellant_fraction(dv_assisted)
            capture_baseline[label][f"assisted_headon_{name}"] = {
                "delta_v_m_s": dv_assisted,
                "propellant_saving_fraction_vs_direct": saving_frac,
            }
        for name, d in overtake_shown.items():
            v_out_m_s = d["v_out_m_s"]
            v_peri_assisted = math.sqrt(v_out_m_s ** 2 + 2.0 * MU_J / c["a_m"])
            v_circ = math.sqrt(MU_J / c["a_m"])
            dv_assisted = v_peri_assisted - v_circ
            saving_frac = propellant_fraction(capture_baseline[label]["delta_v_direct_m_s"]) - propellant_fraction(dv_assisted)
            capture_baseline[label][f"assisted_overtaking_{name}"] = {
                "delta_v_m_s": dv_assisted,
                "propellant_saving_fraction_vs_direct": saving_frac,
            }

    chained_all = best_chained_pair(1.0, 1.0)
    for label, c in orbits.items():
        for pair in chained_all:
            v_out_2_m_s = pair["encounter_2"]["v_out_m_s"]
            v_peri_assisted = math.sqrt(v_out_2_m_s ** 2 + 2.0 * MU_J / c["a_m"])
            v_circ = math.sqrt(MU_J / c["a_m"])
            dv_assisted = v_peri_assisted - v_circ
            saving_frac = propellant_fraction(capture_baseline[label]["delta_v_direct_m_s"]) - propellant_fraction(dv_assisted)
            key = f"assisted_chained_{pair['moon_A']}_{pair['moon_B']}"
            capture_baseline[label][key] = {
                "delta_v_m_s": dv_assisted,
                "propellant_saving_fraction_vs_direct": saving_frac,
            }

    kepler_checks = {name: kepler_period_check(name) for name in _moon_names()}

    return {
        "head_on_sweep_all_moons_all_perigees": head_on_all,
        "overtaking_sweep_all_moons_all_perigees": overtake_all,
        "single_encounter_tightest_flyby": single_best_dec,
        "overtaking_control_case_tightest_flyby": overtake_shown,
        "capture_baseline": capture_baseline,
        "chained_all_pairs": chained_all,
        "kepler_period_cross_check": kepler_checks,
    }'''

new = '''    head_on_all = perigee_sweep_all_moons_all_geometries(r_p_factors)["head_on"]
    overtake_all = perigee_sweep_all_moons_all_geometries(r_p_factors)["overtaking"]

    single_best_dec = {name: rows[0] for name, rows in head_on_all.items()}  # r_p_factor=1.0 row = tightest flyby
    overtake_shown = {name: single_encounter_all_moons("overtaking", r_p_factor=1.0)[name] for name in _moon_names()}

    orbits = {label: {"a_m": c["a_m"]} for label, c in CAPTURE_ORBITS.items()}
    capture_baseline = {}
    for label, c in orbits.items():
        dv = direct_capture_delta_v(c["a_m"])
        frac = propellant_fraction(dv)
        capture_baseline[label] = {
            "delta_v_direct_m_s": dv,
            "propellant_fraction_direct": frac,
        }

    def _assisted_saving(c_a_m, v_out_m_s, base_dv_m_s):
        v_peri_assisted = math.sqrt(v_out_m_s ** 2 + 2.0 * MU_J / c_a_m)
        v_circ = math.sqrt(MU_J / c_a_m)
        dv_assisted = v_peri_assisted - v_circ
        saving_frac = propellant_fraction(base_dv_m_s) - propellant_fraction(dv_assisted)
        return {"delta_v_m_s": dv_assisted, "propellant_saving_fraction_vs_direct": saving_frac}

    for label, c in orbits.items():
        base_dv = capture_baseline[label]["delta_v_direct_m_s"]
        for name, d in single_best_dec.items():
            capture_baseline[label][f"assisted_headon_{name}"] = _assisted_saving(c["a_m"], d["v_out_m_s"], base_dv)
        for name, d in overtake_shown.items():
            capture_baseline[label][f"assisted_overtaking_{name}"] = _assisted_saving(c["a_m"], d["v_out_m_s"], base_dv)

    chained_all = best_chained_pair(1.0, 1.0)
    for label, c in orbits.items():
        base_dv = capture_baseline[label]["delta_v_direct_m_s"]
        for pair in chained_all:
            v_out_2_m_s = pair["encounter_2"]["v_out_m_s"]
            key = f"assisted_chained_{pair['moon_A']}_{pair['moon_B']}"
            capture_baseline[label][key] = _assisted_saving(c["a_m"], v_out_2_m_s, base_dv)

    kepler_checks = {name: kepler_period_check(name) for name in _moon_names()}

    return {
        "head_on_sweep_all_moons_all_perigees": head_on_all,
        "overtaking_sweep_all_moons_all_perigees": overtake_all,
        "single_encounter_tightest_flyby": single_best_dec,
        "overtaking_control_case_tightest_flyby": overtake_shown,
        "capture_baseline": capture_baseline,
        "chained_all_pairs": chained_all,
        "kepler_period_cross_check": kepler_checks,
    }'''

assert old in raw, "run_model body anchor not found"
raw = raw.replace(old, new)
open(p, "w", encoding="utf-8").write(raw)
print("patched run_model capture_baseline logic to use real orbit labels")
