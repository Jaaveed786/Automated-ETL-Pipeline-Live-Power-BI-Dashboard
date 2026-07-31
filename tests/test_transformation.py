"""
Tests for cleaning & star schema transformation logic.
"""
import pytest
import pandas as pd
from src.transformers.cleaning import parse_city_weather, clean_all_cities
from src.transformers.star_schema import build_dim_date, build_dim_city, build_fact_weather_metrics

MOCK_RAW_PAYLOAD = {
    "city_id":   "TYO",
    "city_name": "Tokyo",
    "country":   "Japan",
    "timezone":  "Asia/Tokyo",
    "hourly": {
        "time":                ["2024-06-01T09:00", "2024-06-01T10:00", "2024-06-01T11:00"],
        "temperature_2m":      [28.5, 29.1, 30.0],
        "relative_humidity_2m":[65, 63, 60],
        "precipitation":       [0.0, 0.0, 0.1],
        "wind_speed_10m":      [8.0, 9.5, 10.2],
        "surface_pressure":    [1008.0, 1007.8, 1007.5],
    }
}


class TestCleaning:
    def test_parse_returns_dataframe(self):
        df = parse_city_weather(MOCK_RAW_PAYLOAD)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_required_columns_present(self):
        df = parse_city_weather(MOCK_RAW_PAYLOAD)
        required = ["metric_id", "city_id", "date_key", "timestamp_utc",
                    "timestamp_local", "temperature_c", "relative_humidity"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_metric_id_is_unique(self):
        df = parse_city_weather(MOCK_RAW_PAYLOAD)
        assert df["metric_id"].nunique() == len(df), "metric_id values must all be unique"

    def test_city_id_matches(self):
        df = parse_city_weather(MOCK_RAW_PAYLOAD)
        assert (df["city_id"] == "TYO").all()

    def test_local_timezone_applied(self):
        """Tokyo timestamps should be UTC+9, so local hour != UTC hour."""
        df = parse_city_weather(MOCK_RAW_PAYLOAD)
        utc_h = pd.to_datetime(df["timestamp_utc"].iloc[0]).hour
        local_h = int(df["timestamp_local"].iloc[0][11:13])
        # UTC+9 offset: local - utc should be 9
        assert (local_h - utc_h) % 24 == 9

    def test_temperature_values_match_input(self):
        df = parse_city_weather(MOCK_RAW_PAYLOAD)
        assert df["temperature_c"].tolist() == [28.5, 29.1, 30.0]

    def test_date_key_format(self):
        df = parse_city_weather(MOCK_RAW_PAYLOAD)
        for dk in df["date_key"]:
            assert len(str(dk)) == 8, "date_key should be YYYYMMDD (8 digits)"


class TestStarSchema:
    def setup_method(self):
        self.clean_df = parse_city_weather(MOCK_RAW_PAYLOAD)

    def test_dim_date_has_expected_columns(self):
        dim = build_dim_date(self.clean_df)
        for col in ["date_key", "full_date", "year", "quarter", "month_name",
                    "day_of_week", "is_weekend"]:
            assert col in dim.columns

    def test_dim_city_has_city_id(self):
        dim = build_dim_city(self.clean_df)
        assert "city_id" in dim.columns
        assert (dim["city_id"] == "TYO").all()

    def test_fact_table_no_dimension_columns(self):
        fact = build_fact_weather_metrics(self.clean_df)
        assert "city_name" not in fact.columns
        assert "country" not in fact.columns

    def test_fact_row_count_matches_input(self):
        fact = build_fact_weather_metrics(self.clean_df)
        assert len(fact) == 3
