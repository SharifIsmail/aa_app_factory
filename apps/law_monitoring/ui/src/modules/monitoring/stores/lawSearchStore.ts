import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { preprocessedLawService } from '@/@core/utils/http.ts';
import { withLoader } from '@/@core/utils/lawStoreHelpers.ts';
import type {
  PreprocessedLaw,
  OfficialJournalSeries,
  DocumentTypeLabel,
} from '@/modules/monitoring/types';
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useLawSearchStore = defineStore(createStoreId('law-search'), () => {
  const notificationStore = useNotificationStore();

  // ===== SEARCH QUERY MANAGEMENT =====
  const searchQuery = ref<string>('');
  const isSearching = ref(false);

  function setSearchQuery(query: string): void {
    searchQuery.value = query;
  }

  function clearSearchQuery(): void {
    searchQuery.value = '';
  }

  // ===== SEARCH EXECUTION =====
  async function searchLawsByTitle(query: string): Promise<PreprocessedLaw[]> {
    if (!query.trim()) {
      return [];
    }

    return withLoader(isSearching, async () => {
      try {
        setSearchQuery(query);
        return await preprocessedLawService.searchLawsByTitle(query.trim());
      } catch (err: any) {
        notificationStore.addErrorNotification(
          `Failed to search laws by title "${query}". Please try again later.`
        );
        console.error('Error searching laws by title:', err);
        return [];
      }
    });
  }

  async function searchLawsByEurovoc(eurovocDescriptors: string[]): Promise<PreprocessedLaw[]> {
    if (!eurovocDescriptors.length) {
      return [];
    }

    // Filter out empty descriptors
    const validDescriptors = eurovocDescriptors.filter((desc) => desc.trim());
    if (!validDescriptors.length) {
      return [];
    }

    return withLoader(isSearching, async () => {
      try {
        setSearchQuery(validDescriptors.join(', '));
        return await preprocessedLawService.searchLawsByEurovoc(validDescriptors);
      } catch (err: any) {
        notificationStore.addErrorNotification(
          `Failed to search laws by Eurovoc descriptors. Please try again later.`
        );
        console.error('Error searching laws by Eurovoc:', err);
        return [];
      }
    });
  }

  async function searchLawsByDocumentType(
    documentType: DocumentTypeLabel
  ): Promise<PreprocessedLaw[]> {
    if (!documentType.trim()) {
      return [];
    }

    return withLoader(isSearching, async () => {
      try {
        setSearchQuery(documentType);
        return await preprocessedLawService.searchLawsByDocumentType(
          documentType.trim() as DocumentTypeLabel
        );
      } catch (err: any) {
        notificationStore.addErrorNotification(
          `Failed to search laws by document type "${documentType}". Please try again later.`
        );
        console.error('Error searching laws by document type:', err);
        return [];
      }
    });
  }

  async function searchLawsByJournalSeries(
    journalSeries: OfficialJournalSeries
  ): Promise<PreprocessedLaw[]> {
    if (!journalSeries.trim()) {
      return [];
    }

    return withLoader(isSearching, async () => {
      try {
        setSearchQuery(journalSeries);
        return await preprocessedLawService.searchLawsByJournalSeries(
          journalSeries.trim() as OfficialJournalSeries
        );
      } catch (err: any) {
        notificationStore.addErrorNotification(
          `Failed to search laws by journal series "${journalSeries}". Please try again later.`
        );
        console.error('Error searching laws by journal series:', err);
        return [];
      }
    });
  }

  async function searchLawsByDepartment(department: string): Promise<PreprocessedLaw[]> {
    if (!department.trim()) {
      return [];
    }

    return withLoader(isSearching, async () => {
      try {
        setSearchQuery(department);
        return await preprocessedLawService.searchLawsByDepartment(department.trim());
      } catch (err: any) {
        notificationStore.addErrorNotification(
          `Failed to search laws by department "${department}". Please try again later.`
        );
        console.error('Error searching laws by department:', err);
        return [];
      }
    });
  }

  function resetSearch(): void {
    clearSearchQuery();
  }

  return {
    searchQuery,
    isSearching,
    searchLawsByTitle,
    searchLawsByEurovoc,
    searchLawsByDocumentType,
    searchLawsByJournalSeries,
    searchLawsByDepartment,
    resetSearch,
  };
});
