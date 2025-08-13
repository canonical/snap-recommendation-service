import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/_status': 'http://127.0.0.1:5000',
      '/dashboard': 'http://127.0.0.1:5000',
      '/api': 'http://127.0.0.1:5000',
      '/login': 'http://127.0.0.1:5000'
    },
  },
})
