"""Example model used ONLY to self-test boundary_gate.py: a simple
energy-recovery model where launch speed is proportional to sqrt of stored
PE, so the boundary expectations are analytically known.
"""
import math


def run_model(params):
    """params: h (drop height, m), m (counterweight mass, kg), g (m/s^2).
    Returns dict with 'v_release' ~ sqrt(2*g*h) (simple energy recovery).
    """
    h = params.get("h", 0.0)
    g = params.get("g", 9.8)
    v = math.sqrt(max(0.0, 2.0 * g * h))
    return {"v_release": v}
