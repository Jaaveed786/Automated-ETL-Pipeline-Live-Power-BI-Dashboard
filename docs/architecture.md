# System Architecture — Deep Dive

## Overview

This document provides a detailed technical breakdown of every component in the ETL pipeline, covering design decisions, data flow, failure modes, and extension paths.

---

## Component Map

```
Open-Meteo API
     │
     │  HTTP GET (requests.Session + Retry)
     ▼
WeatherExtractor (src/extractors/weather_extractor.py)
     │
     │  Raw JSON archived to data/raw/YYYY-MM-DD_HHMMSS.json
     │  (Pruned after 30 days by retention.py)
     ▼
clean_all_cities (src/transformers/cleaning.py)
     │
     │  Per-city zoneinfo timezone conversion (UTC + Local)
     │  Flat DataFrame with 1 row per hourly observation
     ▼
Star Schema Builders (src/transformers/star_schema.py)
     │
     ├──► dim_date  (date_key, year, quarter, month, is_weekend …)
     ├──► dim_city  (city_id, city_name, country, timezone)
     └──► fact_weather_metrics (metric_id MD5 hash, FK → dim_date, dim_city)
     │
     ▼
SQLAlchemy Engine (src/loaders/db_engine.py)
     │  DATABASE_URL from environment variable
     │  SQLite (local) or PostgreSQL (cloud)
     ▼
IdempotentLoader (src/loaders/idempotent_loader.py)
     │  ON CONFLICT(metric_id) DO UPDATE
     │  Guaranteed zero duplicate rows on re-runs
     ▼
SQL Data Warehouse
     │  dim_date, dim_city, fact_weather_metrics
     │  Indexed on city_id, date_key, timestamp_utc
     ▼
Power BI Desktop / Power BI Service
     │  DirectQuery or Import mode
     │  Star Schema relationships
     │  DAX time intelligence + anomaly detection
     ▼
Scheduled Refresh (Power BI Service)
     │  Hourly / Daily auto-refresh
     ▼
Executive Dashboard
```

---

## Extraction Layer

### Open-Meteo API
- **Endpoint:** `https://api.open-meteo.com/v1/forecast`
- **Authentication:** None required (public API)
- **Rate Limits:** None enforced for basic usage
- **Data Freshness:** Updates every ~15 minutes; pipeline runs hourly

### Resilience Design
The extractor uses `urllib3.util.Retry` mounted on a `requests.Session`:

```
Max Retries: 3
Backoff Factor: 1s (exponential: 1s → 2s → 4s)
Retry on: 429, 500, 502, 503, 504
```

If all retries are exhausted, the exception propagates to `pipeline.py` which catches it, logs it, and fires the Slack webhook alert.

### Raw Data Archival
Every successful extraction dumps a timestamped JSON file to `data/raw/`. This enables:
- **Replay**: Re-run the transformation on historical data without hitting the API
- **Audit Trail**: Prove what data was fetched and when
- **Debugging**: Compare raw vs. transformed if data quality issues appear

The `retention.py` module prunes files older than 30 days to prevent unbounded disk growth.

---

## Transformation Layer

### Timezone Strategy
Open-Meteo returns timestamps in the **city's local timezone** by default when `timezone` is passed as a parameter. The cleaning module:
1. Parses the local timestamp string using `datetime.strptime`
2. Localizes it with `pytz.timezone(city_timezone).localize(dt)`
3. Converts to UTC using `.astimezone(pytz.utc)`
4. Stores **both** `timestamp_local` and `timestamp_utc` in the fact table

This means Power BI can display visuals in either UTC (for cross-city comparison) or local time (for city-specific business analysis).

### Metric ID (Composite Hash Key)
```python
metric_id = hashlib.md5(f"{city_id}_{utc_timestamp}".encode()).hexdigest()
```
- Deterministic: same city + timestamp always produces the same hash
- Collision-resistant for this cardinality (4 cities × 24 hours × 365 days = ~35K rows/year)
- Enables `ON CONFLICT(metric_id)` upsert without needing a sequence/auto-increment

