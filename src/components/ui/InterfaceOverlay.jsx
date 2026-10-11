import React, { useCallback, useState } from 'react'
import HeaderLogo from './HeaderLogo'
import RadialToolOrbit from './RadialToolOrbit'
import AgentActionBar from './AgentActionBar'
import ChatPanel from './ChatPanel'
import Teardown from '../teardown/Teardown'
import useSpeech from '../../hooks/useSpeech'
import useListen from '../../hooks/useListen'
import './InterfaceOverlay.css'

// Orbit tools steer the 3D scene and seed the question box.
const TOOL_SCENES = {
  manufacturing: ['machining', 'Explain the manufacturing process for '],
  design: ['design', 'Design check: '],
  simulate: ['thermal', 'Estimate / calculate: '],
  cad: ['design', 'Give CAD modelling steps for '],
  docs: ['studio', 'Summarise what my notes say about '],
  data: ['studio', 'What knowledge modules have you learned so far?'],
  code: ['studio', 'Write Python to calculate '],
  internet: ['studio', ''],
}

const ACTION_PROMPTS = {
  research: 'Research in my knowledge base: ',
  plan: 'Make a step-by-step plan for: ',
  build: 'How do I build / manufacture: ',
  test: 'How do I test / inspect: ',
  learn: 'Quiz me with 3 GATE-style questions on ',
  create: 'Create a one-page cheat sheet on ',
}

// Turn a markdown answer into a short spoken line.
function speakable(md) {
  const plain = md
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/\[[^\]]*\]/g, '')
    .replace(/[#*_>`|]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
  const sentences = plain.match(/[^.!?]+[.!?]+/g) || [plain]
  let out = ''
  for (const s of sentences) {
    if ((out + s).length > 280) break
    out += s
  }
  return out || plain.slice(0, 280)
}

export default function InterfaceOverlay({ brain, onVolumeChange }) {
  const [activeTool, setActiveTool] = useState('manufacturing')
  const [draft, setDraft] = useState('')
  const { speak, stop } = useSpeech({ onVolumeChange })

  const ask = useCallback(async (text) => {
    stop()
    const data = await brain.send(text)
    if (data?.answer) speak(speakable(data.answer))
  }, [brain, speak, stop])

  const listen = useListen({ onFinal: ask })

  const handleToggleListen = () => {
    if (listen.listening) return listen.stop()
    stop()
    if (!listen.start()) {
      speak('Voice input needs Chrome or Edge. You can type to me instead.')
    }
  }

  const handleSelectTool = (toolId) => {
    setActiveTool(toolId)
    const [scene, seed] = TOOL_SCENES[toolId] || ['studio', '']
    brain.setScene(scene)
    if (toolId === 'data') ask(seed)
    else if (seed) setDraft(seed)
  }

  const handleAction = (action) => setDraft(ACTION_PROMPTS[action.id] || '')

  // Teardown result: move the twin into the matching workshop and narrate the reveal
  const handleTeardown = useCallback((result) => {
    if (result.scene) brain.setScene(result.scene)
    if (result.narration) speak(result.narration)
  }, [brain, speak])

  return (
    <>
      <HeaderLogo />

      <RadialToolOrbit
        activeTool={activeTool}
        onSelectTool={handleSelectTool}
        isListening={listen.listening}
        onToggleListen={handleToggleListen}
      />

      <AgentActionBar onAction={handleAction} thinking={brain.thinking} />

      <Teardown onStart={stop} onResult={handleTeardown} />

      <ChatPanel
        brain={{ ...brain, send: ask }}
        interim={listen.interim}
        draft={draft}
        setDraft={setDraft}
      />

      <nav className="footer-tags" aria-label="Focus areas">
        {['Manufacturing', 'Automation', 'Engineering', 'More'].map((t, i) => (
          <React.Fragment key={t}>
            {i > 0 && <span className="footer-sep">•</span>}
            <span>{t}</span>
          </React.Fragment>
        ))}
      </nav>
    </>
  )
}
