# STAR Interview Story — ETL Pipeline + Power BI Dashboard

Use this document as a structured guide for talking about this project in interviews.
Practice each section out loud until it flows naturally in under 3 minutes.

---

## The STAR Framework

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ S — SITUATION                                                                    │
│                                                                                  │
│ "In most academic and student BI projects, the workflow is static — you upload   │
│ a pre-cleaned CSV, connect it to Power BI, drag a few fields into bar charts,   │
│ and call it done. That kind of project doesn't demonstrate the skills that       │
│ analytics engineering roles actually require: building pipelines, handling       │
│ real-world data inconsistencies, or thinking about what happens when the source  │
│ API goes down at 2am."                                                           │
├──────────────────────────────────────────────────────────────────────────────────┤
│ T — TASK                                                                         │
│                                                                                  │
│ "I wanted to build something that looked and behaved like a real production      │
│ data pipeline — one that could run unattended, recover from failures, and        │
│ feed an always-fresh dashboard without me needing to manually trigger anything.  │
│ I chose weather analytics as the domain because Open-Meteo provides free,        │
│ reliable hourly data across global cities with no API key required."             │
├──────────────────────────────────────────────────────────────────────────────────┤
│ A — ACTION                                                                       │
│                                                                                  │
│ "I built the pipeline in five stages:                                            │
│                                                                                  │
│ First, the extractor — a Python class using requests with automatic exponential  │
│ backoff and retry on 5xx errors and rate limits. It archives every raw API       │
│ response to disk for replayability and audit trail.                              │
│                                                                                  │
│ Second, the transformation — I used pytz to handle per-city timezone             │
│ conversion dynamically. Tokyo, London, New York, and Dubai all have different    │
│ UTC offsets, so local hour had to be computed per city rather than applying a    │
│ single global offset. I then modelled the data into a Star Schema with a         │
│ fact_weather_metrics table and two dimension tables: dim_date and dim_city.      │
│                                                                                  │
│ Third, the loading layer — I used SQLAlchemy with ON CONFLICT DO UPDATE upserts, │
│ so running the pipeline 10 times on the same data produces exactly the same      │
│ result as running it once. I verified this with a SQL assertion test in pytest.  │
│                                                                                  │
│ Fourth, orchestration — I set up a GitHub Actions cron workflow that fires every │
│ hour, with pipeline secrets stored as GitHub Repository Secrets and a Slack      │
│ webhook that fires automatically on any pipeline exception.                      │
│                                                                                  │
│ Fifth, the Power BI dashboard — I built time intelligence DAX measures including │
│ a 7-day moving average, year-to-date average, month-over-month change, and a    │
│ temperature anomaly detector using globally-scoped standard deviation."          │
├──────────────────────────────────────────────────────────────────────────────────┤
│ R — RESULT                                                                       │
│                                                                                  │
│ [Fill in with your actual measured values after running the pipeline:]           │
│                                                                                  │
│ "The pipeline has been running every hour for [X days] with [0 / N] failures.   │
│ The duplicate-check SQL query returns zero rows after [X] pipeline runs.         │
│ Power BI visuals load in approximately [X] seconds after a dataset refresh.      │
│ The full pipeline execution takes roughly [X] seconds per run."                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## How to Measure Your RESULT Numbers

Run the following after at least 24 hours of live pipeline operation:

### 1. Count successful pipeline runs
```bash
# Check GitHub Actions run history in the Actions tab
# Note: total runs, successful runs, failed runs
```

### 2. Verify zero duplicates
```sql
-- Run in SQLite or Neon SQL editor
SELECT COUNT(*) AS total_rows FROM fact_weather_metrics;

SELECT metric_id, COUNT(*) AS cnt
FROM fact_weather_metrics
GROUP BY metric_id
HAVING cnt > 1;
-- Must return: (empty)
```

### 3. Time a pipeline run
```bash
# Windows PowerShell
Measure-Command { python pipeline.py --run-once }

# macOS / Linux
time python pipeline.py --run-once
```

### 4. Time a Power BI refresh
- In Power BI Desktop → click **Refresh** → note start and end times in the status bar

---

## Key Talking Points by Interview Type

### For Data Analyst Roles
Focus on:
- Star Schema design and why it enables faster DAX calculations
- DAX time intelligence (YTD, moving averages, MoM change)
- Power BI data model relationships and why bidirectional filtering is avoided
- SQL analytical views pre-aggregated for query performance

### For Data Engineer / Analytics Engineer Roles
Focus on:
- Idempotent upserts (ON CONFLICT DO UPDATE) and why they matter
- Retry logic with exponential backoff on the API client
- GitHub Actions cron + Repository Secrets pattern
- SQLAlchemy abstraction enabling SQLite → PostgreSQL → Snowflake with one config change
- Per-city timezone handling with pytz

### For BI Developer Roles
Focus on:
- DAX measure correctness — specifically the CALCULATE(STDEV.P, ALL(dim_date)) scoping decision
- Power BI star schema relationship setup (single vs. bidirectional)
- Report page structure for executive vs. analyst audiences
- Scheduled refresh configuration on Power BI Service

### For General Software Engineering Roles
Focus on:
- Modular Python package structure (extractors / transformers / loaders / utils)
- pytest test coverage for extraction, transformation, and idempotency
- Secrets management via environment variables + GitHub Repository Secrets
- Raw data retention policy and why it matters operationally

---

## Anticipated Follow-Up Questions & Short Answers

**"Why Open-Meteo and not a paid API?"**
> Free, no key required, reliable uptime, rich hourly data — ideal for an automated portfolio project. The architecture is API-agnostic; swapping to Alpha Vantage or OpenWeatherMap requires changing the extractor class only.

**"Could you handle 400 cities instead of 4?"**
> Yes — the current sequential loop would be replaced with `concurrent.futures.ThreadPoolExecutor` for parallel fetching, and bulk upserts via `COPY` or pandas `to_sql()` for PostgreSQL.

**"Why not Airflow?"**
> Airflow is appropriate for team-scale pipeline management with dozens of DAGs and complex dependencies. For a single automated pipeline on a solo project timeline, GitHub Actions provides equivalent scheduling with zero infrastructure overhead and demonstrates CI/CD literacy.

**"What breaks first as this scales?"**
> The row-by-row SQLAlchemy upsert loop — it becomes the bottleneck beyond ~100K rows/run. Fix: batch upserts using PostgreSQL `COPY` command or SQLAlchemy `insert().on_conflict_do_update()` with bulk arrays.

**"What would you monitor in production?"**
> Pipeline success/failure rate via GitHub Actions history, data freshness (MAX timestamp within last 2 hours), duplicate row count via daily assertion query, and raw data directory size for retention compliance.
