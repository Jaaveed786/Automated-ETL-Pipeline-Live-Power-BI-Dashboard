# Interview Q&A — Automated ETL Pipeline + Live Power BI Dashboard

30 technical interview questions with detailed answers covering Data Engineering,
Python, SQL, Power BI, DAX, and system design — tailored to this project.

---

## Section 1: ETL & Data Engineering Fundamentals

**Q1. What does ETL stand for, and what does each stage do in your project?**

> ETL stands for **Extract, Transform, Load**.
> - **Extract**: My `WeatherExtractor` class fetches hourly weather data from the Open-Meteo REST API for 4 global cities using a resilient `requests.Session` with automatic retry logic.
> - **Transform**: The cleaning module normalises timestamps using per-city `pytz` timezone conversion, then the star schema builders split the flat data into `dim_date`, `dim_city`, and `fact_weather_metrics` tables.
> - **Load**: The `IdempotentLoader` uses SQLAlchemy to upsert records with `ON CONFLICT(metric_id) DO UPDATE`, guaranteeing zero duplicates on any number of re-runs.

---

**Q2. What is idempotency and why does it matter in a data pipeline?**

> Idempotency means running the same operation multiple times produces the same result as running it once. In my pipeline, if GitHub Actions retries a failed run or the cron fires twice, no duplicate rows appear in the database. I achieve this by computing a deterministic `metric_id = MD5(city_id + timestamp_utc)` for every row. The SQL upsert then uses `ON CONFLICT(metric_id) DO UPDATE` — existing rows are refreshed, not duplicated. Without idempotency, every retry would bloat the fact table and corrupt downstream Power BI aggregations.

---

**Q3. What is a Star Schema and why did you choose it over a flat table?**

> A Star Schema organises data into a central **fact table** surrounded by **dimension tables**. My design has:
> - `fact_weather_metrics` — one row per hourly observation per city (the measurable events)
> - `dim_date` — calendar attributes (year, quarter, month, is_weekend) derived from each date
> - `dim_city` — city metadata (name, country, timezone)
>
> Over a flat denormalised table, Star Schema gives:
> 1. **Faster Power BI queries** — dimensions are small, fact is narrow
> 2. **Clean DAX time intelligence** — requires a proper `dim_date` table
> 3. **No update anomalies** — city name stored once in `dim_city`, not in every fact row
> 4. **Industry standard** — every BI analyst/engineer recognises it immediately

---

**Q4. How does your pipeline handle API failures or network timeouts?**

> The `WeatherExtractor` builds a `requests.Session` with a `urllib3.util.Retry` adapter configured for:
> - 3 total retries
> - Exponential backoff: 1s → 2s → 4s between attempts
> - Automatic retry on HTTP status codes 429 (rate limited), 500, 502, 503, 504
>
> If all retries are exhausted, the exception propagates to `pipeline.py`, which catches it, formats the full traceback, and fires a Slack webhook alert via `notifier.py`. The GitHub Actions workflow step then marks as failed, preventing silent data gaps.

---

**Q5. Why did you use MD5 hashing for the `metric_id` primary key instead of an auto-increment?**

> Auto-increment IDs are non-deterministic — inserting the same record twice generates two different IDs, making idempotency impossible. An MD5 hash of `city_id + timestamp_utc` is:
> - **Deterministic**: same inputs always produce the same key
> - **Collision-resistant** at this cardinality (~35K rows/year)
> - **Upsert-compatible**: the database can use it as a conflict target in `ON CONFLICT(metric_id) DO UPDATE`
>
> This pattern is common in data warehouses for surrogate key generation without sequences.

---

**Q6. What is raw data archival and why did you include it?**

> After every successful API fetch, my extractor saves a timestamped JSON dump to `data/raw/YYYY-MM-DD_HHMMSS.json`. This serves three purposes:
> 1. **Replayability** — if a transformation bug is discovered, I can re-run the transform on stored raw data without hitting the API again
> 2. **Audit trail** — proves exactly what data was received and when
> 3. **Debugging** — compare raw vs. transformed to isolate bugs
>
> A `retention.py` module auto-prunes files older than 30 days to prevent unbounded disk growth on the cloud runner.

