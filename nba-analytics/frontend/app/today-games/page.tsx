'use client';

import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { api } from '@/lib/api';
import type { RecentGame } from '@/lib/types';

export default function TodayGamesPage() {
  const [games, setGames] = useState<RecentGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchGames = async () => {
    try {
      setLoading(true);
      const data = await api.getTodaysGames();
      setGames(data);
      setError(null);
    } catch (err) {
      setError('Failed to load games');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGames();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchGames();
      }, 30000); // Refresh every 30 seconds

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'live':
        return 'error';
      case 'final':
        return 'success';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'live':
        return '🔴';
      case 'final':
        return '✅';
      default:
        return '⏰';
    }
  };

  if (loading && games.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Today's Games
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </Typography>
        </Box>
        <FormControlLabel
          control={
            <Switch
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              color="primary"
            />
          }
          label="Auto-refresh (30s)"
        />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {games.length === 0 && !loading ? (
        <Alert severity="info">
          No games scheduled for today. Check back later or view recent games.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {games.map((game) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={game.game_id}>
              <Card
                sx={{
                  height: '100%',
                  borderLeft: game.status === 'live' ? '4px solid #f44336' : 'none',
                }}
              >
                <CardContent>
                  {/* Status Chip */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Chip
                      label={`${getStatusIcon(game.status)} ${game.status.toUpperCase()}`}
                      color={getStatusColor(game.status)}
                      size="small"
                    />
                    {game.status === 'live' && (
                      <Typography variant="caption" color="text.secondary">
                        Q{game.period} {game.clock}
                      </Typography>
                    )}
                  </Box>

                  {/* Away Team */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body1" fontWeight="600">
                      {game.away_team.abbr}
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {game.away_team.score}
                    </Typography>
                  </Box>

                  {/* Home Team */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body1" fontWeight="600">
                      {game.home_team.abbr}
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {game.home_team.score}
                    </Typography>
                  </Box>

                  {/* Game Date/Time for scheduled games */}
                  {game.status === 'scheduled' && game.game_date && (
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                      {new Date(game.game_date).toLocaleTimeString('en-US', {
                        hour: 'numeric',
                        minute: '2-digit',
                        timeZoneName: 'short',
                      })}
                    </Typography>
                  )}

                  {/* Full Team Names (smaller text) */}
                  <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {game.away_team.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                      @ {game.home_team.name}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
