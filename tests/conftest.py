"""
tests/conftest.py — Shared pytest fixtures used across all test modules.
"""
import pytest
import pandas as pd
from sqlalchemy import create_engine
from src.loaders.idempotent_loader import ensure_schema


# ── Shared sample data ────────────────────────────────────────────────────────

@pytest.fixture
def sample_raw_payload():
    """A minimal Open-Meteo-like raw payload for a single city."""
    return {
        "city_id":   "LON",
        "city_name": "London",
        "country":   "United Kingdom",
        "timezone":  "Europe/London",
        "hourly": {
            "time":                ["2024-06-15T10:00", "2024-06-15T11:00"],
            "temperature_2m":      [18.5, 19.2],
            "relative_humidity_2m":[72, 68],
            "precipitation":       [0.0, 0.0],
            "wind_speed_10m":      [14.0, 15.5],
            "surface_pressure":    [1015.0, 1014.5],
        }
    }


@pytest.fixture
def sample_fact_df():
    """A minimal fact DataFrame for loader tests."""
    return pd.DataFrame([
        {
            "metric_id": "aabbcc001",
            "city_id": "LON",
            "date_key": 20240615,
            "timestamp_utc": "2024-06-15T09:00:00Z",
            "timestamp_local": "2024-06-15T10:00:00+0100",
            "temperature_c": 18.5,
            "relative_humidity": 72.0,
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 14.0,
            "surface_pressure_hpa": 1015.0,
        },
        {
            "metric_id": "aabbcc002",
            "city_id": "LON",
            "date_key": 20240615,
            "timestamp_utc": "2024-06-15T10:00:00Z",
            "timestamp_local": "2024-06-15T11:00:00+0100",
            "temperature_c": 19.2,
            "relative_humidity": 68.0,
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 15.5,
            "surface_pressure_hpa": 1014.5,
        }
    ])


@pytest.fixture
def sample_dim_date():
    return pd.DataFrame([{
        "date_key": 20240615, "full_date": "2024-06-15",
        "year": 2024, "quarter": 2, "month": 6,
        "month_name": "June", "week": 24,
        "day_of_week": 6, "day_name": "Saturday", "is_weekend": 1
    }])


@pytest.fixture
def sample_dim_city():
    return pd.DataFrame([{
        "city_id": "LON", "city_name": "London",
        "country": "United Kingdom", "timezone": "Europe/London"
    }])


@pytest.fixture
def mem_engine():
    """Fresh in-memory SQLite engine with schema initialised."""
    engine = create_engine("sqlite:///:memory:")
    ensure_schema(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def mock_config():
    return {
        "pipeline": {
            "name": "test_pipeline",
            "raw_data_dir": "data/raw",
            "retention_days": 30
        },
        "api": {
            "base_url": "https://api.open-meteo.com/v1/forecast",
            "hourly_metrics": [
                "temperature_2m", "relative_humidity_2m",
                "precipitation", "wind_speed_10m", "surface_pressure"
            ],
            "timeout_seconds": 10,
            "max_retries": 1,
        },
        "cities": [
            {
                "id": "LON", "name": "London", "country": "United Kingdom",
                "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"
            }
        ],
    }
