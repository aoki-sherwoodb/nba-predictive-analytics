"""
Database models for NBA Analytics Platform.
Uses SQLAlchemy ORM for PostgreSQL.
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean, 
    ForeignKey, Text, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Team(Base):
    """NBA Team information."""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    nba_id = Column(Integer, unique=True, nullable=False, index=True)
    abbreviation = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    city = Column(String(100))
    conference = Column(String(10))  # 'East' or 'West'
    division = Column(String(50))
    logo_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")
    standings = relationship("TeamStanding", back_populates="team")
    
    def __repr__(self):
        return f"<Team {self.abbreviation}: {self.name}>"


class Player(Base):
    """NBA Player information."""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True)
    nba_id = Column(Integer, unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    jersey_number = Column(String(10))
    position = Column(String(20))
    height = Column(String(10))  # e.g., "6-8"
    weight = Column(Integer)  # in pounds
    birth_date = Column(Date)
    country = Column(String(100))
    years_pro = Column(String(10))  # Can be "R" for rookie or number
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="players")
    game_stats = relationship("PlayerGameStats", back_populates="player")
    
    def __repr__(self):
        return f"<Player {self.full_name}>"


class Game(Base):
    """NBA Game information."""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True)
    nba_game_id = Column(String(20), unique=True, nullable=False, index=True)
    season = Column(String(10), nullable=False, index=True)  # e.g., "2024-25"
    season_type = Column(String(20))  # "Regular Season", "Playoffs", "Pre Season"
    game_date = Column(Date, nullable=False, index=True)
    game_time = Column(DateTime)
    
    # Teams
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    
    # Scores
    home_score = Column(Integer)
    away_score = Column(Integer)
    
    # Quarter scores (stored as JSON for flexibility)
    home_quarter_scores = Column(JSON)  # e.g., [28, 32, 25, 30]
    away_quarter_scores = Column(JSON)
    
    # Game status
    status = Column(String(20), default="scheduled")  # scheduled, live, final
    period = Column(Integer)  # Current period if live
    game_clock = Column(String(10))  # Current clock if live
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    player_stats = relationship("PlayerGameStats", back_populates="game")
    
    __table_args__ = (
        Index("ix_games_date_status", "game_date", "status"),
    )
    
    def __repr__(self):
        return f"<Game {self.away_team_id}@{self.home_team_id} on {self.game_date}>"


class PlayerGameStats(Base):
    """Player statistics for a single game."""
    __tablename__ = "player_game_stats"
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Playing time
    minutes_played = Column(Float)
    
    # Scoring
    points = Column(Integer, default=0)
    field_goals_made = Column(Integer, default=0)
    field_goals_attempted = Column(Integer, default=0)
    three_pointers_made = Column(Integer, default=0)
    three_pointers_attempted = Column(Integer, default=0)
    free_throws_made = Column(Integer, default=0)
    free_throws_attempted = Column(Integer, default=0)
    
    # Rebounds
    offensive_rebounds = Column(Integer, default=0)
    defensive_rebounds = Column(Integer, default=0)
    total_rebounds = Column(Integer, default=0)
    
    # Other stats
    assists = Column(Integer, default=0)
    steals = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    turnovers = Column(Integer, default=0)
    personal_fouls = Column(Integer, default=0)
    plus_minus = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    player = relationship("Player", back_populates="game_stats")
    game = relationship("Game", back_populates="player_stats")
    
    __table_args__ = (
        UniqueConstraint("player_id", "game_id", name="uq_player_game"),
        Index("ix_player_game_stats_points", "points"),
    )
    
    @property
    def field_goal_percentage(self) -> Optional[float]:
        if self.field_goals_attempted and self.field_goals_attempted > 0:
            return round(self.field_goals_made / self.field_goals_attempted * 100, 1)
        return None
    
    @property
    def three_point_percentage(self) -> Optional[float]:
        if self.three_pointers_attempted and self.three_pointers_attempted > 0:
            return round(self.three_pointers_made / self.three_pointers_attempted * 100, 1)
        return None


class TeamStanding(Base):
    """Team standings for a season."""
    __tablename__ = "team_standings"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    season = Column(String(10), nullable=False, index=True)
    
    # Record
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_percentage = Column(Float, default=0.0)
    
    # Conference/Division standings
    conference_rank = Column(Integer)
    division_rank = Column(Integer)
    games_back = Column(Float, default=0.0)
    
    # Streaks
    current_streak = Column(String(10))  # e.g., "W3", "L2"
    last_10 = Column(String(10))  # e.g., "7-3"
    
    # Home/Away splits
    home_wins = Column(Integer, default=0)
    home_losses = Column(Integer, default=0)
    away_wins = Column(Integer, default=0)
    away_losses = Column(Integer, default=0)
    
    # Timestamps
    recorded_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="standings")
    
    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uq_team_season_standing"),
    )


class IngestionLog(Base):
    """Log of data ingestion runs for monitoring."""
    __tablename__ = "ingestion_logs"
    
    id = Column(Integer, primary_key=True)
    ingestion_type = Column(String(50), nullable=False)  # teams, players, games, standings
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    status = Column(String(20), default="running")  # running, success, failed
    records_processed = Column(Integer, default=0)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<IngestionLog {self.ingestion_type} at {self.started_at}: {self.status}>"
