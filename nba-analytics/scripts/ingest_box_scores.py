#!/usr/bin/env python3
"""
Ingest box scores (player stats) for all completed games.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import init_database, db_manager
from models.database_models import Game
from services.data_ingestion import ingestion_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    """Ingest box scores for all completed games."""
    logger.info("=" * 60)
    logger.info("NBA Analytics - Box Score Ingestion")
    logger.info("=" * 60)

    # Initialize database
    init_database()

    # Get all completed games
    with db_manager.get_session() as session:
        completed_games = session.query(Game).filter(
            Game.status == 'final'
        ).order_by(Game.game_date.desc()).all()

        logger.info(f"Found {len(completed_games)} completed games")

        if len(completed_games) == 0:
            logger.warning("No completed games found in database")
            logger.info("Games must have status='final' to have box scores available")
            return

        total_stats = 0
        successful = 0
        failed = 0

        for idx, game in enumerate(completed_games, 1):
            try:
                logger.info(f"[{idx}/{len(completed_games)}] Processing {game.nba_game_id} - {game.game_date}")
                stats_count = ingestion_service.ingest_game_box_score(game.nba_game_id)
                total_stats += stats_count
                successful += 1
                logger.info(f"  ✓ Ingested {stats_count} player stats")
            except Exception as e:
                failed += 1
                logger.error(f"  ✗ Failed to ingest box score: {e}")
                # Continue with next game instead of stopping

    logger.info("=" * 60)
    logger.info(f"Ingestion Summary:")
    logger.info(f"  Total games processed: {len(completed_games)}")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total player stats ingested: {total_stats}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
