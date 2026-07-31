"""
Quality checks module — custom data assertions on transformed DataFrames.

These checks run AFTER pandera schema validation and test for business-logic
correctness that pandera column-level constraints cannot express (e.g.
cross-column checks, aggregate invariants, FK integrity).
"""
import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger("quality_checks")


class QualityCheckError(Exception):
    """Raised when a mandatory data quality assertion fails."""
    pass


def check_no_null_metric_ids(df: pd.DataFrame) -> None:
    """Every row must have a non-null, non-empty metric_id."""
    null_count = df["metric_id"].isnull().sum()
    empty_count = (df["metric_id"] == "").sum()
    if null_count > 0 or empty_count > 0:
        raise QualityCheckError(
            f"metric_id has {null_count} null and {empty_count} empty values — "
            "composite key generation failed."
        )
    logger.debug("[OK] check_no_null_metric_ids passed.")


def check_no_duplicate_metric_ids(df: pd.DataFrame) -> None:
    """metric_id must be unique across the entire DataFrame batch."""
    dupe_count = df["metric_id"].duplicated().sum()
    if dupe_count > 0:
        raise QualityCheckError(
            f"Found {dupe_count} duplicate metric_id values in batch — "
            "hash collision or timestamp parsing error."
        )
    logger.debug("✅ check_no_duplicate_metric_ids passed.")


def check_city_ids_known(df: pd.DataFrame, known_city_ids: list) -> None:
    """All city_id values must be in the configured cities list."""
    unknown = set(df["city_id"].unique()) - set(known_city_ids)
    if unknown:
        raise QualityCheckError(
            f"Unknown city_id(s) found in batch: {unknown}. "
            "Check config/config.yaml city definitions."
        )
    logger.debug("✅ check_city_ids_known passed.")


def check_temperature_range(df: pd.DataFrame,
                             min_c: float = -60.0,
                             max_c: float = 60.0) -> None:
    """Temperature values must fall within physically plausible range."""
    temp_col = df["temperature_c"].dropna()
    out_of_range = temp_col[(temp_col < min_c) | (temp_col > max_c)]
    if not out_of_range.empty:
        raise QualityCheckError(
            f"Found {len(out_of_range)} temperature values outside [{min_c}, {max_c}]°C range: "
            f"{out_of_range.tolist()[:5]}"
        )
    logger.debug("✅ check_temperature_range passed.")


def check_timestamps_not_future(df: pd.DataFrame, max_forecast_hours: int = 72) -> None:
    """No timestamp_utc should be beyond the configured forecast window (default 72 hours)."""
    import pytz
    from datetime import datetime, timedelta

    now_utc = datetime.now(pytz.utc)
    threshold = now_utc + timedelta(hours=max_forecast_hours)

    future_count = 0
    for ts_str in df["timestamp_utc"].dropna():
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
            if ts > threshold:
                future_count += 1
        except ValueError:
            pass

    if future_count > 0:
        raise QualityCheckError(
            f"{future_count} timestamp_utc values are beyond the {max_forecast_hours}-hour forecast window — "
            "possible API data anomaly."
        )
    logger.debug("✅ check_timestamps_not_future passed.")


def check_non_negative_precipitation(df: pd.DataFrame) -> None:
    """Precipitation cannot be negative."""
    neg_count = (df["precipitation_mm"].dropna() < 0).sum()
    if neg_count > 0:
        raise QualityCheckError(
            f"Found {neg_count} negative precipitation_mm values — data integrity issue."
        )
    logger.debug("✅ check_non_negative_precipitation passed.")


def run_all_checks(df: pd.DataFrame, known_city_ids: list) -> None:
    """
    Runs the full quality check suite on a cleaned fact DataFrame.
    Raises QualityCheckError on first failure.
    """
    logger.info(f"Running data quality checks on {len(df)} rows...")
    check_no_null_metric_ids(df)
    check_no_duplicate_metric_ids(df)
    check_city_ids_known(df, known_city_ids)
    check_temperature_range(df)
    check_timestamps_not_future(df)
    check_non_negative_precipitation(df)
    logger.info("[OK] All data quality checks passed.")
