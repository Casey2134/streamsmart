import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react' // or vue

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Catch any request starting with /api
      '/api': {
        target: 'http://backend:8000', // CHANGE THIS to your backend port
        changeOrigin: true,
        secure: false,
      },
    },
  },
})