import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/upload': 'http://localhost:5001',
      '/integration-status': 'http://localhost:5001',
      '/create-integrations': 'http://localhost:5001'
    }
  }
})
