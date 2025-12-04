'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { api } from '@/lib/api';
import type { Team, Game } from '@/lib/types';

interface GameData {
  date: string;
  opponent: string;
  result: 'W' | 'L';
  score: string;
  margin: number;
  isHome: boolean;
}

export default function TeamAnalysisPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [gamesLoading, setGamesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch teams on mount
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const data = await api.getTeams();
        setTeams(data);
        if (data.length > 0) {
          setSelectedTeamId(data[0].id);
        }
        setError(null);
      } catch (err) {
        setError('Failed to load teams');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  // Fetch ALL games when team changes
  useEffect(() => {
    if (selectedTeamId === null) return;

    const fetchGames = async () => {
      try {
        setGamesLoading(true);
        // Fetch all games for the season (set days very high to get all games)
        const data = await api.getRecentGames(365, selectedTeamId);
        // Filter to only include games involving this team
        const teamGames = data.filter(
          (game) =>
            game.home_team.id === selectedTeamId || game.away_team.id === selectedTeamId
        );
        setGames(teamGames);
        setError(null);
      } catch (err) {
        setError('Failed to load team games');
        console.error(err);
      } finally {
        setGamesLoading(false);
      }
    };

    fetchGames();
  }, [selectedTeamId]);

  const processGameData = (): GameData[] => {
    if (!selectedTeamId) return [];

    return games
      .filter((game) => game.status === 'final') // Only show completed games
      .map((game) => {
        const isHome = game.home_team.id === selectedTeamId;
        const teamScore = isHome ? game.home_team.score : game.away_team.score;
        const oppScore = isHome ? game.away_team.score : game.home_team.score;
        const opponent = isHome ? game.away_team.abbr : game.home_team.abbr;
        const result: 'W' | 'L' = teamScore > oppScore ? 'W' : 'L';

        return {
          date: game.game_date,
          opponent: `${isHome ? 'vs' : '@'} ${opponent}`,
          result,
          score: `${teamScore}-${oppScore}`,
          margin: teamScore - oppScore,
          isHome,
        };
      });
  };

  const gameData = processGameData();
  const wins = gameData.filter((g) => g.result === 'W').length;
  const losses = gameData.filter((g) => g.result === 'L').length;
  const avgMargin =
    gameData.length > 0
      ? gameData.reduce((sum, g) => sum + g.margin, 0) / gameData.length
      : 0;

  // Chart data with game numbers
  const chartData = gameData.map((game, index) => ({
    game: index + 1,
    margin: game.margin,
    opponent: game.opponent,
    result: game.result,
  }));

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const selectedTeam = teams.find((t) => t.id === selectedTeamId);

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Team Analysis
      </Typography>

      <FormControl fullWidth sx={{ mb: 3, maxWidth: 400 }}>
        <InputLabel>Select Team</InputLabel>
        <Select
          value={selectedTeamId || ''}
          onChange={(e) => setSelectedTeamId(e.target.value as number)}
          label="Select Team"
          renderValue={(value) => {
            const team = teams.find((t) => t.id === value);
            return team ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Image
                  src={`https://cdn.nba.com/logos/nba/${team.nba_id}/global/L/logo.svg`}
                  alt={team.abbreviation}
                  width={24}
                  height={24}
                  style={{ objectFit: 'contain' }}
                />
                {team.abbreviation} - {team.name}
              </Box>
            ) : null;
          }}
        >
          {teams.map((team) => (
            <MenuItem key={team.id} value={team.id}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Image
                  src={`https://cdn.nba.com/logos/nba/${team.nba_id}/global/L/logo.svg`}
                  alt={team.abbreviation}
                  width={24}
                  height={24}
                  style={{ objectFit: 'contain' }}
                />
                {team.abbreviation} - {team.name}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {gamesLoading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
          <CircularProgress />
        </Box>
      ) : gameData.length === 0 ? (
        <Alert severity="info">No completed games found for this team in the current season.</Alert>
      ) : (
        <>
          {/* Stats Cards */}
          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Record
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {wins}-{losses}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Win %
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {wins + losses > 0
                      ? ((wins / (wins + losses)) * 100).toFixed(1)
                      : '0.0'}
                    %
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Avg Margin
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight="bold"
                    color={avgMargin >= 0 ? 'success.main' : 'error.main'}
                  >
                    {avgMargin > 0 ? '+' : ''}
                    {avgMargin.toFixed(1)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Games Played
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {gameData.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Point Differential Trend Chart */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom fontWeight="600">
              Point Differential Trend (All Season Games)
            </Typography>
            <Paper sx={{ p: 2 }}>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis
                    dataKey="game"
                    label={{ value: 'Game Number', position: 'insideBottom', offset: -5, fill: '#e0e0e0' }}
                    stroke="#e0e0e0"
                    style={{ fill: '#e0e0e0' }}
                  />
                  <YAxis
                    label={{ value: 'Point Margin', angle: -90, position: 'insideLeft', fill: '#e0e0e0' }}
                    stroke="#e0e0e0"
                    style={{ fill: '#e0e0e0' }}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <Paper sx={{ p: 1.5 }}>
                            <Typography variant="body2">
                              Game {data.game}: {data.opponent}
                            </Typography>
                            <Typography
                              variant="body2"
                              color={data.margin >= 0 ? 'success.main' : 'error.main'}
                              fontWeight="bold"
                            >
                              {data.result} by {Math.abs(data.margin)}
                            </Typography>
                          </Paper>
                        );
                      }
                      return null;
                    }}
                  />
                  <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
                  <Line
                    type="monotone"
                    dataKey="margin"
                    stroke="#42a5f5"
                    strokeWidth={2}
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      return (
                        <circle
                          cx={cx}
                          cy={cy}
                          r={5}
                          fill={payload.margin >= 0 ? '#4caf50' : '#f44336'}
                          stroke="#fff"
                          strokeWidth={2}
                        />
                      );
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Box>

          {/* Recent Games Table */}
          <Box>
            <Typography variant="h5" gutterBottom fontWeight="600">
              All Season Games ({gameData.length} games)
            </Typography>
            <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Opponent</TableCell>
                    <TableCell align="center">Result</TableCell>
                    <TableCell align="center">Score</TableCell>
                    <TableCell align="center">Margin</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {gameData.map((game, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        {new Date(game.date).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </TableCell>
                      <TableCell>{game.opponent}</TableCell>
                      <TableCell align="center">
                        <Typography
                          fontWeight="bold"
                          color={game.result === 'W' ? 'success.main' : 'error.main'}
                        >
                          {game.result}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">{game.score}</TableCell>
                      <TableCell
                        align="center"
                        sx={{
                          color: game.margin >= 0 ? 'success.main' : 'error.main',
                          fontWeight: 'bold',
                        }}
                      >
                        {game.margin > 0 ? '+' : ''}
                        {game.margin}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </>
      )}
    </Box>
  );
}
