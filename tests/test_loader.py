"""
Tests for idempotent database loader — verifies zero duplicate rows on repeated upserts.
Uses an in-memory SQLite database for full isolation (no disk writes).
"""
import pytest
import pandas as pd
from sqlalchemy import create_engine, text
from src.loaders.idempotent_loader import (
    ensure_schema,
    upsert_dim_date,
    upsert_dim_city,
    upsert_fact_weather,
)


@pytest.fixture
def mem_engine():
    """Provides a fresh in-memory SQLite engine for each test."""
    engine = create_engine("sqlite:///:memory:")
    ensure_schema(engine)
    yield engine
    engine.dispose()


SAMPLE_DIM_DATE = pd.DataFrame([{
    "date_key": 20240601, "full_date": "2024-06-01",
    "year": 2024, "quarter": 2, "month": 6,
    "month_name": "June", "week": 22,
    "day_of_week": 6, "day_name": "Saturday", "is_weekend": 1
}])

SAMPLE_DIM_CITY = pd.DataFrame([{
    "city_id": "LON", "city_name": "London",
    "country": "United Kingdom", "timezone": "Europe/London"
}])

SAMPLE_FACT = pd.DataFrame([{
    "metric_id": "abc123",
    "city_id": "LON",
    "date_key": 20240601,
    "timestamp_utc": "2024-06-01T00:00:00Z",
    "timestamp_local": "2024-06-01T01:00:00+0100",
    "temperature_c": 18.5,
    "relative_humidity": 72.0,
    "precipitation_mm": 0.0,
    "wind_speed_kmh": 15.0,
    "surface_pressure_hpa": 1015.0,
}])


class TestIdempotentLoader:

    def test_schema_creates_tables(self, mem_engine):
        with mem_engine.connect() as conn:
            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
            table_names = [t[0] for t in tables]
        assert "dim_date" in table_names
        assert "dim_city" in table_names
        assert "fact_weather_metrics" in table_names

    def test_dim_date_upsert(self, mem_engine):
        upsert_dim_date(mem_engine, SAMPLE_DIM_DATE)
        with mem_engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM dim_date")).scalar()
        assert count == 1

    def test_dim_date_idempotent(self, mem_engine):
        """Running the upsert 5x should still result in exactly 1 row."""
        for _ in range(5):
            upsert_dim_date(mem_engine, SAMPLE_DIM_DATE)
        with mem_engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM dim_date")).scalar()
        assert count == 1, "dim_date must have exactly 1 row regardless of re-runs"

    def test_dim_city_upsert(self, mem_engine):
        upsert_dim_city(mem_engine, SAMPLE_DIM_CITY)
        with mem_engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM dim_city")).scalar()
        assert count == 1

    def test_fact_upsert(self, mem_engine):
        upsert_dim_date(mem_engine, SAMPLE_DIM_DATE)
        upsert_dim_city(mem_engine, SAMPLE_DIM_CITY)
        upsert_fact_weather(mem_engine, SAMPLE_FACT)
        with mem_engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_weather_metrics")).scalar()
        assert count == 1

    def test_fact_idempotent_no_duplicates(self, mem_engine):
        """Core idempotency test — 5 runs must produce exactly 1 row."""
        upsert_dim_date(mem_engine, SAMPLE_DIM_DATE)
        upsert_dim_city(mem_engine, SAMPLE_DIM_CITY)
        for _ in range(5):
            upsert_fact_weather(mem_engine, SAMPLE_FACT)
        with mem_engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_weather_metrics")).scalar()
        assert count == 1, "0 duplicate rows must exist after repeated pipeline runs"

    def test_fact_update_on_conflict(self, mem_engine):
        """Verify that re-upserting updates the metric value rather than erroring."""
        upsert_dim_date(mem_engine, SAMPLE_DIM_DATE)
        upsert_dim_city(mem_engine, SAMPLE_DIM_CITY)
        upsert_fact_weather(mem_engine, SAMPLE_FACT)

        # Update temperature in same record
        updated = SAMPLE_FACT.copy()
        updated.loc[0, "temperature_c"] = 25.0
        upsert_fact_weather(mem_engine, updated)

        with mem_engine.connect() as conn:
            result = conn.execute(
                text("SELECT temperature_c FROM fact_weather_metrics WHERE metric_id='abc123'")
            ).scalar()
        assert result == 25.0
