'use client';

import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
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
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '@/lib/api';
import type { PlayerStats } from '@/lib/types';

const statCategories = [
  { value: 'points', label: 'Points' },
  { value: 'rebounds', label: 'Rebounds' },
  { value: 'assists', label: 'Assists' },
  { value: 'steals', label: 'Steals' },
  { value: 'blocks', label: 'Blocks' },
];

const columnsByCategory: Record<string, string[]> = {
  points: ['Player', 'Team', 'MPG', 'PPG', 'FG%', '3P%', 'FT%'],
  rebounds: ['Player', 'Team', 'MPG', 'RPG', 'PPG'],
  assists: ['Player', 'Team', 'MPG', 'APG', 'PPG', 'TOV'],
  steals: ['Player', 'Team', 'MPG', 'SPG', 'PPG'],
  blocks: ['Player', 'Team', 'MPG', 'BPG', 'PPG'],
};

export default function LeadersPage() {
  const [leaders, setLeaders] = useState<PlayerStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState('points');
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    const fetchLeaders = async () => {
      try {
        setLoading(true);
        const data = await api.getLeaders(category, limit);
        setLeaders(data);
        setError(null);
      } catch (err) {
        setError('Failed to load leaders');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchLeaders();
  }, [category, limit]);

  const getStatValue = (player: PlayerStats, stat: string): string | number => {
    switch (stat) {
      case 'Player':
        return player.player_name;
      case 'Team':
        return player.team_abbr;
      case 'MPG':
        return player.minutes.toFixed(1);
      case 'PPG':
        return player.points.toFixed(1);
      case 'RPG':
        return player.rebounds.toFixed(1);
      case 'APG':
        return player.assists.toFixed(1);
      case 'SPG':
        return player.steals.toFixed(1);
      case 'BPG':
        return player.blocks.toFixed(1);
      case 'TOV':
        return player.turnovers.toFixed(1);
      case 'FG%':
        return player.fg_pct !== null ? player.fg_pct.toFixed(1) + '%' : 'N/A';
      case '3P%':
        return player.three_pct !== null ? player.three_pct.toFixed(1) + '%' : 'N/A';
      case 'FT%':
        return player.ft_pct !== null ? player.ft_pct.toFixed(1) + '%' : 'N/A';
      case '+/-':
        return player.plus_minus > 0 ? `+${player.plus_minus.toFixed(1)}` : player.plus_minus.toFixed(1);
      default:
        return '';
    }
  };

  const getChartData = () => {
    const statMap: Record<string, 'points' | 'rebounds' | 'assists' | 'steals' | 'blocks'> = {
      points: 'points',
      rebounds: 'rebounds',
      assists: 'assists',
      steals: 'steals',
      blocks: 'blocks',
    };

    const statKey = statMap[category];
    return leaders.map((player) => ({
      name: player.player_name,
      value: parseFloat(player[statKey].toFixed(1)),
      team: player.team_abbr,
    }));
  };

  if (loading && leaders.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const columns = columnsByCategory[category] || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Statistical Leaders
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <FormControl fullWidth>
            <InputLabel>Category</InputLabel>
            <Select value={category} onChange={(e) => setCategory(e.target.value)} label="Category">
              {statCategories.map((cat) => (
                <MenuItem key={cat.value} value={cat.value}>
                  {cat.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Box sx={{ px: 2 }}>
            <Typography gutterBottom>Number of Leaders: {limit}</Typography>
            <Slider
              value={limit}
              onChange={(_, value) => setLimit(value as number)}
              min={5}
              max={25}
              step={5}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        </Grid>
      </Grid>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Leaders Table */}
      <TableContainer component={Paper} sx={{ mb: 4 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>#</TableCell>
              {columns.map((col) => (
                <TableCell key={col} align={col === 'Player' || col === 'Team' ? 'left' : 'center'}>
                  {col}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {leaders.map((player, index) => (
              <TableRow key={player.player_id} hover>
                <TableCell>{index + 1}</TableCell>
                {columns.map((col) => (
                  <TableCell
                    key={col}
                    align={col === 'Player' || col === 'Team' ? 'left' : 'center'}
                  >
                    {col === 'Player' ? (
                      <strong>{getStatValue(player, col)}</strong>
                    ) : (
                      getStatValue(player, col)
                    )}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Visualization */}
      <Box>
        <Typography variant="h5" gutterBottom fontWeight="600">
          Top {limit} in {statCategories.find((c) => c.value === category)?.label}
        </Typography>
        <Paper sx={{ p: 2 }}>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={getChartData()} margin={{ top: 5, right: 30, left: 20, bottom: 50 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#1976d2" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Box>
    </Box>
  );
}
