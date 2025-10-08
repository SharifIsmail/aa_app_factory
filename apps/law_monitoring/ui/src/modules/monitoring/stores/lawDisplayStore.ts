import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { applyCombinedFilters } from '@/@core/utils/lawStoreHelpers.ts';
import {
  Category,
  AiClassification,
  type PreprocessedLaw,
  type DateRange,
} from '@/modules/monitoring/types';
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

export enum DisplayMode {
  DATE = 'date',
  DEFAULT = 'default',
  SEARCH = 'search',
}

export const useLawDisplayStore = defineStore(createStoreId('law-display'), () => {
  // ===== DISPLAY MODE MANAGEMENT =====
  const displayMode = ref<DisplayMode>(DisplayMode.DEFAULT);
  const isInitialFilterApplied = ref<boolean>(true);

  function setDisplayMode(mode: DisplayMode): void {
    displayMode.value = mode;
  }

  // ===== LAW COLLECTION & FILTERING =====
  const allDisplayedLaws = ref<PreprocessedLaw[]>([]);
  const categoryFilter = ref<'ALL' | Category>('ALL');
  const aiClassificationFilter = ref<'ALL' | AiClassification>(AiClassification.LIKELY_RELEVANT);

  // ===== DATE RANGE SELECTION =====
  const selectedDateRange = ref<DateRange | undefined>(undefined);
  const dateSelectionMessage = ref<string>('');

  const displayedLaws = computed(() => {
    return applyCombinedFilters(
      allDisplayedLaws.value,
      categoryFilter.value,
      aiClassificationFilter.value
    );
  });

  function setAllDisplayedLaws(laws: PreprocessedLaw[]): void {
    allDisplayedLaws.value = laws;
  }

  function setCategoryFilter(filter: 'ALL' | Category): void {
    categoryFilter.value = filter;
  }

  function setAiClassificationFilter(filter: 'ALL' | AiClassification): void {
    aiClassificationFilter.value = filter;
  }

  function clearDisplayedLaws(): void {
    allDisplayedLaws.value = [];
  }

  // ===== DATE RANGE MANAGEMENT =====
  function setSelectedDateRange(dateRange: DateRange | undefined): void {
    selectedDateRange.value = dateRange;
  }

  function setDateSelectionMessage(message: string): void {
    dateSelectionMessage.value = message;
  }

  // ===== OPTIMISTIC UPDATES =====
  function updateLawInCollection(lawId: string, updates: Partial<PreprocessedLaw>): void {
    const lawIndex = allDisplayedLaws.value.findIndex((l) => l.law_file_id === lawId);
    if (lawIndex !== -1) {
      allDisplayedLaws.value = allDisplayedLaws.value.map((law, index) =>
        index === lawIndex ? { ...law, ...updates } : law
      );
    }
  }

  return {
    // Display Mode Management
    displayMode,
    setDisplayMode,
    isInitialFilterApplied,

    // Law Collection & Filtering
    allDisplayedLaws,
    displayedLaws,
    categoryFilter,
    aiClassificationFilter,
    setAllDisplayedLaws,
    setCategoryFilter,
    setAiClassificationFilter,
    clearDisplayedLaws,

    // Date Range Management
    selectedDateRange,
    dateSelectionMessage,
    setSelectedDateRange,
    setDateSelectionMessage,

    // Optimistic Updates
    updateLawInCollection,
  };
});
