-- ============================================================
--  Analytical SQL Views — Pre-aggregated for Power BI
--  Compatible with: SQLite, PostgreSQL
-- ============================================================

-- ── View 1: Daily Summary per City ──────────────────────────
CREATE VIEW IF NOT EXISTS vw_daily_city_summary AS
SELECT
    f.date_key,
    d.full_date,
    d.year,
    d.month,
    d.month_name,
    d.quarter,
    d.is_weekend,
    c.city_id,
    c.city_name,
    c.country,
    c.timezone,
    COUNT(*)                                 AS hourly_record_count,
    ROUND(AVG(f.temperature_c), 2)           AS avg_temp_c,
    ROUND(MAX(f.temperature_c), 2)           AS max_temp_c,
    ROUND(MIN(f.temperature_c), 2)           AS min_temp_c,
    ROUND(AVG(f.relative_humidity), 2)       AS avg_humidity_pct,
    ROUND(SUM(f.precipitation_mm), 2)        AS total_precipitation_mm,
    ROUND(AVG(f.wind_speed_kmh), 2)          AS avg_wind_speed_kmh,
    ROUND(AVG(f.surface_pressure_hpa), 2)    AS avg_pressure_hpa
FROM fact_weather_metrics f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_city c ON f.city_id  = c.city_id
GROUP BY f.date_key, c.city_id;

-- ── View 2: Last 7-Day Temperature Trend ────────────────────
CREATE VIEW IF NOT EXISTS vw_last7days_temp_trend AS
SELECT
    f.timestamp_utc,
    c.city_name,
    c.country,
    f.temperature_c,
    f.relative_humidity,
    f.wind_speed_kmh
FROM fact_weather_metrics f
JOIN dim_city c ON f.city_id = c.city_id
WHERE date(f.timestamp_utc) >= date('now', '-7 days')
ORDER BY f.timestamp_utc DESC;

-- ── View 3: City Comparison Latest Hour ─────────────────────
CREATE VIEW IF NOT EXISTS vw_latest_city_snapshot AS
SELECT
    c.city_name,
    c.country,
    c.timezone,
    f.timestamp_utc,
    f.timestamp_local,
    f.temperature_c,
    f.relative_humidity,
    f.precipitation_mm,
    f.wind_speed_kmh
FROM fact_weather_metrics f
JOIN dim_city c ON f.city_id = c.city_id
WHERE f.timestamp_utc = (
    SELECT MAX(timestamp_utc)
    FROM fact_weather_metrics fi
    WHERE fi.city_id = f.city_id
);
