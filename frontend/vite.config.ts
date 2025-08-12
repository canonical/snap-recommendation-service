import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, '../snaprecommend/static'),
    emptyOutDir: true,
    assetsDir: '',
  }, 
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
