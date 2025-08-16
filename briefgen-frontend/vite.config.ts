import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // optional proxy if you want same-origin during dev:
      // '/api': 'http://127.0.0.1:8000',
      // '/agent': 'http://127.0.0.1:8000',
      // '/export': 'http://127.0.0.1:8000',
    }
  }
})