import pandas as pd
from src.curve import curve_from_df

df = pd.read_parquet("data/yields.parquet")

date = df.index.max()

curve_lin = curve_from_df(df, date=date, method="linear")
curve_cub = curve_from_df(df, date=date, method="cubic")

print("Using date:", date)
print("Tenors:", curve_lin.tenors)
print("Node yields (decimals):", curve_lin.yields)

for t in [2, 3, 7, 10, 20, 30]:
    print(f"t={t:>2}y  linear={curve_lin.y(t):.6f}  cubic={curve_cub.y(t):.6f}")
