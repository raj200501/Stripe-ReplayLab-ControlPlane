export const pages = [
  'Overview Dashboard','Runs Explorer','Run Detail','Scenario Builder','Webhook Monitor','API Call Trace Explorer','Object State Timeline','Diff Reports','Idempotency Analyzer','Chaos Lab','Metrics & SLOs','Runbooks & Guides'
]

export function renderPage(name){
  if(!pages.includes(name)) throw new Error('Unknown page')
  return `<section><h1>${name}</h1><p>loading / empty / error states included</p></section>`
}
