import os
import time
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger("retention_pruner")

def prune_raw_payloads(raw_dir: str = "data/raw", retention_days: int = 30) -> int:
    """
    Deletes raw JSON dump files in `raw_dir` that are older than `retention_days`.
    Prevents unconstrained disk growth on automated cron runs.
    """
    target_path = Path(raw_dir)
    if not target_path.exists():
        logger.info(f"Directory {raw_dir} does not exist. Skipping retention prune.")
        return 0

    cutoff_time = time.time() - (retention_days * 86400)
    pruned_count = 0

    for file_path in target_path.glob("*.json"):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
                pruned_count += 1
                logger.debug(f"Pruned old raw payload: {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path.name}: {e}")

    logger.info(f"Raw data retention check complete. Pruned {pruned_count} file(s) older than {retention_days} days.")
    return pruned_count
