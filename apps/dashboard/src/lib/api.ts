import type { Delivery, Finding, Run, Scenario } from '../types'

const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init
  })
  if (!response.ok) throw new Error(`Request failed ${response.status}`)
  return (await response.json()) as T
}

export const api = {
  scenarios: () => request<Scenario[]>('/api/scenarios'),
  runs: () => request<Run[]>('/api/runs'),
  runDetail: (id: string) => request<Run>(`/api/runs/${id}`),
  deliveries: (runId: string) => request<Delivery[]>(`/api/runs/${runId}/deliveries`),
  findings: (runId: string) => request<Finding[]>(`/api/runs/${runId}/findings`),
  createScenario: (payload: Partial<Scenario>) =>
    request<Scenario>('/api/scenarios', { method: 'POST', body: JSON.stringify(payload) })
}
