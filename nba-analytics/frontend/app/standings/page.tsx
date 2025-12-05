'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import {
  Box,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { api } from '@/lib/api';
import type { StandingsResponse } from '@/lib/types';

export default function StandingsPage() {
  const [standings, setStandings] = useState<StandingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStandings = async () => {
      try {
        setLoading(true);
        const data = await api.getStandings();
        setStandings(data);
        setError(null);
      } catch (err) {
        setError('Failed to load standings data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchStandings();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !standings) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error || 'No standings data available'}
      </Alert>
    );
  }

  // Prepare data for visualization
  const allStandings = [...standings.east, ...standings.west].sort(
    (a, b) => b.win_pct - a.win_pct
  );

  const chartData = allStandings.map((team) => ({
    team: team.team_abbr,
    winPct: parseFloat((team.win_pct * 100).toFixed(1)),
    conference: team.conference,
    teamId: team.team_id,
  }));

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Conference Standings
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Season: {standings.season || 'Current'} | Last updated: {standings.updated_at ? new Date(standings.updated_at).toLocaleString() : 'N/A'}
      </Typography>

      <Grid container spacing={3}>
        {/* Eastern Conference */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="h5" gutterBottom color="primary.main" fontWeight="600">
            Eastern Conference
          </Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Rank</TableCell>
                  <TableCell>Team</TableCell>
                  <TableCell align="center">W</TableCell>
                  <TableCell align="center">L</TableCell>
                  <TableCell align="center">PCT</TableCell>
                  <TableCell align="center">GB</TableCell>
                  <TableCell align="center">Streak</TableCell>
                  <TableCell align="center">L10</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {standings.east.map((team) => (
                  <TableRow key={team.team_id} hover>
                    <TableCell>{team.conf_rank}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Image
                          src={`https://cdn.nba.com/logos/nba/${team.nba_team_id}/global/L/logo.svg`}
                          alt={team.team_abbr}
                          width={24}
                          height={24}
                          style={{ objectFit: 'contain' }}
                        />
                        <strong>{team.team_abbr}</strong>
                      </Box>
                    </TableCell>
                    <TableCell align="center">{team.wins}</TableCell>
                    <TableCell align="center">{team.losses}</TableCell>
                    <TableCell align="center">{team.win_pct.toFixed(3)}</TableCell>
                    <TableCell align="center">{team.games_back}</TableCell>
                    <TableCell align="center">{team.streak}</TableCell>
                    <TableCell align="center">{team.last_10}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        {/* Western Conference */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="h5" gutterBottom color="error.main" fontWeight="600">
            Western Conference
          </Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Rank</TableCell>
                  <TableCell>Team</TableCell>
                  <TableCell align="center">W</TableCell>
                  <TableCell align="center">L</TableCell>
                  <TableCell align="center">PCT</TableCell>
                  <TableCell align="center">GB</TableCell>
                  <TableCell align="center">Streak</TableCell>
                  <TableCell align="center">L10</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {standings.west.map((team) => (
                  <TableRow key={team.team_id} hover>
                    <TableCell>{team.conf_rank}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Image
                          src={`https://cdn.nba.com/logos/nba/${team.nba_team_id}/global/L/logo.svg`}
                          alt={team.team_abbr}
                          width={24}
                          height={24}
                          style={{ objectFit: 'contain' }}
                        />
                        <strong>{team.team_abbr}</strong>
                      </Box>
                    </TableCell>
                    <TableCell align="center">{team.wins}</TableCell>
                    <TableCell align="center">{team.losses}</TableCell>
                    <TableCell align="center">{team.win_pct.toFixed(3)}</TableCell>
                    <TableCell align="center">{team.games_back}</TableCell>
                    <TableCell align="center">{team.streak}</TableCell>
                    <TableCell align="center">{team.last_10}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      </Grid>

      {/* Win Percentage Chart */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom fontWeight="600">
          Win Percentage by Team
        </Typography>
        <Paper sx={{ p: 2, mt: 2 }}>
          <ResponsiveContainer width="100%" height={600}>
            <BarChart
              data={chartData}
              layout="horizontal"
              margin={{ top: 5, right: 30, left: 20, bottom: 100 }}
            >
              <XAxis
                dataKey="team"
                angle={-45}
                textAnchor="end"
                height={100}
                stroke="#e0e0e0"
                style={{ fill: '#e0e0e0', fontSize: '12px' }}
              />
              <YAxis
                label={{
                  value: 'Win %',
                  angle: -90,
                  position: 'insideLeft',
                  style: { fill: '#e0e0e0' },
                }}
                stroke="#e0e0e0"
                style={{ fill: '#e0e0e0' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e1e1e',
                  border: '1px solid #444',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#fff' }}
                itemStyle={{ color: '#4fc3f7' }}
              />
              <Legend wrapperStyle={{ color: '#e0e0e0' }} />
              <Bar dataKey="winPct" name="Win %" label={{ position: 'top', fontSize: 10, fill: '#e0e0e0' }}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.conference === 'East' ? '#42a5f5' : '#ef5350'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Box>
    </Box>
  );
}
