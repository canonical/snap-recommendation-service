import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // build: {
  //   outDir: path.resolve(__dirname, '../snaprecommend/static'),
  //   emptyOutDir: true,
  //   rollupOptions: {
  //     input: path.resolve(__dirname, 'index.html'),
  //   }
  // }
  server: {
    host: '0.0.0.0',
    proxy: {
      '/_status': {
        target: 'http://127.0.0.1:5000',
      },
      '/dashboard': {
        target: 'http://127.0.0.1:5000',
      },
      '/api': {
        target: 'http://127.0.0.1:5000',
      },
      '/login': {
        target: 'http://127.0.0.1:5000',
      },
    },
  },
})
