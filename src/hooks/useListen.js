import { useCallback, useRef, useState } from 'react'

/**
 * Browser speech-to-text (Web Speech API — works in Chrome and Edge).
 * Calls onFinal(text) once the user stops speaking.
 */
export default function useListen({ onFinal, lang = 'en-IN' } = {}) {
  const [listening, setListening] = useState(false)
  const [interim, setInterim] = useState('')
  const recRef = useRef(null)
  const Recognition = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)

  const stop = useCallback(() => {
    recRef.current?.stop()
  }, [])

  const start = useCallback(() => {
    if (!Recognition) return false
    const rec = new Recognition()
    rec.lang = lang
    rec.interimResults = true
    rec.continuous = false
    let finalText = ''
    rec.onresult = (e) => {
      let live = ''
      for (const r of e.results) {
        if (r.isFinal) finalText = r[0].transcript
        else live += r[0].transcript
      }
      setInterim(finalText || live)
    }
    rec.onend = () => {
      setListening(false)
      setInterim('')
      if (finalText.trim()) onFinal?.(finalText.trim())
    }
    rec.onerror = () => setListening(false)
    recRef.current = rec
    rec.start()
    setListening(true)
    return true
  }, [Recognition, lang, onFinal])

  return { listening, interim, start, stop, supported: !!Recognition }
}
