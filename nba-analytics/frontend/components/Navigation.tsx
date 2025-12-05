'use client';

import * as React from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  Button,
  Container,
  Tabs,
  Tab,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { api } from '@/lib/api';

const navItems = [
  { text: 'Home', href: '/' },
  { text: 'Standings', href: '/standings' },
  { text: "Today's Games", href: '/today-games' },
  { text: 'Leaders', href: '/leaders' },
  { text: 'Team Analysis', href: '/team-analysis' },
  { text: 'Predictions', href: '/predictions' },
  { text: 'Live Game', href: '/live-game' },
];

export default function Navigation({ children }: { children: React.ReactNode }) {
  const [refreshing, setRefreshing] = React.useState(false);
  const pathname = usePathname();

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await api.refreshFull();
      window.location.reload();
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const currentTab = navItems.findIndex((item) => item.href === pathname);

  return (
    <Box>
      {/* Floating Banner */}
      <AppBar
        position="fixed"
        elevation={4}
        sx={{
          background: 'linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%)',
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        }}
      >
        <Container maxWidth="xl">
          <Toolbar disableGutters sx={{ minHeight: { xs: 70, md: 80 } }}>
            {/* NBA Logo */}
            <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
              <Image
                src="https://cdn.nba.com/logos/leagues/logo-nba.svg"
                alt="NBA Logo"
                width={60}
                height={60}
                style={{ filter: 'brightness(0) invert(1)' }}
              />
            </Box>

            {/* App Title */}
            <Typography
              variant="h4"
              component="div"
              sx={{
                flexGrow: 0,
                mr: 6,
                fontWeight: 900,
                letterSpacing: '0.1em',
                background: 'linear-gradient(45deg, #ffffff 30%, #e3f2fd 90%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
                fontSize: { xs: '1.75rem', md: '2.125rem' },
              }}
            >
              🎱 8 BALL
            </Typography>

            {/* Navigation Tabs */}
            <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
              <Tabs
                value={currentTab !== -1 ? currentTab : false}
                textColor="inherit"
                TabIndicatorProps={{
                  style: {
                    backgroundColor: '#fff',
                    height: 3,
                    borderRadius: '3px 3px 0 0',
                  },
                }}
                sx={{
                  '& .MuiTab-root': {
                    color: 'rgba(255,255,255,0.7)',
                    fontWeight: 600,
                    fontSize: '0.9rem',
                    minWidth: 'auto',
                    px: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      color: '#fff',
                      backgroundColor: 'rgba(255,255,255,0.1)',
                    },
                    '&.Mui-selected': {
                      color: '#fff',
                    },
                  },
                }}
              >
                {navItems.map((item) => (
                  <Tab
                    key={item.href}
                    label={item.text}
                    component={Link}
                    href={item.href}
                  />
                ))}
              </Tabs>
            </Box>

            {/* Refresh Button */}
            <Button
              color="inherit"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={refreshing}
              sx={{
                ml: 2,
                backgroundColor: 'rgba(255,255,255,0.15)',
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.25)',
                },
                borderRadius: 2,
                px: 2,
              }}
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
          </Toolbar>

          {/* Mobile Navigation */}
          <Box sx={{ display: { xs: 'flex', md: 'none' }, pb: 1, overflowX: 'auto' }}>
            <Tabs
              value={currentTab !== -1 ? currentTab : false}
              variant="scrollable"
              scrollButtons="auto"
              textColor="inherit"
              TabIndicatorProps={{
                style: {
                  backgroundColor: '#fff',
                  height: 2,
                },
              }}
              sx={{
                '& .MuiTab-root': {
                  color: 'rgba(255,255,255,0.7)',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  minWidth: 'auto',
                  px: 1.5,
                  '&.Mui-selected': {
                    color: '#fff',
                  },
                },
              }}
            >
              {navItems.map((item) => (
                <Tab
                  key={item.href}
                  label={item.text}
                  component={Link}
                  href={item.href}
                />
              ))}
            </Tabs>
          </Box>
        </Container>
      </AppBar>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          pt: { xs: '140px', md: '100px' },
          pb: 4,
          minHeight: '100vh',
        }}
      >
        <Container maxWidth="xl">
          {children}
        </Container>
      </Box>
    </Box>
  );
}
