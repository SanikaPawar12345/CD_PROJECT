import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/ai-suggestions': 'http://localhost:8000',
      '/parse-tree-diff': 'http://localhost:8000',
      '/validate-syntax': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
      '/history': 'http://localhost:8000',
      '/grammars': 'http://localhost:8000',
      '/grammar-rules': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
