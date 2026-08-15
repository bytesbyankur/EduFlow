import React, { useState } from 'react';

export default function AttendanceGraph({ dataPoints = [0, 0, 0, 0, 0, 0, 0] }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const days = ['6d ago', '5d ago', '4d ago', '3d ago', '2d ago', 'Yesterday', 'Today'];
  const safeData = dataPoints && dataPoints.length > 0 ? dataPoints : [0, 0, 0, 0, 0, 0, 0];
  const maxVal = Math.max(...safeData, 3); // Minimum scale of 3 to avoid flatline

  // Compute SVG viewBox coordinates (width: 400, height: 160)
  const svgWidth = 400;
  const svgHeight = 140;
  const paddingX = 25;
  const paddingY = 25;

  const points = safeData.map((val, idx) => {
    const x = paddingX + (idx / (safeData.length - 1)) * (svgWidth - paddingX * 2);
    const y = svgHeight - paddingY - (val / maxVal) * (svgHeight - paddingY * 2);
    return { x, y, val, day: days[idx] || `Day ${idx + 1}` };
  });

  const polylineStr = points.map(p => `${p.x},${p.y}`).join(' ');

  // Generate Area polygon string for gradient fill beneath curve
  const areaPolyStr = `${points[0].x},${svgHeight - paddingY} ` + 
                      polylineStr + 
                      ` ${points[points.length - 1].x},${svgHeight - paddingY}`;

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '0.75rem'
      }}>
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
            Attendance Trends
          </span>
          <p style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Past 7 Days Activity
          </p>
        </div>

        {hoveredPoint ? (
          <div style={{
            backgroundColor: 'rgba(99, 102, 241, 0.2)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            padding: '0.25rem 0.65rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.75rem',
            fontWeight: 700,
            color: '#a5b4fc',
            animation: 'fadeIn 0.2s ease'
          }}>
            {hoveredPoint.day}: <strong style={{ color: '#ffffff' }}>{hoveredPoint.val}</strong> {hoveredPoint.val === 1 ? 'Class' : 'Classes'}
          </div>
        ) : (
          <div style={{
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            fontWeight: 600
          }}>
            Hover on points for details
          </div>
        )}
      </div>

      {/* SVG Canvas Chart */}
      <div style={{
        width: '100%',
        backgroundColor: 'rgba(15, 23, 42, 0.4)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        padding: '0.75rem 0.5rem 0.25rem',
        overflow: 'hidden'
      }}>
        <svg 
          viewBox={`0 0 ${svgWidth} ${svgHeight}`} 
          style={{ width: '100%', height: 'auto', display: 'block' }}
        >
          <defs>
            <linearGradient id="curveGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
            </linearGradient>
            <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#6366f1" floodOpacity="0.45" />
            </filter>
          </defs>

          {/* Horizontal Grid lines */}
          <line x1={paddingX} y1={paddingY} x2={svgWidth - paddingX} y2={paddingY} stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
          <line x1={paddingX} y1={(svgHeight - paddingY * 2) / 2 + paddingY} x2={svgWidth - paddingX} y2={(svgHeight - paddingY * 2) / 2 + paddingY} stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
          <line x1={paddingX} y1={svgHeight - paddingY} x2={svgWidth - paddingX} y2={svgHeight - paddingY} stroke="rgba(255,255,255,0.1)" />

          {/* Area fill */}
          <polygon points={areaPolyStr} fill="url(#curveGradient)" />

          {/* Main Polyline Curve */}
          <polyline
            points={polylineStr}
            fill="none"
            stroke="#6366f1"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="url(#glowEffect)"
          />

          {/* Data point dots */}
          {points.map((pt, i) => (
            <g key={i}>
              {/* Outer pulsing ring on hover */}
              {hoveredPoint?.day === pt.day && (
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r="7.5"
                  fill="rgba(99, 102, 241, 0.4)"
                  stroke="#6366f1"
                  strokeWidth="1.5"
                />
              )}
              {/* Core dot */}
              <circle
                cx={pt.x}
                cy={pt.y}
                r="4"
                fill="#ffffff"
                stroke="#4f46e5"
                strokeWidth="2.5"
                style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
                onMouseEnter={() => setHoveredPoint(pt)}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            </g>
          ))}
        </svg>

        {/* X-axis Day labels */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          padding: '0.35rem 0.75rem 0.5rem',
          fontSize: '0.68rem',
          color: 'var(--text-muted)',
          fontWeight: 600,
          userSelect: 'none'
        }}>
          {days.map((d, i) => (
            <span key={i} style={{ color: i === days.length - 1 ? '#818cf8' : 'var(--text-muted)' }}>
              {d}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
