import { useCallback, useEffect, useRef, useState } from 'react'

export const BRAIN_API = '/api'

const THREAD_KEY = 'siddhivinayak.thread'
const HISTORY_KEY = 'siddhivinayak.history'

function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback } catch { return fallback }
}
function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* private mode */ }
}

/**
 * Talks to the Python brain server: chat, learning uploads and status.
 * The conversation thread id is kept so the agent's memory continues across reloads.
 */
export default function useBrain() {
  const [messages, setMessages] = useState(() => load(HISTORY_KEY, []))
  const [thinking, setThinking] = useState(false)
  const [scene, setScene] = useState(() => new URLSearchParams(window.location.search).get('scene') || 'studio')
  const [health, setHealth] = useState(null)
  const threadRef = useRef(load(THREAD_KEY, null) || `t-${Date.now()}`)

  useEffect(() => { save(THREAD_KEY, threadRef.current) }, [])
  useEffect(() => { save(HISTORY_KEY, messages.slice(-60)) }, [messages])

  const refreshHealth = useCallback(async () => {
    try {
      const r = await fetch(`${BRAIN_API}/health`)
      setHealth(await r.json())
    } catch {
      setHealth({ status: 'offline' })
    }
  }, [])

  useEffect(() => {
    refreshHealth()
    const id = setInterval(refreshHealth, 8000)
    return () => clearInterval(id)
  }, [refreshHealth])

  const send = useCallback(async (text) => {
    const message = text.trim()
    if (!message) return null
    setMessages((m) => [...m, { role: 'user', text: message }])
    setThinking(true)
    try {
      const r = await fetch(`${BRAIN_API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, thread_id: threadRef.current }),
      })
      const data = await r.json().catch(() => ({}))
      if (!r.ok || !data.answer) {
        throw new Error(data.error || (r.status >= 500
          ? 'my brain server is restarting or not running — try again in a few seconds.'
          : `HTTP ${r.status}`))
      }
      setMessages((m) => [...m, { role: 'assistant', text: data.answer, sources: data.sources, tools: data.tools }])
      if (data.scene) setScene(data.scene)
      return data
    } catch (e) {
      const offline = e instanceof TypeError
      setMessages((m) => [...m, {
        role: 'assistant', error: true,
        text: offline
          ? 'My brain server is not running. Start it with `venv\\Scripts\\python server\\brain_server.py`.'
          : `Something went wrong: ${e.message}`,
      }])
      return null
    } finally {
      setThinking(false)
    }
  }, [])

  const learn = useCallback(async (file, module = 'inbox') => {
    const form = new FormData()
    form.append('file', file)
    form.append('module', module)
    setMessages((m) => [...m, { role: 'system', text: `Learning **${file.name}** into *${module}*…` }])
    try {
      const r = await fetch(`${BRAIN_API}/learn`, { method: 'POST', body: form })
      const data = await r.json()
      if (!r.ok) throw new Error(data.error)
      setMessages((m) => [...m, { role: 'system', text: `Learned **${data.file}**: ${data.added} new knowledge chunks in *${data.module}*.` }])
      refreshHealth()
    } catch (e) {
      setMessages((m) => [...m, { role: 'system', error: true, text: `Could not learn ${file.name}: ${e.message}` }])
    }
  }, [refreshHealth])

  const newChat = useCallback(() => {
    threadRef.current = `t-${Date.now()}`
    save(THREAD_KEY, threadRef.current)
    setMessages([])
    setScene('studio')
  }, [])

  return { messages, thinking, scene, setScene, health, send, learn, newChat }
}
