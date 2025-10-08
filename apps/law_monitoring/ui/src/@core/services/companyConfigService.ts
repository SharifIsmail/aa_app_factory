import type { CompanyConfig, TeamDescription } from '@/@core/types/companyConfig';
import type { Http } from '@aleph-alpha/lib-http';

export class CompanyConfigService {
  constructor(readonly httpClient: Http) {}

  async getCompanyConfig(): Promise<CompanyConfig> {
    const response = await this.httpClient.get<CompanyConfig>('company-config');
    return response.data;
  }

  async updateCompanyDescription(description: string): Promise<string> {
    const response = await this.httpClient.post<string>('company-config/company-description', {
      body: { description: description },
    });
    return response.data;
  }

  async addTeam(team: TeamDescription): Promise<TeamDescription> {
    const response = await this.httpClient.post<TeamDescription>('company-config/team', {
      body: team,
    });
    return response.data;
  }

  async addOrUpdateTeam(team: TeamDescription): Promise<TeamDescription> {
    const response = await this.httpClient.post<TeamDescription>('company-config/team', {
      body: team,
    });
    return response.data;
  }

  async updateTeam(teamName: string, team: TeamDescription): Promise<TeamDescription> {
    const response = await this.httpClient.put<TeamDescription>(
      `company-config/team/${encodeURIComponent(teamName)}`,
      {
        body: team,
      }
    );
    return response.data;
  }

  async deleteTeam(teamName: string): Promise<{ message: string }> {
    const response = await this.httpClient.delete<{ message: string }>(
      `company-config/team/${encodeURIComponent(teamName)}`
    );
    return response.data;
  }
}
