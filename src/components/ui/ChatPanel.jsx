import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import { BRAIN_API } from '../../hooks/useBrain'
import { sceneOf } from '../../scenes'
import './ChatPanel.css'

const MODULES = ['inbox', 'notes', 'screws', 'welding', 'memory']

const PROVIDER_NAMES = { anthropic: 'Claude', groq: 'Groq', google_genai: 'Gemini', ollama: 'Ollama' }

const SUGGESTIONS = [
  'Tightening torque for an M12 8.8 bolt?',
  'Decode electrode E7018-1 H4R',
  'Explain Taylor tool life equation',
  'Heat input: 24 V, 220 A, 300 mm/min MAG',
]

// Normalise LLM math/citation styles so remark-math can render them:
// \[..\] → $$..$$, \(..\) → $..$, and 【notes p.12】 → (notes p.12)
function normalise(md) {
  return md
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, m) => `\n$$${m}$$\n`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, m) => `$${m}$`)
    .replace(/【([^】]+)】/g, ' ($1)')
}

function shortFile(name) {
  return name.length > 22 ? name.slice(0, 18) + '…' : name
}

export default function ChatPanel({ brain, interim, draft, setDraft }) {
  const { messages, thinking, health, send, learn, newChat, scene } = brain
  const [open, setOpen] = useState(true)
  const [module, setModule] = useState('inbox')
  const [page, setPage] = useState(null)
  const [dragging, setDragging] = useState(false)
  const listRef = useRef(null)
  const fileRef = useRef(null)

  // Tell the layout how much width the panel takes so the 3D stage re-centres
  useEffect(() => {
    const root = document.documentElement
    root.style.setProperty('--chat-w', open ? 'calc(min(400px, 100vw - 32px) + 48px)' : '0px')
    root.dataset.chat = open ? 'open' : 'closed'
  }, [open])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  const submit = (e) => {
    e?.preventDefault()
    if (!draft.trim() || thinking) return
    send(draft)
    setDraft('')
  }

  const onFiles = (files) => {
    for (const f of files) learn(f, module)
  }

  const llm = health?.llm
  const status = health?.status === 'offline' ? 'Brain offline'
    : health?.index?.state && health.index.state !== 'idle' ? `Learning… ${health.index.detail}`
    : llm ? `${PROVIDER_NAMES[llm.split('/')[0]] || llm.split('/')[0]} · ${llm.split('/').pop()}`
    : 'Offline retrieval mode'

  if (!open) {
    return (
      <button className="chat-fab" onClick={() => setOpen(true)} aria-label="Open chat">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
        {messages.length > 0 && <span className="chat-fab-dot" />}
      </button>
    )
  }

  return (
    <aside
      className={`chat-panel ${dragging ? 'dragging' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); onFiles(e.dataTransfer.files) }}
    >
      <header className="chat-header">
        <div>
          <div className="chat-title">Engineering Brain</div>
          <div className="chat-status">
            <span className={`chat-status-dot ${health?.status === 'offline' ? 'off' : ''}`} />
            {status}
            {health?.chunks ? <span className="chat-muted"> · {health.chunks.toLocaleString()} chunks</span> : null}
          </div>
        </div>
        <div className="chat-header-actions">
          <span className="chat-scene-pill">{sceneOf(scene).label}</span>
          <button className="chat-icon-btn" onClick={newChat} title="New conversation" aria-label="New conversation">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14" /></svg>
          </button>
          <button className="chat-icon-btn" onClick={() => setOpen(false)} title="Minimise" aria-label="Minimise chat">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12h14" /></svg>
          </button>
        </div>
      </header>

      <div className="chat-list" ref={listRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Ask me anything from your notes, screws or welding — or drop a PDF/DOCX here to teach me.</p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg msg-${m.role} ${m.error ? 'msg-error' : ''}`}>
            <div className="msg-body">
              <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>{normalise(m.text)}</ReactMarkdown>
            </div>
            {m.tools?.length > 0 && (
              <div className="msg-tools">
                {[...new Set(m.tools)].map((t) => <span key={t}>⚙ {t.replace(/_/g, ' ')}</span>)}
              </div>
            )}
            {m.sources?.length > 0 && (
              <div className="msg-sources">
                {m.sources.map((s) => (
                  <button
                    key={`${s.doc_id}-${s.page}`}
                    className="source-chip"
                    title={`${s.file} — page ${s.page}`}
                    onClick={() => s.file.toLowerCase().endsWith('.pdf') && setPage(s)}
                  >
                    {shortFile(s.file)} · p.{s.page}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {thinking && (
          <div className="msg msg-assistant">
            <div className="typing"><span /><span /><span /></div>
          </div>
        )}
      </div>

      <form className="chat-input" onSubmit={submit}>
        <button type="button" className="chat-icon-btn" onClick={() => fileRef.current?.click()} title="Teach me a file" aria-label="Upload file">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" /></svg>
        </button>
        <select className="chat-module" value={module} onChange={(e) => setModule(e.target.value)} title="Module to learn into">
          {MODULES.map((m) => <option key={m}>{m}</option>)}
        </select>
        <input ref={fileRef} type="file" hidden multiple accept=".pdf,.docx,.pptx,.txt,.md,.csv,.json"
          onChange={(e) => { onFiles(e.target.files); e.target.value = '' }} />
        <textarea
          rows={1}
          value={interim || draft}
          placeholder={interim ? '' : 'Ask Siddhivinayak…'}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) submit(e) }}
        />
        <button type="submit" className="chat-send" disabled={thinking || !draft.trim()} aria-label="Send">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
        </button>
      </form>

      {page && (
        <div className="page-modal" onClick={() => setPage(null)}>
          <div className="page-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="page-modal-head">
              <span>{page.file} — page {page.page}</span>
              <button className="chat-icon-btn" onClick={() => setPage(null)} aria-label="Close">✕</button>
            </div>
            <img src={`${BRAIN_API}/page?doc_id=${encodeURIComponent(page.doc_id)}&page=${page.page}`} alt={`Page ${page.page}`} />
          </div>
        </div>
      )}
    </aside>
  )
}
