import numpy as np
import pandas as pd
from dataclasses import dataclass
from scipy.interpolate import CubicSpline

TENOR_TO_YEARS = {
    "1M": 1.0 / 12.0,
    "3M": 3.0 / 12.0,
    "6M": 6.0 / 12.0,
    "1Y": 1.0,
    "2Y": 2.0,
    "3Y": 3.0,
    "5Y": 5.0,
    "7Y": 7.0,
    "10Y": 10.0,
    "20Y": 20.0,
    "30Y": 30.0,
}


@dataclass
class YieldCurve:
    """
    Single-date yield curve with interpolation.
    Rates are decimals (0.042 = 4.2%).
    method: "linear" or "cubic"
    """
    tenors: list
    maturities: np.ndarray
    yields: np.ndarray
    method: str = "linear"

    def __post_init__(self):
        self.maturities = np.asarray(self.maturities, dtype=float)
        self.yields = np.asarray(self.yields, dtype=float)

        if len(self.maturities) != len(self.yields):
            raise ValueError("maturities and yields length mismatch")
        if np.any(np.diff(self.maturities) <= 0):
            raise ValueError("maturities must be strictly increasing")

        self._spline = None
        if self.method == "cubic":
            self._spline = CubicSpline(self.maturities, self.yields, bc_type="natural")

    def y(self, t: float) -> float:
        """
        Interpolated yield at maturity t in years.
        Extrapolation: clamp to nearest endpoint.
        """
        t = float(t)
        t_clamped = min(max(t, self.maturities[0]), self.maturities[-1])

        if self.method == "cubic":
            return float(self._spline(t_clamped))
        return float(np.interp(t_clamped, self.maturities, self.yields))

    def grid(self, t_min=0.25, t_max=30.0, n=200):
        xs = np.linspace(t_min, t_max, n)
        ys = np.array([self.y(x) for x in xs])
        return xs, ys

def curve_from_df(df: pd.DataFrame, date, method="linear") -> YieldCurve:
    """
    Build a YieldCurve for a chosen date from the parquet DataFrame.
    Uses forward-fill to handle missing values.
    If exact date not present, uses nearest previous available date.
    """
    date = pd.to_datetime(date)

    df2 = df.sort_index().ffill()

    if date not in df2.index:
        date = df2.index[df2.index.get_loc(date, method="pad")]

    row = df2.loc[date]

    tenors = [c for c in df2.columns if c in TENOR_TO_YEARS]
    maturities = np.array([TENOR_TO_YEARS[t] for t in tenors], dtype=float)
    yields = row[tenors].astype(float).to_numpy()

    order = np.argsort(maturities)
    maturities = maturities[order]
    yields = yields[order]
    tenors = [tenors[i] for i in order]

    return YieldCurve(tenors=tenors, maturities=maturities, yields=yields, method=method)

def bp_to_decimal(bp: float) -> float:
    """1 bp = 0.0001 in decimal yield terms."""
    return float(bp) / 10000.0

def shock_parallel(curve: YieldCurve, bp: float) -> YieldCurve:
    bump = bp_to_decimal(bp)
    return YieldCurve(curve.tenors, curve.maturities, curve.yields + bump, curve.method)

def shock_steepen(curve: YieldCurve, bp: float) -> YieldCurve:
    """
    Long end up more than short end (steepens).
    Ramp: 0 at shortest maturity -> +bp at longest.
    """
    bump = bp_to_decimal(bp)
    w = (curve.maturities - curve.maturities[0]) / (curve.maturities[-1] - curve.maturities[0])
    return YieldCurve(curve.tenors, curve.maturities, curve.yields + bump * w, curve.method)

def shock_flatten(curve: YieldCurve, bp: float) -> YieldCurve:
    """
    Opposite of steepen: long end down relative to short (flattens).
    Ramp: 0 at shortest -> -bp at longest.
    """
    bump = bp_to_decimal(bp)
    w = (curve.maturities - curve.maturities[0]) / (curve.maturities[-1] - curve.maturities[0])
    return YieldCurve(curve.tenors, curve.maturities, curve.yields - bump * w, curve.method)

def shock_twist(curve: YieldCurve, bp: float, short_up: bool = True) -> YieldCurve:
    """
    Twist: short up & long down (or reversed).
    We create weights from +1 (short) to -1 (long).
    """
    bump = bp_to_decimal(bp)
    w01 = (curve.maturities - curve.maturities[0]) / (curve.maturities[-1] - curve.maturities[0])
    w = 1.0 - 2.0 * w01  
    if not short_up:
        w = -w
    return YieldCurve(curve.tenors, curve.maturities, curve.yields + bump * w, curve.method)

def shock_butterfly(curve: YieldCurve, bp: float) -> YieldCurve:
    """
    Butterfly: belly moves opposite of wings.
    Use a bell-shaped weight centered at mid maturity, then de-mean.
    """
    bump = bp_to_decimal(bp)

    mid = 0.5 * (curve.maturities[0] + curve.maturities[-1])
    span = curve.maturities[-1] - curve.maturities[0]

    w = np.exp(-((curve.maturities - mid) ** 2) / (0.15 * span) ** 2)
    w = w / w.max()          
    w = w - w.mean()         

    return YieldCurve(curve.tenors, curve.maturities, curve.yields + bump * w, curve.method)

def apply_shock(curve: YieldCurve, shock_type: str, bp: float, twist_short_up: bool = True) -> YieldCurve:
    shock_type = shock_type.lower().strip()
    if shock_type == "parallel":
        return shock_parallel(curve, bp)
    if shock_type == "steepen":
        return shock_steepen(curve, bp)
    if shock_type == "flatten":
        return shock_flatten(curve, bp)
    if shock_type == "twist":
        return shock_twist(curve, bp, short_up=twist_short_up)
    if shock_type == "butterfly":
        return shock_butterfly(curve, bp)
    raise ValueError(f"Unknown shock_type: {shock_type}")
