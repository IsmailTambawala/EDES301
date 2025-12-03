import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { API_BASE_URL } from './src/config.js'

const websocketTarget = API_BASE_URL.replace(/^http/i, 'ws')

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ws': {
        target: websocketTarget,
        ws: true
      }
    }
  }
})

