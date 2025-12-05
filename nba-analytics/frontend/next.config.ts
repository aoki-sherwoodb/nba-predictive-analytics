import type { NextConfig } from "next";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || '';

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.nba.com',
        pathname: '/logos/**',
      },
      {
        protocol: 'https',
        hostname: 'cdn.nba.com',
        pathname: '/headshots/**',
      },
    ],
  },
  // Only use rewrites for local development (when API_BASE_URL is not set)
  async rewrites() {
    // In production with Cloud Run, API calls go directly to API_BASE_URL
    if (apiBaseUrl) {
      return [];
    }
    // Local development: proxy to local API
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/health',
        destination: 'http://localhost:8000/health',
      },
    ];
  },
};

export default nextConfig;
