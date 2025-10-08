import { ApplicationConfigService } from '@/@core/services/applicationConfigService.ts';
import { CompanyConfigService } from '@/@core/services/companyConfigService.ts';
import { ManualLawAnalysisService } from '@/modules/manual/services/manualLawAnalysisService.ts';
import { DashboardService } from '@/modules/monitoring/services/dashboardService.ts';
import { PreprocessedLawService } from '@/modules/monitoring/services/preprocessedLawService.ts';
import { http } from '@aleph-alpha/lib-http';

export const HTTP_CLIENT = http({
  timeout: 60_000,
  baseURL: '',
});

export const companyConfigService = new CompanyConfigService(HTTP_CLIENT);
export const applicationConfigService = new ApplicationConfigService(HTTP_CLIENT);
export const manualLawAnalysisService = new ManualLawAnalysisService(HTTP_CLIENT);
export const preprocessedLawService = new PreprocessedLawService(HTTP_CLIENT);
export const dashboardService = new DashboardService(HTTP_CLIENT);