---

**Q7. What is the difference between a data warehouse and a database?**

> A **database** (OLTP) is optimised for fast transactional reads/writes — e.g., insert a new order, update a user record. Normalised schema, row-level operations.
>
> A **data warehouse** (OLAP) is optimised for analytical queries across large historical datasets — e.g., average temperature by city over the past 12 months. Denormalised (Star/Snowflake schemas), column-oriented aggregation, batch loads.
>
> My project uses a **relational database (SQLite/PostgreSQL) as a lightweight warehouse** — the Star Schema design and indexed fact table make it behave like a warehouse for the query patterns Power BI generates.

---

## Section 2: Python & Pandas

**Q8. How did you handle timezone differences across cities like Tokyo and London?**

> Open-Meteo returns timestamps in each city's local timezone when you pass the `timezone` parameter. My `cleaning.py` module:
> 1. Parses the local timestamp string using `datetime.strptime`
> 2. Localises it with `pytz.timezone(city_timezone).localize(dt)` — this attaches the correct UTC offset per city
> 3. Converts to UTC using `.astimezone(pytz.utc)` for a universal reference
> 4. Stores **both** `timestamp_local` and `timestamp_utc` in the fact table
>
> This means Tokyo's 09:00 JST becomes 00:00 UTC correctly, not offset by a single hardcoded value. Power BI can then display either timezone based on the visual context.

---

**Q9. What is Pandera and why did you use it instead of Great Expectations?**

> **Pandera** is a lightweight Python library for DataFrame schema validation using class-based or decorator-based models. I used it to define a `WeatherFactSchema` that enforces:
> - Temperature must be in range [-60°C, 60°C]
> - Humidity must be in [0%, 100%]
> - `metric_id` must be unique and non-null
>
> I chose Pandera over Great Expectations because:
> - **Installation is 10x lighter** — Great Expectations pulls in dozens of dependencies and requires a project config file
> - **Schema as code** — Pandera schemas live as Python classes alongside the transform code, not in separate JSON config files
> - For a solo portfolio project on a deadline, Pandera gives 90% of the validation value at 10% of the setup cost

---

**Q10. How do you ensure the pipeline doesn't break if one city's API call fails?**

> In the current v1 design, an exception in any city's fetch propagates upward and halts the full pipeline. This is acceptable for v1 because:
> - Open-Meteo has excellent uptime (~99.9%)
> - A single retry-wrapped session handles transient failures
>
> For v2, I'd wrap each city's fetch in a `try/except` with individual failure logging, allowing the pipeline to succeed for 3 cities even if 1 fails. I documented this as an explicit extension path in `docs/architecture.md`.

---

**Q11. What does `pandas.concat` do and when would you use it?**

> `pd.concat` combines multiple DataFrames along a given axis (default: row-wise). In my `clean_all_cities()` function, each city returns its own DataFrame from `parse_city_weather()`. `pd.concat(frames, ignore_index=True)` stacks them vertically into a single DataFrame covering all 4 cities, which is then passed to the star schema builders. `ignore_index=True` resets the index to avoid duplicate index values from the individual city frames.

---

## Section 3: SQL & Database Design

**Q12. What SQL statement did you use to prevent duplicates?**

> ```sql
> INSERT INTO fact_weather_metrics (metric_id, city_id, ...)
> VALUES (:metric_id, :city_id, ...)
> ON CONFLICT(metric_id) DO UPDATE SET
>     temperature_c = EXCLUDED.temperature_c,
>     relative_humidity = EXCLUDED.relative_humidity,
>     ...
> ```
> `EXCLUDED` refers to the row that was attempted to be inserted. This pattern is supported natively in SQLite 3.24+ and PostgreSQL. It refreshes metric values while keeping the primary key stable, which is correct behaviour for hourly data that may be backfilled.

