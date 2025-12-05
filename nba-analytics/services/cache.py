"""
Redis cache management for NBA Analytics Platform.
Provides caching for frequently accessed data.
"""
import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

import redis
from redis.exceptions import ConnectionError, TimeoutError

from config import config

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis cache operations."""
    
    # Cache key prefixes for organization
    PREFIX_STANDINGS = "standings"
    PREFIX_TEAM = "team"
    PREFIX_PLAYER = "player"
    PREFIX_GAME = "game"
    PREFIX_LIVE = "live"
    PREFIX_STATS = "stats"
    PREFIX_PREDICTIONS = "predictions"
    PREFIX_MODEL = "model"

    # Default TTL values (in seconds)
    TTL_STANDINGS = 300  # 5 minutes
    TTL_TEAM = 3600  # 1 hour
    TTL_PLAYER = 3600  # 1 hour
    TTL_GAME_FINAL = 86400  # 24 hours for completed games
    TTL_GAME_LIVE = 30  # 30 seconds for live games
    TTL_STATS = 600  # 10 minutes
    TTL_PREDICTIONS = 3600  # 1 hour for predictions
    TTL_MODEL = 86400  # 24 hours for model metadata
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    @property
    def client(self) -> redis.Redis:
        """Lazy initialization of Redis client."""
        if self._client is None:
            self._client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                password=config.redis.password,
                db=config.redis.db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
        return self._client
    
    def _make_key(self, prefix: str, *args) -> str:
        """Create a cache key with prefix and arguments."""
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        Returns None if key doesn't exist or on error.
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache get failed for {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Cache JSON decode error for {key}: {e}")
            return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Union[int, timedelta] = 300
    ) -> bool:
        """
        Set a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds or timedelta
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache set failed for {key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Cache serialization error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            self.client.delete(key)
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache delete failed for {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache delete pattern failed for {pattern}: {e}")
            return 0
    
    # High-level caching methods for NBA data
    
    def get_standings(self, season: str) -> Optional[dict]:
        """Get cached standings for a season."""
        key = self._make_key(self.PREFIX_STANDINGS, season)
        return self.get(key)
    
    def set_standings(self, season: str, standings: dict) -> bool:
        """Cache standings for a season."""
        key = self._make_key(self.PREFIX_STANDINGS, season)
        return self.set(key, standings, self.TTL_STANDINGS)
    
    def get_team(self, team_id: int) -> Optional[dict]:
        """Get cached team info."""
        key = self._make_key(self.PREFIX_TEAM, team_id)
        return self.get(key)
    
    def set_team(self, team_id: int, team_data: dict) -> bool:
        """Cache team info."""
        key = self._make_key(self.PREFIX_TEAM, team_id)
        return self.set(key, team_data, self.TTL_TEAM)
    
    def get_player(self, player_id: int) -> Optional[dict]:
        """Get cached player info."""
        key = self._make_key(self.PREFIX_PLAYER, player_id)
        return self.get(key)
    
    def set_player(self, player_id: int, player_data: dict) -> bool:
        """Cache player info."""
        key = self._make_key(self.PREFIX_PLAYER, player_id)
        return self.set(key, player_data, self.TTL_PLAYER)
    
    def get_live_game(self, game_id: str) -> Optional[dict]:
        """Get cached live game data."""
        key = self._make_key(self.PREFIX_LIVE, game_id)
        return self.get(key)
    
    def set_live_game(self, game_id: str, game_data: dict) -> bool:
        """Cache live game data with short TTL."""
        key = self._make_key(self.PREFIX_LIVE, game_id)
        return self.set(key, game_data, self.TTL_GAME_LIVE)
    
    def get_todays_games(self) -> Optional[list]:
        """Get cached today's games list."""
        key = self._make_key(self.PREFIX_GAME, "today")
        return self.get(key)
    
    def set_todays_games(self, games: list) -> bool:
        """Cache today's games list."""
        key = self._make_key(self.PREFIX_GAME, "today")
        return self.set(key, games, self.TTL_STANDINGS)
    
    def get_player_stats(self, player_id: int, season: str) -> Optional[dict]:
        """Get cached player season stats."""
        key = self._make_key(self.PREFIX_STATS, "player", player_id, season)
        return self.get(key)
    
    def set_player_stats(self, player_id: int, season: str, stats: dict) -> bool:
        """Cache player season stats."""
        key = self._make_key(self.PREFIX_STATS, "player", player_id, season)
        return self.set(key, stats, self.TTL_STATS)

    # Prediction caching methods

    def get_predictions(self, season: str) -> Optional[dict]:
        """Get cached predictions for all teams in a season."""
        key = self._make_key(self.PREFIX_PREDICTIONS, "all", season)
        return self.get(key)

    def set_predictions(self, season: str, predictions: dict) -> bool:
        """Cache predictions for all teams in a season."""
        key = self._make_key(self.PREFIX_PREDICTIONS, "all", season)
        return self.set(key, predictions, self.TTL_PREDICTIONS)

    def get_team_prediction(self, season: str, team_id: int) -> Optional[dict]:
        """Get cached prediction for a single team."""
        key = self._make_key(self.PREFIX_PREDICTIONS, season, team_id)
        return self.get(key)

    def set_team_prediction(self, season: str, team_id: int, prediction: dict) -> bool:
        """Cache prediction for a single team."""
        key = self._make_key(self.PREFIX_PREDICTIONS, season, team_id)
        return self.set(key, prediction, self.TTL_PREDICTIONS)

    def invalidate_predictions(self, season: str) -> int:
        """Invalidate all prediction caches for a season."""
        pattern = f"{self.PREFIX_PREDICTIONS}:*{season}*"
        return self.delete_pattern(pattern)

    def get_model_info(self) -> Optional[dict]:
        """Get cached model metadata."""
        key = self._make_key(self.PREFIX_MODEL, "active")
        return self.get(key)

    def set_model_info(self, info: dict) -> bool:
        """Cache model metadata."""
        key = self._make_key(self.PREFIX_MODEL, "active")
        return self.set(key, info, self.TTL_MODEL)

    def check_connection(self) -> bool:
        """Check if Redis connection is working."""
        try:
            self.client.ping()
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection check failed: {e}")
            return False
    
    def close(self):
        """Close Redis connection."""
        if self._client:
            self._client.close()
            logger.info("Redis connection closed")


# Global cache manager instance
cache_manager = CacheManager()


if __name__ == "__main__":
    # Quick test of Redis connection
    logging.basicConfig(level=logging.INFO)
    
    print(f"Testing connection to Redis at {config.redis.host}:{config.redis.port}")
    
    if cache_manager.check_connection():
        print("✓ Redis connection successful!")
        
        # Test set/get
        cache_manager.set("test:key", {"message": "Hello, NBA Analytics!"}, ttl=60)
        result = cache_manager.get("test:key")
        print(f"✓ Test value: {result}")
        
        cache_manager.delete("test:key")
        print("✓ Test key cleaned up")
    else:
        print("✗ Redis connection failed!")
