export interface TeamDescription {
  name: string;
  description: string;
  department: string;
  daily_processes: string[];
  relevant_laws_or_topics: string;
}

export interface CompanyConfig {
  company_description: string | null;
  teams: TeamDescription[];
}
