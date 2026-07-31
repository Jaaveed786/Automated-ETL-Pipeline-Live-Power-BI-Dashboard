# Setup Guide — Step-by-Step Local & Cloud Deployment

Complete instructions for setting up the ETL pipeline from scratch on Windows, macOS, or Linux.

---

## Prerequisites

| Requirement | Version | Check Command |
|---|---|---|
| Python | 3.11+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |
| SQLite (local dev) | 3.24+ | `sqlite3 --version` |

---

## Part 1: Local Setup (SQLite)

### Step 1 — Clone the Repository
```bash
git clone https://github.com/yourusername/etl-powerbi-pipeline.git
cd "etl-powerbi-pipeline"
```

### Step 2 — Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure Environment Variables
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` with your preferred text editor:
```env
DATABASE_URL=sqlite:///data/warehouse.db
SLACK_WEBHOOK_URL=                         # Optional — leave blank to skip alerts
LOG_LEVEL=INFO
```

### Step 5 — Create Data Directory
```bash
mkdir data
mkdir data\raw          # Windows
mkdir -p data/raw       # macOS / Linux
```

### Step 6 — Run the Pipeline
```bash
python pipeline.py --run-once
```

Expected console output:
```
[2024-07-01 09:00:00] [INFO] [pipeline] - ============================================================
[2024-07-01 09:00:00] [INFO] [pipeline] - Starting pipeline: weather_etl_pipeline
[2024-07-01 09:00:00] [INFO] [pipeline] - ============================================================
[2024-07-01 09:00:00] [INFO] [pipeline] - [1/5] EXTRACT — Fetching weather data from Open-Meteo API...
[2024-07-01 09:00:01] [INFO] [weather_extractor] - Extracting weather data for London (LON)...
[2024-07-01 09:00:02] [INFO] [weather_extractor] - Extracting weather data for New York (NYC)...
[2024-07-01 09:00:03] [INFO] [weather_extractor] - Extracting weather data for Tokyo (TYO)...
[2024-07-01 09:00:04] [INFO] [weather_extractor] - Extracting weather data for Dubai (DXB)...
[2024-07-01 09:00:04] [INFO] [pipeline] - Extracted payloads for 4 cities.
[2024-07-01 09:00:04] [INFO] [pipeline] - [2/5] CLEAN — Normalising timestamps & flattening records...
[2024-07-01 09:00:04] [INFO] [pipeline] - [3/5] TRANSFORM — Building Star Schema dimension & fact tables...
[2024-07-01 09:00:04] [INFO] [pipeline] - [4/5] LOAD — Upserting data into warehouse...
[2024-07-01 09:00:05] [INFO] [pipeline] - [5/5] RETAIN — Pruning raw JSON dumps older than 30 days...
[2024-07-01 09:00:05] [INFO] [pipeline] - Pipeline completed successfully.
```

### Step 7 — Verify Data in Database
```bash
sqlite3 data/warehouse.db
```

```sql
-- Check row counts
SELECT 'dim_date'             AS tbl, COUNT(*) AS rows FROM dim_date
UNION ALL
SELECT 'dim_city',             COUNT(*) FROM dim_city
UNION ALL
SELECT 'fact_weather_metrics', COUNT(*) FROM fact_weather_metrics;

-- Verify zero duplicates (must return empty)
SELECT metric_id, COUNT(*) as cnt
FROM fact_weather_metrics
GROUP BY metric_id
HAVING cnt > 1;

-- Preview latest data
SELECT c.city_name, f.timestamp_utc, f.temperature_c, f.relative_humidity
FROM fact_weather_metrics f
JOIN dim_city c ON f.city_id = c.city_id
ORDER BY f.timestamp_utc DESC
LIMIT 10;

-- Exit
.quit
```

### Step 8 — Run Tests
```bash
pytest tests/ -v
```

All tests should pass with output like:
```
tests/test_extraction.py::test_fetch_city_weather_returns_dict  PASSED
tests/test_extraction.py::test_extract_all_returns_list         PASSED
tests/test_extraction.py::test_fetch_raises_on_http_error       PASSED
tests/test_transformation.py::TestCleaning::test_parse_returns_dataframe PASSED
...
tests/test_loader.py::TestIdempotentLoader::test_fact_idempotent_no_duplicates PASSED
```

---

## Part 2: Cloud Database Setup (Neon PostgreSQL — Free)

Required for GitHub Actions cloud orchestration since Actions runners cannot access local SQLite files.

### Step 1 — Create Neon Account
1. Go to [neon.tech](https://neon.tech) → Sign up (free, no credit card)
2. Create a new project → Choose region closest to your GitHub Actions runner (US East)
3. Copy the **Connection String** from the dashboard:
   ```
   postgresql+psycopg2://username:password@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### Step 2 — Update Local `.env` for Testing
```env
DATABASE_URL=postgresql+psycopg2://username:password@ep-xyz.neon.tech/neondb?sslmode=require
```

### Step 3 — Run Pipeline Against Cloud DB
```bash
python pipeline.py --run-once
```
Verify rows appear in Neon's SQL editor on the dashboard.

---

## Part 3: GitHub Actions Setup

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial ETL pipeline project"
git remote add origin https://github.com/yourusername/etl-powerbi-pipeline.git
git push -u origin main
```

### Step 2 — Add Repository Secrets
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

| Name | Value |
|---|---|
| `DATABASE_URL` | Your Neon PostgreSQL connection string |
| `SLACK_WEBHOOK_URL` | Your Slack webhook URL (optional) |

### Step 3 — Enable GitHub Actions
The workflow file `.github/workflows/etl_cron.yml` activates automatically on push.
- Go to **Actions** tab → Confirm workflow is listed
- Click **Run workflow** → **Run workflow** to trigger a manual test run
- Check logs to confirm successful execution

### Step 4 — Verify Cron Schedule
The pipeline is configured to run **every hour** (`0 * * * *`). GitHub Actions may have a delay of up to 15 minutes on the free tier. After 2 hours, check the Actions tab for completed runs.

---

## Part 4: Power BI Desktop Connection

See [powerbi_setup.md](powerbi_setup.md) for full Power BI connection and dashboard setup instructions.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'src'` | Running from wrong directory | Run from project root: `python pipeline.py` |
| `sqlite3.OperationalError: no such table` | Schema not initialised | `ensure_schema()` is called on every run automatically |
| `requests.exceptions.ConnectionError` | No internet connection | Check network; retry automatically handles transient failures |
| `psycopg2.OperationalError: could not connect` | Wrong DATABASE_URL | Double-check connection string and sslmode=require |
| `pandera.errors.SchemaError` | API returned unexpected data | Check raw JSON in `data/raw/` for the anomalous response |
| GitHub Actions: `SECRET not found` | Secret not configured | Add secret in repo Settings → Secrets and variables → Actions |
