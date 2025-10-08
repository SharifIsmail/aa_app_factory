type ApiTaskStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';

export type AgentResponse = string | { data?: string };

export interface StartResearchAgentRequest {
  query: string;
  execution_id?: string;
  flow_name?: string;
  params?: object;
}

export interface ResearchAgentResponse {
  id: string;
  status: 'OK' | 'ERROR';
}

export interface QuickActionFilterRequest {
  flow_name: string;
  filter_params: Record<string, any>;
}

export interface QuickActionFilterResponse<T = any> {
  success: boolean;
  data: T[];
  error?: string;
}

// Specific types for summarize business partner quick action
export interface PartnerData {
  id: string;
  name: string;
}

export type SummarizeBusinessPartnerFilterResponse = QuickActionFilterResponse<PartnerData>;

export interface Task {
  key: string;
  description: string;
  status: ApiTaskStatus;
  subtasks?: Task[];
}

export interface ToolLog {
  timestamp: string;
  level: 'INFO' | 'ERROR' | 'WARNING' | 'DEBUG';
  result: string;
  tool_name?: string;
}

export interface ExplainedStep {
  executed_code?: string;
  execution_log?: string;
  code_output?: string;
  explanation?: string;
  time_start?: number;
  time_end?: number;
  agent_name?: string;
}

export interface SerializedDataFrame {
  data: { index: (string | number)[] | (string | number)[][]; columns: string[]; data: any[][] };
  type: 'DataFrame';
  dtypes: Record<string, string>;
  index_names?: string[];
}

export interface SerializedSeries {
  data: { name?: string; index: (string | number)[]; data: any[] };
  type: 'Series';
  dtype: string;
  index_names?: string[];
}

export type SerializedPandasObject = SerializedDataFrame | SerializedSeries;

export interface ResearchStatusResponse {
  status: ApiTaskStatus;
  tasks: Task[];
  tool_logs: ToolLog[];
  explained_steps: ExplainedStep[];
  extracted_data?: Record<string, any>;
  final_result?: {
    agent_response?: AgentResponse;
  };
  pandas_objects_data?: Record<string, SerializedPandasObject>;
  results_data?: Record<string, any>;
  progress?: number;
}
