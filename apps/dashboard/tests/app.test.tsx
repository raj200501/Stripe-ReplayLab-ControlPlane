import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { AppShell } from '../src/AppShell'

vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
  const path = String(input)
  if (path.includes('/api/runs/run_1/deliveries')) {
    return new Response(JSON.stringify([{ id: 'd_1', event_type: 'payment_intent.succeeded', attempt_no: 1 }]))
  }
  if (path.includes('/api/runs')) {
    return new Response(JSON.stringify([{ id: 'run_1', status: 'completed', scenario_id: 's1', started_at: '', finished_at: '', seed: 1 }]))
  }
  if (path.includes('/api/scenarios')) {
    return new Response(JSON.stringify([{ id: 's1', name: 'Scenario One', description: '', seed: 1, target_url: '', chaos_profile: {}, expected_invariants: {} }]))
  }
  return new Response(JSON.stringify([]))
}) as unknown as typeof fetch)

describe('routing works', () => {
  it('renders overview by default', () => {
    render(<MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>)
    expect(screen.getByText('Overview')).toBeInTheDocument()
  })

  it('scenario builder validation toggles', () => {
    render(<MemoryRouter initialEntries={['/scenario-builder']}><AppShell /></MemoryRouter>)
    expect(screen.getByText('invalid')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('name'), { target: { value: 'Valid Scenario' } })
    expect(screen.getByText('valid')).toBeInTheDocument()
  })

  it('run explorer renders and filters', async () => {
    render(<MemoryRouter initialEntries={['/run-explorer']}><AppShell /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText(/run_1/)).toBeInTheDocument())
    fireEvent.change(screen.getByLabelText('filter'), { target: { value: 'completed' } })
    expect(screen.getByText(/completed/)).toBeInTheDocument()
  })

  it('run detail renders deliveries', async () => {
    render(<MemoryRouter initialEntries={['/run-detail']}><AppShell /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText(/payment_intent.succeeded/)).toBeInTheDocument())
  })

  it('command palette opens', () => {
    render(<MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>)
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    expect(screen.getByTestId('command-palette')).toBeInTheDocument()
  })
})
