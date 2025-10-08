import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useLawCategoryStore } from '@/modules/monitoring/stores/lawCategoryStore.ts';
import { useLawDateBrowsingStore } from '@/modules/monitoring/stores/lawDateBrowsingStore.ts';
import { useLawDisplayStore, DisplayMode } from '@/modules/monitoring/stores/lawDisplayStore.ts';
import { useLawPaginationStore } from '@/modules/monitoring/stores/lawPaginationStore.ts';
import { useLawSearchStore } from '@/modules/monitoring/stores/lawSearchStore.ts';
import {
  Category,
  type PreprocessedLaw,
  type OfficialJournalSeries,
  type DocumentTypeLabel,
  type DateRange,
  AiClassification,
} from '@/modules/monitoring/types';
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

export const useLawCoordinatorStore = defineStore(createStoreId('law-coordinator'), () => {
  const displayStore = useLawDisplayStore();
  const searchStore = useLawSearchStore();
  const dateBrowsingStore = useLawDateBrowsingStore();
  const paginationStore = useLawPaginationStore();
  const categoryStore = useLawCategoryStore();

  const isAutoFetching = ref(false);

  async function autoLoadUntilFilterSatisfied(): Promise<void> {
    // Only auto-load in DEFAULT mode when we're not already fetching and have more laws available
    if (
      displayStore.displayMode !== DisplayMode.DEFAULT ||
      isAutoFetching.value ||
      !paginationStore.hasMoreLaws
    ) {
      return;
    }

    isAutoFetching.value = true;
    try {
      while (displayStore.displayedLaws.length === 0 && paginationStore.hasMoreLaws) {
        await loadMoreDays();
        // Break if we found some laws after loading more
        if (displayStore.displayedLaws.length > 0) break;
      }
    } finally {
      isAutoFetching.value = false;
    }
  }

  // ===== SEARCH OPERATIONS =====
  async function performSearch<T>(
    searchParam: T,
    searchMethod: (param: T) => Promise<PreprocessedLaw[]>
  ): Promise<void> {
    displayStore.setDisplayMode(DisplayMode.SEARCH);
    displayStore.setCategoryFilter('ALL');

    const searchResults = await searchMethod(searchParam);

    displayStore.setAllDisplayedLaws(searchResults);
  }

  async function searchLawsByTitle(query: string): Promise<void> {
    await performSearch(query, searchStore.searchLawsByTitle);
  }

  async function searchLawsByEurovoc(eurovocDescriptors: string[]): Promise<void> {
    await performSearch(eurovocDescriptors, searchStore.searchLawsByEurovoc);
  }

  async function searchLawsByDocumentType(documentType: DocumentTypeLabel): Promise<void> {
    await performSearch(documentType, searchStore.searchLawsByDocumentType);
  }

  async function searchLawsByJournalSeries(journalSeries: OfficialJournalSeries): Promise<void> {
    await performSearch(journalSeries, searchStore.searchLawsByJournalSeries);
  }

  async function searchLawsByDepartment(department: string): Promise<void> {
    await performSearch(department, searchStore.searchLawsByDepartment);
  }

  async function resetSearch(): Promise<void> {
    searchStore.resetSearch();
    displayStore.setDisplayMode(DisplayMode.DEFAULT);
    displayStore.setCategoryFilter('ALL');
    await loadDefaultLaws();
  }

  // ===== DATE-BASED BROWSING =====
  async function fetchLawsByDateRange(dateRange: DateRange): Promise<PreprocessedLaw[]> {
    const [startDate, endDate] = dateRange;
    const laws = await dateBrowsingStore.fetchLawsForDateRange(startDate, endDate);
    displayStore.setDisplayMode(DisplayMode.DATE);
    displayStore.setAllDisplayedLaws(laws);
    return displayStore.displayedLaws;
  }

  // ===== DEFAULT LAW LOADING & PAGINATION =====
  async function loadDefaultLaws(daysToLoad?: number): Promise<void> {
    const laws = await paginationStore.loadDefaultLaws(daysToLoad);
    if (displayStore.isInitialFilterApplied) return;
    else {
      displayStore.setDisplayMode(DisplayMode.DEFAULT);
      displayStore.setAllDisplayedLaws(laws);
    }
  }

  async function loadMoreDays(additionalDays?: number): Promise<void> {
    if (displayStore.displayMode !== DisplayMode.DEFAULT || !paginationStore.hasMoreLaws) {
      return;
    }

    const currentLawCount = displayStore.displayedLaws.length;
    const moreLaws = await paginationStore.loadMoreDays(currentLawCount, additionalDays);
    displayStore.setAllDisplayedLaws(moreLaws);
  }

  // ===== CATEGORY MANAGEMENT =====
  async function updateLawCategory(lawId: string, category: Category): Promise<void> {
    await categoryStore.updateLawCategory(
      lawId,
      category,
      // Optimistic update callback
      (lawId: string, category: Category) => {
        displayStore.updateLawInCollection(lawId, { category });
      },
      // Rollback callback
      (lawId: string, originalCategory: Category) => {
        displayStore.updateLawInCollection(lawId, { category: originalCategory });
      },
      // Get current category callback
      (lawId: string) => {
        return displayStore.displayedLaws.find((l) => l.law_file_id === lawId)?.category;
      }
    );
  }

  // ===== FILTER MANAGEMENT WITH AUTO-LOADING =====
  async function setCategoryFilter(filter: 'ALL' | Category): Promise<void> {
    if (filter === 'ALL') {
      displayStore.setCategoryFilter('ALL');
    } else {
      displayStore.setCategoryFilter(filter);
    }
    await autoLoadUntilFilterSatisfied();
  }

  async function setAiClassificationFilter(filter: 'ALL' | AiClassification): Promise<void> {
    displayStore.setAiClassificationFilter(filter);
    await autoLoadUntilFilterSatisfied();
  }

  // ===== COMPUTED PROPERTIES (DELEGATED) =====
  const displayedLaws = computed(() => displayStore.displayedLaws);
  const displayMode = computed(() => displayStore.displayMode);
  const categoryFilter = computed(() => displayStore.categoryFilter);
  const aiClassificationFilter = computed(() => displayStore.aiClassificationFilter);
  const searchQuery = computed(() => searchStore.searchQuery);
  const isSearching = computed(() => searchStore.isSearching);
  const isLoading = computed(() => paginationStore.isLoading);
  const isLoadingMore = computed(() => paginationStore.isLoadingMore || isAutoFetching.value);
  const hasMoreLaws = computed(() => paginationStore.hasMoreLaws);
  const currentDaysLoaded = computed(() => paginationStore.currentDaysLoaded);
  const hasLawsForDate = computed(() => dateBrowsingStore.hasLawsForDate);
  const getLawsForDate = computed(() => dateBrowsingStore.getLawsForDate);
  const getAvailableDates = computed(() => dateBrowsingStore.getAvailableDates);
  const isLoadingDates = computed(() => dateBrowsingStore.isLoadingDates);
  const isLoadingLawsByDate = computed(() => dateBrowsingStore.isLoadingLawsByDate);
  const isCategoryLoading = computed(() => categoryStore.isCategoryLoading);

  return {
    // Search Operations
    searchLawsByTitle,
    searchLawsByEurovoc,
    searchLawsByDocumentType,
    searchLawsByJournalSeries,
    searchLawsByDepartment,
    resetSearch,

    // Date-based Browsing
    fetchAvailableDates: dateBrowsingStore.fetchAvailableDates,
    fetchLawsByDateRange,

    // Default Law Loading & Pagination
    loadDefaultLaws,
    loadMoreDays,

    // Category Management
    setCategoryFilter,
    setAiClassificationFilter,
    updateLawCategory,

    // Computed Properties (Read-only state)
    displayedLaws,
    displayMode,
    categoryFilter,
    aiClassificationFilter,
    searchQuery,
    isLoading,
    isLoadingMore,
    isSearching,
    hasMoreLaws,
    currentDaysLoaded,
    hasLawsForDate,
    getLawsForDate,
    getAvailableDates,
    isLoadingDates,
    isLoadingLawsByDate,
    isCategoryLoading,
    isAutoFetching,
    // Direct access to underlying stores for advanced use cases
    displayStore,
    searchStore,
    dateBrowsingStore,
    paginationStore,
    categoryStore,
  };
});
