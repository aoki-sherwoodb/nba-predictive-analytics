# NBA Analytics Frontend

Modern Next.js frontend for the NBA Analytics Platform, featuring real-time statistics, standings, and ML-powered predictions.

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Material-UI v5** - Component library and dark theme
- **Recharts** - Data visualization
- **SWR** - Data fetching (optional)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies (if not already done)
npm install

# Run development server
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
# Create optimized production build
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── page.tsx             # Home page with feature cards
│   ├── standings/           # Conference standings
│   ├── today-games/         # Live game scores
│   ├── leaders/             # Statistical leaders
│   ├── team-analysis/       # Team performance analysis
│   ├── predictions/         # ML predictions
│   ├── layout.tsx           # Root layout with MUI theme
│   └── globals.css          # Global styles
├── components/              # Reusable React components
│   └── Navigation.tsx       # Sidebar navigation
├── lib/                     # Utility libraries
│   ├── api.ts              # API service layer
│   ├── theme.ts            # MUI dark theme config
│   └── types.ts            # TypeScript interfaces
└── public/                  # Static assets
```

## Features

### Pages

1. **Home** (`/`) - Landing page with feature cards
2. **Standings** (`/standings`) - East/West conference standings with win % chart
3. **Today's Games** (`/today-games`) - Live scores with auto-refresh
4. **Leaders** (`/leaders`) - Top performers by category (points, rebounds, assists, etc.)
5. **Team Analysis** (`/team-analysis`) - Team-specific stats, record, and point differential trends
6. **Predictions** (`/predictions`) - ML-powered end-of-season forecasts and playoff probabilities

### Key Features

- Dark mode theme optimized for readability
- Responsive design (mobile, tablet, desktop)
- Real-time data with auto-refresh options
- Interactive charts and visualizations
- Type-safe API integration

## API Configuration

The frontend expects the backend API to be running at `http://localhost:8000` by default. This is configured in `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

To change the API URL, edit `.env.local` and restart the development server.

## Available Scripts

- `npm run dev` - Start development server (port 3000)
- `npm run build` - Create production build
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Development Notes

- All pages are client-side rendered (`'use client'`) for dynamic data fetching
- API calls are made directly using the fetch API (no external libraries required)
- Charts use Recharts for responsive, customizable visualizations
- MUI components follow Material Design principles with custom dark theme
- Navigation is persistent across all pages via the root layout

## Troubleshooting

### API Connection Issues

If you see "Failed to load data" errors:
1. Verify the backend is running: `curl http://localhost:8000/health`
2. Check `.env.local` has the correct API URL
3. Check browser console for CORS errors

### Build Errors

If you encounter build errors:
1. Delete `.next` folder: `rm -rf .next`
2. Clear npm cache: `npm cache clean --force`
3. Reinstall dependencies: `rm -rf node_modules && npm install`
4. Rebuild: `npm run build`

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new).

Check out the [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
