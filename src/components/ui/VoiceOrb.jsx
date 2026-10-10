import React, { useState } from 'react'
import './VoiceOrb.css'

export default function VoiceOrb({ isListening = false, onToggleListen }) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div className="voice-orb-wrapper">
      {/* Interactive Microphone Orb */}
      <div
        className={`voice-orb-container ${isListening ? 'listening' : ''} ${isHovered ? 'hover' : ''}`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onToggleListen}
        role="button"
        tabIndex={0}
        aria-label="Tap to speak"
      >
        {/* Outer Glow Ripples matching reference */}
        <div className="orb-halo halo-3" />
        <div className="orb-halo halo-2" />
        <div className="orb-halo halo-1" />

        {/* Central Pure White Glass Disc */}
        <div className="orb-core">
          <svg className="mic-icon" width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2Z"
              fill="#264478"
            />
            <path
              d="M19 10V11C19 14.53 16.39 17.44 13 17.93V21H11V17.93C7.61 17.44 5 14.53 5 11V10H7V11C7 13.76 9.24 16 12 16C14.76 16 17 13.76 17 11V10H19Z"
              fill="#264478"
            />
          </svg>
        </div>
      </div>

      {/* Label */}
      <span className="voice-orb-label">Tap to Speak</span>
    </div>
  )
}
