export interface DatasetSummary {
  id: string
  name: string
  created_at: string
  source: string
  timezone: string
  synthetic: boolean
  notes: string | null
  generator_seed: number | null
  generator_cases: number | null
  row_count: number
  eligible_event_count: number
  case_count: number
}

export interface Meta {
  name: string
  version: string
  environment: string
  demo_banner: boolean
  demo_banner_text: string
  pm4py_available: boolean
  pm4py_message: string
  privacy_notice: string
  ordering_contract: string
  max_upload_bytes: number
  max_rows: number
  synthetic_case_min: number
  synthetic_case_max: number
}

export interface Job {
  id: string
  dataset_id: string | null
  kind: string
  status: "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED"
  error: string | null
  created_at: string | null
  started_at: string | null
  heartbeat_at: string | null
  finished_at: string | null
}

export interface FieldMapping {
  case_id: string | null
  activity: string | null
  timestamp: string | null
  resource: string | null
  role: string | null
  channel: string | null
  outcome: string | null
  cost: string | null
  job_family: string | null
}

export interface QualityReport {
  row_count: number
  eligible_event_count: number
  excluded_event_count: number
  unique_cases: number
  missing_case_id: number
  missing_activity: number
  missing_timestamp: number
  parse_failures: number
  ambiguous_timestamps: number
  nonexistent_timestamps: number
  duplicate_count: number
  invalid_cost_warnings: number
  exclusion_breakdown: Record<string, number>
  timezone: string
  timezone_warnings: string[]
  duplicate_rule: string
  privacy_notice: string
  eligible_definition: string
  issue_sample: Array<{
    source_row: number
    case_id: string | null
    activity: string | null
    raw_timestamp: string | null
    exclusion_reason: string | null
    warning: string | null
  }>
  dataset_id?: string
  name?: string
  synthetic?: boolean
}

export interface Preview {
  draft_id: string
  filename: string
  headers: string[]
  raw_sample: Array<Record<string, string | null>>
  suggested_mapping: FieldMapping
  applied_mapping: FieldMapping
  timezone_suggestion: string
  timezone: string
  synthetic: boolean
  row_count: number
  parsed_sample: Array<{
    source_row: number
    case_id: string | null
    activity: string | null
    raw_timestamp: string | null
    timestamp_utc: string | null
    exclusion_reason: string | null
    warning: string | null
  }>
  quality: QualityReport | null
  privacy_notice: string
}

export interface ProcessNode {
  id: string
  activity: string
  event_count: number
  case_count: number
}

export interface ProcessEdge {
  id: string
  source: string
  target: string
  frequency: number
  case_count: number
  case_ratio: number
  mean_delay_seconds: number | null
  median_delay_seconds: number | null
  p90_delay_seconds: number | null
  p95_delay_seconds: number | null
  delay_sample_size: number
}

export interface FilterImpact {
  cases_before: number
  cases_after: number
  cases_retained_ratio: number | null
  events_before: number
  events_after: number
  events_retained_ratio: number | null
  definition: string
  caution: string
}

export interface ProcessGraph {
  nodes: ProcessNode[]
  edges: ProcessEdge[]
  total_cases: number
  total_events: number
  min_case_ratio: number
  edges_before_filter: number
  edges_after_filter: number
  ordering: string
  delay_definition: string
  filter_impact?: FilterImpact
}

export interface InsightCard {
  id: string
  title: string
  statement: string
  numerator: number
  numerator_definition: string
  sample_size: number
  sample_size_definition: string
  value: number | null
  unit: string
  method: string
  caution: string
  source_activity: string | null
  target_activity: string | null
}

export interface Insights {
  ordering: string
  min_observations: number
  cards: InsightCard[]
}

