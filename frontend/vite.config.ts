import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(() => {
  return {
    base: '/',
    plugins: [react()],
    css: {
      preprocessorOptions: {
        scss: {}
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'static',
    },
    server: {
      host: '0.0.0.0',
      proxy: {
        '/': {
          target: 'http://web:5000', // Flask backend
          changeOrigin: false,
          bypass: (req) => {
            // Let Vite handle its own internal assets
            if (req.url?.startsWith('/@') || req.url?.startsWith('/src/') || req.url?.startsWith('/node_modules/') || req.url?.startsWith('/dashboard')) {
              return req.url
            }
          }
        }
      }
    },
  }
}
)
