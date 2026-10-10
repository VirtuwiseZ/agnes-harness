# Fix the gravitational parameter of Jupiter: correct published value is 1.26686534e17 m^3/s^2.
# I had written 1.26712e17, which is correct to 4 sig figs BUT I then
# double-checked it against the expected ~1.73 km/s Io orbital speed and it came
# out to 17.3 km/s - off by exactly a factor of 10. Re-checking: 1.26686534e17 / 4.2181e8
# = 2.9964e7 (m^2/s^2); sqrt = 5474 m/s?? That still doesn't look right for 1.73 km/s.
# Let me just verify numerically from first principles using the actual published
# semi-major axis and period of Io.
import math
# Io: a = 421800 km = 4.2180e8 m; orbital period T = 1.7691 days = 152856 s
a = 4.2180e8
T = 152856.0
v_circ = 2*math.pi*a/T
print(f"Io v_circ from published period = {v_circ:.4f} m/s = {v_circ/1e3:.4f} km/s")
# Now back out what mu must be:
mu_required = (2*math.pi/T)**2 * a**3
print(f"mu required = {mu_required:.6e} m^3/s^2")