### Star Schema Design Rationale

| Design Choice | Reason |
|---|---|
| Separate `dim_date` | Enables Power BI native date hierarchy and time intelligence functions |
| Integer `date_key` (YYYYMMDD) | Faster join than string date; human-readable; standard BI pattern |
| Separate `dim_city` | Enables city-level filtering without fact table fan-out |
| No slowly changing dimension (SCD) | City metadata is static for this v1 scope |

---

## Loading Layer

### Idempotency Contract
The pipeline can be run N times on the same data and the database will always end in the same state. This is achieved via:

**SQLite:**
```sql
INSERT OR REPLACE INTO fact_weather_metrics (...)
-- or equivalently:
INSERT INTO fact_weather_metrics (...) ON CONFLICT(metric_id) DO UPDATE SET ...
```

**PostgreSQL (Neon/Supabase):**
```sql
INSERT INTO fact_weather_metrics (...) 
ON CONFLICT (metric_id) DO UPDATE SET
    temperature_c = EXCLUDED.temperature_c, ...
```

### SQLAlchemy Abstraction
The `db_engine.py` factory reads `DATABASE_URL` from the environment:
- `sqlite:///data/warehouse.db` → SQLite (zero-config local dev)
- `postgresql+psycopg2://...` → PostgreSQL (cloud production)

Switching databases requires changing **one environment variable**, not the application code.

---

## Orchestration Layer

### GitHub Actions Cron
```yaml
on:
  schedule:
    - cron: "0 * * * *"   # Every hour at :00
```
- Runs on GitHub's free ubuntu-latest runners
- Secrets injected from GitHub Repository Secrets (never from `.env`)
- No always-on server required

### Failure Notification Flow
```
pipeline.py raises exception
     │
     ▼
traceback captured as string
     │
     ▼
notifier.send_failure_alert() called
     │
     ▼
HTTP POST to SLACK_WEBHOOK_URL
     │
     ▼
Slack / Discord message with error snippet
```

---

## Power BI Layer

### Connection Mode
| Database | Recommended Mode |
|---|---|
| Local SQLite | Import (manual refresh or scheduled via Gateway) |
| Neon / Supabase Postgres | Import with scheduled refresh (no Gateway needed) |

### Relationship Configuration
In Power BI Desktop Model View:
1. `dim_date[date_key]` → `fact_weather_metrics[date_key]` — Single direction filter
2. `dim_city[city_id]` → `fact_weather_metrics[city_id]` — Single direction filter

Do NOT enable bidirectional cross-filtering — it causes ambiguity in multi-city slicers.

---

## Data Flow Volumes (Estimates)

| Period | Rows in fact_weather_metrics |
|---|---|
| Per run | ~48 rows (4 cities × ~12 new hours) |
| Per day | ~96 rows |
| Per month | ~2,880 rows |
| Per year | ~35,040 rows |

At this scale, SQLite is more than sufficient. PostgreSQL becomes relevant if you add more cities or metrics.

---

## Extension Paths

### Snowflake / Oracle
- Change `DATABASE_URL` to Snowflake connector URI
- Install `snowflake-sqlalchemy` 
- DDL in `sql/ddl_schema.sql` is dialect-portable (standard SQL)

### Apache Airflow
Replace GitHub Actions with a DAG:
```python
extract_task  = PythonOperator(task_id="extract",  python_callable=extractor.extract_all)
clean_task    = PythonOperator(task_id="clean",    python_callable=clean_all_cities)
load_task     = PythonOperator(task_id="load",     python_callable=run_load_phase)
extract_task >> clean_task >> load_task
```

### dbt (Data Build Tool)
Replace `sql/analytical_views.sql` with dbt models for:
- Automatic lineage tracking
- Column-level documentation
- Test assertions on SQL transforms
