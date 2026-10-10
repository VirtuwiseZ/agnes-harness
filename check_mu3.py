# Final, definitive check: derive Mu_jupiter two independent ways and see which
# matches the model's constant.
import math

# Method 1: from Io's published orbital period (most authoritative, decades of
# tracking data - Galileo, spacecraft tracking, etc.)
a_io = 4.218e8          # m (published Io semi-major axis)
T_io = 1.7691*86400    # s (published Io orbital period, 1.7691 days)
mu1 = (2*math.pi/T_io)**2 * a_io**3
print(f"Mu_jupiter (from Io period + a): {mu1:.6e} m^3/s^2")

# Method 2: from Jupiter's published mass + G
M_jup = 1.898e27       # kg (published Jupiter mass, ~5.97 Earth-mass * 5.97)
G = 6.67430e-11
mu2 = G * M_jup
print(f"Mu_jupiter (from M_jup*G):      {mu2:.6e} m^3/s^2")

print(f"\nModel's current constant:        1.26712e17")
print(f"Difference vs method 1: {abs(mu1-1.26712e17)/mu1*100:.3f}%")
print(f"Difference vs method 2: {abs(mu2-1.26712e17)/mu2*100:.3f}%")

# So the model's constant is actually CORRECT to within ~0.1%! My "expected 1-4 km/s"
# guess was the bug - the real orbital speed of Io is ~1.73 km/s *only if* a_io were
# 4.218e9, not 4.218e8 m. Let me check: is Io's real semi-major axis 421,800 km
# (4.218e8 m) or 4,218,000 km?
print(f"\nIo semi-major axis: 4.218e8 m = 421,800 km = 421.8e6 m... wait, 4.218e8 m")
print(f"= 421,800,000 m = 421,800 km. YES that is correct (Jupiter's radius is only")
print(f"~71,492 km, so Io orbits at ~421,800 km from Jupiter's center - plausible).")
print(f"\nSo the model was RIGHT all along: Io's orbital speed really is ~1.73 km/s?? ")
print(f"No wait: {math.sqrt(mu1/a_io)/1e3:.4f} km/s. Let me just recompute cleanly.")
v = math.sqrt(mu1/a_io)
print(f"v_io = sqrt(mu1/a_io) = {v:.4f} m/s = {v/1e3:.4f} km/s")
