#!/usr/bin/env python3
"""
Ingest games for a specific date range.
Useful for populating the database with historical game data.
"""
import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def ingest_games_for_date(target_date):
    """Ingest games for a specific date."""
    from nba_api.stats.endpoints import scoreboardv2
    from models.database import db_manager
    from models.database_models import Game, Team
    from sqlalchemy.dialects.postgresql import insert
    from config import config
    import requests

    logger.info(f"Ingesting games for {target_date}...")

    scoreboard_data = None
    try:
        # Fetch scoreboard
        try:
            scoreboard = scoreboardv2.ScoreboardV2(
                game_date=target_date.strftime('%Y-%m-%d'),
                league_id='00'
            )
            scoreboard_data = scoreboard.get_normalized_dict()
        except KeyError as ke:
            # NBA API library bug - fall back to direct request
            logger.debug(f"NBA API bug on {target_date}: missing field '{ke}'. Using direct request...")

            url = "https://stats.nba.com/stats/scoreboardv2"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://stats.nba.com/',
            }
            params = {
                'GameDate': target_date.strftime('%m/%d/%Y'),
                'LeagueID': '00',
                'DayOffset': '0'
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            raw_data = response.json()

            # Convert raw response to normalized format
            result_sets = raw_data.get('resultSets', [])
            scoreboard_data = {}

            for result_set in result_sets:
                name = result_set.get('name', '')
                headers_list = result_set.get('headers', [])
                rows = result_set.get('rowSet', [])

                # Convert to list of dicts
                scoreboard_data[name] = [
                    dict(zip(headers_list, row)) for row in rows
                ]

    except Exception as e:
        logger.error(f"Error fetching games on {target_date}: {e}")
        return 0

    if not scoreboard_data:
        logger.warning(f"No data available for {target_date}")
        return 0

    game_headers = scoreboard_data.get('GameHeader', [])
    logger.info(f"Found {len(game_headers)} games on {target_date}")

    if len(game_headers) == 0:
        return 0

    count = 0
    with db_manager.get_session() as session:
        for game_data in game_headers:
            game_id = game_data.get('GAME_ID')
            if not game_id:
                continue

            # Get teams
            home_team_id = game_data.get('HOME_TEAM_ID')
            away_team_id = game_data.get('VISITOR_TEAM_ID')

            if not home_team_id or not away_team_id:
                logger.warning(f"Game {game_id} missing team IDs, skipping")
                continue

            home_team = session.query(Team).filter(Team.nba_id == home_team_id).first()
            away_team = session.query(Team).filter(Team.nba_id == away_team_id).first()

            if not home_team or not away_team:
                logger.warning(f"Teams not found for game {game_id}")
                continue

            # Parse game status
            status_code = game_data.get('GAME_STATUS_ID', 1)
            if status_code == 1:
                status = 'scheduled'
            elif status_code == 2:
                status = 'live'
            elif status_code == 3:
                status = 'final'
            else:
                status = 'scheduled'

            # Get scores from line score data
            home_score = 0
            away_score = 0
            for line in scoreboard_data.get('LineScore', []):
                line_game_id = line.get('GAME_ID')
                line_team_id = line.get('TEAM_ID')

                if line_game_id == game_id and line_team_id:
                    if line_team_id == home_team_id:
                        home_score = line.get('PTS', 0) or 0
                    elif line_team_id == away_team_id:
                        away_score = line.get('PTS', 0) or 0

            # Upsert game
            stmt = insert(Game).values(
                nba_game_id=game_id,
                season=config.ingestion.current_season,
                season_type='Regular Season',
                game_date=target_date,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_score=home_score,
                away_score=away_score,
                status=status,
                period=game_data.get('LIVE_PERIOD'),
                game_clock=game_data.get('LIVE_PC_TIME')
            ).on_conflict_do_update(
                index_elements=['nba_game_id'],
                set_={
                    'home_score': home_score,
                    'away_score': away_score,
                    'status': status,
                    'period': game_data.get('LIVE_PERIOD'),
                    'game_clock': game_data.get('LIVE_PC_TIME')
                }
            )
            session.execute(stmt)
            count += 1

        logger.info(f"Ingested {count} games for {target_date}")

    return count


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Ingest NBA games for a date range')
    parser.add_argument('--start', type=parse_date, required=True,
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=parse_date, required=True,
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--delay', type=int, default=2,
                        help='Delay between API calls in seconds (default: 2)')

    args = parser.parse_args()

    if args.start > args.end:
        logger.error("Start date must be before or equal to end date")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("NBA Analytics - Date Range Ingestion")
    logger.info("=" * 60)
    logger.info(f"Date range: {args.start} to {args.end}")

    # Initialize database
    from models.database import init_database
    init_database()

    # Iterate through dates
    current_date = args.start
    total_games = 0

    while current_date <= args.end:
        games = ingest_games_for_date(current_date)
        total_games += games

        current_date += timedelta(days=1)

        # Rate limiting
        if current_date <= args.end:
            time.sleep(args.delay)

    logger.info("=" * 60)
    logger.info(f"Total games ingested: {total_games}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
