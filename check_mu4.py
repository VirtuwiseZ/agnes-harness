# Definitive check of Io's REAL orbital speed, via an independent published
# period measurement (most reliable - this is what decades of spacecraft
# tracking actually measures), NOT via a semi-major axis that may have a
# unit-conversion error lurking in it.
import math
T_io_days = 1.76913711350  # Io sidereal orbital period, days (published, high-precision)
T_io = T_io_days * 86400   # s
# Two independent published semi-major axis figures to cross-check against:
a_io_1 = 421800e3   # 421,800 km, the commonly cited "421,800 km" figure
a_io_2 = 421800.0   # m (in case the "421,800" figure was already in meters, not km)
for a, label in [(a_io_1, "421,800 km -> 4.218e8 m"), (a_io_2, "421,800 m (tiny, clearly wrong scale)")]:
    v = 2*math.pi*a/T_io
    print(f"v_io = {v:.4f} m/s = {v/1e3:.4f} km/s   [{label}]")
# And the physically correct one for a real moon of Jupiter must be of order
# 1-4 km/s. Check: does a_io_1 give that?
print("\nIo semi-major axis should be ~6.3 Jupiter radii (Jupiter radius ~71,492 km) = ~450,000 km")
print("=> 4.5e8 m = 450,000 km. So 421,800 km is actually reasonable (4.218e8 m), giving v ~ 1.73 km/s? Let's see.")
v_check = 2*math.pi*4.218e8/T_io
print(f"v_io (a=4.218e8 m) = {v_check:.4f} m/s = {v_check/1e3:.4f} km/s")
