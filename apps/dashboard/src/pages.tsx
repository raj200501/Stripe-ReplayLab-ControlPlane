import { useMemo, useState } from 'react'
import { api } from './lib/api'
import { useFetch } from './hooks/useFetch'

export function OverviewPage() {
  const { data, loading } = useFetch(api.runs, [])
  const total = data?.length ?? 0
  return <section><h2>Overview</h2>{loading ? 'Loading' : <p>Runs today: {total}</p>}</section>
}

export function ScenarioLibraryPage() {
  const { data, loading } = useFetch(api.scenarios, [])
  return <section><h2>Scenario Library</h2>{loading ? 'Loading' : (data ?? []).map((s) => <div key={s.id}>{s.name}</div>)}</section>
}

export function ScenarioBuilderPage() {
  const [name, setName] = useState('')
  const [target, setTarget] = useState('http://127.0.0.1:9000/webhook')
  const valid = name.length >= 3 && target.startsWith('http')
  return <section><h2>Scenario Builder</h2><input aria-label="name" value={name} onChange={(e) => setName(e.target.value)} /><input aria-label="target" value={target} onChange={(e) => setTarget(e.target.value)} /><p>{valid ? 'valid' : 'invalid'}</p></section>
}

export function RunExplorerPage() {
  const { data } = useFetch(api.runs, [])
  const [query, setQuery] = useState('')
  const filtered = useMemo(() => (data ?? []).filter((run) => run.id.includes(query) || run.status.includes(query)), [data, query])
  return <section><h2>Run Explorer</h2><input aria-label="filter" value={query} onChange={(e) => setQuery(e.target.value)} />{filtered.map((run) => <div key={run.id}>{run.id}:{run.status}</div>)}</section>
}

export function RunDetailPage() {
  const { data } = useFetch(async () => {
    const runs = await api.runs()
    if (runs.length === 0) return []
    return api.deliveries(runs[0].id)
  }, [])
  return <section><h2>Run Detail</h2>{(data ?? []).map((d) => <div key={d.id}>{d.event_type} #{d.attempt_no}</div>)}</section>
}

export function LiveReplayPage() { return <section><h2>Live Replay</h2><p>SSE stream visible during runs</p></section> }
export function FindingsPage() { return <section><h2>Findings</h2><p>Severity grouped diagnostics</p></section> }
export function DiffViewerPage() { return <section><h2>Diff Viewer</h2><p>Expected vs actual comparison</p></section> }
export function MerchantSandboxPage() { return <section><h2>Merchant Sandbox</h2><p>State tables and bug toggles</p></section> }
export function SettingsPage() { return <section><h2>Settings</h2><p>Signing secret and import/export controls</p></section> }
