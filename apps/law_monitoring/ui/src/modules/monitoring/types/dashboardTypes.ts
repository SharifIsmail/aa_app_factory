export interface HumanDecisionCounts {
  relevant?: number;
  not_relevant?: number;
  awaiting_decision?: number;
}

export interface AIClassificationCounts {
  likely_relevant?: number;
  likely_not_relevant?: number;
}

export interface ClassificationOverviewMetrics {
  recall?: number;
}

export interface LegalActTimeline {
  date?: string; // ISO datetime string
  human_decision?: HumanDecisionCounts;
  legal_acts?: number;
}

export interface LegalActTimelineResponse {
  total_legal_acts?: number;
  legal_acts?: LegalActTimeline[];
}

export interface LegalActOverviewResponse {
  total_acts?: number;
  total_evaluations?: number;
  ai_classification?: AIClassificationCounts;
  human_decision?: HumanDecisionCounts;
  metrics?: ClassificationOverviewMetrics;
}

export interface DepartmentRelevanceCount {
  department: string;
  relevant_acts: number;
}

export interface DepartmentsOverviewResponse {
  total_relevant_acts: number;
  departments: DepartmentRelevanceCount[];
}

export interface EurovocDescriptorCount {
  descriptor: string;
  frequency: number;
}

export interface EurovocOverviewResponse {
  total_descriptors: number;
  descriptors: EurovocDescriptorCount[];
}