export interface Performance {
  ordering: string
  total_cases: number
  completed_cases: number
  ongoing_cases: number
  excluded_negative_cycle_cases: number
  cycle_time: {
    sample_size: number
    sample_definition: string
    mean_seconds: number | null
    median_seconds: number | null
    p90_seconds: number | null
    p95_seconds: number | null
    method: string
  }
  transitions: Array<{
    source: string
    target: string
    frequency: number
    case_count: number
    mean_delay_seconds: number | null
    median_delay_seconds: number | null
    p90_delay_seconds: number | null
    p95_delay_seconds: number | null
    delay_sample_size: number
  }>
  active_aging: {
    as_of: string | null
    as_of_definition: string
    sample_size: number
    mean_seconds_since_last_event: number | null
    median_seconds_since_last_event: number | null
    p90_seconds_since_last_event: number | null
    p95_seconds_since_last_event: number | null
    mean_seconds_since_start: number | null
    median_seconds_since_start: number | null
    p90_seconds_since_start: number | null
    p95_seconds_since_start: number | null
    method: string
  }
  processing_time: null
  processing_time_reason: string
  filter_impact?: FilterImpact
}

export interface Funnel {
  ordering: string
  denominator: number
  denominator_definition: string
  counting: string
  stages: Array<{
    stage: string
    cases_reached: number
    share_of_denominator: number | null
    previous_stage: string | null
    cases_reached_previous: number | null
    drop_off_cases: number | null
    drop_off_definition: string | null
  }>
  exits: Array<{ activity: string; cases: number }>
}

export interface Variant {
  rank: number
  key: string
  activities: string[]
  case_count: number
  share: number | null
  sample_size: number
  completed_cases: number
  mean_cycle_seconds: number | null
  median_cycle_seconds: number | null
  p90_cycle_seconds: number | null
  p95_cycle_seconds: number | null
  cycle_sample_size: number
  outcomes: Record<string, number>
  event_length: number
}

export interface Variants {
  ordering: string
  total_cases: number
  variant_count: number
  shown: number
  variants: Variant[]
}

export interface VariantCompare {
  ordering: string
  a: Variant | null
  b: Variant | null
  same_activity_sequence: boolean
}

export interface Conformance {
  ordering: string
  method: string
  total_cases: number
  fitting_cases: number
  numerator: number
  numerator_definition: string
  sample_size: number
  sample_size_definition: string
  fit_rate: number | null
  deviations: Array<{
    source: string
    target: string
    frequency: number
    case_count: number
    example_case_ids: string[]
  }>
  allowed_transitions: Array<{ source: string; target: string }>
  pm4py: { available: boolean; used: boolean; feature: string; message: string }
}

export interface FilterOptions {
  channels: string[]
  job_families: string[]
  outcomes: string[]
  time_min: string | null
  time_max: string | null
  case_status: string[]
}

export interface CaseRow {
  case_id: string
  variant_key: string
  event_count: number
  outcome: string
  completed: boolean
  cycle_seconds: number | null
  start: string
  end: string
}

export interface CasePage {
  total: number
  limit: number
  offset: number
  cases: CaseRow[]
}

export interface CaseDetail {
  case_id: string
  outcome: string
  completed: boolean
  cycle_seconds: number | null
  events: Array<{
    source_row: number
    activity: string
    timestamp: string
    resource: string | null
    role: string | null
    channel: string | null
    outcome: string | null
    job_family: string | null
    cost: number | null
  }>
}

export interface Rework {
  total_cases: number
  cases_with_any_repeat: number
  activities: Array<{
    activity: string
    cases_with_repeat: number
    numerator: number
    sample_size: number
    self_loop_frequency: number
    example_case_ids: string[]
    method: string
  }>
}

export interface Methodology {
  ordering_contract: string
  sections: Array<{ id: string; title: string; body: string }>
}

export interface Filters {
  case_status: "all" | "completed" | "ongoing"
  channel: string
  job_family: string
  outcome: string
}

export const EMPTY_MAPPING: FieldMapping = {
  case_id: null,
  activity: null,
  timestamp: null,
  resource: null,
  role: null,
  channel: null,
  outcome: null,
  cost: null,
  job_family: null,
}
