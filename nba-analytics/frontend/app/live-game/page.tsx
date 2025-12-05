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
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  FormControlLabel,
  Switch,
  List,
  ListItem,
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';
import { api } from '@/lib/api';
import type { LiveGame, Shot, Play } from '@/lib/types';
import ShotChart3D from '@/components/ShotChart3D';

// Helper function to format game clock from PT format to MM:SS
const formatGameClock = (clock: string): string => {
  if (!clock || clock.trim() === '') return '0:00';

  // Parse PT12M34.56S format
  const match = clock.match(/PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?/);
  if (match) {
    const minutes = parseInt(match[1] || '0');
    const seconds = Math.floor(parseFloat(match[2] || '0'));
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }

  // If already in M:SS or MM:SS format, return as is
  if (clock.match(/^\d+:\d{2}$/)) return clock;

  return clock;
};

export default function LiveGamePage() {
  const [games, setGames] = useState<LiveGame[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<string>('');
  const [shots, setShots] = useState<Shot[]>([]);
  const [plays, setPlays] = useState<Play[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [awayFilter, setAwayFilter] = useState(true);
  const [homeFilter, setHomeFilter] = useState(true);
  const [selectedPlayer, setSelectedPlayer] = useState<string>('all');

  const fetchGames = async () => {
    try {
      const data = await api.getLiveGames();
      setGames(data);
      if (data.length > 0 && !selectedGameId) {
        setSelectedGameId(data[0].game_id);
      }
      setError(null);
    } catch (err) {
      setError('Failed to load games');
      console.error(err);
    }
  };

  const fetchGameData = async (gameId: string) => {
    try {
      const [shotsData, playsData] = await Promise.all([
        api.getGameShots(gameId),
        api.getGamePlays(gameId),
      ]);
      setShots(shotsData);
      setPlays(playsData);
    } catch (err) {
      console.error('Failed to load game data:', err);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await fetchGames();
      setLoading(false);
    };
    init();
  }, []);

  useEffect(() => {
    if (selectedGameId) {
      fetchGameData(selectedGameId);
    }
  }, [selectedGameId]);

  useEffect(() => {
    if (autoRefresh && selectedGameId) {
      const interval = setInterval(() => {
        fetchGameData(selectedGameId);
      }, 15000); // Refresh every 15 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedGameId]);

  if (loading && games.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (games.length === 0) {
    return (
      <Alert severity="info">
        No games currently in progress or scheduled for today. Check back later for live game updates!
      </Alert>
    );
  }

  const selectedGame = games.find((g) => g.game_id === selectedGameId);

  // Get unique players from shots
  const uniquePlayers = Array.from(
    new Set(shots.map(s => `${s.player_id}|${s.player_name}|${s.team_abbr}`))
  ).map(p => {
    const [id, name, team] = p.split('|');
    return { player_id: parseInt(id), player_name: name, team_abbr: team };
  }).sort((a, b) => a.player_name.localeCompare(b.player_name));

  const filteredShots = shots.filter((shot) => {
    if (!awayFilter && shot.team_abbr === selectedGame?.away_team_abbr) return false;
    if (!homeFilter && shot.team_abbr === selectedGame?.home_team_abbr) return false;
    if (selectedPlayer !== 'all' && shot.player_id.toString() !== selectedPlayer) return false;
    return true;
  });

  const madeShots = filteredShots.filter((s) => s.made);
  const missedShots = filteredShots.filter((s) => !s.made);

  // Calculate quarterly scores from plays data
  const getQuarterlyScores = () => {
    if (!selectedGame || plays.length === 0) return null;

    const periods = Array.from(new Set(plays.map(p => p.period))).sort((a, b) => a - b);
    const scores: { period: number; away: number; home: number }[] = [];

    periods.forEach(period => {
      const periodPlays = plays.filter(p => p.period === period);
      if (periodPlays.length > 0) {
        const lastPlay = periodPlays[periodPlays.length - 1];
        scores.push({
          period,
          away: lastPlay.away_score,
          home: lastPlay.home_score,
        });
      }
    });

    return scores;
  };

  const quarterlyScores = getQuarterlyScores();

  // Custom component to render basketball court overlay on heatmap
  const CourtOverlay = (props: any) => {
    const { xAxisMap, yAxisMap } = props;
    if (!xAxisMap || !yAxisMap) return null;

    const xAxis = xAxisMap[0];
    const yAxis = yAxisMap[0];
    if (!xAxis || !yAxis) return null;

    const xScale = xAxis.scale;
    const yScale = yAxis.scale;

    // Helper to convert court coordinates to SVG coordinates
    const toX = (x: number) => xScale(x);
    const toY = (y: number) => yScale(y);

    // Generate 3-point arc path
    const generate3PtArc = () => {
      const radius = 237.5;
      const startAngle = Math.acos(220 / radius);
      const endAngle = Math.PI - startAngle;
      const points = Array.from({ length: 50 }, (_, i) => {
        const angle = startAngle + (i / 49) * (endAngle - startAngle);
        return [radius * Math.cos(angle), radius * Math.sin(angle)];
      });
      return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${toX(p[0])} ${toY(p[1])}`).join(' ');
    };

    // Generate free throw circle path
    const generateFTCircle = () => {
      const cx = 0;
      const cy = 140;
      const r = 60;
      const points = Array.from({ length: 50 }, (_, i) => {
        const angle = (i / 49) * 2 * Math.PI;
        return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
      });
      return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${toX(p[0])} ${toY(p[1])}`).join(' ') + ' Z';
    };

    // Generate rim circle path
    const generateRim = () => {
      const cx = 0;
      const cy = 0;
      const r = 7.5;
      const points = Array.from({ length: 30 }, (_, i) => {
        const angle = (i / 29) * 2 * Math.PI;
        return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
      });
      return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${toX(p[0])} ${toY(p[1])}`).join(' ') + ' Z';
    };

    return (
      <g>
        {/* Court outline */}
        <rect
          x={toX(-250)}
          y={toY(420)}
          width={toX(250) - toX(-250)}
          height={toY(-50) - toY(420)}
          fill="none"
          stroke="#1a365d"
          strokeWidth={2}
        />

        {/* Paint area */}
        <rect
          x={toX(-80)}
          y={toY(140)}
          width={toX(80) - toX(-80)}
          height={toY(-50) - toY(140)}
          fill="none"
          stroke="#c53030"
          strokeWidth={2}
        />

        {/* Free throw circle */}
        <path d={generateFTCircle()} fill="none" stroke="#c53030" strokeWidth={2} />

        {/* 3-point arc */}
        <path d={generate3PtArc()} fill="none" stroke="#1a365d" strokeWidth={2} />

        {/* 3-point corner lines */}
        <line x1={toX(-220)} y1={toY(-50)} x2={toX(-220)} y2={toY(90)} stroke="#1a365d" strokeWidth={2} />
        <line x1={toX(220)} y1={toY(-50)} x2={toX(220)} y2={toY(90)} stroke="#1a365d" strokeWidth={2} />

        {/* Rim */}
        <path d={generateRim()} fill="none" stroke="#dd6b20" strokeWidth={3} />

        {/* Backboard */}
        <line x1={toX(-30)} y1={toY(-7.5)} x2={toX(30)} y2={toY(-7.5)} stroke="#fff" strokeWidth={3} />
      </g>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Live Game
      </Typography>

      {/* Game Selector and Auto-Refresh */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <FormControl fullWidth>
            <InputLabel>Select Game</InputLabel>
            <Select
              value={selectedGameId}
              onChange={(e) => setSelectedGameId(e.target.value)}
              label="Select Game"
            >
              {games.map((game) => (
                <MenuItem key={game.game_id} value={game.game_id}>
                  {game.away_team_abbr} @ {game.home_team_abbr} - {game.status}
                  {game.is_live && ` (Q${game.period} ${formatGameClock(game.game_clock)})`}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={4}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                color="primary"
              />
            }
            label="Auto-refresh (15s)"
          />
        </Grid>
      </Grid>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {selectedGame && (
        <>
          {/* Game Header */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={4} textAlign="center">
                  <Typography variant="h6" fontWeight="bold">
                    {selectedGame.away_team_name}
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" color="primary">
                    {selectedGame.away_score}
                  </Typography>
                </Grid>
                <Grid item xs={4} textAlign="center">
                  <Typography variant="h5" fontWeight="bold">
                    VS
                  </Typography>
                  {selectedGame.is_live ? (
                    <Box>
                      <Chip label="LIVE" color="error" size="small" sx={{ mt: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        Q{selectedGame.period} {formatGameClock(selectedGame.game_clock)}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      {selectedGame.status}
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={4} textAlign="center">
                  <Typography variant="h6" fontWeight="bold">
                    {selectedGame.home_team_name}
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" color="primary">
                    {selectedGame.home_score}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Quarterly Scores Table */}
          {quarterlyScores && quarterlyScores.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="600">
                  Score by Quarter
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Team</TableCell>
                        {quarterlyScores.map((score) => (
                          <TableCell key={score.period} align="center">
                            Q{score.period}
                          </TableCell>
                        ))}
                        <TableCell align="center"><strong>Total</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>
                          <strong>{selectedGame.away_team_abbr}</strong>
                        </TableCell>
                        {quarterlyScores.map((score, index) => {
                          const prevScore = index > 0 ? quarterlyScores[index - 1].away : 0;
                          const quarterPoints = score.away - prevScore;
                          return (
                            <TableCell key={score.period} align="center">
                              {quarterPoints}
                            </TableCell>
                          );
                        })}
                        <TableCell align="center">
                          <strong>{selectedGame.away_score}</strong>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>
                          <strong>{selectedGame.home_team_abbr}</strong>
                        </TableCell>
                        {quarterlyScores.map((score, index) => {
                          const prevScore = index > 0 ? quarterlyScores[index - 1].home : 0;
                          const quarterPoints = score.home - prevScore;
                          return (
                            <TableCell key={score.period} align="center">
                              {quarterPoints}
                            </TableCell>
                          );
                        })}
                        <TableCell align="center">
                          <strong>{selectedGame.home_score}</strong>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
              <Tab label="Shot Chart" />
              <Tab label="Play-by-Play" />
              <Tab label="Shot Heatmap" />
            </Tabs>
          </Box>

          {/* Tab 1: Shot Chart */}
          {activeTab === 0 && (
            <Box>
              {/* Filters */}
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>Filter by Player</InputLabel>
                    <Select
                      value={selectedPlayer}
                      onChange={(e) => setSelectedPlayer(e.target.value)}
                      label="Filter by Player"
                      renderValue={(value) => {
                        if (value === 'all') return 'All Players';
                        const player = uniquePlayers.find(p => p.player_id.toString() === value);
                        return player ? player.player_name : '';
                      }}
                    >
                      <MenuItem value="all">All Players</MenuItem>
                      {uniquePlayers.map((player) => (
                        <MenuItem key={player.player_id} value={player.player_id.toString()}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Image
                              src={`https://cdn.nba.com/headshots/nba/latest/260x190/${player.player_id}.png`}
                              alt={player.player_name}
                              width={30}
                              height={30}
                              style={{ borderRadius: '50%', objectFit: 'cover' }}
                              onError={(e) => {
                                e.currentTarget.src = '/placeholder-player.png';
                              }}
                            />
                            {player.player_name} ({player.team_abbr})
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6} md={4}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={awayFilter}
                        onChange={(e) => setAwayFilter(e.target.checked)}
                        color="primary"
                      />
                    }
                    label={`${selectedGame.away_team_abbr} (Away)`}
                  />
                </Grid>
                <Grid item xs={6} md={4}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={homeFilter}
                        onChange={(e) => setHomeFilter(e.target.checked)}
                        color="primary"
                      />
                    }
                    label={`${selectedGame.home_team_abbr} (Home)`}
                  />
                </Grid>
              </Grid>

              {/* Selected Player Headshot */}
              {selectedPlayer !== 'all' && (() => {
                const player = uniquePlayers.find(p => p.player_id.toString() === selectedPlayer);
                return player ? (
                  <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
                    <Paper sx={{ p: 3, display: 'inline-block' }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Image
                          src={`https://cdn.nba.com/headshots/nba/latest/260x190/${player.player_id}.png`}
                          alt={player.player_name}
                          width={200}
                          height={150}
                          style={{ borderRadius: '8px', objectFit: 'cover' }}
                          onError={(e) => {
                            e.currentTarget.src = '/placeholder-player.png';
                          }}
                        />
                        <Typography variant="h6" sx={{ mt: 2 }} fontWeight="bold">
                          {player.player_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {player.team_abbr}
                        </Typography>
                      </Box>
                    </Paper>
                  </Box>
                ) : null;
              })()}

              {/* 3D Shot Chart */}
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  3D Shot Chart
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                  Green circles with arcs = Made shots | Red X = Missed shots | {madeShots.length} made, {missedShots.length} missed
                </Typography>
                <ShotChart3D shots={filteredShots} />
                <Typography variant="caption" color="text.secondary" display="block" textAlign="center" sx={{ mt: 1 }}>
                  Interactive 3D view - Drag to rotate, scroll to zoom
                </Typography>
              </Paper>
            </Box>
          )}

          {/* Tab 2: Play-by-Play */}
          {activeTab === 1 && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Play-by-Play
              </Typography>
              {plays.length === 0 ? (
                <Alert severity="info">No play-by-play data available yet.</Alert>
              ) : (
                <List sx={{ maxHeight: 600, overflow: 'auto' }}>
                  {[...plays].reverse().map((play, index) => {
                    const eventIcons: Record<string, string> = {
                      SHOT_MADE: '🏀',
                      SHOT_MISSED: '❌',
                      FREE_THROW: '🎱',
                      REBOUND: '🔄',
                      TURNOVER: '💨',
                      FOUL: '📍',
                      TIMEOUT: '⏸️',
                      SUBSTITUTION: '🔀',
                    };
                    const icon = eventIcons[play.event_type] || '📋';
                    const isScore = play.event_type === 'SHOT_MADE' || play.event_type === 'FREE_THROW';

                    return (
                      <ListItem
                        key={index}
                        sx={{
                          borderLeft: `4px solid ${isScore ? '#4caf50' : '#666'}`,
                          mb: 1,
                          bgcolor: 'background.paper',
                          borderRadius: 1,
                        }}
                      >
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center" gap={1}>
                              <span>{icon}</span>
                              <Typography variant="body2" fontWeight="bold">
                                Q{play.period} {play.clock}
                              </Typography>
                              <Chip label={play.team_abbr} size="small" />
                              <Typography variant="body2">{play.description}</Typography>
                            </Box>
                          }
                          secondary={
                            <Typography variant="caption" color="text.secondary">
                              {play.away_score} - {play.home_score}
                            </Typography>
                          }
                        />
                      </ListItem>
                    );
                  })}
                </List>
              )}
            </Paper>
          )}

          {/* Tab 3: Shot Heatmap */}
          {activeTab === 2 && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Shot Heatmap
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Heatmap visualization showing shot frequency by location
              </Typography>
              <ResponsiveContainer width="100%" height={600}>
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <defs>
                    <rect id="courtBg" x={0} y={0} width="100%" height="100%" fill="#e8dcc4" />
                  </defs>
                  <XAxis type="number" dataKey="x" domain={[-250, 250]} hide />
                  <YAxis type="number" dataKey="y" domain={[-50, 420]} hide />
                  <ZAxis type="number" range={[100, 400]} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const shot = payload[0].payload as Shot;
                        return (
                          <Paper sx={{ p: 1 }}>
                            <Typography variant="body2" fontWeight="bold">
                              {shot.player_name}
                            </Typography>
                            <Typography variant="caption" display="block">
                              {shot.made ? 'MADE' : 'MISSED'} - {shot.shot_type}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {shot.distance}ft
                            </Typography>
                          </Paper>
                        );
                      }
                      return null;
                    }}
                  />
                  <CourtOverlay />
                  <Scatter
                    data={filteredShots}
                    fill="#ff9800"
                    fillOpacity={0.6}
                    shape={(props: any) => {
                      const { cx, cy, fill, payload } = props;
                      return (
                        <circle
                          cx={cx}
                          cy={cy}
                          r={6}
                          fill={payload.made ? '#38a169' : '#e53e3e'}
                          fillOpacity={0.7}
                          stroke={payload.made ? '#276749' : '#c53030'}
                          strokeWidth={1.5}
                        />
                      );
                    }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </Paper>
          )}
        </>
      )}
    </Box>
  );
}
