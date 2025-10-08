import {
  composeFilters,
  applyAiClassificationFilter,
  applyCategoryFilter,
  applySorting,
} from '@/@core/utils/filterUtils';
import {
  type Category,
  type PreprocessedLaw,
  type FilterConfig,
  type TeamRelevancyClassification,
  AiClassification,
} from '@/modules/monitoring/types';
import type { Ref } from 'vue';

/**
 * Composed filter that applies all filters in sequence
 */
const lawFilters = composeFilters<FilterConfig>({
  categoryFilter: applyCategoryFilter,
  aiClassificationFilter: applyAiClassificationFilter,
  shouldSort: applySorting,
});

/**
 * Main function to apply all filters with sorting
 */
export function applyCombinedFilters(
  allDisplayedLaws: PreprocessedLaw[],
  categoryFilter: 'ALL' | Category,
  aiClassificationFilter: 'ALL' | AiClassification
): PreprocessedLaw[] {
  return lawFilters(allDisplayedLaws, {
    categoryFilter,
    aiClassificationFilter,
    shouldSort: true,
  });
}

// ===== UTILITY FUNCTIONS =====

export function withLoader<T>(loading: Ref<boolean>, fn: () => Promise<T>): Promise<T> {
  loading.value = true;
  return fn().finally(() => (loading.value = false));
}

export const getRelevantTeams = (law: PreprocessedLaw): TeamRelevancyClassification[] => {
  return law.team_relevancy_classification?.filter((team) => team.is_relevant) || [];
};
