import { useRef, useCallback } from 'react'

const TTS_API = '/tts/speak'

/**
 * useSpeech hook
 * 
 * Sends text to our local in-memory Piper TTS server, plays the returned WAV audio,
 * and provides a real-time volume level (0-1) via an onVolumeChange callback
 * that drives the jaw/mouth animation on the 3D character.
 */
export default function useSpeech({ onVolumeChange } = {}) {
  const audioCtxRef = useRef(null)
  const analyserRef = useRef(null)
  const sourceRef = useRef(null)
  const rafRef = useRef(null)
  const isSpeakingRef = useRef(false)

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext
      audioCtxRef.current = new AudioContextClass()
      analyserRef.current = audioCtxRef.current.createAnalyser()
      analyserRef.current.fftSize = 256
      analyserRef.current.smoothingTimeConstant = 0.75
    }
    if (audioCtxRef.current.state === 'suspended') {
      audioCtxRef.current.resume()
    }
    return audioCtxRef.current
  }, [])

  // Continuously read volume from the analyser and call onVolumeChange
  const startVolumeTracking = useCallback(() => {
    if (!analyserRef.current || !onVolumeChange) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)

    const tick = () => {
      if (!analyserRef.current) return
      analyserRef.current.getByteFrequencyData(dataArray)
      // Calculate average volume (0-255) and normalize to 0-1
      const sum = dataArray.reduce((a, b) => a + b, 0)
      const avg = sum / dataArray.length
      const normalizedVolume = Math.min(avg / 100, 1)
      onVolumeChange(normalizedVolume)
      rafRef.current = requestAnimationFrame(tick)
    }

    tick()
  }, [onVolumeChange])

  const stopVolumeTracking = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    if (onVolumeChange) {
      onVolumeChange(0) // Reset jaw to closed
    }
  }, [onVolumeChange])

  const speak = useCallback(async (text) => {
    if (!text || !text.trim()) return

    // Allow interrupting prior speech for immediate response
    if (sourceRef.current) {
      try { sourceRef.current.stop() } catch (_) {}
      sourceRef.current = null
    }

    isSpeakingRef.current = true

    try {
      const ctx = getAudioContext()
      if (ctx.state === 'suspended') {
        await ctx.resume()
      }

      const response = await fetch(TTS_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim() }),
      })

      if (!response.ok) {
        console.error('TTS server returned error:', response.status)
        isSpeakingRef.current = false
        stopVolumeTracking()
        return
      }

      const audioData = await response.arrayBuffer()
      const audioBuffer = await ctx.decodeAudioData(audioData)

      // Double-check if another speak call interrupted while decoding
      if (sourceRef.current) {
        try { sourceRef.current.stop() } catch (_) {}
      }

      const source = ctx.createBufferSource()
      source.buffer = audioBuffer
      source.connect(analyserRef.current)
      analyserRef.current.connect(ctx.destination)
      sourceRef.current = source

      source.onended = () => {
        isSpeakingRef.current = false
        stopVolumeTracking()
      }

      source.start(0)
      startVolumeTracking()
    } catch (err) {
      console.error('Speech playback failed:', err)
      isSpeakingRef.current = false
      stopVolumeTracking()
    }
  }, [getAudioContext, startVolumeTracking, stopVolumeTracking])

  const stop = useCallback(() => {
    if (sourceRef.current) {
      try { sourceRef.current.stop() } catch (_) {}
      sourceRef.current = null
    }
    isSpeakingRef.current = false
    stopVolumeTracking()
  }, [stopVolumeTracking])

  return { speak, stop, isSpeaking: isSpeakingRef }
}
