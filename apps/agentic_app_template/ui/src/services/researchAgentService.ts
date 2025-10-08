import type { Http } from '@aleph-alpha/lib-http';

export class ResearchAgentService {
  constructor(readonly httpClient: Http) {}

  async startResearchAgent(
    researchTopic: string,
    researchType: string = 'comprehensive'
  ): Promise<any> {
    return (
      await this.httpClient.post<any>('research/start', {
        body: {
          research_topic: researchTopic,
          research_type: researchType,
        },
      })
    ).data;
  }

  async getResearchAgentStatus(uuid: string): Promise<any> {
    return (await this.httpClient.get<any>(`research/status/${uuid}`)).data;
  }

  async stopResearchAgent(uuid: string): Promise<any> {
    return (await this.httpClient.delete<any>(`research/stop/${uuid}`)).data;
  }

  async getReports(): Promise<any> {
    return (await this.httpClient.get<any>('reports')).data;
  }

  async getReport(uuid: string, download: boolean = false): Promise<any> {
    const endpoint = `reports/${uuid}`;
    const response = await this.httpClient.get<any>(endpoint, {
      params: download ? { download: 'true' } : undefined,
    });
    return response.data;
  }
}