---

**Q13. Why did you create indexes on `city_id`, `date_key`, and `timestamp_utc`?**

> Power BI sends filter queries like:
> ```sql
> SELECT AVG(temperature_c) FROM fact_weather_metrics
> WHERE city_id = 'LON' AND date_key BETWEEN 20240101 AND 20240131
> ```
> Without indexes, this performs a full table scan. With indexes, the database jumps directly to the matching rows. At ~35K rows/year, the difference is milliseconds vs. microseconds — but as data grows and Power BI sends multiple concurrent queries, indexes make the difference between sub-second visuals and spinning load icons.

---

**Q14. What is the difference between `INTEGER` and `TEXT` for storing dates in SQLite?**

> SQLite has no native `DATE` type — it stores dates as TEXT, INTEGER, or REAL. I use:
> - `date_key INTEGER` (e.g., `20240601`) — fast arithmetic comparisons, human-readable, 4 bytes
> - `timestamp_utc TEXT` (ISO-8601 string) — preserves full precision including time component
>
> The integer date key enables efficient range queries (`BETWEEN 20240101 AND 20240131`) and joins to `dim_date` without string parsing overhead.

---

**Q15. How would you migrate this from SQLite to Snowflake?**

> Since I built the loading layer on SQLAlchemy, migration requires:
> 1. `pip install snowflake-sqlalchemy`
> 2. Set `DATABASE_URL=snowflake://user:pass@account/db/schema?warehouse=WH`
> 3. Replace `ON CONFLICT` syntax in `idempotent_loader.py` with Snowflake's `MERGE INTO` statement
> 4. Update DDL in `ddl_schema.sql` for Snowflake column types
>
> The transformation and extraction layers require zero changes. I explicitly documented Snowflake as an extension path in the README rather than building it in v1, since I don't have a Snowflake account to test against — and untested code in a portfolio project is worse than documented-but-not-built code.

---

## Section 4: Power BI & DAX

**Q16. What is DirectQuery vs. Import mode in Power BI?**

> - **Import mode**: Power BI pulls data from the source into an in-memory compressed dataset. Queries run fast against the cache. Data freshness depends on scheduled refresh intervals (minimum 30 minutes on Power BI Service free tier).
> - **DirectQuery mode**: Every visual sends a live SQL query to the source database. Always current, but visual rendering speed depends on database query performance.
>
> For this project I recommend **Import mode with scheduled hourly refresh** — it gives fast visual rendering and the hourly pipeline already ensures data freshness matches the refresh interval.

---

**Q17. Explain how your 7-Day Moving Average DAX measure works.**

> ```dax
> 7D Moving Avg Temp =
> CALCULATE(
>     AVERAGE(fact_weather_metrics[temperature_c]),
>     DATESINPERIOD(
>         dim_date[full_date],
>         MAX(dim_date[full_date]),
>         -7, DAY
>     )
> )
> ```
> - `MAX(dim_date[full_date])` — the latest date in the current filter context (e.g., the date shown on the X-axis of a line chart)
> - `DATESINPERIOD(..., -7, DAY)` — creates a set of 7 dates ending on that max date
> - `CALCULATE(AVERAGE(...), ...)` — overrides the filter context to average temperature over those 7 days
>
> As the X-axis date moves forward, `MAX(dim_date[full_date])` advances, creating a rolling window effect.

---

**Q18. Why did you use `ALL(dim_date)` in the Temp Anomaly Flag measure?**

> Without `ALL(dim_date)`, `STDEV.P(fact_weather_metrics[temperature_c])` would compute standard deviation only over the dates visible in the current filter context (e.g., one month selected in a slicer). The threshold would shift as the user changes the date filter — making "anomaly" mean something different depending on what's selected.
>
> By wrapping it in `CALCULATE(..., ALL(dim_date))`, I compute the standard deviation over the **entire dataset regardless of the date slicer**. This gives a stable, meaningful threshold: a reading is flagged as anomalous only if it deviates >2σ from the global historical average — a proper statistical definition.

