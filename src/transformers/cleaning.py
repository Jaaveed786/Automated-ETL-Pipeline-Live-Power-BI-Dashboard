import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List

import pandas as pd
import pytz

from src.utils.logger import setup_logger

logger = setup_logger("cleaning")


def parse_city_weather(raw_payload: Dict[str, Any]) -> pd.DataFrame:
    """
    Parses a raw Open-Meteo API payload for a single city and returns
    a flat DataFrame with one row per hourly observation.

    Applies per-city zoneinfo timezone conversion to derive accurate
    local timestamps (e.g. Asia/Tokyo, America/New_York).
    """
    city_id = raw_payload["city_id"]
    city_name = raw_payload["city_name"]
    country = raw_payload["country"]
    city_timezone = raw_payload["timezone"]
    hourly = raw_payload.get("hourly", {})

    timestamps_utc_str = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    precipitations = hourly.get("precipitation", [])
    wind_speeds = hourly.get("wind_speed_10m", [])
    pressures = hourly.get("surface_pressure", [])

    tz = pytz.timezone(city_timezone)
    records = []

    for i, ts_str in enumerate(timestamps_utc_str):
        # Parse local datetime from Open-Meteo (returned in city-local time)
        local_dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M")
        local_dt = tz.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.utc)

        date_key = int(utc_dt.strftime("%Y%m%d"))

        # Build a deterministic composite hash key for idempotent upserts
        metric_id = hashlib.md5(f"{city_id}_{utc_dt.isoformat()}".encode()).hexdigest()

        records.append({
            "metric_id": metric_id,
            "city_id": city_id,
            "city_name": city_name,
            "country": country,
            "timezone": city_timezone,
            "date_key": date_key,
            "timestamp_utc": utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timestamp_local": local_dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "temperature_c": _safe_float(temperatures, i),
            "relative_humidity": _safe_float(humidities, i),
            "precipitation_mm": _safe_float(precipitations, i),
            "wind_speed_kmh": _safe_float(wind_speeds, i),
            "surface_pressure_hpa": _safe_float(pressures, i),
        })

    df = pd.DataFrame(records)
    logger.info(f"Parsed {len(df)} hourly records for {city_name}.")
    return df


def _safe_float(lst: List, idx: int):
    """Return float value at index, or None if missing/out-of-bounds."""
    try:
        val = lst[idx]
        return float(val) if val is not None else None
    except (IndexError, TypeError):
        return None


def clean_all_cities(raw_payloads: List[Dict[str, Any]]) -> pd.DataFrame:
    """Parse and concatenate all city payloads into a single clean DataFrame."""
    frames = [parse_city_weather(p) for p in raw_payloads]
    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"Combined cleaned DataFrame shape: {combined.shape}")
    return combined
