import numpy as np
from dataclasses import dataclass
from src.curve import YieldCurve, shock_parallel, bp_to_decimal

@dataclass
class Bond:
    """
    Simple fixed coupon bond.
    face: principal (e.g., 100)
    coupon_rate: annual coupon rate in decimals (0.05 = 5%)
    maturity_years: years to maturity
    freq: coupon payments per year (2 = semiannual)
    """
    face: float = 100.0
    coupon_rate: float = 0.05
    maturity_years: float = 5.0
    freq: int = 2

def price_bond(curve: YieldCurve, bond: Bond) -> float:
    """
    Price = sum( CF_t / (1 + y(t))^t )
    Uses annual compounding (matches our project spec).
    """
    n = int(round(bond.maturity_years * bond.freq))
    if n <= 0:
        raise ValueError("Bond maturity_years * freq must be >= 1")

    times = np.array([(i + 1) / bond.freq for i in range(n)], dtype=float)

    coupon = bond.face * bond.coupon_rate / bond.freq
    cfs = np.full(n, coupon, dtype=float)
    cfs[-1] += bond.face 

    dfs = np.array([1.0 / ((1.0 + curve.y(t)) ** t) for t in times], dtype=float)

    return float(np.sum(cfs * dfs))

from src.curve import shock_parallel, bp_to_decimal

def dv01_duration_convexity(curve: YieldCurve, bond: Bond, bp: float = 1.0) -> dict:
    """
    Finite difference risk using parallel bumps.

    Let P0 = price(curve)
        P_up = price(curve bumped +bp)   (yields up -> price down)
        P_dn = price(curve bumped -bp)   (yields down -> price up)

    DV01 (per 1bp) ≈ (P_dn - P_up) / 2

    Modified Duration ≈ (P_dn - P_up) / (2 * P0 * dy)
      where dy = bp in decimal (e.g. 1bp = 0.0001)

    Convexity ≈ (P_dn + P_up - 2*P0) / (P0 * dy^2)
    """
    dy = bp_to_decimal(bp)

    p0 = price_bond(curve, bond)
    curve_up = shock_parallel(curve, +bp)
    curve_dn = shock_parallel(curve, -bp)

    p_up = price_bond(curve_up, bond)
    p_dn = price_bond(curve_dn, bond)

    dv01 = (p_dn - p_up) / 2.0
    mod_duration = (p_dn - p_up) / (2.0 * p0 * dy)
    convexity = (p_dn + p_up - 2.0 * p0) / (p0 * (dy ** 2))

    return {
        "price": p0,
        "price_up_+bp": p_up,
        "price_dn_-bp": p_dn,
        "DV01_per_1bp": dv01,
        "mod_duration": mod_duration,
        "convexity": convexity,
    }
