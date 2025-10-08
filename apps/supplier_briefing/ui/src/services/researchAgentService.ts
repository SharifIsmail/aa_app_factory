import type {
  StartResearchAgentRequest,
  ResearchAgentResponse,
  ResearchStatusResponse,
  QuickActionFilterRequest,
  QuickActionFilterResponse,
} from '@/types/api';
import type { Http } from '@aleph-alpha/lib-http';

export class ResearchAgentService {
  constructor(readonly httpClient: Http) {}

  async startResearchAgent(
    researchTopic: string,
    executionId?: string,
    flowName?: string,
    params?: object
  ): Promise<ResearchAgentResponse> {
    const body: StartResearchAgentRequest = {
      query: researchTopic,
    };

    // Add execution_id if provided for conversation continuity
    if (executionId) {
      body.execution_id = executionId;
    }

    // Add structured flow parameters if provided
    if (flowName) {
      body.flow_name = flowName;
    }

    if (params) {
      body.params = params;
    }

    return (
      await this.httpClient.post<ResearchAgentResponse>('query/start', {
        body,
      })
    ).data;
  }

  async getResearchAgentStatus(uuid: string): Promise<ResearchStatusResponse> {
    return (await this.httpClient.get<ResearchStatusResponse>(`query/status/${uuid}`)).data;
  }

  async stopResearchAgent(uuid: string): Promise<ResearchAgentResponse> {
    const res = await this.httpClient.delete<{
      uuid: string;
      task_cancelled: boolean;
      work_log_deleted?: boolean;
      agent_deleted?: boolean;
    }>(`query/stop/${uuid}`);
    const status = res.data.task_cancelled ? 'OK' : 'ERROR';
    return { id: res.data.uuid, status };
  }

  async getTransactionsColumns(): Promise<string[]> {
    return (await this.httpClient.get<string[]>('columns')).data;
  }

  async filterQuickActionData<T = any>(
    request: QuickActionFilterRequest
  ): Promise<QuickActionFilterResponse<T>> {
    return (
      await this.httpClient.post<QuickActionFilterResponse<T>>('quick-actions/filter', {
        body: request,
      })
    ).data;
  }
}
