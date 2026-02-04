import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from src.curve import curve_from_df, apply_shock
from src.bond import Bond, price_bond, dv01_duration_convexity

st.set_page_config(page_title="Yield Curve Deformation Simulator", layout="wide")

@st.cache_data
def load_yields():
    return pd.read_parquet("data/yields.parquet").sort_index()

df = load_yields()

st.title("Yield Curve Deformation Simulator (Daily)")
st.caption("Loads FRED daily Treasury yields → applies curve shocks → prices a bond → DV01 / duration / convexity")

st.sidebar.header("Curve")

available_dates = df.index
default_idx = len(available_dates) - 1
date = st.sidebar.selectbox("Date", options=available_dates, index=default_idx)

interp_method = st.sidebar.selectbox("Interpolation", ["linear", "cubic"], index=0)

shock_type = st.sidebar.selectbox(
    "Shock type",
    ["parallel", "steepen", "flatten", "twist", "butterfly"],
    index=0
)
bp = st.sidebar.slider("Shock size (bp)", min_value=-300, max_value=300, value=25, step=1)

twist_short_up = True
if shock_type == "twist":
    twist_short_up = st.sidebar.radio(
        "Twist direction",
        ["Short up / Long down", "Short down / Long up"]
    ) == "Short up / Long down"

st.sidebar.header("Bond")

maturity_years = st.sidebar.slider("Maturity (years)", min_value=1, max_value=30, value=5, step=1)
coupon_pct = st.sidebar.slider("Coupon (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.25)
freq = st.sidebar.selectbox("Coupon frequency", [1, 2, 4], index=1)
face = st.sidebar.number_input("Face value", value=100.0, step=10.0)

bond = Bond(
    face=float(face),
    coupon_rate=float(coupon_pct) / 100.0,
    maturity_years=float(maturity_years),
    freq=int(freq),
)

base_curve = curve_from_df(df, date=date, method=interp_method)
shocked_curve = apply_shock(base_curve, shock_type, bp, twist_short_up=twist_short_up)

base_price = price_bond(base_curve, bond)
shocked_price = price_bond(shocked_curve, bond)
risk = dv01_duration_convexity(base_curve, bond, bp=1.0)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Yield Curve: Original vs Shocked")

    xs, ys0 = base_curve.grid(t_min=1/12, t_max=30.0, n=250)
    _, ys1 = shocked_curve.grid(t_min=1/12, t_max=30.0, n=250)


    fig = plt.figure()
    plt.plot(xs, ys0 * 100.0, label="Original")
    plt.plot(xs, ys1 * 100.0, label=f"Shocked ({shock_type}, {bp:+} bp)")
    plt.xlabel("Maturity (years)")
    plt.ylabel("Yield (%)")
    plt.title("Yield Curve")
    plt.grid(True, alpha=0.3)
    plt.legend()

    st.pyplot(fig, clear_figure=True)

    st.write("**Raw curve nodes (%):**")
    nodes = pd.DataFrame(
        {"tenor": base_curve.tenors, "years": base_curve.maturities, "yield_%": base_curve.yields * 100.0}
    )
    st.dataframe(nodes, use_container_width=True)

with col2:
    st.subheader("Bond Pricing & Risk")

    st.metric("Bond price (original)", f"{base_price:,.4f}")
    st.metric("Bond price (shocked)", f"{shocked_price:,.4f}", delta=f"{(shocked_price - base_price):+.4f}")

    st.divider()
    st.write("**Risk (parallel ±1bp, finite diff):**")
    st.write(f"- DV01 (per 1bp): **{risk['DV01_per_1bp']:.6f}**")
    st.write(f"- Modified Duration: **{risk['mod_duration']:.6f}**")
    st.write(f"- Convexity: **{risk['convexity']:.6f}**")

    st.caption("Sanity: yields up → price down. DV01, duration, convexity should be positive for a plain bond.")

