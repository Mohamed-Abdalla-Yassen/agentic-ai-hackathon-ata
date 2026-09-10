import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The FastAPI backend serves everything under /api (see docs/api-contract.md).
// Proxying in dev keeps the frontend origin-relative, so no CORS setup is needed.
const BACKEND = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND,
        changeOrigin: true,
      },
    },
  },
})
