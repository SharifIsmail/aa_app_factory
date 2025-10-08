import type {
  LegalActTimelineResponse,
  LegalActOverviewResponse,
  DepartmentsOverviewResponse,
  EurovocOverviewResponse,
  OfficialJournalSeries,
} from '@/modules/monitoring/types';
import type { Http } from '@aleph-alpha/lib-http';

export class DashboardService {
  constructor(readonly httpClient: Http) {}

  /**
   * Fetch legal act timeline data for a given date range and optional journal series filter
   * @param startDate Start date in YYYY-MM-DD format
   * @param endDate End date in YYYY-MM-DD format
   * @param journalSeries Optional journal series filter
   * @returns Promise with timeline data
   */
  async getLegalActTimeline(
    startDate: string,
    endDate: string,
    journalSeries?: OfficialJournalSeries
  ): Promise<LegalActTimelineResponse> {
    const params: Record<string, string> = {
      start_date: startDate,
      end_date: endDate,
    };

    if (journalSeries) {
      params.journal_series = journalSeries;
    }

    const response = await this.httpClient.get<LegalActTimelineResponse>(
      'dashboard/legal-act-timeline',
      { params }
    );
    return response.data;
  }

  /**
   * Fetch legal act overview data for a given date range and optional journal series filter
   * @param startDate Start date in YYYY-MM-DD format
   * @param endDate End date in YYYY-MM-DD format
   * @param journalSeries Optional journal series filter
   * @returns Promise with overview data
   */
  async getLegalActOverview(
    startDate?: string,
    endDate?: string,
    journalSeries?: OfficialJournalSeries
  ): Promise<LegalActOverviewResponse> {
    const params: Record<string, string> = {};

    if (startDate && endDate) {
      params.start_date = startDate;
      params.end_date = endDate;
    }

    if (journalSeries) {
      params.journal_series = journalSeries;
    }

    const response = await this.httpClient.get<LegalActOverviewResponse>(
      'dashboard/classification-overview',
      Object.keys(params).length > 0 ? { params } : {}
    );
    return response.data;
  }

  /**
   * Fetch departments overview data for a given date range and optional journal series filter
   * @param startDate Start date in YYYY-MM-DD format
   * @param endDate End date in YYYY-MM-DD format
   * @param journalSeries Optional journal series filter
   * @returns Promise with departments overview data
   */
  async getDepartmentsOverview(
    startDate?: string,
    endDate?: string,
    journalSeries?: OfficialJournalSeries
  ): Promise<DepartmentsOverviewResponse> {
    const params: Record<string, string> = {};

    if (startDate && endDate) {
      params.start_date = startDate;
      params.end_date = endDate;
    }

    if (journalSeries) {
      params.journal_series = journalSeries;
    }

    const response = await this.httpClient.get<DepartmentsOverviewResponse>(
      'dashboard/departments-overview',
      Object.keys(params).length > 0 ? { params } : {}
    );
    return response.data;
  }

  /**
   * Fetch EuroVoc descriptors overview data for a given date range and optional journal series filter
   * @param startDate Start date in YYYY-MM-DD format
   * @param endDate End date in YYYY-MM-DD format
   * @param journalSeries Optional journal series filter
   * @returns Promise with EuroVoc descriptors overview data
   */
  async getEurovocOverview(
    startDate?: string,
    endDate?: string,
    journalSeries?: OfficialJournalSeries
  ): Promise<EurovocOverviewResponse> {
    const params: Record<string, string> = {};

    if (startDate && endDate) {
      params.start_date = startDate;
      params.end_date = endDate;
    }

    if (journalSeries) {
      params.journal_series = journalSeries;
    }

    const response = await this.httpClient.get<EurovocOverviewResponse>(
      'dashboard/eurovoc-overview',
      Object.keys(params).length > 0 ? { params } : {}
    );
    return response.data;
  }
}
