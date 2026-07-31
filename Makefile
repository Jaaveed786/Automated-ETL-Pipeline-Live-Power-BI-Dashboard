# ============================================================
#  Makefile — Developer Convenience Commands
#  Usage: make <target>
#  Windows: install 'make' via 'winget install GnuWin32.Make'
#           or use Git Bash / WSL
# ============================================================

.PHONY: install install-dev run test test-cov lint format clean help

## Install production dependencies
install:
	pip install -r requirements.txt

## Install dev dependencies (linting, formatting, coverage)
install-dev:
	pip install -r requirements.txt -r requirements-dev.txt

## Run the ETL pipeline once
run:
	python pipeline.py --run-once

## Run all tests
test:
	pytest tests/ -v

## Run tests with coverage report
test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov

## Lint code with flake8
lint:
	flake8 src/ tests/ pipeline.py --max-line-length=100

## Format code with black and isort
format:
	black src/ tests/ pipeline.py --line-length=100
	isort src/ tests/ pipeline.py

## Verify zero duplicate rows in the database
check-dupes:
	sqlite3 data/warehouse.db "SELECT metric_id, COUNT(*) AS cnt FROM fact_weather_metrics GROUP BY metric_id HAVING cnt > 1;"

## Show latest 10 rows in the fact table
preview-data:
	sqlite3 data/warehouse.db "SELECT city_id, timestamp_utc, temperature_c, relative_humidity FROM fact_weather_metrics ORDER BY timestamp_utc DESC LIMIT 10;"

## Show row counts for all tables
row-counts:
	sqlite3 data/warehouse.db "SELECT 'dim_date' AS tbl, COUNT(*) FROM dim_date UNION ALL SELECT 'dim_city', COUNT(*) FROM dim_city UNION ALL SELECT 'fact_weather_metrics', COUNT(*) FROM fact_weather_metrics;"

## Remove generated files (logs, coverage, pycache)
clean:
	rmdir /s /q htmlcov 2>nul || true
	rmdir /s /q .pytest_cache 2>nul || true
	del /s /q *.pyc 2>nul || true

## Show available commands
help:
	@echo Available targets:
	@echo   install       Install production dependencies
	@echo   install-dev   Install dev dependencies
	@echo   run           Run the ETL pipeline once
	@echo   test          Run all tests
	@echo   test-cov      Run tests with HTML coverage report
	@echo   lint          Lint code with flake8
	@echo   format        Format code with black + isort
	@echo   check-dupes   Verify zero duplicate rows in warehouse
	@echo   preview-data  Show latest 10 fact table rows
	@echo   row-counts    Show row counts for all tables
	@echo   clean         Remove generated artifacts
