#!/usr/bin/env python3
"""
Run full multi-season ingestion with historical data.
This will ingest data for the current season plus the number of historical seasons
specified in config.ingestion.historical_seasons (default: 3).
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import init_database
from services.data_ingestion import ingestion_service
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    """Run full multi-season ingestion."""
    logger.info("=" * 60)
    logger.info("NBA Analytics - Multi-Season Ingestion")
    logger.info("=" * 60)
    logger.info(f"Current season: {config.ingestion.current_season}")
    logger.info(f"Historical seasons to ingest: {config.ingestion.historical_seasons}")
    logger.info("=" * 60)

    # Initialize database
    init_database()

    # Run full ingestion with historical data
    ingestion_service.run_full_ingestion(ingest_historical=True)

    logger.info("=" * 60)
    logger.info("Multi-season ingestion complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
