import { readFileSync } from 'node:fs'
const source = readFileSync(new URL('../app.js', import.meta.url), 'utf8')
if (!source.includes('pages')) {
  console.error('expected pages export')
  process.exit(1)
}
console.log('lint ok')