---

**Q19. What is a DAX filter context and why does it matter?**

> Filter context is the set of active filters applied to a measure at evaluation time. It comes from:
> - Slicers (e.g., city = London)
> - Report page filters
> - Row/column headers in a matrix visual
> - `CALCULATE()` modifiers
>
> Understanding filter context is what separates DAX beginners from practitioners. A common mistake is writing `AVERAGE(fact[temperature_c])` and expecting it to always return the global average — but in a matrix with city rows, it returns the per-city average because city is in the filter context.

---

**Q20. How did you set up relationships in the Power BI data model?**

> In Power BI Desktop Model View:
> 1. Drag `dim_date[date_key]` → `fact_weather_metrics[date_key]` — creates a Many-to-One relationship
> 2. Drag `dim_city[city_id]` → `fact_weather_metrics[city_id]` — creates a Many-to-One relationship
> 3. Set **Single direction** filtering (dim → fact only) on both relationships
>
> Bidirectional cross-filtering is disabled intentionally — it causes filter ambiguity when both `dim_date` and `dim_city` try to filter each other through the fact table, producing incorrect DAX results in multi-slicer reports.

---

## Section 5: Orchestration & DevOps

**Q21. Why did you use GitHub Actions instead of Apache Airflow?**

> For a solo portfolio project on a timeline, GitHub Actions offers:
> - **Zero infrastructure** — no always-on server, no Docker container, no Python environment to maintain
> - **Free compute** — 2,000 minutes/month on GitHub Free tier (my hourly pipeline uses ~5 min/day = ~150 min/month)
> - **Native CI/CD integration** — the same YAML that runs tests also runs the pipeline
> - **Resume signal** — "orchestrated with GitHub Actions" shows CI/CD literacy, which recruiters in analytics and data engineering roles value
>
> Airflow is appropriate when you have dozens of interdependent pipelines, complex task dependencies, or team-level DAG management. It's significant operational overhead for a single pipeline.

---

**Q22. How do you pass secrets to GitHub Actions without committing them?**

> GitHub provides a native **Repository Secrets** store (Settings → Secrets and variables → Actions). Secrets are:
> - Encrypted at rest by GitHub
> - Never visible in logs (masked as `***`)
> - Injected as environment variables in the workflow:
>
> ```yaml
> env:
>   DATABASE_URL:      ${{ secrets.DATABASE_URL }}
>   SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
> ```
>
> The `.env` file is only for local development and is git-ignored. This is the correct pattern — never commit secrets to `.env` or `config.yaml` in a repository.

---

**Q23. Why can't GitHub Actions read a local SQLite file?**

> GitHub Actions runs on cloud-hosted Ubuntu runners. These are ephemeral, isolated virtual machines — they have no access to your laptop's filesystem. A `sqlite:///data/warehouse.db` path would create a brand new empty database on the runner's local disk, which is discarded after the job finishes.
>
> The correct architecture for cloud orchestration is:
> - **Local dev**: SQLite (zero setup, instant)
> - **Cloud cron (GitHub Actions)**: PostgreSQL on Neon.tech or Supabase — both offer free tiers with a persistent connection string that GitHub Actions can reach over HTTPS

---

**Q24. What does your 30-day raw data retention policy prevent?**

> The pipeline runs every hour and archives one JSON file per run. Without pruning, that's 720 files/month growing indefinitely. On a GitHub Actions runner (ephemeral, so irrelevant there), but on a local dev machine or a persistent server, the `data/raw/` directory would grow without bound.
>
> `retention.py` runs as the final step of every pipeline execution. It scans `data/raw/` for any `.json` file whose `mtime` is older than 30 days and deletes it. This is a minimal but production-appropriate data lifecycle management pattern.

---

## Section 6: System Design & Trade-offs

**Q25. How would you scale this pipeline from 4 cities to 400 cities?**

