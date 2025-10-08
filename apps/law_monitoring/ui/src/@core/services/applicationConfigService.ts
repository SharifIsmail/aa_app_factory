import type { ApplicationConfig } from '@/@core/types/applicationConfig';
import type { Http } from '@aleph-alpha/lib-http';

export class ApplicationConfigService {
  constructor(readonly httpClient: Http) {}

  async getApplicationConfig(): Promise<ApplicationConfig> {
    const response = await this.httpClient.get<ApplicationConfig>('application-config');
    return response.data;
  }
}
