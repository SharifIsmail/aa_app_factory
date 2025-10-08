import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { dashboardService } from '@/@core/utils/http.ts';
import { withLoader } from '@/@core/utils/lawStoreHelpers.ts';
import {
  OfficialJournalSeries,
  type AIClassificationCounts,
  type ClassificationOverviewMetrics,
  type HumanDecisionCounts,
  type LegalActTimeline,
  type DepartmentRelevanceCount,
  type EurovocDescriptorCount,
} from '@/modules/monitoring/types';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useDashboardStore = defineStore(createStoreId('dashboard'), () => {
  const notificationStore = useNotificationStore();

  // State
  const timelineData = ref<LegalActTimeline[]>([]);
  const isLoading = ref(false);
  const isLoadingLegalActOverview = ref(false);
  const error = ref<string | null>(null);
  const totalTimelineActs = ref<number>(0);

  // Overview data
  const totalLegalActs = ref<number>(0);
  const totalEvaluations = ref<number>(0);
  const aiClassification = ref<AIClassificationCounts>();
  const humanClassification = ref<HumanDecisionCounts>();
  const metrics = ref<ClassificationOverviewMetrics>();
  const currentJournalSeries = ref<OfficialJournalSeries | null>(null);

  // Departments overview data
  const departmentsData = ref<DepartmentRelevanceCount[]>([]);
  const totalRelevantActs = ref<number>(0);
  const isLoadingDepartments = ref(false);

  // EuroVoc overview data
  const eurovocData = ref<EurovocDescriptorCount[]>([]);
  const totalDescriptors = ref<number>(0);
  const isLoadingEurovoc = ref(false);

  const fetchTimelineForDateRange = async (
    dateRange: [Date, Date],
    journalSeries?: OfficialJournalSeries,
    skipLoading = false
  ) => {
    const loaderFn = skipLoading
      ? (fn: () => Promise<any>) => fn()
      : (fn: () => Promise<any>) => withLoader(isLoading, fn);

    return loaderFn(async () => {
      try {
        error.value = null;
        const [start, end] = dateRange;

        // Format dates to ISO string for the API
        const startStr = start.toISOString().split('T')[0];
        const endStr = end.toISOString().split('T')[0];

        const response = await dashboardService.getLegalActTimeline(
          startStr,
          endStr,
          journalSeries
        );
        timelineData.value = response.legal_acts ?? [];
        totalTimelineActs.value = response.total_legal_acts ?? 0;
        currentJournalSeries.value = journalSeries || null;

        return response;
      } catch (err: any) {
        error.value = err instanceof Error ? err.message : 'Failed to fetch timeline data';
        notificationStore.addErrorNotification(
          'Failed to fetch timeline data for selected date range, please retry later.'
        );
        console.error('Error fetching legal act timeline for date range:', err);
        throw err;
      }
    });
  };

  // Fetch legal act overview data for a given date range
  // make dateRange optional
  const fetchLegalActOverview = async (
    dateRange?: [Date, Date],
    journalSeries?: OfficialJournalSeries
  ) => {
    return withLoader(isLoadingLegalActOverview, async () => {
      try {
        const [start, end] = dateRange || [];

        // Format dates to ISO string for the API
        const startStr = start?.toISOString().split('T')[0];
        const endStr = end?.toISOString().split('T')[0];
        // if startStr or endStr is empty, dont send it to the API
        const response = await dashboardService.getLegalActOverview(
          startStr,
          endStr,
          journalSeries
        );

        totalLegalActs.value = response.total_acts ?? 0;
        totalEvaluations.value = response.total_evaluations ?? 0;
        aiClassification.value = response.ai_classification ?? {};
        humanClassification.value = response.human_decision ?? {};
        metrics.value = response.metrics ?? {};

        return response;
      } catch (err: any) {
        error.value = err instanceof Error ? err.message : 'Failed to fetch legal act overview';
        notificationStore.addErrorNotification(
          'Failed to fetch legal act overview, please retry later.'
        );
        console.error('Error fetching legal act overview:', err);
        throw err;
      }
    });
  };

  // Fetch departments overview data for a given date range
  const fetchDepartmentsOverview = async (
    dateRange?: [Date, Date],
    journalSeries?: OfficialJournalSeries
  ) => {
    return withLoader(isLoadingDepartments, async () => {
      try {
        const [start, end] = dateRange || [];

        // Format dates to ISO string for the API
        const startStr = start?.toISOString().split('T')[0];
        const endStr = end?.toISOString().split('T')[0];

        const response = await dashboardService.getDepartmentsOverview(
          startStr,
          endStr,
          journalSeries
        );

        departmentsData.value = response.departments ?? [];
        totalRelevantActs.value = response.total_relevant_acts ?? 0;

        return response;
      } catch (err: any) {
        error.value = err instanceof Error ? err.message : 'Failed to fetch departments overview';
        notificationStore.addErrorNotification(
          'Failed to fetch departments overview, please retry later.'
        );
        console.error('Error fetching departments overview:', err);
        throw err;
      }
    });
  };

  const fetchEurovocOverview = async (
    dateRange?: [Date, Date],
    journalSeries?: OfficialJournalSeries
  ) => {
    return withLoader(isLoadingEurovoc, async () => {
      try {
        const [start, end] = dateRange || [];

        // Format dates to ISO string for the API
        const startStr = start?.toISOString().split('T')[0];
        const endStr = end?.toISOString().split('T')[0];

        const response = await dashboardService.getEurovocOverview(startStr, endStr, journalSeries);

        eurovocData.value = response.descriptors ?? [];
        totalDescriptors.value = response.total_descriptors ?? 0;

        return response;
      } catch (err: any) {
        error.value = err instanceof Error ? err.message : 'Failed to fetch EuroVoc overview';
        notificationStore.addErrorNotification(
          'Failed to fetch EuroVoc overview, please retry later.'
        );
        console.error('Error fetching EuroVoc overview:', err);
        throw err;
      }
    });
  };

  // Computed properties for current data
  const currentTimelineData = computed(() => timelineData.value);
  const currentTotalActs = computed(() => totalTimelineActs.value);

  // Actions
  const setJournalSeriesFilter = (series: OfficialJournalSeries | null) => {
    currentJournalSeries.value = series;
  };

  return {
    // State
    timelineData,
    isLoading,
    isLoadingLegalActOverview,
    isLoadingDepartments,
    error,
    totalTimelineActs,
    currentJournalSeries,

    // Overview data
    totalLegalActs,
    totalEvaluations,
    aiClassification,
    humanClassification,
    metrics,

    // Departments data
    departmentsData,
    totalRelevantActs,

    // EuroVoc data
    eurovocData,
    totalDescriptors,
    isLoadingEurovoc,

    // Actions
    fetchTimelineForDateRange,
    fetchLegalActOverview,
    fetchDepartmentsOverview,
    fetchEurovocOverview,
    setJournalSeriesFilter,

    // Computed
    currentTimelineData,
    currentTotalActs,
  };
});
