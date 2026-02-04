import pandas as pd
from src.curve import curve_from_df
from src.bond import Bond, dv01_duration_convexity

df = pd.read_parquet("data/yields.parquet")
date = df.index.max()

curve = curve_from_df(df, date=date, method="linear")

bond = Bond(face=100.0, coupon_rate=0.05, maturity_years=5, freq=2)

r = dv01_duration_convexity(curve, bond, bp=1.0)

print("Date:", date)
for k, v in r.items():
    if isinstance(v, float):
        print(f"{k:>18}: {v:.8f}")
    else:
        print(f"{k:>18}: {v}")

if r["DV01_per_1bp"] <= 0:
    raise RuntimeError("DV01 should be positive.")
if r["mod_duration"] <= 0:
    raise RuntimeError("Duration should be positive.")
if r["convexity"] <= 0:
    raise RuntimeError("Convexity should be positive.")

print("Risk sanity checks passed")
