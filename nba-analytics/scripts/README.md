# NBA Analytics - Data Ingestion Scripts

## Overview

This directory contains scripts for data ingestion and management.

## Scripts

### run_ingestion.py

Main ingestion script that runs a full data refresh (teams, standings, rosters, today's games).

**Usage:**
```bash
python scripts/run_ingestion.py
```

**Docker Usage:**
```bash
docker compose --profile ingestion up ingestion
```

### test_todays_games.py

Test script to check if games are scheduled for today and display recent/upcoming games.

**Usage:**
```bash
python scripts/test_todays_games.py
```

**What it does:**
- Checks if there are games scheduled for today
- If no games today, finds the next scheduled games
- Shows recent games from the past week
- Suggests commands to populate the database with game data

### ingest_date_range.py

Ingest games for a specific date range. Useful for populating historical game data.

**Usage:**
```bash
# Ingest games from the past week
python scripts/ingest_date_range.py --start 2025-11-25 --end 2025-12-02

# Ingest games with custom delay between API calls
python scripts/ingest_date_range.py --start 2025-11-25 --end 2025-12-02 --delay 3
```

**Parameters:**
- `--start`: Start date in YYYY-MM-DD format (required)
- `--end`: End date in YYYY-MM-DD format (required)
- `--delay`: Delay between API calls in seconds (default: 2)

## Common Workflows

### Populate Dashboard with Recent Games

If the "Today's Games" panel is empty:

1. **Check for games:**
   ```bash
   python scripts/test_todays_games.py
   ```

2. **Ingest recent games:**
   ```bash
   # For the past week
   python scripts/ingest_date_range.py --start 2025-11-25 --end 2025-12-02
   ```

3. **Refresh the dashboard:**
   - Click the "Sync" button in the dashboard sidebar, or
   - Restart the dashboard container

### Full Data Refresh

To refresh all data (teams, standings, rosters, games):

```bash
docker compose --profile ingestion up ingestion --force-recreate
```

Or manually:
```bash
python scripts/run_ingestion.py
```

## Notes

- The NBA API has rate limits. Use the `--delay` parameter if you encounter rate limiting issues.
- The NBA API sometimes has bugs with missing fields (like 'WinProbability'). The scripts handle these gracefully.
- Games are ingested for the season configured in `CURRENT_SEASON` environment variable (default: 2025-26).
