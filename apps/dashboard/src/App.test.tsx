import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { App } from './App'

describe('routing and pages', () => {
  const routes = ['/', '/runs', '/run-detail', '/scenarios', '/webhooks', '/api-trace', '/objects', '/diffs', '/idempotency', '/chaos', '/metrics', '/runbooks']
  it.each(routes)('renders %s', (route) => {
    render(<MemoryRouter initialEntries={[route]}><App /></MemoryRouter>)
    expect(screen.getByText('ReplayLab')).toBeInTheDocument()
  })
})
