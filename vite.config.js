import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The browser only talks to Vite; Vite forwards to the local Python servers.
//   /api/*  → brain server (LangGraph agent, knowledge base)   :5060
//   /tts/*  → voice server (Edge neural TTS / Piper)           :5050
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5060',
      '/tts': { target: 'http://127.0.0.1:5050', rewrite: (p) => p.replace(/^\/tts/, '/api') },
    },
  },
})
