'use client';

import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import { api } from '@/lib/api';
import type { PredictionsResponse, ModelInfo, StandingsResponse, TeamPrediction } from '@/lib/types';

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<PredictionsResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [standings, setStandings] = useState<StandingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedTeam, setSelectedTeam] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [predData, modelData, standingsData] = await Promise.all([
          api.getPredictions(),
          api.getModelInfo().catch(() => null),
          api.getStandings().catch(() => null),
        ]);
        setPredictions(predData);
        setModelInfo(modelData);
        setStandings(standingsData);

        // Set first team as default selection
        if (predData && predData.east.length > 0) {
          setSelectedTeam(`${predData.east[0].team_abbr} - ${predData.east[0].team_name}`);
        }

        setError(null);
      } catch (err) {
        setError('Failed to load predictions');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !predictions) {
    return (
      <Alert severity="warning" sx={{ mt: 2 }}>
        {error ||
          'No predictions available. The LSTM model may need to be trained first. Use the Admin API to trigger model training.'}
      </Alert>
    );
  }

  const allTeams = [...predictions.east, ...predictions.west];
  const teamOptions = allTeams.map((t) => `${t.team_abbr} - ${t.team_name}`);
  const selectedTeamData = allTeams.find((t) => `${t.team_abbr} - ${t.team_name}` === selectedTeam);

  const standingsMap = standings
    ? [...standings.east, ...standings.west].reduce(
        (acc, team) => {
          acc[team.team_abbr] = team.wins;
          return acc;
        },
        {} as Record<string, number>
      )
    : {};

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        End-of-Season Predictions
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Predictions generated: {new Date(predictions.prediction_date).toLocaleString()}
      </Typography>

      {/* Model Info */}
      {modelInfo && (
        <Accordion sx={{ mb: 3 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Model Information</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Model Version
                    </Typography>
                    <Typography variant="h6">{modelInfo.model_version}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Wins MAE
                    </Typography>
                    <Typography variant="h6">
                      {modelInfo.mae_wins ? modelInfo.mae_wins.toFixed(2) : 'N/A'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Training Seasons
                    </Typography>
                    <Typography variant="h6">{modelInfo.training_seasons.length}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label="Conference Rankings" />
          <Tab label="Playoff Probabilities" />
          <Tab label="Statistical Forecasts" />
        </Tabs>
      </Box>

      {/* Tab 1: Conference Rankings */}
      {activeTab === 0 && (
        <Box>
          <Grid container spacing={3}>
            {/* Eastern Conference */}
            <Grid item xs={12} md={6}>
              <Typography variant="h5" gutterBottom color="primary.main" fontWeight="600">
                Eastern Conference
              </Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Rank</TableCell>
                      <TableCell>Team</TableCell>
                      <TableCell align="center">Pred W</TableCell>
                      <TableCell align="center">Pred L</TableCell>
                      <TableCell align="center">Actual W</TableCell>
                      <TableCell align="center">Playoff %</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {predictions.east.map((team) => (
                      <TableRow key={team.team_id} hover>
                        <TableCell>{team.predicted_conference_rank}</TableCell>
                        <TableCell>
                          <strong>{team.team_abbr}</strong>
                        </TableCell>
                        <TableCell align="center">{Math.round(team.predicted_wins)}</TableCell>
                        <TableCell align="center">{Math.round(team.predicted_losses)}</TableCell>
                        <TableCell align="center">{standingsMap[team.team_abbr] || '-'}</TableCell>
                        <TableCell align="center">
                          {(team.playoff_probability * 100).toFixed(0)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>

            {/* Western Conference */}
            <Grid item xs={12} md={6}>
              <Typography variant="h5" gutterBottom color="error.main" fontWeight="600">
                Western Conference
              </Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Rank</TableCell>
                      <TableCell>Team</TableCell>
                      <TableCell align="center">Pred W</TableCell>
                      <TableCell align="center">Pred L</TableCell>
                      <TableCell align="center">Actual W</TableCell>
                      <TableCell align="center">Playoff %</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {predictions.west.map((team) => (
                      <TableRow key={team.team_id} hover>
                        <TableCell>{team.predicted_conference_rank}</TableCell>
                        <TableCell>
                          <strong>{team.team_abbr}</strong>
                        </TableCell>
                        <TableCell align="center">{Math.round(team.predicted_wins)}</TableCell>
                        <TableCell align="center">{Math.round(team.predicted_losses)}</TableCell>
                        <TableCell align="center">{standingsMap[team.team_abbr] || '-'}</TableCell>
                        <TableCell align="center">
                          {(team.playoff_probability * 100).toFixed(0)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>

          {/* Predicted vs Actual Wins Chart */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h5" gutterBottom fontWeight="600">
              Predicted vs Current Wins
            </Typography>
            <Paper sx={{ p: 2 }}>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart
                  data={allTeams.map((team) => ({
                    team: team.team_abbr,
                    predicted: team.predicted_wins,
                    actual: standingsMap[team.team_abbr] || 0,
                  }))}
                  margin={{ top: 5, right: 30, left: 20, bottom: 50 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="team" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="predicted" fill="#667eea" name="Predicted Wins" />
                  <Bar dataKey="actual" fill="#48bb78" name="Current Wins" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Box>
        </Box>
      )}

      {/* Tab 2: Playoff Probabilities */}
      {activeTab === 1 && (
        <Box>
          <Typography variant="h5" gutterBottom fontWeight="600">
            Playoff Qualification Probabilities
          </Typography>
          <Grid container spacing={3}>
            {/* East */}
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom color="primary.main">
                Eastern Conference
              </Typography>
              <Paper sx={{ p: 2 }}>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    data={[...predictions.east].sort((a, b) => b.playoff_probability - a.playoff_probability)}
                    margin={{ top: 5, right: 30, left: 20, bottom: 50 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="team_abbr" angle={-45} textAnchor="end" height={80} />
                    <YAxis label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                    <ReferenceLine y={50} stroke="#666" strokeDasharray="3 3" label="50%" />
                    <Bar dataKey={(d: TeamPrediction) => d.playoff_probability * 100} name="Playoff %">
                      {predictions.east.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.playoff_probability > 0.5 ? '#48bb78' : '#f56565'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* West */}
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom color="error.main">
                Western Conference
              </Typography>
              <Paper sx={{ p: 2 }}>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    data={[...predictions.west].sort((a, b) => b.playoff_probability - a.playoff_probability)}
                    margin={{ top: 5, right: 30, left: 20, bottom: 50 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="team_abbr" angle={-45} textAnchor="end" height={80} />
                    <YAxis label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                    <ReferenceLine y={50} stroke="#666" strokeDasharray="3 3" label="50%" />
                    <Bar dataKey={(d: TeamPrediction) => d.playoff_probability * 100} name="Playoff %">
                      {predictions.west.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.playoff_probability > 0.5 ? '#48bb78' : '#f56565'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Tab 3: Statistical Forecasts */}
      {activeTab === 2 && (
        <Box>
          <Typography variant="h5" gutterBottom fontWeight="600">
            Predicted Season Statistics
          </Typography>

          <FormControl fullWidth sx={{ mb: 3, maxWidth: 400 }}>
            <InputLabel>Select Team</InputLabel>
            <Select value={selectedTeam} onChange={(e) => setSelectedTeam(e.target.value)} label="Select Team">
              {teamOptions.map((team) => (
                <MenuItem key={team} value={team}>
                  {team}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {selectedTeamData && (
            <>
              {/* Team Stats Cards */}
              <Grid container spacing={2} sx={{ mb: 4 }}>
                <Grid item xs={6} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom variant="body2">
                        Predicted Wins
                      </Typography>
                      <Typography variant="h5" fontWeight="bold">
                        {selectedTeamData.predicted_wins.toFixed(0)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Win %: {(selectedTeamData.predicted_win_pct * 100).toFixed(1)}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom variant="body2">
                        Predicted PPG
                      </Typography>
                      <Typography variant="h5" fontWeight="bold">
                        {selectedTeamData.predicted_ppg.toFixed(1)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        OPPG: {selectedTeamData.predicted_oppg.toFixed(1)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom variant="body2">
                        Predicted Pace
                      </Typography>
                      <Typography variant="h5" fontWeight="bold">
                        {selectedTeamData.predicted_pace.toFixed(1)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Def Rating: {selectedTeamData.predicted_defensive_rating.toFixed(1)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom variant="body2">
                        Conf Rank
                      </Typography>
                      <Typography variant="h5" fontWeight="bold">
                        #{selectedTeamData.predicted_conference_rank}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Playoff: {(selectedTeamData.playoff_probability * 100).toFixed(0)}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Offense vs Defense Scatter Plot */}
              <Box>
                <Typography variant="h5" gutterBottom fontWeight="600">
                  Team Efficiency: Offense vs Defense
                </Typography>
                <Paper sx={{ p: 2 }}>
                  <ResponsiveContainer width="100%" height={500}>
                    <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        type="number"
                        dataKey="ppg"
                        name="PPG"
                        label={{ value: 'Predicted PPG (Offense)', position: 'insideBottom', offset: -10 }}
                      />
                      <YAxis
                        type="number"
                        dataKey="oppg"
                        name="OPPG"
                        label={{ value: 'Predicted OPPG (Defense)', angle: -90, position: 'insideLeft' }}
                      />
                      <Tooltip
                        cursor={{ strokeDasharray: '3 3' }}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0].payload;
                            return (
                              <Paper sx={{ p: 1.5 }}>
                                <Typography variant="body2" fontWeight="bold">
                                  {data.team}
                                </Typography>
                                <Typography variant="body2">PPG: {data.ppg.toFixed(1)}</Typography>
                                <Typography variant="body2">OPPG: {data.oppg.toFixed(1)}</Typography>
                                <Typography variant="body2">
                                  Playoff: {(data.playoff * 100).toFixed(0)}%
                                </Typography>
                              </Paper>
                            );
                          }
                          return null;
                        }}
                      />
                      <Scatter
                        name="Teams"
                        data={allTeams.map((t) => ({
                          team: t.team_abbr,
                          ppg: t.predicted_ppg,
                          oppg: t.predicted_oppg,
                          playoff: t.playoff_probability,
                        }))}
                      >
                        {allTeams.map((team, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={
                              team.playoff_probability > 0.7
                                ? '#48bb78'
                                : team.playoff_probability > 0.3
                                  ? '#f6ad55'
                                  : '#f56565'
                            }
                          />
                        ))}
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1, textAlign: 'center' }}>
                    Teams in upper-right (high PPG, low OPPG) are predicted to be most successful. Green = high playoff probability, Orange = medium, Red = low.
                  </Typography>
                </Paper>
              </Box>
            </>
          )}
        </Box>
      )}
    </Box>
  );
}
