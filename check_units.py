import sys
sys.path.insert(0, r"E:\agh-test")
import jovian_flyby_model as M

print("Sanity check: v_moon for each moon, in m/s AND km/s")
for moon in M.MOONS:
    p = M._moon_params(moon)
    print(f"{moon:>10s}  v_moon = {p['v_moon']:.4f} m/s = {p['v_moon']/1e3:.4f} km/s  "
          f"(a_m={p['a_m']:.4e} m, expected ~1-4 km/s for Galilean moons)")
