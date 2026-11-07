"""Unit tests for the transform step. Run with:  python -m pytest -q"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from transform import add_features, clean, heat_category, indian_season, response_to_frame  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "history_sample.json"


@pytest.fixture
def cleaned():
    raw = response_to_frame(json.loads(FIXTURE.read_text()), "Jaipur")
    df, report = clean(raw)
    return add_features(df), report


def test_duplicates_removed(cleaned):
    df, report = cleaned
    assert report["duplicates_removed"] == 1
    assert not df.duplicated(subset=["city", "date"]).any()


def test_invalid_row_removed(cleaned):
    # 2025-05-05 has min temperature (32.0) above max (30.0)
    df, report = cleaned
    assert report["invalid_removed"] == 1
    assert "2025-05-05" not in df["date"].dt.strftime("%Y-%m-%d").tolist()


def test_missing_values_filled(cleaned):
    df, report = cleaned
    assert report["missing_after"] == 0
    day2 = df[df["date"] == "2025-05-02"].iloc[0]
    assert day2["temp_max_c"] == pytest.approx((41.2 + 39.8) / 2)  # interpolated
    assert day2["precipitation_mm"] == 0  # missing rain treated as no rain


def test_derived_columns(cleaned):
    df, _ = cleaned
    first = df.iloc[0]
    assert first["temp_range_c"] == pytest.approx(41.2 - 27.5, abs=0.05)
    assert first["heat_category"] == "Extreme Heat"
    assert first["season"] == "Summer"
    assert first["sunshine_hours"] == pytest.approx(41000 / 3600, abs=0.05)
    assert df.loc[df["date"] == "2025-05-04", "is_rainy_day"].iloc[0] == 1


@pytest.mark.parametrize("month,season", [(1, "Winter"), (4, "Summer"), (7, "Monsoon"), (10, "Post-Monsoon"), (12, "Winter")])
def test_indian_season(month, season):
    assert indian_season(month) == season


@pytest.mark.parametrize("temp,label", [(42, "Extreme Heat"), (36, "Hot"), (28, "Warm"), (18, "Mild"), (10, "Cold")])
def test_heat_category(temp, label):
    assert heat_category(temp) == label


def test_extract_saves_raw_files(tmp_path, monkeypatch):
    """extract_all should call the API for every city and save history + forecast JSON."""
    import extract

    payload = json.loads(FIXTURE.read_text())

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    calls = []
    monkeypatch.setattr(extract.requests, "get", lambda url, params, timeout: calls.append(url) or FakeResponse())
    monkeypatch.setattr(extract, "RAW_DIR", tmp_path)
    monkeypatch.setattr(extract.time, "sleep", lambda s: None)
    extract.extract_all(history_days=30)

    assert len(list(tmp_path.glob("history_*.json"))) == len(extract.CITIES)
    assert len(list(tmp_path.glob("forecast_*.json"))) == len(extract.CITIES)
    assert len(calls) == 2 * len(extract.CITIES)
