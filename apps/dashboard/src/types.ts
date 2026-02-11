export type Scenario = {
  id: string
  name: string
  description: string
  seed: number
  target_url: string
  chaos_profile: Record<string, unknown>
  expected_invariants: Record<string, unknown>
}

export type Run = {
  id: string
  scenario_id: string
  status: string
  started_at: string
  finished_at: string | null
  seed: number
}

export type Delivery = {
  id: string
  event_type: string
  attempt_no: number
  result_status: number
  latency_ms: number
}

export type Finding = {
  id: string
  severity: string
  category: string
  summary: string
  suggested_fix: string
}
