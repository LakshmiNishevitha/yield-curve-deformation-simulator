import os
import pandas as pd

FRED_SERIES = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30",
}

def fetch_fred_series(series_id: str) -> pd.Series:
    """
    Fetch one FRED series as a pandas Series indexed by date.
    Handles both DATE and observation_date column naming.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url)

    date_col = None
    for candidate in ["DATE", "observation_date", "date"]:
        if candidate in df.columns:
            date_col = candidate
            break

    if date_col is None or series_id not in df.columns:
        raise ValueError(
            f"Unexpected CSV format for {series_id}: columns={df.columns.tolist()}"
        )

    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()

    s = pd.to_numeric(df[series_id], errors="coerce")
    s.name = series_id
    return s


def fetch_yield_curve(start="2000-01-01") -> pd.DataFrame:
    series_list = []
    for tenor, code in FRED_SERIES.items():
        s = fetch_fred_series(code).rename(tenor)
        series_list.append(s)

    df = pd.concat(series_list, axis=1)

    df = df[df.index >= pd.to_datetime(start)]

    df = df / 100.0

    df = df.sort_index().ffill()

    return df

def main():
    os.makedirs("data", exist_ok=True)

    df = fetch_yield_curve(start="2000-01-01")
    out_path = "data/yields.parquet"
    df.to_parquet(out_path)

    print(f"Saved to {out_path}")
    print("Shape:", df.shape)
    print(df.tail())
    print("\nColumns:", list(df.columns))

if __name__ == "__main__":
    main()
