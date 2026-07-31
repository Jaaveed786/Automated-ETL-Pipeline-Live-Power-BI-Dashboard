"""
tests/test_retention.py — Unit tests for the 30-day raw data retention pruner.
"""
import os
import time
import pytest
from pathlib import Path
from src.utils.retention import prune_raw_payloads


@pytest.fixture
def tmp_raw_dir(tmp_path):
    """Creates a temporary raw data directory with test JSON files."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    return raw_dir


def create_file_aged(directory: Path, filename: str, age_days: float) -> Path:
    """Helper: create a file and backdating its mtime by age_days."""
    fpath = directory / filename
    fpath.write_text('{"test": true}')
    # Backdate mtime
    past_time = time.time() - (age_days * 86400)
    os.utime(fpath, (past_time, past_time))
    return fpath


class TestRetentionPruner:

    def test_old_file_is_deleted(self, tmp_raw_dir):
        """Files older than retention_days should be deleted."""
        old_file = create_file_aged(tmp_raw_dir, "old_payload.json", age_days=31)
        assert old_file.exists()

        pruned = prune_raw_payloads(raw_dir=str(tmp_raw_dir), retention_days=30)

        assert pruned == 1
        assert not old_file.exists()

    def test_recent_file_is_kept(self, tmp_raw_dir):
        """Files newer than retention_days must NOT be deleted."""
        recent_file = create_file_aged(tmp_raw_dir, "recent_payload.json", age_days=5)
        assert recent_file.exists()

        pruned = prune_raw_payloads(raw_dir=str(tmp_raw_dir), retention_days=30)

        assert pruned == 0
        assert recent_file.exists()

    def test_boundary_file_kept(self, tmp_raw_dir):
        """File exactly at the retention boundary (29.9 days) should be kept."""
        boundary_file = create_file_aged(tmp_raw_dir, "boundary.json", age_days=29.9)
        pruned = prune_raw_payloads(raw_dir=str(tmp_raw_dir), retention_days=30)
        assert pruned == 0
        assert boundary_file.exists()

    def test_multiple_files_mixed_age(self, tmp_raw_dir):
        """Only files older than threshold are deleted; recent ones survive."""
        old1 = create_file_aged(tmp_raw_dir, "old1.json", age_days=45)
        old2 = create_file_aged(tmp_raw_dir, "old2.json", age_days=60)
        new1 = create_file_aged(tmp_raw_dir, "new1.json", age_days=2)
        new2 = create_file_aged(tmp_raw_dir, "new2.json", age_days=10)

        pruned = prune_raw_payloads(raw_dir=str(tmp_raw_dir), retention_days=30)

        assert pruned == 2
        assert not old1.exists()
        assert not old2.exists()
        assert new1.exists()
        assert new2.exists()

    def test_non_json_files_are_ignored(self, tmp_raw_dir):
        """Non-.json files (e.g. .gitkeep, .txt) must never be deleted."""
        gitkeep = tmp_raw_dir / ".gitkeep"
        gitkeep.write_text("")
        # Backdate it too
        past_time = time.time() - (60 * 86400)
        os.utime(gitkeep, (past_time, past_time))

        pruned = prune_raw_payloads(raw_dir=str(tmp_raw_dir), retention_days=30)
        assert gitkeep.exists(), ".gitkeep should not be deleted by retention pruner"

    def test_missing_directory_returns_zero(self, tmp_path):
        """Pruner should gracefully handle a non-existent directory."""
        pruned = prune_raw_payloads(raw_dir=str(tmp_path / "nonexistent"), retention_days=30)
        assert pruned == 0
