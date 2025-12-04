'use client';

import Link from 'next/link';
import { Box, Card, CardContent, Grid, Typography, Button } from '@mui/material';
import LeaderboardIcon from '@mui/icons-material/Leaderboard';
import SportsBasketballIcon from '@mui/icons-material/SportsBasketball';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import BarChartIcon from '@mui/icons-material/BarChart';
import PredictIcon from '@mui/icons-material/Psychology';

const features = [
  {
    title: 'Standings',
    description: 'View current NBA conference standings with win percentages, streaks, and more',
    icon: <LeaderboardIcon sx={{ fontSize: 60 }} />,
    href: '/standings',
    color: '#1976d2',
  },
  {
    title: "Today's Games",
    description: 'Live scores and schedules for games happening today',
    icon: <SportsBasketballIcon sx={{ fontSize: 60 }} />,
    href: '/today-games',
    color: '#dc004e',
  },
  {
    title: 'Statistical Leaders',
    description: 'Top performers in points, rebounds, assists, steals, and blocks',
    icon: <EmojiEventsIcon sx={{ fontSize: 60 }} />,
    href: '/leaders',
    color: '#f57c00',
  },
  {
    title: 'Team Analysis',
    description: 'In-depth team statistics, recent performance, and game-by-game breakdowns',
    icon: <BarChartIcon sx={{ fontSize: 60 }} />,
    href: '/team-analysis',
    color: '#388e3c',
  },
  {
    title: 'Predictions',
    description: 'ML-powered end-of-season forecasts and playoff probabilities',
    icon: <PredictIcon sx={{ fontSize: 60 }} />,
    href: '/predictions',
    color: '#7b1fa2',
  },
];

export default function Home() {
  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
          Welcome to NBA Analytics
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Real-time NBA statistics, standings, and predictions powered by machine learning
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {features.map((feature) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={feature.title}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ color: feature.color, mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h5" component="h2" gutterBottom fontWeight="600">
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  {feature.description}
                </Typography>
                <Button
                  component={Link}
                  href={feature.href}
                  variant="contained"
                  fullWidth
                  sx={{
                    backgroundColor: feature.color,
                    '&:hover': {
                      backgroundColor: feature.color,
                      opacity: 0.9,
                    },
                  }}
                >
                  View {feature.title}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 6, p: 3, bgcolor: 'background.paper', borderRadius: 2 }}>
        <Typography variant="h5" gutterBottom fontWeight="600">
          About This Platform
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          This NBA Analytics Platform provides real-time statistics, standings, and game data
          powered by a FastAPI backend and PostgreSQL database. The platform features:
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Live Data
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Real-time game scores and player statistics
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Advanced Analytics
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Team performance trends and statistical analysis
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              ML Predictions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              LSTM-based forecasts for end-of-season outcomes
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Fast Performance
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Redis caching for instant data retrieval
            </Typography>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}
