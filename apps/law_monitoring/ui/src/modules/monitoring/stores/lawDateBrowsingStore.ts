import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useLawDataStore } from '@/modules/monitoring/stores/lawDataStore.ts';
import { defineStore } from 'pinia';
import type { PreprocessedLaw } from 'src/modules/monitoring/types';
import { computed } from 'vue';

export const useLawDateBrowsingStore = defineStore(createStoreId('law-date-browsing'), () => {
  const dataStore = useLawDataStore();

  // ===== AVAILABLE DATES MANAGEMENT =====
  const getAvailableDates = computed(() => {
    return dataStore.availableDates;
  });

  const isLoadingDates = computed(() => {
    return dataStore.isLoadingDates;
  });

  const isLoadingLawsByDate = computed(() => {
    return dataStore.isLoadingLawsByDate;
  });

  async function fetchAvailableDates(): Promise<string[]> {
    return dataStore.fetchAvailableDates();
  }

  // ===== DATE-SPECIFIC LAW RETRIEVAL =====
  const hasLawsForDate = computed(() => (date: string) => {
    return !!dataStore.lawsByDate[date] && dataStore.lawsByDate[date].length > 0;
  });

  const getLawsForDate = computed(() => (date: string) => {
    return dataStore.lawsByDate[date] || [];
  });

  async function fetchLawsForDate(date: Date): Promise<PreprocessedLaw[]> {
    try {
      const dateString = date.toISOString().split('T')[0];
      // Check if we already have laws for this date
      if (dataStore.lawsByDate[dateString]) {
        return dataStore.lawsByDate[dateString];
      }

      // Fetch laws for the specific date
      await dataStore.fetchLawsByDateRange(date, date);
      return dataStore.lawsByDate[dateString] || [];
    } catch (err: any) {
      console.error('Error fetching laws for date ' + date.toISOString().split('T')[0] + ':', err);
      return [];
    }
  }

  async function fetchLawsForDateRange(startDate: Date, endDate: Date): Promise<PreprocessedLaw[]> {
    try {
      // Fetch laws for the date range - returns all laws aggregated
      return await dataStore.fetchLawsByDateRange(startDate, endDate);
    } catch (err: any) {
      console.error(
        `Error fetching laws for date range ${startDate.toISOString().split('T')[0]} to ${endDate.toISOString().split('T')[0]}:`,
        err
      );
      return [];
    }
  }

  return {
    // Available Dates Management
    getAvailableDates,
    isLoadingDates,
    isLoadingLawsByDate,
    fetchAvailableDates,

    // Date-specific Law Retrieval
    hasLawsForDate,
    getLawsForDate,
    fetchLawsForDate,
    fetchLawsForDateRange,
  };
});
