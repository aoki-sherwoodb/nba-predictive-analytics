#!/usr/bin/env python3
"""
Data Ingestion Runner Script.
Runs a full data ingestion cycle.
"""
import logging
import sys
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def wait_for_database(max_retries: int = 30, retry_interval: int = 2):
    """Wait for database to be ready."""
    from models.database import db_manager
    
    logger.info("Waiting for database connection...")
    
    for attempt in range(max_retries):
        if db_manager.check_connection():
            logger.info("Database connection established!")
            return True
        
        logger.info(f"Database not ready, attempt {attempt + 1}/{max_retries}")
        time.sleep(retry_interval)
    
    logger.error("Failed to connect to database after maximum retries")
    return False


def wait_for_redis(max_retries: int = 30, retry_interval: int = 2):
    """Wait for Redis to be ready."""
    from services.cache import cache_manager
    
    logger.info("Waiting for Redis connection...")
    
    for attempt in range(max_retries):
        if cache_manager.check_connection():
            logger.info("Redis connection established!")
            return True
        
        logger.info(f"Redis not ready, attempt {attempt + 1}/{max_retries}")
        time.sleep(retry_interval)
    
    logger.error("Failed to connect to Redis after maximum retries")
    return False


def run_ingestion():
    """Run the full data ingestion process."""
    from models.database import init_database
    from services.data_ingestion import ingestion_service
    from config import config
    
    logger.info("=" * 60)
    logger.info("NBA Analytics - Data Ingestion")
    logger.info("=" * 60)
    
    # Wait for dependencies
    if not wait_for_database():
        sys.exit(1)
    
    if not wait_for_redis():
        logger.warning("Redis not available, continuing without cache")
    
    # Initialize database tables
    logger.info("Initializing database tables...")
    init_database()
    
    # Run ingestion
    logger.info(f"Starting data ingestion for season {config.ingestion.current_season}")
    
    try:
        ingestion_service.run_full_ingestion()
        logger.info("Data ingestion completed successfully!")
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Ingestion Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_ingestion()
