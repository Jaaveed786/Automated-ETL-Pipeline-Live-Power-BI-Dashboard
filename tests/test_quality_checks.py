"""
tests/test_quality_checks.py — Unit tests for custom business-logic data assertions.
"""
import pytest
import pandas as pd
from src.utils.quality_checks import (
    check_no_null_metric_ids,
    check_no_duplicate_metric_ids,
    check_city_ids_known,
    check_temperature_range,
    check_non_negative_precipitation,
    run_all_checks,
    QualityCheckError,
)

KNOWN_CITIES = ["LON", "NYC", "TYO", "DXB"]


def make_df(**overrides):
    base = {
        "metric_id": ["id001", "id002"],
        "city_id": ["LON", "NYC"],
        "timestamp_utc": ["2024-06-01T00:00:00Z", "2024-06-01T01:00:00Z"],
        "temperature_c": [18.5, 22.0],
        "relative_humidity": [70.0, 65.0],
        "precipitation_mm": [0.0, 0.1],
        "wind_speed_kmh": [12.0, 14.0],
        "surface_pressure_hpa": [1013.0, 1012.5],
    }
    base.update(overrides)
    return pd.DataFrame(base)


class TestNullMetricIds:
    def test_passes_on_valid_data(self):
        check_no_null_metric_ids(make_df())

    def test_fails_on_null_metric_id(self):
        df = make_df(metric_id=[None, "id002"])
        with pytest.raises(QualityCheckError, match="null"):
            check_no_null_metric_ids(df)

    def test_fails_on_empty_string_metric_id(self):
        df = make_df(metric_id=["", "id002"])
        with pytest.raises(QualityCheckError, match="empty"):
            check_no_null_metric_ids(df)


class TestDuplicateMetricIds:
    def test_passes_on_unique_ids(self):
        check_no_duplicate_metric_ids(make_df())

    def test_fails_on_duplicates(self):
        df = make_df(metric_id=["id001", "id001"])
        with pytest.raises(QualityCheckError, match="duplicate"):
            check_no_duplicate_metric_ids(df)


class TestCityIds:
    def test_passes_on_known_cities(self):
        check_city_ids_known(make_df(), KNOWN_CITIES)

    def test_fails_on_unknown_city(self):
        df = make_df(city_id=["LON", "UNKNOWN"])
        with pytest.raises(QualityCheckError, match="Unknown city_id"):
            check_city_ids_known(df, KNOWN_CITIES)


class TestTemperatureRange:
    def test_passes_on_valid_range(self):
        check_temperature_range(make_df())

    def test_fails_on_extreme_high(self):
        df = make_df(temperature_c=[18.5, 99.0])
        with pytest.raises(QualityCheckError, match="temperature"):
            check_temperature_range(df)

    def test_fails_on_extreme_low(self):
        df = make_df(temperature_c=[-100.0, 22.0])
        with pytest.raises(QualityCheckError, match="temperature"):
            check_temperature_range(df)

    def test_nulls_are_skipped(self):
        df = make_df(temperature_c=[None, 22.0])
        check_temperature_range(df)  # should not raise


class TestPrecipitation:
    def test_passes_on_zero(self):
        check_non_negative_precipitation(make_df())

    def test_fails_on_negative_value(self):
        df = make_df(precipitation_mm=[-1.0, 0.0])
        with pytest.raises(QualityCheckError, match="negative"):
            check_non_negative_precipitation(df)


class TestRunAllChecks:
    def test_passes_on_clean_data(self):
        run_all_checks(make_df(), KNOWN_CITIES)

    def test_fails_fast_on_first_error(self):
        df = make_df(metric_id=[None, "id002"])
        with pytest.raises(QualityCheckError):
            run_all_checks(df, KNOWN_CITIES)
