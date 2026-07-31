"""
pipeline.py — Main ETL Pipeline Entrypoint

Usage:
    python pipeline.py              # Single run (default)
    python pipeline.py --run-once   # Explicit single run
"""
import argparse
import traceback
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.extractors.weather_extractor import WeatherExtractor
from src.transformers.cleaning import clean_all_cities
from src.transformers.star_schema import (
    build_dim_date,
    build_dim_city,
    build_fact_weather_metrics,
)
from src.loaders.db_engine import get_engine
from src.loaders.idempotent_loader import (
    ensure_schema,
    upsert_dim_date,
    upsert_dim_city,
    upsert_fact_weather,
)
from src.utils.logger import setup_logger
from src.utils.quality_checks import run_all_checks
from src.utils.retention import prune_raw_payloads
from src.utils.notifier import send_failure_alert

load_dotenv()
logger = setup_logger("pipeline")


def load_config(config_path: str = "config/config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(config: dict) -> None:
    pipeline_name = config["pipeline"]["name"]
    retention_days = config["pipeline"]["retention_days"]
    raw_dir = config["pipeline"]["raw_data_dir"]

    # Ensure directories exist
    Path(raw_dir).mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    logger.info("=" * 60)
    logger.info(f"Starting pipeline: {pipeline_name}")
    logger.info("=" * 60)

    try:
        # ── STEP 1: EXTRACT ───────────────────────────────────────────
        logger.info("[1/5] EXTRACT — Fetching weather data from Open-Meteo API...")
        extractor = WeatherExtractor(config)
        raw_payloads = extractor.extract_all()
        logger.info(f"Extracted payloads for {len(raw_payloads)} cities.")

        # ── STEP 2: CLEAN ─────────────────────────────────────────────
        logger.info("[2/5] CLEAN — Normalising timestamps & flattening records...")
        clean_df = clean_all_cities(raw_payloads)

        # ── STEP 3: QUALITY CHECKS ────────────────────────────────────
        logger.info("[3/6] VALIDATE — Running data quality assertions...")
        known_city_ids = [c["id"] for c in config["cities"]]
        run_all_checks(clean_df, known_city_ids)

        # ── STEP 4: TRANSFORM (Star Schema) ───────────────────────────
        logger.info("[4/6] TRANSFORM — Building Star Schema dimension & fact tables...")
        dim_date = build_dim_date(clean_df)
        dim_city = build_dim_city(clean_df)
        fact_df  = build_fact_weather_metrics(clean_df)

        # ── STEP 5: LOAD ──────────────────────────────────────────────
        logger.info("[5/6] LOAD — Upserting data into warehouse...")
        engine = get_engine()
        ensure_schema(engine)
        upsert_dim_date(engine, dim_date)
        upsert_dim_city(engine, dim_city)
        upsert_fact_weather(engine, fact_df)

        # ── STEP 6: RETAIN ────────────────────────────────────────────
        logger.info("[6/6] RETAIN — Pruning raw JSON dumps older than 30 days...")
        prune_raw_payloads(raw_dir=raw_dir, retention_days=retention_days)

        logger.info("=" * 60)
        logger.info("Pipeline completed successfully.")
        logger.info("=" * 60)

    except Exception as exc:
        err_msg = traceback.format_exc()
        logger.error(f"Pipeline FAILED: {exc}")
        logger.error(err_msg)
        send_failure_alert(pipeline_name, err_msg)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL Pipeline Runner")
    parser.add_argument("--run-once", action="store_true", help="Execute a single pipeline run")
    args = parser.parse_args()

    cfg = load_config()
    run_pipeline(cfg)
