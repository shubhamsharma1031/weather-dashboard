"""
Load: write the processed tables into MySQL.

Connection details are read from environment variables (never hard-code passwords):
    MYSQL_HOST (default localhost), MYSQL_PORT (3306), MYSQL_USER (root),
    MYSQL_PASSWORD, MYSQL_DATABASE (weather_db)

Rows are upserted with INSERT ... ON DUPLICATE KEY UPDATE, so running the
pipeline every day only adds new dates and refreshes the forecast.
"""

import os

import mysql.connector
import pandas as pd

from config import ROOT

try:  # read settings from a .env file if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

TABLE_COLUMNS = {
    "weather_daily": ["city", "date", "temp_max_c", "temp_min_c", "temp_mean_c", "precipitation_mm",
                      "rain_mm", "wind_max_kmh", "humidity_pct", "sunshine_hours", "temp_range_c",
                      "is_rainy_day", "heat_category", "month", "month_name", "year", "week", "season",
                      "latitude", "longitude"],
    "weather_forecast": ["city", "date", "temp_max_c", "temp_min_c", "temp_mean_c", "precipitation_mm",
                         "rain_mm", "wind_max_kmh", "sunshine_hours", "temp_range_c", "is_rainy_day",
                         "heat_category", "season"],
}


def connect():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "weather_db"),
    )


def upsert(conn, table, df):
    cols = [c for c in TABLE_COLUMNS[table] if c in df.columns]
    data = df[cols].astype(object).where(df[cols].notna(), None)
    data["date"] = pd.to_datetime(data["date"]).dt.date
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join(f"{c} = VALUES({c})" for c in cols if c not in ("city", "date"))
    sql = (f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
           f"ON DUPLICATE KEY UPDATE {updates}")
    with conn.cursor() as cur:
        cur.executemany(sql, [tuple(r) for r in data.itertuples(index=False)])
    conn.commit()
    print(f"  {table}: {len(data)} rows upserted")


def load_all(outputs=None):
    if outputs is None:
        processed = ROOT / "data" / "processed"
        outputs = {name: pd.read_csv(processed / f"{name}.csv") for name in TABLE_COLUMNS}
    conn = connect()
    try:
        for name, df in outputs.items():
            upsert(conn, name, df)
    finally:
        conn.close()


if __name__ == "__main__":
    load_all()
