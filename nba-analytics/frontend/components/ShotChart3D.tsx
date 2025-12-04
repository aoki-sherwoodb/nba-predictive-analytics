'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import type { Shot } from '@/lib/types';

// Dynamically import Plot to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface ShotChart3DProps {
  shots: Shot[];
}

export default function ShotChart3D({ shots }: ShotChart3DProps) {
  const plotData = useMemo(() => {
    const scale = 1.0;
    const traces: any[] = [];

    // Court floor outline
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: [-250, 250, 250, -250, -250].map(v => v * scale),
      y: [-50, -50, 420, 420, -50].map(v => v * scale),
      z: [0, 0, 0, 0, 0],
      line: { color: '#1a365d', width: 4 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Paint/Key outline
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: [-80, 80, 80, -80, -80].map(v => v * scale),
      y: [-50, -50, 140, 140, -50].map(v => v * scale),
      z: [0, 0, 0, 0, 0],
      line: { color: '#c53030', width: 3 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Free throw circle
    const thetaFT = Array.from({ length: 50 }, (_, i) => (i / 49) * 2 * Math.PI);
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: thetaFT.map(t => 60 * Math.cos(t) * scale),
      y: thetaFT.map(t => (140 + 60 * Math.sin(t)) * scale),
      z: thetaFT.map(() => 0),
      line: { color: '#c53030', width: 2 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Three-point arc
    const theta3pt = Array.from({ length: 100 }, (_, i) => {
      const start = Math.acos(220 / 237.5);
      const end = Math.PI - Math.acos(220 / 237.5);
      return start + (i / 99) * (end - start);
    });
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: theta3pt.map(t => 237.5 * Math.cos(t) * scale),
      y: theta3pt.map(t => 237.5 * Math.sin(t) * scale),
      z: theta3pt.map(() => 0),
      line: { color: '#1a365d', width: 3 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Three-point corner lines (left)
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: [-220 * scale, -220 * scale],
      y: [-50 * scale, 90 * scale],
      z: [0, 0],
      line: { color: '#1a365d', width: 3 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Three-point corner lines (right)
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: [220 * scale, 220 * scale],
      y: [-50 * scale, 90 * scale],
      z: [0, 0],
      line: { color: '#1a365d', width: 3 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Basket/Rim
    const rimTheta = Array.from({ length: 30 }, (_, i) => (i / 29) * 2 * Math.PI);
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: rimTheta.map(t => 7.5 * Math.cos(t) * scale),
      y: rimTheta.map(t => 7.5 * Math.sin(t) * scale),
      z: rimTheta.map(() => 100),
      line: { color: '#dd6b20', width: 6 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Backboard (horizontal top)
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: [-30 * scale, 30 * scale],
      y: [-7.5 * scale, -7.5 * scale],
      z: [130, 130],
      line: { color: 'white', width: 8 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Backboard (horizontal bottom)
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: [-30 * scale, 30 * scale],
      y: [-7.5 * scale, -7.5 * scale],
      z: [80, 80],
      line: { color: 'white', width: 8 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Backboard (vertical left)
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: [-30 * scale, -30 * scale],
      y: [-7.5 * scale, -7.5 * scale],
      z: [80, 130],
      line: { color: 'white', width: 8 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Backboard (vertical right)
    traces.push({
      type: 'scatter3d',
      mode: 'lines',
      x: [30 * scale, 30 * scale],
      y: [-7.5 * scale, -7.5 * scale],
      z: [80, 130],
      line: { color: 'white', width: 8 },
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Helper function to create parabolic arc
    const createShotArc = (shotX: number, shotY: number, distance: number) => {
      const t = Array.from({ length: 30 }, (_, i) => i / 29);
      const x0 = shotX * scale;
      const y0 = shotY * scale;
      const z0 = 80; // Release height
      const x1 = 0;
      const y1 = 0;
      const z1 = 100; // Rim height
      const arcHeight = Math.max(150, 100 + distance * 3);

      return {
        x: t.map(ti => x0 + (x1 - x0) * ti),
        y: t.map(ti => y0 + (y1 - y0) * ti),
        z: t.map(ti => z0 + (z1 - z0) * ti + 4 * (arcHeight - Math.max(z0, z1)) * ti * (1 - ti)),
      };
    };

    // Separate made and missed shots
    const madeShots = shots.filter(s => s.made);
    const missedShots = shots.filter(s => !s.made);

    // Draw arcs for made shots
    madeShots.forEach(shot => {
      const arc = createShotArc(shot.x, shot.y, shot.distance);
      traces.push({
        type: 'scatter3d',
        mode: 'lines',
        x: arc.x,
        y: arc.y,
        z: arc.z,
        line: { color: '#38a169', width: 4 },
        opacity: 0.7,
        showlegend: false,
        hoverinfo: 'skip',
      });
    });

    // Made shots as circle markers
    if (madeShots.length > 0) {
      traces.push({
        type: 'scatter3d',
        mode: 'markers',
        x: madeShots.map(s => s.x * scale),
        y: madeShots.map(s => s.y * scale),
        z: madeShots.map(() => 80),
        marker: {
          size: 10,
          color: '#38a169',
          symbol: 'circle',
          line: { width: 2, color: '#276749' },
          opacity: 0.9,
        },
        text: madeShots.map(s =>
          `<b style="font-size:14px">${s.player_name}</b><br>` +
          `<span style="color:#48bb78">MADE</span><br>` +
          `${s.team_abbr} | ${s.shot_type} | ${s.distance}ft`
        ),
        hovertemplate: '%{text}<extra></extra>',
        showlegend: false,
      });
    }

    // Missed shots as X markers
    if (missedShots.length > 0) {
      traces.push({
        type: 'scatter3d',
        mode: 'markers',
        x: missedShots.map(s => s.x * scale),
        y: missedShots.map(s => s.y * scale),
        z: missedShots.map(() => 80),
        marker: {
          size: 8,
          color: '#e53e3e',
          symbol: 'x',
          line: { width: 2, color: '#c53030' },
          opacity: 0.7,
        },
        text: missedShots.map(s =>
          `<b style="font-size:14px">${s.player_name}</b><br>` +
          `<span style="color:#e53e3e">MISSED</span><br>` +
          `${s.team_abbr} | ${s.shot_type} | ${s.distance}ft`
        ),
        hovertemplate: '%{text}<extra></extra>',
        showlegend: false,
      });
    }

    return traces;
  }, [shots]);

  const layout = {
    scene: {
      xaxis: {
        range: [-300, 300],
        showgrid: false,
        showbackground: true,
        backgroundcolor: '#e8dcc4',
        showticklabels: false,
        title: '',
        showspikes: false,
      },
      yaxis: {
        range: [-100, 450],
        showgrid: false,
        showbackground: true,
        backgroundcolor: '#e8dcc4',
        showticklabels: false,
        title: '',
        showspikes: false,
      },
      zaxis: {
        range: [0, 250],
        showgrid: false,
        showbackground: false,
        showticklabels: false,
        title: '',
        showspikes: false,
      },
      camera: {
        eye: { x: 0, y: -1.5, z: 1.3 },
        center: { x: 0, y: 0, z: -0.1 },
      },
      aspectmode: 'manual',
      aspectratio: { x: 1, y: 1.2, z: 0.5 },
    },
    margin: { l: 0, r: 0, b: 0, t: 0 },
    paper_bgcolor: '#1e1e1e',
    plot_bgcolor: '#1e1e1e',
    showlegend: false,
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['select2d', 'lasso2d'],
  };

  return (
    <Plot
      data={plotData}
      layout={layout}
      config={config}
      style={{ width: '100%', height: '600px' }}
      useResizeHandler
    />
  );
}
