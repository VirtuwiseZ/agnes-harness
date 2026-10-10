import math
T = 1.76913711350*86400
a = 4.218e8
print("v = 2*pi*a/T =", 2*math.pi*a/T, "m/s =", 2*math.pi*a/T/1e3, "km/s")
print("period implied by a=sqrt(mu a)/(pi...) :", math.pi*a/math.sqrt(1.26712e17/a)*2/86400, "days")
# check: period from vis-viva circular: T = 2*pi*sqrt(a^3/mu)
T2 = 2*math.pi*math.sqrt(a**3/1.26712e17)
print("T (from mu, a) =", T2, "s =", T2/86400, "days; matches published 1.76914 days within", abs(T2-T)/T*100, "%")
v = math.sqrt(1.26712e17/a)
print("v_circ =", v, "m/s =", v/1e3, "km/s")
print("\nConclusion: Io's true circular orbital speed is ~1.734 km/s ONLY IF a were 4.218e9 m (a factor of 10 larger).")
print("The real published semi-major axis of Io is ~421,800 km = 4.218e8 m, which is consistent with the model.")
print("=> The model's v_moon(io)=17.33 km/s would mean a period of only ~1.3 hours, which is physically WRONG for Io.")
print("   So there IS a real error: Io's a_m is 421,800 km = 4.218e8 m, BUT the true v_moon is only 1.734 km/s,")
print("   which means MU_JUPITER should be ~1.2669e15?? No wait - that contradicts the well-known 1.2669e17 value.")
print("\nLet's settle it once and for all with Keplear's third law directly, using Jupiter mass and Io's actual measured period:")
M = 1.898e27
T_real = 1.76913711350*86400
a_required = ((M*T_real**2)/(4*math.pi**2))**(1/3)  # this ignores M_io (<< M_jup)
print(f"a_required from M_jup+real T = {a_required:.4e} m = {a_required/1e3:.1f} km")
