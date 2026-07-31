import pandas as pd
from sqlalchemy import Engine, text
from src.utils.logger import setup_logger

logger = setup_logger("idempotent_loader")


def ensure_schema(engine: Engine) -> None:
    """Creates all required tables (DDL) if they do not already exist."""
    with engine.connect() as conn:
        # Detect dialect
        dialect = engine.dialect.name

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_date (
                date_key    INTEGER PRIMARY KEY,
                full_date   TEXT NOT NULL,
                year        INTEGER,
                quarter     INTEGER,
                month       INTEGER,
                month_name  TEXT,
                week        INTEGER,
                day_of_week INTEGER,
                day_name    TEXT,
                is_weekend  INTEGER
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_city (
                city_id   TEXT PRIMARY KEY,
                city_name TEXT NOT NULL,
                country   TEXT,
                timezone  TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_weather_metrics (
                metric_id            TEXT PRIMARY KEY,
                city_id              TEXT NOT NULL,
                date_key             INTEGER NOT NULL,
                timestamp_utc        TEXT NOT NULL,
                timestamp_local      TEXT,
                temperature_c        REAL,
                relative_humidity    REAL,
                precipitation_mm     REAL,
                wind_speed_kmh       REAL,
                surface_pressure_hpa REAL,
                FOREIGN KEY (city_id)  REFERENCES dim_city(city_id),
                FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
            )
        """))
        conn.commit()

    logger.info("Schema ensured (all tables present).")


def upsert_dim_date(engine: Engine, df: pd.DataFrame) -> int:
    """Idempotent insert of dim_date rows — skips existing date_keys."""
    if df.empty:
        return 0
    with engine.connect() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO dim_date
                    (date_key, full_date, year, quarter, month, month_name,
                     week, day_of_week, day_name, is_weekend)
                VALUES
                    (:date_key, :full_date, :year, :quarter, :month, :month_name,
                     :week, :day_of_week, :day_name, :is_weekend)
                ON CONFLICT(date_key) DO NOTHING
            """), row.to_dict())
        conn.commit()
    logger.info(f"Upserted {len(df)} rows into dim_date.")
    return len(df)


def upsert_dim_city(engine: Engine, df: pd.DataFrame) -> int:
    """Idempotent insert of dim_city rows — skips existing city_ids."""
    if df.empty:
        return 0
    with engine.connect() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO dim_city (city_id, city_name, country, timezone)
                VALUES (:city_id, :city_name, :country, :timezone)
                ON CONFLICT(city_id) DO NOTHING
            """), row.to_dict())
        conn.commit()
    logger.info(f"Upserted {len(df)} rows into dim_city.")
    return len(df)


def upsert_fact_weather(engine: Engine, df: pd.DataFrame) -> int:
    """
    Idempotent upsert of fact_weather_metrics rows.
    Conflicts on metric_id trigger a full UPDATE of all metric columns.
    Prevents any duplicate rows on re-runs.
    """
    if df.empty:
        return 0
    with engine.connect() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_weather_metrics
                    (metric_id, city_id, date_key, timestamp_utc, timestamp_local,
                     temperature_c, relative_humidity, precipitation_mm,
                     wind_speed_kmh, surface_pressure_hpa)
                VALUES
                    (:metric_id, :city_id, :date_key, :timestamp_utc, :timestamp_local,
                     :temperature_c, :relative_humidity, :precipitation_mm,
                     :wind_speed_kmh, :surface_pressure_hpa)
                ON CONFLICT(metric_id) DO UPDATE SET
                    temperature_c        = excluded.temperature_c,
                    relative_humidity    = excluded.relative_humidity,
                    precipitation_mm     = excluded.precipitation_mm,
                    wind_speed_kmh       = excluded.wind_speed_kmh,
                    surface_pressure_hpa = excluded.surface_pressure_hpa
            """), row.to_dict())
        conn.commit()
    logger.info(f"Upserted {len(df)} rows into fact_weather_metrics.")
    return len(df)
