import React, { useState, useEffect, useRef } from 'react';
import './AgentActionBar.css';

export default function AgentActionBar({ onAction, thinking = false }) {
  // null = docked at bottom-centre of the 3D stage (CSS); {x, y} once the user drags it
  const [position, setPosition] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const offsetRef = useRef({ x: 0, y: 0 });
  const containerRef = useRef(null);

  useEffect(() => {
    if (!isDragging) return;

    const handlePointerMove = (e) => {
      setPosition({
        x: e.clientX - offsetRef.current.x,
        y: e.clientY - offsetRef.current.y
      });
    };

    const handlePointerUp = () => {
      setIsDragging(false);
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };
  }, [isDragging]);

  const handlePointerDown = (e) => {
    if (e.button !== 0 && e.type !== 'touchstart') return;
    const rect = containerRef.current.getBoundingClientRect();
    setPosition({ x: rect.left, y: rect.top });
    setIsDragging(true);
    offsetRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  // Double-click the handle to snap back to the docked position
  const handleDoubleClick = () => setPosition(null);

  const actions = [
    { 
      id: 'research', 
      label: 'Research', 
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      ) 
    },
    { 
      id: 'plan', 
      label: 'Plan', 
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="8" y1="6" x2="21" y2="6"/>
          <line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/>
          <line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/>
          <line x1="3" y1="18" x2="3.01" y2="18"/>
        </svg>
      ) 
    },
    { 
      id: 'build', 
      label: 'Build', 
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
      ) 
    },
    { 
      id: 'test', 
      label: 'Test', 
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 3h6"/>
          <path d="M10 9l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3h-4v6z"/>
        </svg>
      ) 
    },
    { 
      id: 'learn', 
      label: 'Learn', 
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
      ) 
    },
    { 
      id: 'create', 
      label: 'Create', 
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2l1.6 4.9L18.5 7l-4.9 1.6L12 13.5l-1.6-4.9L5.5 7l4.9-1.6L12 2z"/>
          <path d="M19 14l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3z"/>
          <path d="M6 16l.5 1.5 1.5.5-1.5.5-.5 1.5-.5-1.5-1.5-.5 1.5-.5L6 16z"/>
        </svg>
      ) 
    }
  ];

  return (
    <div 
      ref={containerRef}
      className={`agent-action-bar-container ${position ? 'floating' : 'docked'}`}
      style={position ? { left: `${position.x}px`, top: `${position.y}px` } : undefined}
    >
      <div className="agent-action-bar">
        <div className="action-bar-header">
          <div className="action-bar-status">
            <span className={`status-dot ${thinking ? 'busy' : ''}`}></span>
            <span className="status-text">{thinking ? 'Thinking…' : 'Running'}</span>
          </div>
          <button 
            className="drag-handle"
            onPointerDown={handlePointerDown}
            onDoubleClick={handleDoubleClick}
            title="Drag to move · double-click to dock"
            aria-label="Move Panel"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
               <polyline points="5 9 2 12 5 15"></polyline>
               <polyline points="9 5 12 2 15 5"></polyline>
               <polyline points="19 9 22 12 19 15"></polyline>
               <polyline points="9 19 12 22 15 19"></polyline>
               <line x1="2" y1="12" x2="22" y2="12"></line>
               <line x1="12" y1="2" x2="12" y2="22"></line>
            </svg>
          </button>
        </div>
        <div className="action-bar-items">
          {actions.map((action) => (
            <div key={action.id} className="action-item">
              <button 
                className="action-btn"
                onClick={() => onAction && onAction(action)}
                aria-label={action.label}
              >
                {action.icon}
              </button>
              <span className="action-label">{action.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
