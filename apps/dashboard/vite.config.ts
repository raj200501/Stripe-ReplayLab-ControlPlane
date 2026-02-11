import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './src/testSetup.ts',
    coverage: {
      provider: 'v8',
      thresholds: { lines: 80, functions: 80, statements: 80, branches: 70 }
    }
  }
})
