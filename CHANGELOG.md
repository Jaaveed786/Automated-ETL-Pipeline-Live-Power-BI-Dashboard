# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-07-27

### Added
- **Extractor**: `WeatherExtractor` — Open-Meteo API client with exponential backoff retry logic (urllib3)
- **Raw archival**: Timestamped JSON dump of every API response to `data/raw/`
- **Cleaning**: `clean_all_cities()` with per-city `pytz` timezone conversion (UTC + Local timestamps)
- **Star Schema**: `dim_date`, `dim_city`, `fact_weather_metrics` builders
- **Pandera schemas**: `WeatherFactSchema` enforcing column-level data contracts
- **Quality checks**: 6 custom business-logic assertions (`quality_checks.py`)
- **SQLAlchemy engine factory**: Single `DATABASE_URL` env var switching SQLite ↔ PostgreSQL
- **Idempotent loader**: `ON CONFLICT(metric_id) DO UPDATE` upsert for all three tables
- **Retention pruner**: Auto-delete raw JSON files older than 30 days
- **Slack notifier**: Webhook alert on pipeline exception
- **GitHub Actions**: Hourly cron workflow with Repository Secrets injection
- **Logging**: Structured console logging with optional rotating file handler
- **Tests**: 4 test modules — extraction, transformation, loader, retention, quality checks
- **Shared fixtures**: `conftest.py` with reusable in-memory DB and sample data fixtures

### Documentation
- `README.md` — architecture, quick start, schema diagram, tech stack
- `docs/architecture.md` — deep-dive component walkthrough
- `docs/interview_qa.md` — 30 technical Q&As (ETL, Python, SQL, DAX, system design)
- `docs/setup_guide.md` — local + cloud deployment instructions
- `docs/powerbi_setup.md` — Power BI connection, star schema model, DAX, scheduled refresh
- `docs/star_story.md` — STAR interview storytelling guide with measurement instructions
- `docs/project_plans.md` — all iteration decisions and scope choices documented
- `docs/glossary.md` — 60+ technical term definitions
- `docs/resume_bullets.md` — ATS-optimised resume bullets for various role types
- `dax/dax_measures.md` — 15 production DAX measures with implementation notes

### Configuration
- `config/config.yaml` — cities, API settings, retention policy
- `config/logging_config.py` — structured logging configuration
- `.env.example` — environment variable template
- `.gitignore` — comprehensive ignore rules
- `Makefile` — developer convenience commands
- `pyproject.toml` — pytest configuration
- `requirements.txt` + `requirements-dev.txt` — split production/dev dependencies

---

## [Unreleased] — Planned for v1.1.0

### Planned
- Per-city try/except for partial failure resilience (currently all-or-nothing)
- `test_notifier.py` — unit tests for Slack webhook with mocked HTTP
- Concurrent city fetching with `ThreadPoolExecutor`
- Data freshness Power BI measure (flag if MAX timestamp > 2 hours old)
- `notebooks/exploratory_analysis.ipynb` — EDA on warehouse data
