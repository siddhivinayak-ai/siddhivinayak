import React, { useState } from 'react'
import './RadialToolOrbit.css'
import VoiceOrb from './VoiceOrb'

const TOOL_ITEMS = [
  {
    id: 'internet',
    label: 'Internet',
    x: 70,
    y: 52,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#253858" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    ),
  },
  {
    id: 'docs',
    label: 'Docs',
    x: 26,
    y: 36,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#253858" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <line x1="10" y1="9" x2="8" y2="9" />
      </svg>
    ),
  },
  {
    id: 'design',
    label: 'Design',
    x: 28,
    y: 15,
    icon: (
      <svg width="22" height="22" viewBox="0 0 38 57" fill="none">
        <path d="M19 28.5C19 23.2533 23.2533 19 28.5 19C33.7467 19 38 23.2533 38 28.5C38 33.7467 33.7467 38 28.5 38C23.2533 38 19 33.7467 19 28.5Z" fill="#1ABCFE"/>
        <path d="M0 47.5C0 42.2533 4.25329 38 9.5 38H19V47.5C19 52.7467 14.7467 57 9.5 57C4.25329 57 0 52.7467 0 47.5Z" fill="#0ACF83"/>
        <path d="M19 0V19H28.5C33.7467 19 38 14.7467 38 9.5C38 4.25329 33.7467 0 28.5 0H19Z" fill="#FF7262"/>
        <path d="M0 9.5C0 14.7467 4.25329 19 9.5 19H19V0H9.5C4.25329 0 0 4.25329 0 9.5Z" fill="#F24E1E"/>
        <path d="M0 28.5C0 33.7467 4.25329 38 9.5 38H19V19H9.5C4.25329 19 0 23.2533 0 28.5Z" fill="#A259FF"/>
      </svg>
    ),
  },
  {
    id: 'code',
    label: 'Code',
    x: 39,
    y: 3,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#253858" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="4" />
        <path d="m8 10-2 2 2 2" />
        <path d="m16 10 2 2-2 2" />
        <path d="m13 8-2 8" />
      </svg>
    ),
  },
  {
    id: 'data',
    label: 'Data',
    x: 61,
    y: 3,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#253858" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
  },
  {
    id: 'cad',
    label: '3D / CAD',
    x: 72,
    y: 15,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#253858" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
        <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
        <line x1="12" y1="22.08" x2="12" y2="12" />
      </svg>
    ),
  },
  {
    id: 'simulate',
    label: 'Simulate',
    x: 74,
    y: 36,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#253858" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
        <polyline points="16 7 22 7 22 13" />
        <path d="M5 21h14" strokeDasharray="2 2" />
      </svg>
    ),
  },
  {
    id: 'manufacturing',
    label: 'Manufacturing',
    x: 30,
    y: 52,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#253858" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
]

export default function RadialToolOrbit({ activeTool, onSelectTool, isListening, onToggleListen }) {
  const [hoveredTool, setHoveredTool] = useState(null)

  return (
    <div className="radial-orbit-container">
      {/* Voice Orb positioned accurately on the left */}
      <div
        className="voice-orb-positioner"
        style={{
          left: `${(115 / 1200) * 100}%`,
          top: `${(455 / 700) * 100}%`,
        }}
      >
        <VoiceOrb isListening={isListening} onToggleListen={onToggleListen} />
      </div>

      {/* Floating Tool Buttons Layer */}
      <div className="orbit-items-layer">
        {TOOL_ITEMS.map((item) => {
          const isActive = activeTool === item.id
          const isHovered = hoveredTool === item.id

          return (
            <button
              key={item.id}
              className={`tool-orb-btn ${isActive ? 'active' : ''} ${isHovered ? 'hovered' : ''}`}
              style={{
                left: `${item.x}%`,
                top: `${item.y}%`,
                cursor: 'pointer',
              }}
              onClick={() => onSelectTool && onSelectTool(item.id)}
              onMouseEnter={() => setHoveredTool(item.id)}
              onMouseLeave={() => setHoveredTool(null)}
              aria-label={item.label}
            >
              <div className="tool-orb-icon-card">
                {item.icon}
              </div>
              <span className="tool-orb-label">{item.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