> Current bottleneck: the extractor fetches cities **sequentially** in a `for` loop. At 400 cities, this would take ~400 × 0.5s ≈ 200 seconds per run.
>
> Scaling approach:
> 1. **Concurrent extraction**: Use `concurrent.futures.ThreadPoolExecutor` to fetch all cities in parallel (~0.5s total instead of 200s)
> 2. **Bulk upserts**: Replace row-by-row SQLAlchemy inserts with `pandas.to_sql()` + `COPY` for PostgreSQL bulk loading
> 3. **Partition the fact table** by `date_key` to keep query times stable as rows grow into millions
> 4. **Upgrade orchestrator**: At 400 cities, consider Prefect or Airflow for task-level parallelism monitoring

---

**Q26. What would you add to this project if you had another week?**

> In priority order:
> 1. **Per-city error isolation** — wrap each city fetch in try/except so 1 failure doesn't halt the other 3
> 2. **dbt integration** — replace `analytical_views.sql` with dbt models for lineage tracking and column-level documentation
> 3. **Data freshness monitoring** — a Power BI measure that flags if the latest `timestamp_utc` is >2 hours old (pipeline gap detection)
> 4. **Unit test for retention.py** — currently untested, should verify files outside the window are deleted and files inside are kept
> 5. **Concurrent city fetching** using `ThreadPoolExecutor`

---

**Q27. What is the difference between OLTP and OLAP?**

> | | OLTP | OLAP |
> |---|---|---|
> | Purpose | Transactional operations | Analytical queries |
> | Operations | INSERT/UPDATE/DELETE | SELECT with aggregations |
> | Schema | Highly normalised (3NF) | Denormalised (Star/Snowflake) |
> | Query pattern | Single row lookups | Aggregations over millions of rows |
> | Examples | PostgreSQL for an e-commerce app | Snowflake, BigQuery, Redshift |
>
> My project uses PostgreSQL/SQLite as a **lightweight OLAP store** — the Star Schema design optimises it for the aggregation-heavy queries Power BI generates.

---

**Q28. What is data lineage and does your project implement it?**

> Data lineage tracks the origin, movement, and transformation of data from source to final output — answering "where did this number come from?"
>
> My project implements **basic lineage** through:
> - Raw JSON archival: every number in the database can be traced back to a timestamped API response file
> - `timestamp_utc` in the fact table: every row is traceable to an exact API call time
>
> Full lineage (column-level tracking across all transforms) would require dbt or Apache Atlas — documented as a v2 extension.

---

**Q29. How would you add a new metric (e.g., UV Index) to this pipeline?**

> The pipeline is designed for extensibility:
> 1. Add `"uv_index"` to the `hourly_metrics` list in `config/config.yaml`
> 2. Add `_safe_float(uv_index_list, i)` in `cleaning.py`'s record builder
> 3. Add `uv_index REAL` column to `fact_weather_metrics` in `sql/ddl_schema.sql`
> 4. Add `uv_index` to the Pandera schema bounds in `schemas.py`
> 5. Update the upsert statement in `idempotent_loader.py`
>
> The extractor, GitHub Actions workflow, and Power BI connection require **zero changes** — the schema change propagates automatically on the next pipeline run that calls `ensure_schema()`.

---

**Q30. How do you know your pipeline is working correctly in production?**

> Three layers of verification:
> 1. **Automated tests**: `pytest tests/` runs on every GitHub Actions push, verifying extraction parsing, timezone conversions, and idempotency before any code reaches the cron job
> 2. **SQL duplicate check**: `SELECT metric_id, COUNT(*) FROM fact_weather_metrics GROUP BY metric_id HAVING COUNT(*) > 1` — must return zero rows
> 3. **Power BI freshness measure**: A DAX measure checking that `MAX(fact_weather_metrics[timestamp_utc])` is within the last 2 hours — visible on the dashboard as a data freshness indicator
>
> On failure, the Slack webhook provides immediate notification with the full traceback for rapid diagnosis.
