import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { preprocessedLawService } from '@/@core/utils/http.ts';
import { withLoader } from '@/@core/utils/lawStoreHelpers.ts';
import { useLawDataStore } from '@/modules/monitoring/stores/lawDataStore.ts';
import { defineStore } from 'pinia';
import type { PreprocessedLaw } from 'src/modules/monitoring/types';
import { ref } from 'vue';

const DEFAULT_DAYS_TO_LOAD = 5;
const NO_LAWS_FOUND_THRESHOLD_DAYS = 30;

export const useLawPaginationStore = defineStore(createStoreId('law-pagination'), () => {
  const dataStore = useLawDataStore();
  const notificationStore = useNotificationStore();

  // ===== PAGINATION STATE MANAGEMENT =====
  const isLoading = ref(false);
  const isLoadingMore = ref(false);
  const hasMoreLaws = ref(true);
  const currentDaysLoaded = ref<number>(DEFAULT_DAYS_TO_LOAD);
  const consecutiveDaysWithoutLaws = ref<number>(0);

  function resetPaginationState(): void {
    hasMoreLaws.value = true;
    consecutiveDaysWithoutLaws.value = 0;
    currentDaysLoaded.value = DEFAULT_DAYS_TO_LOAD;
  }

  // ===== INITIAL LAW LOADING =====
  async function loadDefaultLaws(
    daysToLoad: number = DEFAULT_DAYS_TO_LOAD
  ): Promise<PreprocessedLaw[]> {
    return withLoader(isLoading, async () => {
      currentDaysLoaded.value = daysToLoad;
      resetPaginationState();

      /**
       * Update:
       * Commented out as it is redundant, as available dates fetched is invoked centrally from MonitoringHome.vue
       * Uncomment in case of noticeable issues with laws fetching
       */
      // Ensure we have available dates
      // if (dataStore.availableDates.length === 0) {
      //   await dataStore.fetchAvailableDates();
      //   if (dataStore.availableDates.length === 0) {
      //     notificationStore.addInfoNotification('No available dates to fetch laws from.');
      //     return [];
      //   }
      // }

      try {
        const fetchedLaws = await fetchLawsForDateRange(daysToLoad);

        // If no laws found, try loading more days
        if (fetchedLaws.length === 0) {
          return await loadLawsUntilFoundOrThreshold(0, DEFAULT_DAYS_TO_LOAD);
        }

        return fetchedLaws;
      } catch (err: any) {
        console.error(`Error loading default laws:`, err);
        return [];
      }
    });
  }

  // ===== LOAD MORE =====
  async function loadMoreDays(
    currentLawCount: number,
    additionalDays: number = DEFAULT_DAYS_TO_LOAD
  ): Promise<PreprocessedLaw[]> {
    if (!hasMoreLaws.value) {
      return [];
    }

    return withLoader(isLoadingMore, async () => {
      try {
        return await loadLawsUntilFoundOrThreshold(currentLawCount, additionalDays);
      } catch (err: any) {
        notificationStore.addErrorNotification(`Failed to load more laws`);
        console.error(`Error loading additional laws:`, err);
        return [];
      }
    });
  }

  async function loadLawsUntilFoundOrThreshold(
    initialLawCount: number,
    additionalDays: number
  ): Promise<PreprocessedLaw[]> {
    let newTotalDays = currentDaysLoaded.value + additionalDays;

    while (true) {
      const fetchedLaws = await fetchLawsForDateRange(newTotalDays);

      if (fetchedLaws.length > initialLawCount) {
        consecutiveDaysWithoutLaws.value = 0;
        return fetchedLaws;
      }

      consecutiveDaysWithoutLaws.value += additionalDays;

      if (consecutiveDaysWithoutLaws.value >= NO_LAWS_FOUND_THRESHOLD_DAYS) {
        return await handleThresholdReached();
      }

      newTotalDays += additionalDays;
    }
  }

  async function fetchLawsForDateRange(totalDays: number): Promise<PreprocessedLaw[]> {
    const today = new Date();
    const startDateBoundary = new Date(today);
    startDateBoundary.setDate(today.getDate() - (totalDays - 1));

    const fetchedLaws = await dataStore.fetchLawsByDateRange(startDateBoundary, today);
    currentDaysLoaded.value = totalDays;
    return fetchedLaws;
  }

  async function handleThresholdReached(): Promise<PreprocessedLaw[]> {
    const today = new Date();

    try {
      const { law_data } = await preprocessedLawService.getLaws(undefined, today);
      hasMoreLaws.value = false;
      return law_data;
    } catch (err: any) {
      notificationStore.addErrorNotification('Failed to fetch all available laws');
      console.error('Error fetching all laws:', err);
      hasMoreLaws.value = false;
      return [];
    }
  }

  return {
    isLoading,
    isLoadingMore,
    hasMoreLaws,
    currentDaysLoaded,

    loadDefaultLaws,

    loadMoreDays,
  };
});
