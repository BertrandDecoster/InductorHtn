import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend port: 5000 collides with macOS AirPlay Receiver, so default to 5001.
// start_gui.py exports INDHTN_GUI_BACKEND_PORT so the proxy stays in sync.
const backendPort = process.env.INDHTN_GUI_BACKEND_PORT || '5001'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true
      }
    }
  },
  test: {
    environment: 'jsdom',
    globals: true
  }
})
