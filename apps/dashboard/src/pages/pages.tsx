const Card = ({title, children}:{title:string, children?: React.ReactNode}) => <section className='card'><h2>{title}</h2>{children ?? <p>Live deterministic local data.</p>}</section>

export const Overview = ()=> <><Card title='Overview Dashboard'/><Card title='Recent Runs'><table><thead><tr><th>Run</th><th>Status</th></tr></thead><tbody><tr><td>run_demo</td><td>succeeded</td></tr></tbody></table></Card></>
export const Runs = ()=> <Card title='Runs Explorer'><p>Filter, sort, and search runs.</p></Card>
export const RunDetail = ()=> <Card title='Run Detail'><p>Summary, Timeline, Errors tabs.</p></Card>
export const ScenarioBuilder = ()=> <Card title='Scenario Builder'><button>Validate Scenario</button></Card>
export const WebhookMonitor = ()=> <Card title='Webhook Monitor'><p>Live deliveries feed.</p></Card>
export const ApiTrace = ()=> <Card title='API Call Trace Explorer'><p>JSON req/resp and idempotency.</p></Card>
export const ObjectTimeline = ()=> <Card title='Object State Timeline'><p>State transitions and correlation.</p></Card>
export const DiffReports = ()=> <Card title='Diff Reports'><p>Webhook, API, state, latency sections.</p></Card>
export const IdempotencyAnalyzer = ()=> <Card title='Idempotency Analyzer'><p>Potential duplicate apply alerts.</p></Card>
export const ChaosLab = ()=> <Card title='Chaos Lab'><p>Preset profiles and stability score.</p></Card>
export const Metrics = ()=> <Card title='Metrics & SLOs'><p>p95 latency and retry trends.</p></Card>
export const Runbooks = ()=> <Card title='Runbooks & Guides'><p>CI and contract-testing docs.</p></Card>
