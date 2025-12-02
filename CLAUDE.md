# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NBA Predictive Analytics Platform - a real-time NBA statistics dashboard and API built with Python 3.11+. The system ingests NBA game results and player statistics, stores them in PostgreSQL, caches with Redis, and displays analytics through a Streamlit dashboard and FastAPI backend.

## Build & Development Commands

### Local Development Setup
```bash
# Install dependencies
pip install -r nba-analytics/requirements.txt

# Start database services (from nba-analytics/)
docker-compose up postgres redis -d

# Initialize database tables
python -m models.database

# Run data ingestion
python scripts/run_ingestion.py

# Start API server (port 8000)
python -m uvicorn api.main:app --reload --port 8000

# Start dashboard (port 8501)
streamlit run dashboard/app.py
```

### Docker Deployment
```bash
cd nba-analytics
docker-compose up -d                          # Start all services
docker-compose --profile ingestion run ingestion  # Run initial ingestion
docker-compose logs -f api                    # View API logs
```

### Testing
```bash
pytest                              # Run all tests
pytest --cov=. --cov-report=html    # With coverage report
pytest tests/test_api.py::TestHealthEndpoint  # Single test class
```

### Verify Connections
```bash
python -m models.database   # Test PostgreSQL connection
python -m services.cache    # Test Redis connection
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                NBA API (nba_api library)                  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│   Data Ingestion Service (services/data_ingestion.py)    │
│   - Rate limiting (0.6s between NBA API calls)           │
└────────────────────────┬─────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐
│    PostgreSQL    │             │   Redis Cache    │
│  (normalized     │             │  (TTL: 30s-24h)  │
│   historical)    │             │                  │
└────────┬─────────┘             └──────┬───────────┘
         │                              │
         └───────────────┬──────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌──────────────────────┐        ┌──────────────────────┐
│  FastAPI Backend     │        │  Streamlit Dashboard │
│  (api/main.py:8000)  │◄──────►│  (dashboard/app.py)  │
└──────────────────────┘        └──────────────────────┘
```

### Key Components

- **api/main.py** (549 lines) - FastAPI REST endpoints with Pydantic models, CORS middleware, cache-first queries
- **dashboard/app.py** (557 lines) - Streamlit web UI with Plotly charts and custom styling
- **models/database_models.py** (233 lines) - 6 SQLAlchemy ORM models: Team, Player, Game, PlayerGameStats, TeamStanding, IngestionLog
- **services/data_ingestion.py** (630 lines) - ETL from NBA API with rate limiting and upsert logic
- **services/cache.py** (228 lines) - Redis caching with key prefixes and configurable TTLs
- **config.py** (84 lines) - 12-factor configuration via environment variables

### Data Flow Pattern

1. Ingestion service fetches from NBA API → writes to PostgreSQL and Redis
2. API endpoints check Redis cache first → fallback to PostgreSQL
3. Dashboard calls API endpoints → renders with caching decorators

## Configuration

Environment variables (with defaults in config.py):
```
DB_HOST=localhost, DB_PORT=5432, DB_NAME=nba_analytics, DB_USER=postgres, DB_PASSWORD=postgres
REDIS_HOST=localhost, REDIS_PORT=6379
API_HOST=0.0.0.0, API_PORT=8000, API_DEBUG=false
CORS_ORIGINS=http://localhost:8501,http://localhost:3000
CURRENT_SEASON=2024-25
```

## Code Patterns

- **Database sessions:** Use context managers `with db_manager.get_session() as session:`
- **Caching:** Key prefixes (standings:, team:, player:, game:) with TTL-based expiration
- **API responses:** Pydantic BaseModel for validation, Depends(get_db) for session injection
- **Upserts:** PostgreSQL INSERT ON CONFLICT DO UPDATE pattern throughout ingestion
- **Type hints:** Full annotations on all functions (Python 3.10+ style)

## Known Issues

1. **NBA API bug:** `nba_api` library throws KeyError on missing fields in live game responses. Workaround in `data_ingestion.py` lines 347-359 gracefully skips today's games.
2. **No migrations:** Database uses auto-creation; Alembic planned for production.
3. **No auth:** Admin endpoints (POST /api/refresh/*) are unprotected.
