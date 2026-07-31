# Resume Bullets — Automated ETL Pipeline + Live Power BI Dashboard

Copy-paste ready resume bullets for different role types.
Customise the RESULT numbers in brackets `[ ]` with your actual measured values after running the pipeline.

---

## For Data Analyst Roles

```
• Built an end-to-end automated ETL pipeline extracting live hourly weather data from
  Open-Meteo API across 4 global cities, transforming it into a Star Schema
  (dim_date, dim_city, fact_weather_metrics) and loading it into a SQL data warehouse
  using Python (pandas, SQLAlchemy) with idempotent upserts (ON CONFLICT DO UPDATE).

• Designed and deployed a live Power BI executive dashboard with DAX time-intelligence
  measures including 7-day rolling average, YTD aggregation, MoM % change, and a
  statistically-scoped anomaly detection flag using globally-normalised standard deviation.

• Automated hourly data pipeline execution via GitHub Actions cron with Slack webhook
  failure alerting, achieving [X]% pipeline reliability over [X] days of operation.
```

---

## For Data Engineer / Analytics Engineer Roles

```
• Architected a production-grade Python ETL pipeline (requests, pandas, SQLAlchemy)
  with exponential backoff retry logic, per-city pytz timezone normalisation, and
  Pandera schema validation enforcing 6 data quality checks across every pipeline run.

• Implemented idempotent upsert loading (ON CONFLICT DO UPDATE) ensuring zero duplicate
  rows across [X] pipeline re-runs, verified by automated SQL assertion tests in pytest.

• Orchestrated hourly pipeline execution via GitHub Actions cron (zero infrastructure cost)
  with GitHub Repository Secrets management and Slack webhook alerting on failures.

• Designed a modular SQLAlchemy database layer supporting single-line config switching
  from SQLite (local dev) to PostgreSQL (Neon/Supabase cloud), with identical upsert
  logic across both dialects.

• Implemented 30-day raw JSON data retention policy with automated file pruning to
  prevent unbounded disk growth on scheduled cloud runners.
```

---

## For BI Developer Roles

```
• Built a Star Schema data model (fact + 2 dimension tables) in Power BI Desktop with
  correct single-direction relationship filtering between dim_date, dim_city, and
  fact_weather_metrics for accurate cross-slicer DAX evaluation.

• Authored 15 production DAX measures including TOTALYTD, DATESINPERIOD rolling windows,
  DATEADD MoM comparisons, RANKX city ranking, and a globally-scoped anomaly flag using
  CALCULATE(STDEV.P, ALL(dim_date)) for stable threshold computation.

• Configured Power BI Service scheduled refresh on cloud-hosted PostgreSQL source,
  enabling dashboard auto-refresh without manual intervention.
```

---

## For General Software Engineering Roles

```
• Engineered a modular Python data pipeline package (src/extractors, transformers,
  loaders, utils) with full pytest test coverage across 5 test modules including
  mocked API responses, schema validation, idempotency verification, and retention pruner
  boundary condition tests.

• Configured CI/CD via GitHub Actions with hourly cron scheduling, secrets management
  via Repository Secrets (DATABASE_URL, SLACK_WEBHOOK_URL), and automated test
  execution on every push.

• Applied production data engineering patterns: exponential backoff retry, deterministic
  MD5 composite keys, schema-first validation, structured logging, and data lifecycle
  management (30-day retention pruner).
```

---

## LinkedIn Project Description

```
🔄 Automated ETL Pipeline + Live Power BI Dashboard

Built a fully automated, end-to-end data engineering pipeline that:
→ Extracts live hourly weather data from Open-Meteo API (no key required)
→ Transforms it into a Star Schema with per-city timezone normalisation
→ Loads it idempotently into SQLite/PostgreSQL via SQLAlchemy
→ Runs every hour via GitHub Actions cron (zero infrastructure cost)
→ Powers a live Power BI dashboard with DAX time intelligence & anomaly detection

Tech: Python • pandas • SQLAlchemy • pandera • GitHub Actions • Power BI • DAX

What makes it production-grade:
✅ Retry logic with exponential backoff (handles API failures)
✅ ON CONFLICT DO UPDATE upserts (idempotent — zero duplicates on re-runs)
✅ GitHub Repository Secrets (no committed credentials)
✅ 30-day raw data retention pruner
✅ Slack webhook alerts on pipeline failure
✅ Full pytest test suite (5 modules, 25+ test cases)
```

---

## ATS Keywords to Include

Include these keywords naturally in your resume/LinkedIn to pass ATS filters:

`ETL Pipeline` · `Data Warehouse` · `Star Schema` · `Dimensional Modeling` · `Python` ·
`pandas` · `SQLAlchemy` · `PostgreSQL` · `SQLite` · `REST API` · `Power BI` · `DAX` ·
`Time Intelligence` · `GitHub Actions` · `CI/CD` · `Data Quality` · `pytest` ·
`Automated Pipeline` · `Scheduled Refresh` · `Data Engineering` · `Analytics Engineering` ·
`Business Intelligence` · `Data Modeling` · `SQL` · `Idempotent` · `Data Validation`
