import type {
  PreprocessedLaw,
  OfficialJournalSeries,
  DocumentTypeLabel,
  PreprocessedLawsWithPagination,
} from '@/modules/monitoring/types';
import { ExportScope } from '@/modules/monitoring/types';
import type { Http } from '@aleph-alpha/lib-http';

export class PreprocessedLawService {
  constructor(readonly httpClient: Http) {}

  private buildDateQuery(startDate?: Date, endDate?: Date): string {
    const queryParams = new URLSearchParams();

    if (startDate) {
      queryParams.append('start_date', startDate.toISOString().split('T')[0]);
    }

    if (endDate) {
      queryParams.append('end_date', endDate.toISOString().split('T')[0]);
    }

    return queryParams.toString();
  }

  async getLawsWithPagination(
    startDate?: Date,
    endDate?: Date
  ): Promise<PreprocessedLawsWithPagination> {
    const query = this.buildDateQuery(startDate, endDate);
    const url = query ? `laws?${query}` : 'laws';
    const response = await this.httpClient.get<PreprocessedLawsWithPagination>(url);
    return response.data;
  }

  async getLaws(startDate?: Date, endDate?: Date): Promise<PreprocessedLawsWithPagination> {
    const data = await this.getLawsWithPagination(startDate, endDate);
    return data;
  }

  async getLawsByDateRange(
    startDate: Date,
    endDate: Date
  ): Promise<PreprocessedLawsWithPagination> {
    return this.getLaws(startDate, endDate);
  }

  // Get all dates that have laws
  async getAllDatesWithLaws(): Promise<string[]> {
    const response = await this.httpClient.get<string[]>('laws/dates');
    return response.data;
  }

  // Generic GET-based search helper
  private async searchLawsGeneric(
    endpoint: string,
    paramName: string,
    paramValue: string
  ): Promise<PreprocessedLaw[]> {
    const response = await this.httpClient.get<PreprocessedLaw[]>(`laws/${endpoint}`, {
      params: { [paramName]: paramValue },
    });
    return response.data;
  }

  // Search laws by title
  async searchLawsByTitle(title: string): Promise<PreprocessedLaw[]> {
    return this.searchLawsGeneric('title-search', 'title', title);
  }

  // Search laws by Eurovoc descriptors
  async searchLawsByEurovoc(eurovocDescriptors: string[]): Promise<PreprocessedLaw[]> {
    const response = await this.httpClient.post<PreprocessedLaw[]>('laws/eurovoc-search', {
      body: {
        eurovoc_descriptors: eurovocDescriptors,
      },
    });
    return response.data;
  }

  // Search laws by document type
  async searchLawsByDocumentType(documentType: DocumentTypeLabel): Promise<PreprocessedLaw[]> {
    return this.searchLawsGeneric('document-type-search', 'document_type', documentType);
  }

  // Search laws by journal series
  async searchLawsByJournalSeries(
    journalSeries: OfficialJournalSeries
  ): Promise<PreprocessedLaw[]> {
    return this.searchLawsGeneric('journal-series-search', 'journal_series', journalSeries);
  }

  // Search laws by department
  async searchLawsByDepartment(department: string): Promise<PreprocessedLaw[]> {
    return this.searchLawsGeneric('department-search', 'department', department);
  }

  // Get all available Eurovoc descriptors
  async getAllEurovocDescriptors(): Promise<string[]> {
    const response = await this.httpClient.get<string[]>('laws/eurovoc-descriptors');
    return response.data;
  }

  async downloadLawsCsv(
    category?: string,
    exportScope: ExportScope = ExportScope.AllHits,
    startDate?: Date,
    endDate?: Date
  ): Promise<string> {
    const scopeParam = exportScope;

    const params: Record<string, string> = {
      export_scope: scopeParam,
    };
    // Only include category when exporting 'all_hits'; default to RELEVANT
    if (scopeParam === ExportScope.AllHits) {
      params.category = category ?? 'RELEVANT';
    }

    if (startDate) {
      params.start_date = startDate.toISOString().split('T')[0];
    }

    if (endDate) {
      params.end_date = endDate.toISOString().split('T')[0];
    }

    const response = await this.httpClient.get<string>('laws/export-csv', {
      params,
    });

    return response.data;
  }
}
