import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({mode}) => {
  const isProd = mode === 'production'
  return {
    base: isProd ? '/' : '/v2/dashboard/',
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
          changeOrigin: true,
          bypass: (req) => {
            // Let React handle /v2/dashboard and its subpaths
            if (req.url?.startsWith('/v2/dashboard')) {
              return req.url
            }
          }
        }
      }
    },
  }
}
)
