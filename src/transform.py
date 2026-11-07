"""
Transform: turn the raw API responses into clean, analysis-ready tables.

Cleaning steps
1. Flatten each JSON response into a DataFrame and add the city name
2. Rename columns to short, readable names and fix data types
3. Remove duplicate (city, date) rows
4. Fill short gaps in numeric columns by interpolation (max 3 days per city);
   rain/precipitation gaps are filled with 0
5. Flag physically impossible values (e.g. min temperature above max) and drop them
6. Add derived columns used in the dashboard:
   temp_range_c, sunshine_hours, is_rainy_day, heat_category, season, month, week
"""

import json

import numpy as np
import pandas as pd

from config import CITIES, PROCESSED_DIR, RAW_DIR, RENAME

NUMERIC = ["temp_max_c", "temp_min_c", "temp_mean_c", "precipitation_mm", "rain_mm",
           "wind_max_kmh", "humidity_pct", "sunshine_s"]


def response_to_frame(payload, city):
    df = pd.DataFrame(payload["daily"])
    df.insert(0, "city", city)
    return df


def indian_season(month):
    """IMD-style seasons for India."""
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Summer"
    if month in (6, 7, 8, 9):
        return "Monsoon"
    return "Post-Monsoon"


def heat_category(temp_max):
    if pd.isna(temp_max):
        return "Unknown"
    if temp_max >= 40:
        return "Extreme Heat"
    if temp_max >= 35:
        return "Hot"
    if temp_max >= 25:
        return "Warm"
    if temp_max >= 15:
        return "Mild"
    return "Cold"


def clean(df):
    report = {"rows_in": len(df)}
    df = df.rename(columns=RENAME)
    df["date"] = pd.to_datetime(df["date"])
    for col in NUMERIC:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.drop_duplicates(subset=["city", "date"]).sort_values(["city", "date"])
    report["duplicates_removed"] = before - len(df)
    report["missing_before"] = int(df[[c for c in NUMERIC if c in df.columns]].isna().sum().sum())

    # rain gaps -> 0 mm; other numeric gaps -> interpolate within each city (up to 3 days)
    for col in ("precipitation_mm", "rain_mm"):
        if col in df.columns:
            df[col] = df[col].fillna(0)
    for col in [c for c in NUMERIC if c in df.columns and c not in ("precipitation_mm", "rain_mm")]:
        df[col] = df.groupby("city")[col].transform(lambda s: s.interpolate(limit=3, limit_direction="both"))

    # fill a missing daily mean from max and min
    if "temp_mean_c" in df.columns:
        df["temp_mean_c"] = df["temp_mean_c"].fillna((df["temp_max_c"] + df["temp_min_c"]) / 2)
    else:
        df["temp_mean_c"] = (df["temp_max_c"] + df["temp_min_c"]) / 2

    invalid = (df["temp_min_c"] > df["temp_max_c"]) | (df["humidity_pct"].gt(100) if "humidity_pct" in df else False)
    report["invalid_removed"] = int(invalid.sum())
    df = df[~invalid]

    report["missing_after"] = int(df[[c for c in NUMERIC if c in df.columns]].isna().sum().sum())
    report["rows_out"] = len(df)
    return df.reset_index(drop=True), report


def add_features(df):
    df = df.copy()
    df["temp_range_c"] = (df["temp_max_c"] - df["temp_min_c"]).round(1)
    if "sunshine_s" in df.columns:
        df["sunshine_hours"] = (df["sunshine_s"] / 3600).round(1)
        df = df.drop(columns="sunshine_s")
    df["is_rainy_day"] = (df["precipitation_mm"] >= 2.5).astype(int)  # IMD definition of a rainy day
    df["heat_category"] = df["temp_max_c"].apply(heat_category)
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    df["year"] = df["date"].dt.year
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["season"] = df["month"].apply(indian_season)
    df["latitude"] = df["city"].map(lambda c: CITIES[c][0])
    df["longitude"] = df["city"].map(lambda c: CITIES[c][1])
    num = df.select_dtypes("number").columns
    df[num] = df[num].round(2)
    return df


def load_raw(kind):
    frames = []
    for city in CITIES:
        path = RAW_DIR / f"{kind}_{city.lower()}.json"
        if path.exists():
            frames.append(response_to_frame(json.loads(path.read_text()), city))
    if not frames:
        raise FileNotFoundError(f"No raw {kind} files in {RAW_DIR}. Run extract.py first.")
    return pd.concat(frames, ignore_index=True)


def transform_all():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for kind, name in (("history", "weather_daily"), ("forecast", "weather_forecast")):
        df, report = clean(load_raw(kind))
        df = add_features(df)
        df.to_csv(PROCESSED_DIR / f"{name}.csv", index=False, date_format="%Y-%m-%d")
        outputs[name] = df
        print(f"{name}: {report}")
    return outputs


if __name__ == "__main__":
    transform_all()
