import test from 'node:test'
import assert from 'node:assert/strict'
import { buildFindingsDrawer, filterRuns, pages, renderPage, validateScenario } from './app.js'

test('has 12 pages', () => {
  assert.equal(pages.length, 12)
})

test('render each page', () => {
  for (const page of pages){
    assert.match(renderPage(page.route), new RegExp(page.title))
  }
})

test('scenario builder validation', () => {
  const bad = validateScenario({ name: 'x', target_url: 'ftp://bad', chaos_profile: { duplicates: 2 } })
  assert.ok(bad.length >= 3)
  const good = validateScenario({ name: 'Valid Name', target_url: 'http://localhost', chaos_profile: { duplicates: 0.2 } })
  assert.equal(good.length, 0)
})

test('run list filters', () => {
  const runs = [
    { id: 'run_1', status: 'completed' },
    { id: 'run_2', status: 'failed' }
  ]
  assert.equal(filterRuns(runs, 'failed').length, 1)
})

test('findings drawer content', () => {
  const drawer = buildFindingsDrawer([
    { severity: 'high', category: 'idempotency', summary: 'duplicate charge' },
    { severity: 'low', category: 'order', summary: 'stale version' }
  ], 'idempotency')
  assert.equal(drawer.rows.length, 1)
  assert.match(drawer.rows[0], /duplicate charge/)
})
