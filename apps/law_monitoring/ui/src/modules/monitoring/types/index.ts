export * from './dashboardTypes';

export enum Category {
  OPEN = 'OPEN',
  RELEVANT = 'RELEVANT',
  NOT_RELEVANT = 'NOT_RELEVANT',
}

export enum AiClassification {
  LIKELY_RELEVANT = 'LIKELY_RELEVANT',
  LIKELY_IRRELEVANT = 'LIKELY_IRRELEVANT',
}

export enum DocumentTypeLabel {
  DIRECTIVE = 'Directive',
  REGULATION = 'Regulation',
  JUDICIAL_INFORMATION = 'Judicial information',
  DECISION = 'Decision',
  ANNOUNCEMENT = 'Announcements',
  RATE = 'Exchange rate',
  NOTICE = 'Notice',
  CORRIGENDUM = 'Corrigendum',
  IMPLEMENTING_DECISION = 'Implementing decision',
  IMPLEMENTING_REGULATION = 'Implementing regulation',
  SUMMARY = 'Summary',
  OTHER = 'Other',
  UNKNOWN = 'Unknown',
}

export enum OfficialJournalSeries {
  L_SERIES = 'L-Series', // Legislation - legally binding acts
  C_SERIES = 'C-Series', // Communication - non-binding documents
  UNKNOWN = 'Unknown',
}

export type Citation = {
  chunk: DocumentChunk;
  factfulness: {
    is_factual: boolean;
    local_reasoning: string;
  };
};

export type TeamRelevancyClassification = {
  team_name: string;
  is_relevant: boolean; // Global relevancy - overall team relevancy for the legal act
  reasoning: string; // Global reasoning - overall explanation connecting legal act to team
  citations?: Citation[]; // Local chunk-level evidence with local reasoning
  error?: string | null; // Optional error information from backend
};

export type DocumentChunk = {
  content?: string;
  start_pos?: number;
  end_pos?: number;
};

export type DocumentChunksGroup = {
  chunks: DocumentChunk[];
  concatenation_of_chunk_contents: string;
  start_pos_first_chunk?: number;
  end_pos_last_chunk?: number;
};

export type PreprocessedLaw = {
  title: string;
  expression_url: string;
  pdf_url: string;
  publication_date: string; // ISO datetime string from backend
  discovered_at: string; // ISO datetime string from backend
  law_file_id: string;
  status: 'RAW' | 'PROCESSING' | 'PROCESSED' | 'FAILED';
  subject_matter_text: string | null; // Contains subject matter summary extracted from JSON reports for PROCESSED laws
  eurovoc_labels: string[] | null;
  document_date: string | null; // ISO datetime string
  effect_date: string | null; // ISO datetime string
  end_validity_date: string | null; // ISO datetime string
  notification_date: string | null; // ISO datetime string
  // Document type identification fields
  document_type: string | null; // Document type URI (directive, regulation, etc.)
  document_type_label: DocumentTypeLabel | null; // Human-readable document type label
  oj_series_label: OfficialJournalSeries | null; // Official Journal series (L=Legislation, C=Communication)
  category: Category; // User's categorization of the law
  team_relevancy_classification: TeamRelevancyClassification[];
  law_text?: string;
};

export interface Pagination {
  total_items?: number | null;
}

export interface PreprocessedLawsWithPagination {
  law_data: PreprocessedLaw[];
  pagination: Pagination;
}

export enum SearchType {
  TITLE = 'title',
  EUROVOC = 'eurovoc',
  DOCUMENT_TYPE = 'document_type',
  JOURNAL_SERIES = 'journal_series',
  DEPARTMENT = 'department',
}

export type FilterFunction<T> = (laws: PreprocessedLaw[], filterValue: T) => PreprocessedLaw[];

export type DateRange = [Date, Date];

export enum ExportScope {
  AllHits = 'all_hits',
  AllEvaluated = 'all_evaluated',
}

export interface FilterConfig {
  categoryFilter: 'ALL' | Category;
  aiClassificationFilter: 'ALL' | AiClassification;
  shouldSort: boolean;
}

export enum MonitoringTab {
  DASHBOARD = 'dashboard',
  LIST = 'list',
}
