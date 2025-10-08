import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { manualLawAnalysisService, preprocessedLawService } from '@/@core/utils/http.ts';
import { withLoader } from '@/@core/utils/lawStoreHelpers.ts';
import {
  Category,
  type PreprocessedLaw,
  ExportScope,
  type Pagination,
} from '@/modules/monitoring/types';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useLawDataStore = defineStore(createStoreId('law-data'), () => {
  const notificationStore = useNotificationStore();

  // ===== DATE MANAGEMENT =====
  const availableDates = ref<string[]>([]);
  const isLoadingDates = ref(false);
  const isLoadingLawsByDate = ref(false);

  async function fetchAvailableDates(): Promise<string[]> {
    if (availableDates.value.length > 0) {
      return availableDates.value;
    }

    return withLoader(isLoadingDates, async () => {
      try {
        const dates = await preprocessedLawService.getAllDatesWithLaws();
        availableDates.value = dates.sort(
          (a: string, b: string) => new Date(a).getTime() - new Date(b).getTime()
        ); // Sort ascending

        return availableDates.value;
      } catch (err: any) {
        notificationStore.addErrorNotification(
          'Failed to fetch available dates, please retry later.'
        );
        console.error('Error fetching available dates:', err);
        return [];
      }
    });
  }

  // ===== LAW DATA FETCHING & STORAGE =====
  const lawsByDate = ref<Record<string, PreprocessedLaw[]>>({});
  const allLaws = ref<PreprocessedLaw[]>([]);
  const paginationMetadata = ref<Pagination>();

  async function fetchLawsByDateRange(startDate: Date, endDate: Date): Promise<PreprocessedLaw[]> {
    return withLoader(isLoadingLawsByDate, async () => {
      try {
        const { law_data, pagination } = await preprocessedLawService.getLawsByDateRange(
          startDate,
          endDate
        );
        allLaws.value = law_data;
        paginationMetadata.value = pagination;
        const lawsByDateMap: Record<string, PreprocessedLaw[]> = {};
        law_data.forEach((law) => {
          const dateKey = law.publication_date || law.discovered_at;
          if (dateKey) {
            const dateString = dateKey.split('T')[0];
            if (!lawsByDateMap[dateString]) {
              lawsByDateMap[dateString] = [];
            }
            lawsByDateMap[dateString].push(law);
          }
        });

        lawsByDate.value = lawsByDateMap;

        return law_data;
      } catch (err: any) {
        notificationStore.addErrorNotification(
          `Failed to fetch laws for date range ${startDate.toISOString().split('T')[0]} to ${endDate.toISOString().split('T')[0]}. Please try again later`
        );
        console.error('Error fetching laws for date range:', err);
        throw err;
      }
    });
  }

  // ===== LAW CATEGORY MANAGEMENT =====
  const categoryUpdateLoading = ref<string[]>([]);

  async function updateLawCategory(lawId: string, category: Category): Promise<void> {
    if (!categoryUpdateLoading.value.includes(lawId)) {
      categoryUpdateLoading.value.push(lawId);
    }

    try {
      await manualLawAnalysisService.updateLawCategory(lawId, category);

      for (const [dateKey, lawsForDate] of Object.entries(lawsByDate.value)) {
        const lawIndexInDate = lawsForDate.findIndex((l) => l.law_file_id === lawId);
        if (lawIndexInDate !== -1) {
          const updatedLaw = { ...lawsForDate[lawIndexInDate], category };
          lawsByDate.value[dateKey] = lawsForDate.map((law, index) =>
            index === lawIndexInDate ? updatedLaw : law
          );
          return;
        }
      }
    } catch (error) {
      console.error('Failed to update law category:', error);
      throw error;
    } finally {
      const index = categoryUpdateLoading.value.indexOf(lawId);
      if (index > -1) {
        categoryUpdateLoading.value.splice(index, 1);
      }
    }
  }

  // ===== CSV EXPORT =====
  const isDownloadingRelevantCsv = ref(false);
  const isDownloadingAllEvaluatedCsv = ref(false);

  async function downloadRelevantCsv(
    exportScope: ExportScope = ExportScope.AllHits
  ): Promise<string | null> {
    if (exportScope === ExportScope.AllEvaluated) {
      isDownloadingAllEvaluatedCsv.value = true;
    } else if (exportScope === ExportScope.AllHits) {
      isDownloadingRelevantCsv.value = true;
    }

    try {
      return await preprocessedLawService.downloadLawsCsv(undefined, exportScope);
    } catch (error) {
      console.error('CSV download failed:', error);
      return null;
    } finally {
      isDownloadingRelevantCsv.value = false;
      isDownloadingAllEvaluatedCsv.value = false;
    }
  }

  // ===== DATE PICKER CONSTRAINTS (CENTRALIZED LOGIC) =====
  const firstDate = computed<Date>(() => {
    const dates = availableDates.value;
    if (!dates.length) return new Date();
    return new Date(dates[0]);
  });

  const lastDate = computed<Date>(() => {
    const dates = availableDates.value;
    if (!dates.length) return new Date();
    return new Date(dates[dates.length - 1]);
  });

  const disabledDates = computed<Date[]>(() => {
    const avail = availableDates.value;
    if (!firstDate.value || !lastDate.value) return [];

    const set = new Set(avail);
    const disabled: Date[] = [];
    for (let d = new Date(firstDate.value); d <= lastDate.value; d.setDate(d.getDate() + 1)) {
      const iso = d.toISOString().split('T')[0];
      if (!set.has(iso)) {
        disabled.push(new Date(d));
      }
    }
    return disabled;
  });

  return {
    availableDates,
    isLoadingDates,
    isLoadingLawsByDate,
    fetchAvailableDates,

    lawsByDate,
    fetchLawsByDateRange,

    categoryUpdateLoading,
    updateLawCategory,

    isDownloadingRelevantCsv,
    isDownloadingAllEvaluatedCsv,
    downloadRelevantCsv,

    allLaws,
    paginationMetadata,

    // Date picker constraints
    firstDate,
    lastDate,
    disabledDates,
  };
});
