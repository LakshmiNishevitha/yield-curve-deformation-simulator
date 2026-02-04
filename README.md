# Yield Curve Deformation Simulator (Daily)

An interactive fixed-income risk analysis tool built with Python and Streamlit.

This project loads **daily U.S. Treasury yield curve data** from FRED, constructs a smooth yield curve, applies standard **curve deformations**, and prices a fixed-coupon bond to compute **DV01, modified duration, and convexity**.

The tool is designed as a **reusable pricing and risk engine**, suitable for future integration with macro-event or portfolio-level analytics.

---

## Features

### Yield Curve Construction
- Loads daily Treasury yields from FRED
- Supports multiple tenors:
  - 1M, 3M, 6M
  - 1Y, 2Y, 3Y, 5Y, 7Y
  - 10Y, 20Y, 30Y
- Linear and cubic spline interpolation
- Produces a continuous yield function \( y(t) \)

### Curve Deformations
- Parallel shift
- Steepening
- Flattening
- Twist (short-up / long-down or reverse)
- Butterfly (belly vs wings)

### Bond Pricing & Risk
- Fixed-coupon bond pricing using curve-based discounting
- Finite-difference risk metrics:
  - DV01
  - Modified duration
  - Convexity
- Sanity-checked behavior (yields ↑ → price ↓)

### Interactive UI
- Built with Streamlit
- Select:
  - Date
  - Interpolation method
  - Shock type and magnitude (bp)
  - Bond parameters (maturity, coupon, frequency)
- Visualizes:
  - Original vs shocked yield curve
  - Bond price changes
  - Risk metrics in real time

---

## Project Structure
```
yield-curve-sim/
│
├── app_curve.py # Streamlit application
├── requirements.txt # Python dependencies
├── README.md
│
├── data/
│ └── yields.parquet # Daily Treasury yields (generated from FRED)
│
└── src/
├── init.py
├── data_fetch.py # Fetches FRED yield data
├── curve.py # Curve construction + interpolation + shocks
└── bond.py # Bond pricing + DV01 / duration / convexity
```


---

## Setup Instructions

### 1. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
---

##Fetch Yield Curve Data (FRED)
This project pulls daily Treasury Constant Maturity yields directly from FRED.
```bash
python src/data_fetch.py
```
This generates:
```bash
data/yields.parquet
```
---
##Run the Streamlit App
```bash
streamlit run app_curve.py
```
The app will open locally (usually at http://localhost:8501).

----

## Design Notes
- FRED yields are par yields, treated here as spot rates for learning and scenario analysis
- Discounting uses annual compounding for clarity and consistency
- The architecture intentionally separates:
	- Data ingestion
	- Curve construction
	- Shock logic
	- Pricing and risk
- This makes the engine easy to extend (e.g., zero-curve bootstrapping, key-rate DV01, portfolio aggregation)

---
##Future Extensions
- Zero-curve bootstrapping from par yields
- Key-rate DV01 and factor sensitivities
- Portfolio-level aggregation
- Integration with macro-event or scenario engines
