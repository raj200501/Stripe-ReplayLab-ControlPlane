import { Link, Route, Routes } from 'react-router-dom'
import { Overview, Runs, RunDetail, ScenarioBuilder, WebhookMonitor, ApiTrace, ObjectTimeline, DiffReports, IdempotencyAnalyzer, ChaosLab, Metrics, Runbooks } from './pages/pages'

const nav = [
  ['/', 'Overview'], ['/runs', 'Runs Explorer'], ['/run-detail', 'Run Detail'], ['/scenarios', 'Scenario Builder'], ['/webhooks', 'Webhook Monitor'], ['/api-trace', 'API Call Trace Explorer'], ['/objects', 'Object State Timeline'], ['/diffs', 'Diff Reports'], ['/idempotency', 'Idempotency Analyzer'], ['/chaos', 'Chaos Lab'], ['/metrics', 'Metrics & SLOs'], ['/runbooks', 'Runbooks & Guides']
]

export function App(){
  return <div className='shell'><aside className='sidebar'><h3>ReplayLab</h3><nav className='nav'>{nav.map(([to,label])=><Link key={to} to={to}>{label}</Link>)}</nav></aside><main className='content'><Routes>
    <Route path='/' element={<Overview/>}/><Route path='/runs' element={<Runs/>}/><Route path='/run-detail' element={<RunDetail/>}/><Route path='/scenarios' element={<ScenarioBuilder/>}/><Route path='/webhooks' element={<WebhookMonitor/>}/><Route path='/api-trace' element={<ApiTrace/>}/><Route path='/objects' element={<ObjectTimeline/>}/><Route path='/diffs' element={<DiffReports/>}/><Route path='/idempotency' element={<IdempotencyAnalyzer/>}/><Route path='/chaos' element={<ChaosLab/>}/><Route path='/metrics' element={<Metrics/>}/><Route path='/runbooks' element={<Runbooks/>}/>
  </Routes></main></div>
}
