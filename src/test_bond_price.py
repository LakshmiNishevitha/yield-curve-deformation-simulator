import pandas as pd
from src.curve import curve_from_df, apply_shock
from src.bond import Bond, price_bond

df = pd.read_parquet("data/yields.parquet")
date = df.index.max()

curve = curve_from_df(df, date=date, method="linear")

bond = Bond(face=100.0, coupon_rate=0.05, maturity_years=5, freq=2)

p0 = price_bond(curve, bond)

curve_up = apply_shock(curve, "parallel", 50)   
curve_dn = apply_shock(curve, "parallel", -50)

p_up = price_bond(curve_up, bond)
p_dn = price_bond(curve_dn, bond)

print("Date:", date)
print("Base price:", round(p0, 6))
print("Price with +50bp:", round(p_up, 6))
print("Price with -50bp:", round(p_dn, 6))

if not (p_up < p0 < p_dn):
    raise RuntimeError("Sanity check failed: expected price(+50bp) < base < price(-50bp)")
print(" Sanity check passed: yields up => price down")
