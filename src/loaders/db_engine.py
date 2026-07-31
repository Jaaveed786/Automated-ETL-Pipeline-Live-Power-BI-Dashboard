import os
from sqlalchemy import create_engine, Engine
from dotenv import load_dotenv
from src.utils.logger import setup_logger

load_dotenv()
logger = setup_logger("db_engine")


def get_engine() -> Engine:
    """
    Creates and returns a SQLAlchemy Engine instance based on the
    DATABASE_URL environment variable.

    Supports:
    - SQLite  (local dev):  sqlite:///data/warehouse.db
    - PostgreSQL (cloud):   postgresql+psycopg2://user:pass@host/dbname?sslmode=require
    """
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/warehouse.db")

    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(db_url, connect_args=connect_args, echo=False)
    logger.info(f"Database engine created: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    return engine
