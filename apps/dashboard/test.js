import test from 'node:test'
import assert from 'node:assert/strict'
import { pages, renderPage } from './app.js'

test('has 12 pages', () => {
  assert.equal(pages.length, 12)
})

test('render each page', () => {
  for (const page of pages){
    assert.match(renderPage(page), new RegExp(page))
  }
})
