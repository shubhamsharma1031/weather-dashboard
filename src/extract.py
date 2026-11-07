"""
Extract: download daily weather data for each city from the Open-Meteo API.

- Historical data comes from the archive API (data is available up to about 5 days ago).
- The next 7 days come from the forecast API.
Raw JSON responses are saved to data/raw/ so the transform step can be re-run offline.
"""

import json
import time
from datetime import date, timedelta

import requests

from config import ARCHIVE_URL, CITIES, DAILY_VARIABLES, FORECAST_URL, RAW_DIR, TIMEZONE

FORECAST_VARIABLES = [v for v in DAILY_VARIABLES if v not in ("relative_humidity_2m_mean", "temperature_2m_mean")]


def _get(url, params, retries=3):
    """GET with simple retry and back-off, because public APIs sometimes fail."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as err:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"  request failed ({err}); retrying in {wait}s")
            time.sleep(wait)


def fetch_history(city, lat, lon, start, end):
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARIABLES), "timezone": TIMEZONE,
    }
    return _get(ARCHIVE_URL, params)


def fetch_forecast(city, lat, lon, days=7):
    params = {
        "latitude": lat, "longitude": lon,
        "daily": ",".join(FORECAST_VARIABLES), "forecast_days": days, "timezone": TIMEZONE,
    }
    return _get(FORECAST_URL, params)


def extract_all(history_days=365):
    """Download history and forecast for every city and save the raw JSON files."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    end = date.today() - timedelta(days=5)
    start = end - timedelta(days=history_days - 1)
    print(f"Downloading {start} to {end} for {len(CITIES)} cities")
    for city, (lat, lon) in CITIES.items():
        history = fetch_history(city, lat, lon, start, end)
        forecast = fetch_forecast(city, lat, lon)
        (RAW_DIR / f"history_{city.lower()}.json").write_text(json.dumps(history))
        (RAW_DIR / f"forecast_{city.lower()}.json").write_text(json.dumps(forecast))
        print(f"  {city}: {len(history['daily']['time'])} days of history, "
              f"{len(forecast['daily']['time'])} days of forecast")
        time.sleep(0.5)  # be polite to the free API


if __name__ == "__main__":
    extract_all()
