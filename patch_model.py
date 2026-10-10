src = open(r"E:\agh-test\jovian_flyby_model.py", encoding="utf-8").read()

old1 = 'def direct_capture_deltav(target_orbit_name, v_inf=V_INFDIRECT, r_peri=TARGET_ORBITS[target_orbit_name]["a_m"]):\n    """Standard capture burn from hyperbolic approach v_inf to a circular\n    orbit of radius r_peri (executed at perijove = r_peri):\n        v_peri = sqrt(v_inf^2 + 2*mu_j/r_peri)\n        v_circ = sqrt(mu_j/r_peri)\n        delta_v = v_peri - v_circ\n    """\n    v_peri = math.sqrt(v_inf ** 2 + 2 * MU_JUPITER / r_peri)'
new1 = 'def direct_capture_deltav(target_orbit_name, v_inf=V_INFDIRECT, r_peri=None):\n    """Standard capture burn from hyperbolic approach v_inf to a circular\n    orbit of radius r_peri (executed at perijove = r_peri):\n        v_peri = sqrt(v_inf^2 + 2*mu_j/r_peri)\n        v_circ = sqrt(mu_j/r_peri)\n        delta_v = v_peri - v_circ\n    """\n    if r_peri is None:\n        r_peri = TARGET_ORBITS[target_orbit_name]["a_m"]\n    v_peri = math.sqrt(v_inf ** 2 + 2 * MU_JUPITER / r_peri)'

old2 = 'def assisted_capture_deltav(target_orbit_name, v_out, r_peri=TARGET_ORBITS[target_orbit_name]["a_m"]):\n    """Capture burn AFTER a moon assist has already reduced the approach\n    excess speed to v_out (i.e. the same formula as direct, just with\n    v_out in place of v_inf - the assist has done the deceleration, the\n    burn only has to circularize the residual energy)."""\n    v_peri = math.sqrt(v_out ** 2 + 2 * MU_JUPITER / r_peri)'
new2 = 'def assisted_capture_deltav(target_orbit_name, v_out, r_peri=None):\n    """Capture burn AFTER a moon assist has already reduced the approach\n    excess speed to v_out (i.e. the same formula as direct, just with\n    v_out in place of v_inf - the assist has done the deceleration, the\n    burn only has to circularize the residual energy)."""\n    if r_peri is None:\n        r_peri = TARGET_ORBITS[target_orbit_name]["a_m"]\n    v_peri = math.sqrt(v_out ** 2 + 2 * MU_JUPITER / r_peri)'

assert old1 in src, "old1 not found"
assert old2 in src, "old2 not found"
src = src.replace(old1, new1).replace(old2, new2)
open(r"E:\agh-test\jovian_flyby_model.py", "w", encoding="utf-8").write(src)
print("patched")
