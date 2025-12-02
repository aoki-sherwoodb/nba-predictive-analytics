"""
Basic tests for NBA Analytics Platform.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check_returns_status(self):
        """Test that health check returns expected fields."""
        # Mock the database and cache managers
        with patch('api.main.db_manager') as mock_db, \
             patch('api.main.cache_manager') as mock_cache:
            
            mock_db.check_connection.return_value = True
            mock_cache.check_connection.return_value = True
            
            from api.main import app
            client = TestClient(app)
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "database" in data
            assert "cache" in data
            assert "timestamp" in data


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_welcome(self):
        """Test root endpoint returns API info."""
        from api.main import app
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestTeamsEndpoint:
    """Tests for teams endpoints."""
    
    def test_get_teams_empty_db(self):
        """Test teams endpoint with empty database."""
        with patch('api.main.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.order_by.return_value.all.return_value = []
            mock_db.session_factory.return_value = mock_session
            
            from api.main import app
            client = TestClient(app)
            
            response = client.get("/api/teams")
            assert response.status_code == 200
            assert response.json() == []


class TestStandingsEndpoint:
    """Tests for standings endpoints."""
    
    def test_get_standings_from_cache(self):
        """Test standings endpoint uses cache."""
        with patch('api.main.cache_manager') as mock_cache, \
             patch('api.main.db_manager') as mock_db:
            
            # Mock cache hit
            mock_cache.get_standings.return_value = {
                'season': '2024-25',
                'updated_at': '2024-01-01T00:00:00',
                'standings': [
                    {
                        'team_id': 1,
                        'team_name': 'Celtics',
                        'team_abbr': 'BOS',
                        'conference': 'East',
                        'wins': 30,
                        'losses': 10,
                        'win_pct': 0.750,
                        'conf_rank': 1,
                        'games_back': 0.0,
                        'streak': 'W5',
                        'last_10': '8-2'
                    }
                ]
            }
            
            from api.main import app
            client = TestClient(app)
            
            response = client.get("/api/standings")
            assert response.status_code == 200
            
            data = response.json()
            assert data['season'] == '2024-25'
            assert len(data['east']) == 1
            assert data['east'][0]['team_abbr'] == 'BOS'


class TestDatabaseModels:
    """Tests for database models."""
    
    def test_team_model_repr(self):
        """Test Team model string representation."""
        from models.database_models import Team
        
        team = Team(abbreviation='BOS', name='Celtics')
        assert 'BOS' in repr(team)
        assert 'Celtics' in repr(team)
    
    def test_player_model_repr(self):
        """Test Player model string representation."""
        from models.database_models import Player
        
        player = Player(full_name='Test Player')
        assert 'Test Player' in repr(player)
    
    def test_player_game_stats_percentages(self):
        """Test PlayerGameStats percentage calculations."""
        from models.database_models import PlayerGameStats
        
        stats = PlayerGameStats(
            field_goals_made=5,
            field_goals_attempted=10,
            three_pointers_made=2,
            three_pointers_attempted=5
        )
        
        assert stats.field_goal_percentage == 50.0
        assert stats.three_point_percentage == 40.0
    
    def test_player_game_stats_zero_attempts(self):
        """Test percentage calculations with zero attempts."""
        from models.database_models import PlayerGameStats
        
        stats = PlayerGameStats(
            field_goals_made=0,
            field_goals_attempted=0,
            three_pointers_made=0,
            three_pointers_attempted=0
        )
        
        assert stats.field_goal_percentage is None
        assert stats.three_point_percentage is None


class TestCacheManager:
    """Tests for cache manager."""
    
    def test_make_key(self):
        """Test cache key generation."""
        from services.cache import CacheManager
        
        manager = CacheManager()
        key = manager._make_key("prefix", "arg1", 123)
        
        assert key == "prefix:arg1:123"
    
    def test_cache_get_with_connection_error(self):
        """Test cache get handles connection errors gracefully."""
        from services.cache import CacheManager
        from redis.exceptions import ConnectionError
        
        manager = CacheManager()
        
        with patch.object(manager, 'client') as mock_client:
            mock_client.get.side_effect = ConnectionError("Connection refused")
            
            result = manager.get("test:key")
            assert result is None  # Should return None, not raise


class TestConfig:
    """Tests for configuration."""
    
    def test_database_config_connection_string(self):
        """Test database connection string generation."""
        from config import DatabaseConfig
        
        config = DatabaseConfig(
            host='localhost',
            port=5432,
            database='test_db',
            user='test_user',
            password='test_pass'
        )
        
        assert 'localhost' in config.connection_string
        assert 'test_db' in config.connection_string
        assert 'test_user' in config.connection_string
    
    def test_redis_config_url(self):
        """Test Redis URL generation."""
        from config import RedisConfig
        
        # Without password
        config = RedisConfig(host='localhost', port=6379, password=None, db=0)
        assert config.url == "redis://localhost:6379/0"
        
        # With password
        config_with_pass = RedisConfig(host='localhost', port=6379, password='secret', db=0)
        assert ':secret@' in config_with_pass.url


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
