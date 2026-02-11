export const pages = [
  { route: 'overview', title: 'Overview', description: 'KPIs and latest run health' },
  { route: 'scenario-library', title: 'Scenario Library', description: 'Search, duplicate, and manage scenarios' },
  { route: 'scenario-builder', title: 'Scenario Builder', description: 'Create deterministic chaos profiles with validation' },
  { route: 'run-explorer', title: 'Run Explorer', description: 'Filter and sort historical runs' },
  { route: 'run-detail', title: 'Run Detail', description: 'Delivery timelines and latency distribution' },
  { route: 'live-replay', title: 'Live Replay', description: 'Streaming live events from current run' },
  { route: 'findings', title: 'Findings', description: 'Severity and category grouped diagnostics' },
  { route: 'diff-viewer', title: 'Diff Viewer', description: 'Expected vs actual merchant state diff' },
  { route: 'merchant-sandbox', title: 'Merchant Sandbox', description: 'Inspect order/charge state and bug toggles' },
  { route: 'settings', title: 'Settings', description: 'Signing secret and import/export controls' },
  { route: 'integrations', title: 'Integrations', description: 'Merchant endpoint inventory and validation' },
  { route: 'audit-log', title: 'Audit Log', description: 'Chronological operations history for reproducibility' }
]

export function validateScenario(input) {
  const errors = []
  if (!input.name || input.name.length < 3) errors.push('name must be at least 3 chars')
  if (!String(input.target_url || '').startsWith('http')) errors.push('target_url must be http(s)')
  const duplicates = Number(input.chaos_profile?.duplicates ?? 0)
  if (duplicates < 0 || duplicates > 1) errors.push('duplicates must be between 0 and 1')
  return errors
}

export function filterRuns(runs, filter) {
  const q = String(filter || '').toLowerCase()
  return runs.filter((run) => run.id.toLowerCase().includes(q) || run.status.toLowerCase().includes(q))
}

export function buildFindingsDrawer(findings, category) {
  const selected = findings.filter((item) => !category || item.category === category)
  return {
    title: category ? `Findings: ${category}` : 'All Findings',
    rows: selected.map((item) => `${item.severity.toUpperCase()} - ${item.summary}`)
  }
}

export function renderPage(route, state = {}) {
  const page = pages.find((candidate) => candidate.route === route)
  if (!page) throw new Error('Unknown page')
  return `<section data-route="${route}"><h1>${page.title}</h1><p>${page.description}</p><pre>${JSON.stringify(state).slice(0, 200)}</pre></section>`
}
