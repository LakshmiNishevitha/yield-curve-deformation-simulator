import pandas as pd
from src.curve import curve_from_df, apply_shock

df = pd.read_parquet("data/yields.parquet")
date = df.index.max()

base = curve_from_df(df, date=date, method="linear")

def show(curve, label):
    print(f"\n{label}")
    for t in [2, 5, 10, 30]:
        print(f"{t:>2}Y: {curve.y(t):.6f}")

print("Base curve nodes:")
show(base, "BASE")

bp = 50
show(apply_shock(base, "parallel", bp), f"PARALLEL +{bp}bp (all up)")
show(apply_shock(base, "steepen", bp), f"STEEPEN +{bp}bp (long up more)")
show(apply_shock(base, "flatten", bp), f"FLATTEN +{bp}bp (long down more)")
show(apply_shock(base, "twist", bp, twist_short_up=True), f"TWIST +{bp}bp (short up, long down)")
show(apply_shock(base, "butterfly", bp), f"BUTTERFLY +{bp}bp (belly vs wings)")