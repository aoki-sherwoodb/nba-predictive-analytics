# NBA Analytics Platform

A real-time NBA statistics dashboard that displays team standings, game scores, and player statistics. Built with FastAPI, PostgreSQL, Redis, and Streamlit.

## 🏀 Features

- **Live Standings**: View current NBA standings by conference
- **Today's Games**: Track live game scores and final results
- **Statistical Leaders**: See top performers in points, rebounds, assists, etc.
- **Team Analysis**: Deep dive into individual team performance

## 🏗 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NBA API       │────▶│  Ingestion      │────▶│  PostgreSQL     │
│   (nba_api)     │     │  Service        │     │  Database       │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌─────────────────┐              │
                        │  Redis Cache    │◀─────────────┤
                        └────────┬────────┘              │
                                 │                       │
                        ┌────────▼────────┐              │
                        │  FastAPI        │◀─────────────┘
                        │  Backend        │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  Streamlit      │
                        │  Dashboard      │
                        └─────────────────┘
```

## 📁 Project Structure

```
nba-analytics/
├── api/                    # FastAPI backend
│   ├── __init__.py
│   └── main.py            # API endpoints
├── dashboard/             # Streamlit frontend
│   ├── __init__.py
│   └── app.py             # Dashboard application
├── models/                # Database models
│   ├── __init__.py
│   ├── database.py        # Database connection
│   └── database_models.py # SQLAlchemy models
├── services/              # Business logic services
│   ├── __init__.py
│   ├── cache.py           # Redis caching
│   └── data_ingestion.py  # NBA data fetching
├── scripts/               # Utility scripts
│   ├── run_ingestion.py   # Data ingestion runner
│   └── setup_local.sh     # Local setup script
├── tests/                 # Test files
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker orchestration
├── Dockerfile.api         # API container
├── Dockerfile.dashboard   # Dashboard container
└── .env.example           # Environment template
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd nba-analytics
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Run initial data ingestion:**
   ```bash
   docker-compose --profile ingestion run ingestion
   ```

4. **Access the dashboard:**
   - Dashboard: http://localhost:8501
   - API Docs: http://localhost:8000/docs

### Option 2: Local Development

1. **Prerequisites:**
   - Python 3.10+
   - PostgreSQL 14+
   - Redis 7+

2. **Start PostgreSQL and Redis (via Docker):**
   ```bash
   docker-compose up postgres redis -d
   ```

3. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run data ingestion:**
   ```bash
   python scripts/run_ingestion.py
   ```

5. **Start the API server:**
   ```bash
   python -m uvicorn api.main:app --reload --port 8000
   ```

6. **Start the dashboard (new terminal):**
   ```bash
   source venv/bin/activate
   streamlit run dashboard/app.py
   ```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/teams` | GET | List all teams |
| `/api/teams/{id}` | GET | Get team by ID |
| `/api/players` | GET | List players |
| `/api/players/{id}` | GET | Get player by ID |
| `/api/standings` | GET | Get conference standings |
| `/api/games/today` | GET | Get today's games |
| `/api/games/recent` | GET | Get recent games |
| `/api/stats/leaders` | GET | Get statistical leaders |
| `/api/stats/player/{id}` | GET | Get player game stats |
| `/api/refresh/standings` | POST | Refresh standings data |
| `/api/refresh/games` | POST | Refresh games data |
| `/api/refresh/full` | POST | Full data refresh |

## ⚙️ Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | localhost | PostgreSQL host |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_NAME` | nba_analytics | Database name |
| `DB_USER` | postgres | Database user |
| `DB_PASSWORD` | postgres | Database password |
| `REDIS_HOST` | localhost | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `API_PORT` | 8000 | API server port |
| `CURRENT_SEASON` | 2024-25 | NBA season |

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## 🔧 Development

### Adding New Endpoints

1. Add model in `models/database_models.py`
2. Add service logic in `services/`
3. Add API endpoint in `api/main.py`
4. Update dashboard in `dashboard/app.py`

### Database Migrations

For production, consider using Alembic for migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## 📈 GCP Deployment (Future)

For deploying to Google Cloud Platform:

1. **Set up GCP project:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Create Cloud SQL instance:**
   ```bash
   gcloud sql instances create nba-postgres \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1
   ```

3. **Create Redis instance:**
   ```bash
   gcloud redis instances create nba-redis \
     --size=1 \
     --region=us-central1
   ```

4. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy nba-api \
     --image gcr.io/YOUR_PROJECT/nba-api \
     --platform managed \
     --region us-central1
   ```

## 📝 Notes

- The NBA API has rate limits. The ingestion service includes delays to avoid hitting them.
- Data is cached in Redis with appropriate TTLs to reduce API calls.
- For production, consider adding authentication to the API endpoints.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📜 License

MIT License - feel free to use this for your own projects!
