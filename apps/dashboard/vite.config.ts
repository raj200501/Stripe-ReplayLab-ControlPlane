import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    coverage: {
      reporter: ['text', 'html'],
      thresholds: {
        lines: 80,
        statements: 80,
        functions: 70,
        branches: 60
      }
    }
  }
})
