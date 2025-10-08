import { ResearchAgentService } from '@/services/researchAgentService.ts';
import { http } from '@aleph-alpha/lib-http';

export const HTTP_CLIENT = http({
  timeout: 60_000,
  baseURL: '',
});

export const researchAgentService = new ResearchAgentService(HTTP_CLIENT);
