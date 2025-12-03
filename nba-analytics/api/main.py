"""
FastAPI Backend API for NBA Analytics Platform.
Serves data to the dashboard and external clients.
"""

import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from config import config
from models.database_models import Team, Player, Game, PlayerGameStats, TeamStanding
from models.database import db_manager
from services.cache import cache_manager
from services.data_ingestion import ingestion_service
from services.live_game_service import live_game_service

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Pydantic models for API responses
class TeamResponse(BaseModel):
    id: int
    nba_id: int
    abbreviation: str
    name: str
    city: Optional[str]
    conference: Optional[str]

    class Config:
        from_attributes = True


class PlayerResponse(BaseModel):
    id: int
    nba_id: int
    full_name: str
    team_id: Optional[int]
    position: Optional[str]
    jersey_number: Optional[str]
    height: Optional[str]
    weight: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True


class StandingResponse(BaseModel):
    team_id: int
    team_name: str
    team_abbr: str
    conference: str
    wins: int
    losses: int
    win_pct: float
    conf_rank: Optional[int]
    games_back: float
    streak: Optional[str]
    last_10: Optional[str]


class StandingsResponse(BaseModel):
    season: str
    updated_at: str
    east: List[StandingResponse]
    west: List[StandingResponse]


class GameTeamInfo(BaseModel):
    id: int
    name: str
    abbr: str
    score: int


class GameResponse(BaseModel):
    game_id: str
    home_team: GameTeamInfo
    away_team: GameTeamInfo
    status: str
    period: Optional[int]
    clock: Optional[str]
    game_date: Optional[str]


class PlayerStatsResponse(BaseModel):
    player_id: int
    player_name: str
    team_abbr: str
    minutes: float
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    fg_pct: Optional[float]
    three_pct: Optional[float]
    ft_pct: Optional[float]
    plus_minus: int


class HealthResponse(BaseModel):
    status: str
    database: bool
    cache: bool
    timestamp: str


# Live game response models
class LiveGameInfo(BaseModel):
    game_id: str
    home_team_id: int
    away_team_id: int
    home_team_abbr: str
    away_team_abbr: str
    home_team_name: str
    away_team_name: str
    home_score: int
    away_score: int
    status: str
    status_id: int
    is_live: bool
    period: int
    game_clock: str
    start_time: str


class PlayEvent(BaseModel):
    event_id: int
    period: int
    clock: str
    event_type: str
    description: str
    player_name: Optional[str]
    team_abbr: Optional[str]
    home_score: int
    away_score: int
    shot_made: Optional[bool]


class ShotLocation(BaseModel):
    x: float
    y: float
    player_id: int
    player_name: str
    team_id: int
    team_abbr: str
    shot_type: str
    made: bool
    distance: int
    zone: str
    action_type: str
    period: int
    clock: Optional[str] = None  # Live API uses clock string instead of min/sec
    minutes_remaining: Optional[int] = None
    seconds_remaining: Optional[int] = None


class BoxScorePlayer(BaseModel):
    player_id: int
    player_name: str
    team_id: int
    team_abbr: str
    minutes: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    fg_made: int
    fg_attempted: int
    fg_pct: float
    three_made: int
    three_attempted: int
    plus_minus: int


class BoxScoreTeam(BaseModel):
    team_id: int
    team_abbr: str
    points: int
    rebounds: int
    assists: int
    fg_pct: float
    three_pct: float


class LiveGameDataResponse(BaseModel):
    game_info: Optional[LiveGameInfo]
    plays: List[PlayEvent]
    shots: List[ShotLocation]
    box_score: Dict[str, Any]


