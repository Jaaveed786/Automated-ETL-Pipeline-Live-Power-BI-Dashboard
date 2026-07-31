import pandas as pd
from typing import List
from src.utils.logger import setup_logger

logger = setup_logger("star_schema")


def build_dim_date(fact_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates the dim_date dimension table from unique date_key values
    present in the fact DataFrame.

    Columns: date_key, full_date, year, quarter, month, month_name,
             week, day_of_week, day_name, is_weekend
    """
    unique_dates = fact_df["date_key"].unique()
    records = []

    for dk in unique_dates:
        dt = pd.to_datetime(str(dk), format="%Y%m%d")
        records.append({
            "date_key": int(dk),
            "full_date": dt.strftime("%Y-%m-%d"),
            "year": dt.year,
            "quarter": (dt.month - 1) // 3 + 1,
            "month": dt.month,
            "month_name": dt.strftime("%B"),
            "week": dt.isocalendar()[1],
            "day_of_week": dt.dayofweek + 1,     # 1=Monday … 7=Sunday
            "day_name": dt.strftime("%A"),
            "is_weekend": int(dt.dayofweek >= 5),
        })

    dim_date = pd.DataFrame(records).drop_duplicates(subset="date_key")
    logger.info(f"Built dim_date with {len(dim_date)} rows.")
    return dim_date


def build_dim_city(fact_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates the dim_city dimension table from unique city metadata
    embedded in the cleaned fact DataFrame.

    Columns: city_id, city_name, country, timezone
    """
    dim_city = (
        fact_df[["city_id", "city_name", "country", "timezone"]]
        .drop_duplicates(subset="city_id")
        .reset_index(drop=True)
    )
    logger.info(f"Built dim_city with {len(dim_city)} rows.")
    return dim_city


def build_fact_weather_metrics(clean_df: pd.DataFrame) -> pd.DataFrame:
    """
    Selects and returns only the fact columns from the clean DataFrame
    (drops dimension metadata that belongs in dim tables).
    """
    fact_cols = [
        "metric_id", "city_id", "date_key",
        "timestamp_utc", "timestamp_local",
        "temperature_c", "relative_humidity",
        "precipitation_mm", "wind_speed_kmh", "surface_pressure_hpa"
    ]
    fact_df = clean_df[fact_cols].copy()
    logger.info(f"Built fact_weather_metrics with {len(fact_df)} rows.")
    return fact_df
