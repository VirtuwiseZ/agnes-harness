# Fix: v_inf was declared in km/s in the spec but the model's default V_INFDIRECT and
# all caller overrides must be in m/s consistently (they already are - V_INFDIRECT=20000 m/s).
# The REAL bug: MU_JUPITER constant. Published value is 1.26686534e17 m^3/s^2.
# We wrote 1.26712e17 - that is off by a factor of ~100 from what it should be.
# Let me check: expected v_moon for Io ~1.73 km/s. Current v_moon(io) = sqrt(1.26712e17/4.2181e8).
import math
for mu in [1.26712e17, 1.2669e15, 1.2669e16]:
    v = math.sqrt(mu / 4.2181e8)
    print(f"mu={mu:.4e}  ->  v_moon(io) = {v:.4f} m/s = {v/1e3:.4f} km/s")
