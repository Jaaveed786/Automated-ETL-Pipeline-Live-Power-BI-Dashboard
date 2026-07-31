# Automated ETL Pipeline + Live Power BI Dashboard

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20%2F%20PostgreSQL-blue?logo=postgresql)](https://www.postgresql.org/)
[![Power BI](https://img.shields.io/badge/BI-Power%20BI-yellow?logo=powerbi)](https://powerbi.microsoft.com/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-green?logo=githubactions)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **A fully automated, production-grade ETL pipeline** that extracts live hourly weather data from the Open-Meteo API across 4 global business hubs, transforms it into a Star Schema data warehouse, and powers an auto-refreshing live Power BI executive dashboard — orchestrated end-to-end via GitHub Actions.

---

## Why This Project Stands Out

Most student BI projects are static: upload a CSV, make a chart, done. This project demonstrates **real data engineering maturity**:

| What It Shows | Why Recruiters Care |
|---|---|
| REST API extraction with retry + backoff | Production-ready resilience |
| Per-city timezone-aware timestamp parsing | Real-world data complexity |
| Star Schema (fact + dimension tables) | BI data modeling knowledge |
| Idempotent upserts (`ON CONFLICT DO UPDATE`) | Pipeline re-run safety |
| GitHub Actions cron orchestration | CI/CD literacy |
| DAX time intelligence (YTD, 7-day MA, MoM%) | Distinguishes from "bar chart" projects |
| Webhook alerting + 30-day data retention | Ops maturity |

---

## 🌐 Live Interactive Demo & Dashboard Sharing

Recruiters and hiring managers can explore this project **without downloading any files or installing software**:

- **Option A (Live Power BI Web Link):** Publish the dashboard to Power BI Service (`app.powerbi.com`) ➔ File ➔ Embed report ➔ Publish to web (public) to generate an interactive public web link.
- **Option B (GitHub Web Repository):** Browse full source code, Star Schema DDL, DAX measures, and automated pytest suite directly at: [`https://github.com/Jaaveed786/Automated-ETL-Pipeline-Live-Power-BI-Dashboard`](https://github.com/Jaaveed786/Automated-ETL-Pipeline-Live-Power-BI-Dashboard).
- **Option C (15-Second Screen Recording GIF):** Embed a short screen recording GIF of interactive dashboard slicer filters in the repository.

📖 *For step-by-step instructions on generating public embed links and sharing with recruiters, see [`docs/live_sharing_guide.md`](docs/live_sharing_guide.md).*

---

## System Architecture

```
┌─────────────────────────┐      ┌──────────────────────────────────┐      ┌─────────────────────────┐
│ Open-Meteo REST API     │      │ Python ETL Engine                │      │ SQL Data Warehouse      │
│ - London                │      │ 1. Extraction (requests + retry) │      │ - dim_date              │
│ - New York              ├─────>│ 2. Validation (pandera schemas)  ├─────>│ - dim_city              │
│ - Tokyo                 │      │ 3. Transform  (Star Schema)      │      │ - fact_weather_metrics  │
│ - Dubai                 │      │ 4. Idempotent Upsert (SQLAlchemy)│      │ (SQLite / Neon Postgres)│
└─────────────────────────┘      └────────────────┬─────────────────┘      └────────────┬────────────┘
                                                  │ Orchestrated hourly                 │
                                                  ▼                                     ▼
                                 ┌──────────────────────────────────┐      ┌─────────────────────────┐
                                 │ GitHub Actions CI/CD             │      │ Live Power BI Dashboard │
                                 │ - Hourly cron schedule           │      │ - Star Schema model     │
                                 │ - GitHub Repository Secrets      │      │ - DAX time intelligence │
                                 │ - Slack Webhook on failure       │      │ - Scheduled auto-refresh│
                                 └──────────────────────────────────┘      └─────────────────────────┘
```

---

## Project Structure

```
etl_powerbi_pipeline/
├── .github/workflows/etl_cron.yml    ← GitHub Actions hourly schedule
├── config/config.yaml                ← Cities, API settings, retention policy
├── sql/
│   ├── ddl_schema.sql                ← Star Schema DDL
│   └── analytical_views.sql         ← Pre-aggregated Power BI views
├── src/
│   ├── extractors/weather_extractor.py   ← Open-Meteo API client + retry
│   ├── transformers/
│   │   ├── cleaning.py               ← Per-city timezone parsing
│   │   ├── schemas.py                ← Pandera validation schemas
│   │   └── star_schema.py            ← Fact + Dimension table builders
│   ├── loaders/
│   │   ├── db_engine.py              ← SQLAlchemy engine factory
│   │   └── idempotent_loader.py      ← Upsert logic (ON CONFLICT DO UPDATE)
│   └── utils/
│       ├── logger.py                 ← Structured logging
│       ├── retention.py              ← 30-day raw data pruner
│       └── notifier.py              ← Slack/Discord webhook alerts
├── dax/dax_measures.md              ← Power BI DAX measures reference
├── tests/
│   ├── test_extraction.py
│   ├── test_transformation.py
│   └── test_loader.py
├── docs/
│   ├── architecture.md              ← Deep-dive architecture documentation
│   ├── interview_qa.md             ← 30 technical interview Q&As
│   ├── setup_guide.md              ← Step-by-step setup instructions
│   ├── powerbi_setup.md            ← Power BI connection & DAX guide
│   └── star_story.md               ← STAR interview storytelling guide
├── pipeline.py                      ← Main ETL entrypoint
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/etl-powerbi-pipeline.git
cd etl-powerbi-pipeline
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
copy .env.example .env
# Edit .env — set DATABASE_URL and (optionally) SLACK_WEBHOOK_URL
```

### 3. Run the Pipeline (Single Execution)
```bash
python pipeline.py --run-once
```

### 4. Run Tests
```bash
pytest tests/ -v
```

### 5. Verify Zero Duplicates
```bash
# SQLite
sqlite3 data/warehouse.db "SELECT metric_id, COUNT(*) FROM fact_weather_metrics GROUP BY metric_id HAVING COUNT(*) > 1;"
# Expected output: (empty — no duplicates)
```

---

## Database Configuration

| Environment | `DATABASE_URL` value |
|---|---|
| Local (SQLite) | `sqlite:///data/warehouse.db` |
| Cloud (Neon Postgres) | `postgresql+psycopg2://user:pass@ep-xyz.neon.tech/neondb?sslmode=require` |
| Cloud (Supabase) | `postgresql+psycopg2://postgres:pass@db.xyz.supabase.co:5432/postgres` |

> **Note:** For GitHub Actions cloud runs, set `DATABASE_URL` as a **GitHub Repository Secret** (not in `.env`) via: `Settings → Secrets and variables → Actions → New repository secret`

---

## Star Schema Data Model

```
         dim_date              dim_city
     ┌──────────────┐      ┌──────────────┐
     │ date_key (PK)│      │ city_id (PK) │
     │ full_date    │      │ city_name    │
     │ year         │      │ country      │
     │ quarter      │      │ timezone     │
     │ month_name   │      └──────┬───────┘
     │ is_weekend   │             │
     └──────┬───────┘             │
            │    1:Many           │ 1:Many
            └──────────┬──────────┘
                       │
              fact_weather_metrics
           ┌──────────────────────────┐
           │ metric_id (PK)  ← MD5   │
           │ city_id    (FK)          │
           │ date_key   (FK)          │
           │ timestamp_utc            │
           │ timestamp_local          │
           │ temperature_c            │
           │ relative_humidity        │
           │ precipitation_mm         │
           │ wind_speed_kmh           │
           │ surface_pressure_hpa     │
           └──────────────────────────┘
```

---

## GitHub Actions Setup

1. Push this repository to GitHub
2. Go to `Settings → Secrets and variables → Actions`
3. Add these secrets:

| Secret Name | Value |
|---|---|
| `DATABASE_URL` | Your Neon/Supabase PostgreSQL connection string |
| `SLACK_WEBHOOK_URL` | Your Slack Incoming Webhook URL (optional) |

The pipeline then runs **every hour automatically** on GitHub's free compute tier.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| API Client | `requests` + `urllib3.util.Retry` |
| Data Processing | `pandas` |
| Validation | `pandera` |
| ORM / Database | `SQLAlchemy` + SQLite / PostgreSQL |
| Orchestration | GitHub Actions (cron) |
| BI Dashboard | Microsoft Power BI |
| DAX | Time intelligence (YTD, 7D MA, MoM%, Anomaly Detection) |
| Testing | `pytest` |
| Alerting | Slack / Discord Webhook |

---

## Extension Paths (Documented, Not Built in v1)

- **Snowflake / Oracle**: Replace `DATABASE_URL` with Snowflake connector URI. DDL in `sql/ddl_schema.sql` is dialect-compatible.
- **Apache Airflow**: Replace `etl_cron.yml` with a Directed Acyclic Graph (DAG) using `PythonOperator` for each pipeline step.
- **dbt**: Replace `sql/analytical_views.sql` with dbt models for lineage tracking.
- **Incremental Refresh**: Enable Power BI incremental refresh when fact table exceeds ~1M rows.

---

## License
MIT License — see [LICENSE](LICENSE)
