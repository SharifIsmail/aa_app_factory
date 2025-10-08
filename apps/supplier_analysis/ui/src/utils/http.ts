import { type Http, http } from '@aleph-alpha/lib-http';
import { z } from 'zod';

export const HTTP_CLIENT = http({
  timeout: 60_000,
  baseURL: '',
});

export const QUOTE_RESPONSE_SCHEMA = z.object({
  quote: z.string(),
});

export type QuoteResponse = z.infer<typeof QUOTE_RESPONSE_SCHEMA>;

export class QuoteService {
  constructor(readonly httpClient: Http) {}

  async createQuote(): Promise<QuoteResponse> {
    return (await this.httpClient.post<QuoteResponse>('quote', { body: {} })).data;
  }
}

export class CompanyDataService {
  constructor(readonly httpClient: Http) {}

  async searchCompanyData(
    companyName: string,
    countryId: string,
    researchType: string = 'comprehensive'
  ): Promise<any> {
    return (
      await this.httpClient.post<any>('company-data-search', {
        body: {
          company_name: companyName,
          country_id: countryId,
          research_type: researchType,
        },
      })
    ).data;
  }

  async researchCompanyRisks(
    companyName: string,
    researchType: string = 'comprehensive'
  ): Promise<any> {
    return (
      await this.httpClient.post<any>('company-risks-research', {
        body: {
          company_name: companyName,
          research_type: researchType,
        },
      })
    ).data;
  }

  async getCompanyDataSearchStatus(uuid: string): Promise<any> {
    return (await this.httpClient.get<any>(`company-data-search-status/${uuid}`)).data;
  }

  async getCompanyRisksResearchStatus(uuid: string): Promise<any> {
    return (await this.httpClient.get<any>(`company-risks-research-status/${uuid}`)).data;
  }

  async stopCompanyDataSearch(uuid: string): Promise<any> {
    return (await this.httpClient.post<any>(`company-data-search-stop/${uuid}`)).data;
  }

  async stopCompanyRisksResearch(uuid: string): Promise<any> {
    return (await this.httpClient.delete<any>(`company-risks-research/${uuid}`)).data;
  }

  async getReport(
    uuid: string,
    reportType: string = 'data',
    download: boolean = false
  ): Promise<string> {
    const endpoint = `company-data-search/${uuid}/report/${reportType}`;
    const response = await this.httpClient.get<string>(endpoint, {
      params: download ? { download: 'true' } : undefined,
    });
    return response.data;
  }

  // Get the list of previously processed companies
  async getCompaniesList(): Promise<any> {
    return (await this.httpClient.get<any>('companies')).data;
  }
}
export const quoteService = new QuoteService(HTTP_CLIENT);
export const companyDataService = new CompanyDataService(HTTP_CLIENT);
