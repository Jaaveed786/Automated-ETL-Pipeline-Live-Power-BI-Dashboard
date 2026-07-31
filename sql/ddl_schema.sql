-- ============================================================
--  DDL: Star Schema Tables for Weather ETL Data Warehouse
--  Compatible with: SQLite, PostgreSQL
--  Note: ON CONFLICT syntax requires SQLite 3.24+ or PostgreSQL
-- ============================================================

-- ── Dimension: Date ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INTEGER PRIMARY KEY,   -- YYYYMMDD integer key
    full_date   TEXT    NOT NULL,
    year        INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    month_name  TEXT    NOT NULL,
    week        INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,      -- 1=Monday, 7=Sunday
    day_name    TEXT    NOT NULL,
    is_weekend  INTEGER NOT NULL       -- 1=Weekend, 0=Weekday
);

-- ── Dimension: City ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_city (
    city_id   TEXT PRIMARY KEY,
    city_name TEXT NOT NULL,
    country   TEXT,
    timezone  TEXT                     -- e.g. 'Asia/Tokyo', 'Europe/London'
);

-- ── Fact: Weather Hourly Metrics ────────────────────────────
CREATE TABLE IF NOT EXISTS fact_weather_metrics (
    metric_id            TEXT    PRIMARY KEY,  -- MD5(city_id + timestamp_utc)
    city_id              TEXT    NOT NULL,
    date_key             INTEGER NOT NULL,
    timestamp_utc        TEXT    NOT NULL,
    timestamp_local      TEXT,
    temperature_c        REAL,
    relative_humidity    REAL,
    precipitation_mm     REAL,
    wind_speed_kmh       REAL,
    surface_pressure_hpa REAL,
    FOREIGN KEY (city_id)  REFERENCES dim_city(city_id),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- ── Indexes for Power BI Query Performance ──────────────────
CREATE INDEX IF NOT EXISTS idx_fact_city_id   ON fact_weather_metrics (city_id);
CREATE INDEX IF NOT EXISTS idx_fact_date_key  ON fact_weather_metrics (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_ts_utc    ON fact_weather_metrics (timestamp_utc);