# Create FastAPI app
app = FastAPI(
    title="NBA Analytics API",
    description="Real-time NBA statistics and analytics platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for database session
def get_db() -> Session:
    """Get database session."""
    session = db_manager.session_factory()
    try:
        yield session
    finally:
        session.close()


# Health check endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Check the health status of the API and its dependencies."""
    db_ok = db_manager.check_connection()
    cache_ok = cache_manager.check_connection()

    return HealthResponse(
        status="healthy" if db_ok and cache_ok else "degraded",
        database=db_ok,
        cache=cache_ok,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/", tags=["Health"])
def root():
    """API root endpoint."""
    return {"message": "NBA Analytics API", "version": "1.0.0", "docs": "/docs"}


# Team endpoints
@app.get("/api/teams", response_model=List[TeamResponse], tags=["Teams"])
def get_teams(
    conference: Optional[str] = Query(
        None, description="Filter by conference (East/West)"
    ),
    db: Session = Depends(get_db),
):
    """Get all NBA teams."""
    query = db.query(Team)

    if conference:
        query = query.filter(Team.conference == conference)

    teams = query.order_by(Team.name).all()
    return teams


@app.get("/api/teams/{team_id}", response_model=TeamResponse, tags=["Teams"])
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get a specific team by ID."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


# Player endpoints
@app.get("/api/players", response_model=List[PlayerResponse], tags=["Players"])
def get_players(
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    active_only: bool = Query(True, description="Only show active players"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get NBA players with optional filtering."""
    query = db.query(Player)

    if team_id:
        query = query.filter(Player.team_id == team_id)

    if active_only:
        query = query.filter(Player.is_active == True)

    players = query.order_by(Player.full_name).offset(offset).limit(limit).all()
    return players


@app.get("/api/players/{player_id}", response_model=PlayerResponse, tags=["Players"])
def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get a specific player by ID."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


# Standings endpoints
@app.get("/api/standings", response_model=StandingsResponse, tags=["Standings"])
def get_standings(
    season: str = Query(default=None, description="Season (e.g., '2025-26')"),
    db: Session = Depends(get_db),
):
    """Get current NBA standings by conference."""
    season = season or config.ingestion.current_season
    logger.info(f"[STANDINGS] Fetching standings for season: {season} (current_season config: {config.ingestion.current_season})")

    # Try cache first
    cached = cache_manager.get_standings(season)
    if cached:
        # Format cached data
        standings = cached.get("standings", [])
        east = [s for s in standings if s.get("conference") == "East"]
        west = [s for s in standings if s.get("conference") == "West"]

        east.sort(key=lambda x: x.get("conf_rank") or 999)
        west.sort(key=lambda x: x.get("conf_rank") or 999)

        return StandingsResponse(
            season=season,
            updated_at=cached.get("updated_at", ""),
            east=[StandingResponse(**s) for s in east],
            west=[StandingResponse(**s) for s in west],
        )

    # Query database
    standings_query = (
        db.query(TeamStanding, Team).join(Team).filter(TeamStanding.season == season)
    )

    standings_data = standings_query.all()

    east = []
    west = []

    for standing, team in standings_data:
        record = StandingResponse(
            team_id=team.id,
            team_name=team.name,
            team_abbr=team.abbreviation,
            conference=team.conference or "",
            wins=standing.wins,
            losses=standing.losses,
            win_pct=standing.win_percentage,
            conf_rank=standing.conference_rank,
            games_back=standing.games_back,
            streak=standing.current_streak,
            last_10=standing.last_10,
        )

        if team.conference == "East":
            east.append(record)
        else:
            west.append(record)

    east.sort(key=lambda x: x.conf_rank or 999)
    west.sort(key=lambda x: x.conf_rank or 999)

    return StandingsResponse(
        season=season, updated_at=datetime.utcnow().isoformat(), east=east, west=west
    )


# Games endpoints
@app.get("/api/games/today", response_model=List[GameResponse], tags=["Games"])
def get_todays_games(db: Session = Depends(get_db)):
    """Get today's NBA games (based on Eastern Time)."""
    # Try cache first
    cached = cache_manager.get_todays_games()
    if cached:
        return [GameResponse(**g) for g in cached]

    # Query database for current season only, using Eastern Time for "today"
    from datetime import datetime
    from zoneinfo import ZoneInfo

    # Get today's date in Eastern Time
    et_now = datetime.now(ZoneInfo("America/New_York"))
    today = et_now.date()
    current_season = config.ingestion.current_season
    logger.info(f"[TODAY'S GAMES] Looking for games on {today} (ET) in season {current_season}")
    games = db.query(Game).filter(
        Game.game_date == today,
        Game.season == current_season
    ).all()
    logger.info(f"[TODAY'S GAMES] Found {len(games)} games")

    result = []
    for game in games:
        result.append(
            GameResponse(
                game_id=game.nba_game_id,
                home_team=GameTeamInfo(
                    id=game.home_team.id,
                    name=game.home_team.name,
                    abbr=game.home_team.abbreviation,
                    score=game.home_score or 0,
                ),
                away_team=GameTeamInfo(
                    id=game.away_team.id,
                    name=game.away_team.name,
                    abbr=game.away_team.abbreviation,
                    score=game.away_score or 0,
                ),
                status=game.status,
                period=game.period,
                clock=game.game_clock,
                game_date=str(game.game_date),
            )
        )

    return result


@app.get("/api/games/recent", response_model=List[GameResponse], tags=["Games"])
def get_recent_games(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    include_all_statuses: bool = Query(
        False, description="Include scheduled/live games in addition to final games"
    ),
    db: Session = Depends(get_db),
):
    """Get recent games from the past N days."""
    from datetime import timedelta

    start_date = date.today() - timedelta(days=days)

    query = db.query(Game).filter(Game.game_date >= start_date)

    # Only filter by 'final' status if not including all statuses
    if not include_all_statuses:
        query = query.filter(Game.status == "final")

    if team_id:
        query = query.filter(
            (Game.home_team_id == team_id) | (Game.away_team_id == team_id)
        )

    games = query.order_by(desc(Game.game_date)).limit(50).all()

    result = []
    for game in games:
        result.append(
            GameResponse(
                game_id=game.nba_game_id,
                home_team=GameTeamInfo(
                    id=game.home_team.id,
                    name=game.home_team.name,
                    abbr=game.home_team.abbreviation,
                    score=game.home_score or 0,
                ),
                away_team=GameTeamInfo(
                    id=game.away_team.id,
                    name=game.away_team.name,
                    abbr=game.away_team.abbreviation,
                    score=game.away_score or 0,
                ),
                status=game.status,
                period=game.period,
                clock=game.game_clock,
                game_date=str(game.game_date),
            )
        )

    return result


# Live game endpoints
@app.get("/api/games/live", response_model=List[LiveGameInfo], tags=["Live Games"])
def get_live_games():
    """Get all games currently in progress or scheduled for today."""
    games = live_game_service.get_live_games()
    return [LiveGameInfo(**g) for g in games]


@app.get(
    "/api/games/live/active", response_model=List[LiveGameInfo], tags=["Live Games"]
)
def get_active_live_games():
    """Get only games that are currently in progress."""
    games = live_game_service.get_live_games()
    return [LiveGameInfo(**g) for g in games if g.get("is_live")]


@app.get(
    "/api/games/live/upcoming", response_model=List[LiveGameInfo], tags=["Live Games"]
)
def get_upcoming_games():
    """Get games scheduled for today that haven't started yet."""
    games = live_game_service.get_upcoming_games()
    return [LiveGameInfo(**g) for g in games]


@app.get(
    "/api/games/{game_id}/live",
    response_model=LiveGameDataResponse,
    tags=["Live Games"],
)
def get_live_game_data(game_id: str):
    """Get comprehensive live data for a specific game (plays, shots, box score)."""
    data = live_game_service.get_live_game_data(game_id)

    return LiveGameDataResponse(
        game_info=LiveGameInfo(**data["game_info"]) if data.get("game_info") else None,
        plays=[PlayEvent(**p) for p in data.get("plays", [])],
        shots=[ShotLocation(**s) for s in data.get("shots", [])],
        box_score=data.get("box_score", {}),
    )


@app.get(
    "/api/games/{game_id}/plays", response_model=List[PlayEvent], tags=["Live Games"]
)
def get_game_plays(
    game_id: str,
    last_event_id: int = Query(0, description="Only return events after this ID"),
):
    """Get play-by-play events for a game (supports incremental fetching)."""
    plays = live_game_service.get_play_by_play(game_id, last_event_id)
    return [PlayEvent(**p) for p in plays]


@app.get(
    "/api/games/{game_id}/shots", response_model=List[ShotLocation], tags=["Live Games"]
)
def get_game_shots(game_id: str):
    """Get shot chart data for a game with court coordinates."""
    shots = live_game_service.get_shot_chart(game_id)
    return [ShotLocation(**s) for s in shots]


# Statistics endpoints
@app.get(
    "/api/stats/leaders", response_model=List[PlayerStatsResponse], tags=["Statistics"]
)
def get_stat_leaders(
    stat: str = Query(
        "points",
        description="Stat to rank by (points, rebounds, assists, steals, blocks)",
    ),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get statistical leaders for a given category."""
    stat_column_map = {
        "points": PlayerGameStats.points,
        "rebounds": PlayerGameStats.total_rebounds,
        "assists": PlayerGameStats.assists,
        "steals": PlayerGameStats.steals,
        "blocks": PlayerGameStats.blocks,
    }

    if stat not in stat_column_map:
        raise HTTPException(status_code=400, detail=f"Invalid stat: {stat}")

    stat_column = stat_column_map[stat]

    # Get average stats per game for current season
    current_season = config.ingestion.current_season
    subquery = (
        db.query(
            PlayerGameStats.player_id,
            func.avg(PlayerGameStats.points).label("avg_points"),
            func.avg(PlayerGameStats.total_rebounds).label("avg_rebounds"),
            func.avg(PlayerGameStats.assists).label("avg_assists"),
            func.avg(PlayerGameStats.steals).label("avg_steals"),
            func.avg(PlayerGameStats.blocks).label("avg_blocks"),
            func.avg(PlayerGameStats.turnovers).label("avg_turnovers"),
            func.avg(PlayerGameStats.minutes_played).label("avg_minutes"),
            func.avg(PlayerGameStats.plus_minus).label("avg_plus_minus"),
            func.sum(PlayerGameStats.field_goals_made).label("total_fgm"),
            func.sum(PlayerGameStats.field_goals_attempted).label("total_fga"),
            func.sum(PlayerGameStats.three_pointers_made).label("total_3pm"),
            func.sum(PlayerGameStats.three_pointers_attempted).label("total_3pa"),
            func.sum(PlayerGameStats.free_throws_made).label("total_ftm"),
            func.sum(PlayerGameStats.free_throws_attempted).label("total_fta"),
            func.count(PlayerGameStats.id).label("games_played"),
        )
        .join(Game, PlayerGameStats.game_id == Game.id)
        .filter(Game.season == current_season)
        .group_by(PlayerGameStats.player_id)
        .having(func.count(PlayerGameStats.id) >= 1)  # Minimum games played
        .subquery()
    )

    # Join with player info
    results = (
        db.query(
            Player,
            Team,
            subquery.c.avg_points,
            subquery.c.avg_rebounds,
            subquery.c.avg_assists,
            subquery.c.avg_steals,
            subquery.c.avg_blocks,
            subquery.c.avg_turnovers,
            subquery.c.avg_minutes,
            subquery.c.avg_plus_minus,
            subquery.c.total_fgm,
            subquery.c.total_fga,
            subquery.c.total_3pm,
            subquery.c.total_3pa,
            subquery.c.total_ftm,
            subquery.c.total_fta,
        )
        .join(subquery, Player.id == subquery.c.player_id)
        .join(Team, Player.team_id == Team.id)
        .order_by(desc(getattr(subquery.c, f"avg_{stat}")))
        .limit(limit)
        .all()
    )

    leaders = []
    for row in results:
        player = row[0]
        team = row[1]
        avg_points, avg_rebounds, avg_assists, avg_steals, avg_blocks = row[2:7]
        avg_turnovers, avg_minutes, avg_plus_minus = row[7:10]
        total_fgm, total_fga, total_3pm, total_3pa, total_ftm, total_fta = row[10:16]

        fg_pct = None
        if total_fga and total_fga > 0:
            fg_pct = round(total_fgm / total_fga * 100, 1)

        three_pct = None
        if total_3pa and total_3pa > 0:
            three_pct = round(total_3pm / total_3pa * 100, 1)

        ft_pct = None
        if total_fta and total_fta > 0:
            ft_pct = round(total_ftm / total_fta * 100, 1)

        leaders.append(
            PlayerStatsResponse(
                player_id=player.id,
                player_name=player.full_name,
                team_abbr=team.abbreviation,
                minutes=round(avg_minutes or 0, 1),
                points=round(avg_points or 0),
                rebounds=round(avg_rebounds or 0),
                assists=round(avg_assists or 0),
                steals=round(avg_steals or 0),
                blocks=round(avg_blocks or 0),
                turnovers=round(avg_turnovers or 0),
                fg_pct=fg_pct,
                three_pct=three_pct,
                ft_pct=ft_pct,
                plus_minus=round(avg_plus_minus or 0),
            )
        )

    return leaders


@app.get("/api/stats/player/{player_id}", tags=["Statistics"])
def get_player_game_stats(
    player_id: int, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)
):
    """Get recent game stats for a specific player."""
    stats = (
        db.query(PlayerGameStats, Game, Team)
        .join(Game)
        .join(Team, PlayerGameStats.team_id == Team.id)
        .filter(PlayerGameStats.player_id == player_id)
        .order_by(desc(Game.game_date))
        .limit(limit)
        .all()
    )

    result = []
    for stat, game, team in stats:
        result.append(
            {
                "game_date": str(game.game_date),
                "opponent": (
                    game.away_team.abbreviation
                    if game.home_team_id == team.id
                    else game.home_team.abbreviation
                ),
                "minutes": stat.minutes_played,
                "points": stat.points,
                "rebounds": stat.total_rebounds,
                "assists": stat.assists,
                "steals": stat.steals,
                "blocks": stat.blocks,
                "turnovers": stat.turnovers,
                "fg": f"{stat.field_goals_made}/{stat.field_goals_attempted}",
                "fg_pct": stat.field_goal_percentage,
                "three_pt": f"{stat.three_pointers_made}/{stat.three_pointers_attempted}",
                "three_pct": stat.three_point_percentage,
                "plus_minus": stat.plus_minus,
            }
        )

    return result


# Data refresh endpoints
@app.post("/api/refresh/standings", tags=["Admin"])
async def refresh_standings(background_tasks: BackgroundTasks):
    """Trigger a refresh of standings data."""
    background_tasks.add_task(
        ingestion_service.ingest_standings, config.ingestion.current_season
    )
    return {"message": "Standings refresh started"}


@app.post("/api/refresh/games", tags=["Admin"])
async def refresh_games(background_tasks: BackgroundTasks):
    """Trigger a refresh of today's games."""
    background_tasks.add_task(ingestion_service.ingest_todays_games)
    return {"message": "Games refresh started"}


@app.post("/api/refresh/full", tags=["Admin"])
async def refresh_full(background_tasks: BackgroundTasks):
    """Trigger an incremental data refresh (standings, rosters, today's games, recent games)."""
    background_tasks.add_task(ingestion_service.run_incremental_refresh)
    return {"message": "Incremental data refresh started"}


# Prediction endpoints
from services.prediction_service import prediction_service


class TeamPredictionResponse(BaseModel):
    """Response model for team predictions."""

    team_id: int
    team_name: str
    team_abbr: str
    conference: Optional[str]
    predicted_wins: float
    predicted_losses: float
    predicted_win_pct: float
    predicted_conference_rank: int
    playoff_probability: float
    predicted_ppg: float
    predicted_oppg: float
    predicted_pace: float
    predicted_defensive_rating: float
    wins_lower_bound: Optional[float] = None
    wins_upper_bound: Optional[float] = None


class AllPredictionsResponse(BaseModel):
    """Response model for all team predictions."""

    season: str
    prediction_date: Optional[str]
    model_version: Optional[str]
    model_mae_wins: Optional[float]
    east: List[TeamPredictionResponse]
    west: List[TeamPredictionResponse]


class PredictionComparisonItem(BaseModel):
    """Single team prediction vs actual comparison."""

    team_id: int
    team_abbr: str
    conference: Optional[str]
    predicted_wins: float
    actual_wins: int
    wins_diff: float
    predicted_rank: int
    actual_rank: Optional[int]
    rank_diff: int
    playoff_probability: float


class PredictionComparisonResponse(BaseModel):
    """Response model for prediction vs actual comparison."""

    season: str
    prediction_date: Optional[str]
    comparisons: List[PredictionComparisonItem]


class ModelInfoResponse(BaseModel):
    """Response model for model metadata."""

    model_version: str
    model_type: str
    trained_at: Optional[str]
    training_seasons: Optional[List[str]]
    epochs_trained: Optional[int]
    validation_loss: Optional[float]
    mae_wins: Optional[float]
    mae_ppg: Optional[float]
    is_active: bool


@app.get(
    "/api/predictions", response_model=AllPredictionsResponse, tags=["Predictions"]
)
def get_all_predictions(
    season: str = Query(default=None, description="Season (e.g., '2025-26')")
):
    """Get end-of-season predictions for all teams."""
    predictions = prediction_service.get_all_predictions(season)

    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for season {season or config.ingestion.current_season}",
        )

    return AllPredictionsResponse(
        season=predictions["season"],
        prediction_date=predictions.get("prediction_date"),
        model_version=predictions.get("model_version"),
        model_mae_wins=predictions.get("model_mae_wins"),
        east=[TeamPredictionResponse(**p) for p in predictions["east"]],
        west=[TeamPredictionResponse(**p) for p in predictions["west"]],
    )


@app.get("/api/predictions/{team_id}", tags=["Predictions"])
def get_team_prediction(
    team_id: int,
    season: str = Query(default=None, description="Season (e.g., '2025-26')"),
):
    """Get predictions for a specific team."""
    prediction = prediction_service.get_team_prediction(team_id, season)

    if not prediction:
        raise HTTPException(
            status_code=404, detail=f"No prediction found for team {team_id}"
        )

    return prediction


@app.get(
    "/api/predictions/comparison",
    response_model=PredictionComparisonResponse,
    tags=["Predictions"],
)
def get_predictions_vs_actual(
    season: str = Query(default=None, description="Season (e.g., '2025-26')")
):
    """Compare predictions to current actual standings."""
    comparison = prediction_service.get_predictions_vs_actual(season)

    if not comparison:
        raise HTTPException(
            status_code=404,
            detail=f"No comparison data available for season {season or config.ingestion.current_season}",
        )

    return PredictionComparisonResponse(
        season=comparison["season"],
        prediction_date=comparison.get("prediction_date"),
        comparisons=[PredictionComparisonItem(**c) for c in comparison["comparisons"]],
    )


@app.get(
    "/api/predictions/model/info",
    response_model=ModelInfoResponse,
    tags=["Predictions"],
)
def get_model_info():
    """Get information about the active prediction model."""
    info = prediction_service.get_model_info()

    if not info:
        raise HTTPException(status_code=404, detail="No active model found")

    return ModelInfoResponse(**info)


@app.post("/api/predictions/refresh", tags=["Admin"])
async def refresh_predictions(background_tasks: BackgroundTasks):
    """Trigger fresh prediction generation."""
    background_tasks.add_task(
        prediction_service.generate_fresh_predictions, config.ingestion.current_season
    )
    return {"message": "Prediction refresh started"}


@app.post("/api/model/retrain", tags=["Admin"])
async def retrain_model(background_tasks: BackgroundTasks):
    """Trigger model retraining with latest data."""
    from ml.training_pipeline import training_pipeline
    from datetime import datetime

    version = f"lstm_v{datetime.now().strftime('%Y%m%d_%H%M')}"
    background_tasks.add_task(training_pipeline.train_and_save, version)
    return {"message": f"Model retraining started. Version: {version}"}


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    # Initialize database tables
    from models.database import init_database

    init_database()

    uvicorn.run(
        "api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug,
    )
