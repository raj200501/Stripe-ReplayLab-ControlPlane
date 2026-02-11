import { renderPage, pages } from '../app.js'
for (const p of pages) {
  renderPage(p.route)
}
console.log(`build ok (${pages.length} pages rendered)`)
