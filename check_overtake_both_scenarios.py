import json
import math

def hyperbolic_turning_angle(r_p, v_rel, mu_m):
    e = 1.0 + r_p * v_rel ** 2 / mu_m
    return 2.0 * math.asin(1.0 / e)

cases = [
    ("io",       17332.06, 4.2181e8, 8.932e22),
    ("europa",   13740.9,  6.711e8,  4.80e21),
    ("ganymede", 10880.2,  1.0704e9, 1.4819e23),
    ("callisto",  8203.9,  1.8827e9, 1.0759e23),
]
G = 6.67430e-11
V_INF = 20000.0
for name, vm, a, M in cases:
    mu_m = G * M
    R_m = {"io": 1.8216e6, "europa": 1.5608e6, "ganymede": 2.6341e6, "callisto": 2.4104e6}[name]
    v_rel = abs(V_INF - vm)
    delta = hyperbolic_turning_angle(R_m, v_rel, mu_m)
    # Scenario C (spacecraft slower than moon, moon catches up from behind,
    # classic Voyager-class "gain speed off a fast planet"):
    v_out_c = vm + 2.0 * v_rel * math.sin(delta / 2.0)
    # Scenario D (spacecraft faster than moon, moon chases spacecraft, "loss of speed"):
    v_out_d = vm + v_rel - 2.0 * v_rel * math.sin(delta / 2.0)
    print(f"{name:9s}  v_moon={vm/1e3:7.4f} km/s  v_rel={v_rel/1e3:7.4f} km/s  delta={delta*180/math.pi:8.4f} deg")
    print(f"          Scenario C (classic gain):  v_out={v_out_c/1e3:8.4f} km/s   gain vs v_moon={(v_out_c-vm)/1e3:+8.4f} km/s")
    print(f"          Scenario D (loss, Dv=2*v_rel*sin(delta/2)):  v_out={v_out_d/1e3:8.4f} km/s   delta_v={v_out_d-V_INF:+.4f} km/s vs 20")
    print()
