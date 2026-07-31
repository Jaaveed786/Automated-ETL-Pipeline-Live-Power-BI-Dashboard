# Glossary of Terms — ETL Pipeline + Power BI Dashboard

Reference guide for technical terminology used throughout this project.
Useful for interview preparation and onboarding new contributors.

---

## Data Engineering Terms

| Term | Definition |
|---|---|
| **ETL** | Extract, Transform, Load — the three stages of a data pipeline |
| **ELT** | Extract, Load, Transform — modern variant where raw data is loaded first, then transformed inside the warehouse (used by dbt + Snowflake) |
| **Idempotency** | A pipeline is idempotent if running it N times produces the same result as running it once |
| **Upsert** | A database operation that INSERTs new rows and UPDATEs existing ones in a single statement |
| **ON CONFLICT DO UPDATE** | PostgreSQL / SQLite syntax for idempotent upserts using a conflict target (primary key or unique column) |
| **Star Schema** | A data warehouse design with one central fact table connected to multiple dimension tables |
| **Fact Table** | Contains measurable, quantitative data (e.g., temperature readings, sales amounts) |
| **Dimension Table** | Contains descriptive attributes used to filter/group facts (e.g., date attributes, city metadata) |
| **Date Dimension** | A dimension table with pre-computed calendar attributes (year, quarter, month, week, is_weekend) |
| **Surrogate Key** | An artificial primary key (e.g., auto-increment integer or MD5 hash) used in data warehouses |
| **Composite Key** | A primary key made from combining two or more columns |
| **Data Lineage** | Tracking the origin, movement, and transformation of data from source to final output |
| **Data Retention** | Policy defining how long raw or processed data is stored before deletion |
| **Replayability** | Ability to re-process historical raw data without re-fetching from the source |
| **Backfill** | Running a pipeline against historical data to populate a warehouse retroactively |
| **Partition** | Dividing a large table into smaller physical segments for query performance (e.g., by year or month) |
| **Index** | A database structure that speeds up row lookups at the cost of additional storage |
| **OLTP** | Online Transaction Processing — databases optimised for fast reads/writes (e.g., order management systems) |
| **OLAP** | Online Analytical Processing — databases optimised for complex aggregation queries (e.g., Snowflake, BigQuery) |

---

## API & Python Terms

| Term | Definition |
|---|---|
| **REST API** | Representational State Transfer — a web API that responds to HTTP GET/POST/PUT/DELETE requests |
| **HTTP 429** | Too Many Requests — server rate-limit response; trigger for automatic retry |
| **Exponential Backoff** | Retry strategy where wait time doubles between attempts: 1s → 2s → 4s → 8s |
| **Session (requests)** | A reusable HTTP connection object that persists cookies and connection pools across requests |
| **Retry (urllib3)** | Configuration object specifying max retries, backoff factor, and which HTTP status codes to retry |
| **pytz / zoneinfo** | Python libraries for timezone-aware datetime conversion |
| **UTC** | Coordinated Universal Time — universal time reference with no timezone offset |
| **ISO-8601** | International timestamp format: `YYYY-MM-DDTHH:MM:SSZ` |
| **MD5 Hash** | A deterministic 128-bit hash function — used here to generate composite primary keys |
| **SQLAlchemy** | Python ORM (Object-Relational Mapper) providing a unified interface to multiple database backends |
| **ORM** | Object-Relational Mapper — maps Python objects/classes to database rows/tables |
| **Pandera** | Python library for DataFrame schema validation using class-based or decorator models |
| **python-dotenv** | Library that loads environment variables from a `.env` file into `os.environ` |

---

## Power BI & DAX Terms

| Term | Definition |
|---|---|
| **DAX** | Data Analysis Expressions — formula language used in Power BI, Excel, and SSAS |
| **Measure** | A DAX formula that computes a value dynamically based on the current filter context |
| **Filter Context** | The active set of filters applied to a measure at evaluation time (from slicers, visuals, relationships) |
| **CALCULATE** | DAX function that evaluates an expression after modifying the filter context |
| **ALL()** | DAX modifier that removes all filters from a table or column |
| **DATESINPERIOD** | DAX function that returns a set of dates for a rolling window (e.g., last 7 days) |
| **TOTALYTD** | DAX function computing year-to-date aggregation using a date column |
| **DATEADD** | DAX function shifting a date column by N periods (days, months, quarters, years) |
| **STDEV.P** | Population standard deviation — computed over all values in the current filter context |
| **RANKX** | DAX function ranking a table expression relative to other values |
| **Bidirectional Filtering** | Allows filters to flow in both directions across a relationship — avoid in Star Schemas |
| **Import Mode** | Power BI loads data into memory; refresh on schedule |
| **DirectQuery Mode** | Power BI sends live SQL queries to the source database per visual render |
| **Incremental Refresh** | Power BI feature that only imports new/changed rows rather than the full dataset |
| **Scheduled Refresh** | Power BI Service feature that automatically re-imports data on a time schedule |
| **On-Premises Data Gateway** | Software bridge allowing Power BI Service to reach databases inside a private network |

---

## DevOps & Orchestration Terms

| Term | Definition |
|---|---|
| **CI/CD** | Continuous Integration / Continuous Deployment — automated build, test, and deploy workflows |
| **GitHub Actions** | GitHub's native CI/CD platform — runs workflows triggered by push, PR, schedule, or manual dispatch |
| **Cron** | Unix time-based job scheduler; `0 * * * *` = every hour at minute 0 |
| **Repository Secrets** | GitHub's encrypted secret store — values injected as env vars into Actions runners |
| **Webhook** | An HTTP callback sent by one service to another on a triggered event (e.g., pipeline failure) |
| **Ephemeral Runner** | GitHub Actions compute environment that is created fresh and destroyed after each job |
| **Airflow** | Apache Airflow — open-source workflow orchestration platform using Python DAGs |
| **DAG** | Directed Acyclic Graph — Airflow's way of defining pipeline task dependencies |
| **dbt** | Data Build Tool — SQL-based transformation framework with lineage tracking and testing |
