import { sortLawsByDateAndStatus, isLikelyRelevant } from '@/@core/utils/sortLaws';
import {
  Category,
  type PreprocessedLaw,
  type FilterFunction,
  type DateRange,
  AiClassification,
} from '@/modules/monitoring/types';

/**
 * Composes multiple filter functions into a single function
 * Filters are applied in the order they are provided
 */
export const composeFilters = <T extends Record<string, any>>(filters: {
  [K in keyof T]: FilterFunction<T[K]>;
}) => {
  return (laws: PreprocessedLaw[], filterValues: T): PreprocessedLaw[] => {
    return Object.entries(filters).reduce((filteredLaws, [key, filterFn]) => {
      const filterValue = filterValues[key as keyof T];
      return (filterFn as FilterFunction<any>)(filteredLaws, filterValue);
    }, laws);
  };
};

// ===== INDIVIDUAL FILTER FUNCTIONS =====

/**
 * Filters laws by category (Human Decision)
 */
export const applyCategoryFilter: FilterFunction<'ALL' | Category> = (
  allDisplayedLaws: PreprocessedLaw[],
  categoryFilter: 'ALL' | Category
): PreprocessedLaw[] => {
  if (categoryFilter === 'ALL') {
    return allDisplayedLaws;
  } else {
    return allDisplayedLaws.filter((l) => l.category === categoryFilter);
  }
};

/**
 * Filters laws by AI classification
 */
export const applyAiClassificationFilter: FilterFunction<'ALL' | AiClassification> = (
  allDisplayedLaws: PreprocessedLaw[],
  aiClassificationFilter: 'ALL' | AiClassification
): PreprocessedLaw[] => {
  if (aiClassificationFilter === 'ALL') {
    return allDisplayedLaws;
  } else if (aiClassificationFilter === AiClassification.LIKELY_RELEVANT) {
    return allDisplayedLaws.filter((law) => law.status === 'PROCESSED' && isLikelyRelevant(law));
  } else {
    return allDisplayedLaws.filter((law) => law.status === 'PROCESSED' && !isLikelyRelevant(law));
  }
};

/**
 * Filters laws by date range
 */
export const applyDateRangeFilter: FilterFunction<DateRange | null> = (
  allDisplayedLaws: PreprocessedLaw[],
  dateRange: DateRange | null
): PreprocessedLaw[] => {
  if (!dateRange) {
    return allDisplayedLaws;
  }

  const [startDate, endDate] = dateRange;
  return allDisplayedLaws.filter((law) => {
    const lawDateString = law.publication_date || law.discovered_at;
    if (!lawDateString) return false;

    const lawDate = new Date(lawDateString.split('T')[0]); // Extract date part only
    const start = new Date(startDate.toISOString().split('T')[0]);
    const end = new Date(endDate.toISOString().split('T')[0]);

    return lawDate >= start && lawDate <= end;
  });
};

/**
 * Applies sorting to laws (should be applied last)
 */
export const applySorting: FilterFunction<boolean> = (
  laws: PreprocessedLaw[],
  shouldSort: boolean
): PreprocessedLaw[] => {
  return shouldSort ? sortLawsByDateAndStatus(laws) : laws;
};

// ===== TIMELINE FILTER FUNCTIONS =====

export const applyTimelineFilter = (
  allLaws: PreprocessedLaw[],
  timelineFilter: string
): [PreprocessedLaw[], DateRange] => {
  switch (timelineFilter) {
    case 'today': {
      const today = new Date();
      return [
        allLaws.filter(
          (law) => law.publication_date.split('T')[0] === today.toISOString().split('T')[0]
        ),
        [today, today],
      ];
    }
    case 'week': {
      const week = new Date(new Date().setDate(new Date().getDate() - 7));
      return [
        allLaws.filter((law) => law.publication_date >= week.toISOString().split('.')[0]),
        [week, new Date()],
      ];
    }
    case 'month': {
      const month = new Date(new Date().setDate(new Date().getDate() - 30));
      return [
        allLaws.filter((law) => law.publication_date >= month.toISOString().split('.')[0]),
        [month, new Date()],
      ];
    }
  }
  return [allLaws, [new Date(), new Date()]];
};
