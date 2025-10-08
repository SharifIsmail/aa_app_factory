// Base API Response Types
export interface ExecutionConfig {
  project: string
  benchmark: string
  execution: string
}

// Studio Lineage Types
export interface TaskSpan {
  span_id: string
  parent_span_id?: string
  name: string
  start_time: string
  end_time?: string
  status: 'completed' | 'failed' | 'running'
  attributes: Record<string, any>
  events: Array<{
    timestamp: string
    name: string
    attributes: Record<string, any>
  }>
}

export interface Lineage {
  id: string
  created_at: string
  created_by: string
  benchmark_execution_id: string
  example_id: string
  trace_id: string
  task_spans: TaskSpan[]
  input: any
  expected_output: any
  output: any
  evaluation?: any
  run_latency: number
  run_tokens: number
  metadata: Record<string, any>
}

export interface LineagesResponse {
  total: number
  page: number
  size: number
  num_pages: number
  items: Lineage[]
}

// Law Relevancy Specific Types (extracted from task outputs)
export interface DocumentChunk {
  chunk_type: string;
  content: string;
  section_number?: string;
  subsection_number?: string;
  paragraph_number?: string;
  title?: string;
  level: number;
  start_pos: number;
  end_pos: number;
  metadata?: Record<string, any>;
}

export interface DocumentChunksGroup {
  chunks: DocumentChunk[];
  concatenation_of_chunk_contents: string;
  start_pos_first_chunk?: number;
  end_pos_last_chunk?: number;
}

export interface ChunkRelevancy {
  chunk: string | DocumentChunk | DocumentChunksGroup
  relevancy: {
    is_relevant: boolean
    reasoning: string
  }
}

export interface TeamRelevancy {
  team_id?: string
  team_name: string
  is_relevant: boolean
  relevancy_score?: number
  reasoning: string
  error?: string
  chunk_relevancies?: ChunkRelevancy[]
}

export interface LawRelevancyInput {
  law_text: string
  law_title: string
  metadata: {
    expression_url: string
    law_id?: string
    [key: string]: any
  }
}

export interface LawRelevancyOutput {
  team_relevancies: TeamRelevancy[]
  subject_matter_summary?: string
}

export interface LawRelevancyEvaluation {
  accuracy?: number
  precision?: number
  recall?: number
  f1_score?: number
  accuracy_score?: number
  overall_f1_score?: number
  is_correct?: boolean
}

export interface LawRelevancyExecutionItem {
  id: string
  input?: LawRelevancyInput
  output: LawRelevancyOutput
  evaluation: LawRelevancyEvaluation
  expected_output?: LawRelevancyOutput
  latency: number
  tokens: number
  run_latency?: number
  run_tokens?: number
  created_at?: string
  created_by?: string
}

// Classification metrics for evaluation
export interface ClassificationMetrics {
  is_true_positive: boolean
  is_false_positive: boolean
  is_true_negative: boolean
  is_false_negative: boolean
  expected_relevant: boolean
  actual_relevant: boolean
}

// Processed lineage for display
export interface ProcessedLineage extends Lineage {
  parsed_input?: LawRelevancyInput
  parsed_output?: LawRelevancyOutput
  parsed_expected_output?: LawRelevancyOutput
  law_title?: string
  team_relevancies?: TeamRelevancy[]
  classification_metrics?: ClassificationMetrics
}

// Comparison Types
export interface TeamComparisonResult {
  team_id: string
  team_name: string
  expected_relevant: boolean
  actual_relevant: boolean
  expected_score: number
  actual_score: number
  expected_reasoning: string
  actual_reasoning: string
  matches: boolean
  score_difference: number
}

export interface LawComparisonItem {
  lawId: string
  lawTitle: string
  input: LawRelevancyInput
  expectedOutput: LawRelevancyOutput
  execution1: {
    id: string
    output: LawRelevancyOutput
    evaluation: LawRelevancyEvaluation
    latency: number
    tokens: number
  }
  execution2: {
    id: string
    output: LawRelevancyOutput
    evaluation: LawRelevancyEvaluation
    latency: number
    tokens: number
  }
  teamComparisons: TeamComparisonResult[]
}
