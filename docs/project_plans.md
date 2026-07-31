# Project Plans & Iteration History

Documents all planning decisions, reviews, and technical debates made during
the design of this ETL pipeline project for portfolio purposes.

---

## v1 — Initial Plan

**Date:** July 2026

### Decisions Made
- **API**: Open-Meteo (free, no key, reliable, hourly weather data)
- **Database**: SQLite (local) + Neon PostgreSQL (cloud, via SQLAlchemy)
- **Orchestration**: GitHub Actions hourly cron
- **Validation**: Pandera (lightweight vs. Great Expectations)
- **Cities (v1)**: 4 — London, New York, Tokyo, Dubai

### Scope Consciously Excluded from v1
| Feature | Reason Excluded |
|---|---|
| Snowflake / Oracle DDL | No account to test against; documented as extension path |
| Apache Airflow | Significant infrastructure overhead for a single pipeline |
| Great Expectations | Heavy dependency; Pandera gives equivalent value at 10% setup cost |
| 10-city extraction | 4 cities proves architecture equally; reduces data-wrangling surface for v1 |
| dbt models | v2 extension — adds lineage tracking when team-scale is needed |
| Incremental refresh (Power BI) | Relevant only after fact table exceeds ~1M rows |
| Per-city SCD (Slowly Changing Dimension) | City metadata is static; not needed in v1 |

---

## v2 — First Review (Design Iteration)

### Issues Identified & Resolved

| Issue | Resolution |
|---|---|
| No secrets management in config.yaml | Added `.env` with `python-dotenv`, strict `.gitignore` |
| No raw data retention policy | Added `retention.py` 30-day pruner |
| GitHub Actions / SQLite incompatibility | SQLite for local only; Neon PostgreSQL for cloud |
| Great Expectations too heavy | Replaced with Pandera |
| STAR interview guide missing | Added `docs/star_story.md` |
| 10 cities → too much wrangling surface | Scoped down to 4 cities for v1 |

---

## v3 — Final Review (Pre-Build)

### Issues Identified & Resolved

| Issue | Resolution |
|---|---|
| `Temp Anomaly Flag` DAX computed STDEV.P in wrong filter context | Fixed with `CALCULATE(STDEV.P(...), ALL(dim_date))` |
| GitHub Actions runner needs Repository Secrets, not `.env` | Added explicit `${{ secrets.DATABASE_URL }}` in `etl_cron.yml` |
| Per-city timezone parsing not specified in cleaning.py | Added explicit `pytz.timezone(city_timezone).localize(dt)` logic |
| STAR result section had unverified numbers | Changed to measurement placeholders with instructions |
| 10 cities → 4 cities for v1 confirmed | Final scope locked |

---

## Extension Roadmap (v2+)

### Short-Term (Next Sprint)
- [ ] Wrap each city fetch in individual try/except for partial failure resilience
- [ ] Add `test_retention.py` unit tests for the pruner logic
- [ ] Add data freshness Power BI card (flag if MAX timestamp > 2 hours old)

### Medium-Term
- [ ] Concurrent city extraction with `ThreadPoolExecutor`
- [ ] Bulk PostgreSQL upserts (replace row-by-row loop)
- [ ] dbt models replacing `sql/analytical_views.sql`
- [ ] Add 2–3 more cities (Singapore, Frankfurt, São Paulo)

### Long-Term
- [ ] Snowflake connector support (change `DATABASE_URL` + `MERGE INTO` syntax)
- [ ] Apache Airflow DAG migration
- [ ] Power BI incremental refresh policy
- [ ] Column-level data lineage via dbt + Metabase

---

## Design Principles Followed

1. **Test isolation**: All pytest tests use in-memory SQLite — no disk writes, no API calls
2. **Single config change**: Switching databases requires only `DATABASE_URL` change
3. **Fail loudly**: Exceptions propagate immediately + Slack alert — no silent failures
4. **Audit trail**: Raw JSON archival ensures every DB row is traceable to an API response
5. **Zero duplicates**: Every pipeline re-run guaranteed to produce identical DB state
6. **Documented > built**: Extension paths (Snowflake, Airflow, dbt) documented but not implemented — honest about scope
