import type { PreprocessedLaw } from '@/modules/monitoring/types';

/**
 * Check if a law is possibly relevant based on team relevancy classifications
 */
export function isLikelyRelevant(law: PreprocessedLaw): boolean {
  return law.team_relevancy_classification?.some((c) => c.is_relevant) ?? false;
}

/**
 * Get the priority order for relevancy sorting
 * Lower numbers = higher priority (sorted first)
 */
function getRelevancyPriority(law: PreprocessedLaw): number {
  return isLikelyRelevant(law) ? 0 : 1; // Possibly relevant first
}

/**
 * Get the priority order for law status sorting
 * Lower numbers = higher priority (sorted first)
 */
function getStatusPriority(status: string): number {
  switch (status) {
    case 'FAILED':
      return 1; // Highest priority - errors first
    case 'PROCESSED':
      return 2; // Second priority - completed work
    case 'PROCESSING':
      return 3; // Third priority - currently being worked on
    case 'RAW':
      return 3; // Third priority - pending work (same as processing)
    default:
      return 5; // Unknown status goes last
  }
}

/**
 * Sort laws by date first, then relevancy, then by status priority (FAILED → PROCESSED → PENDING)
 */
export function sortLawsByDateAndStatus(laws: PreprocessedLaw[]): PreprocessedLaw[] {
  return laws.sort((a, b) => {
    // First sort by publication date (newer first)
    const dateA = new Date(a.publication_date).getTime();
    const dateB = new Date(b.publication_date).getTime();
    const dateDiff = dateB - dateA;
    if (dateDiff !== 0) {
      return dateDiff;
    }

    // If same date, sort by relevancy priority (possibly relevant first)
    const relevancyDiff = getRelevancyPriority(a) - getRelevancyPriority(b);
    if (relevancyDiff !== 0) {
      return relevancyDiff;
    }

    // If same date and relevancy, sort by status priority
    return getStatusPriority(a.status) - getStatusPriority(b.status);
  });
}

/**
 * Group laws by their publication date
 * Returns a record where keys are date strings and values are arrays of laws
 */
export function groupLawsByDate(laws: PreprocessedLaw[]): Record<string, PreprocessedLaw[]> {
  return laws.reduce(
    (grouped, law) => {
      const dateKey = law.publication_date;
      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(law);
      return grouped;
    },
    {} as Record<string, PreprocessedLaw[]>
  );
}

/**
 * Get sorted date keys from grouped laws (newest first)
 */
export function getSortedDateKeys(groupedLaws: Record<string, PreprocessedLaw[]>): string[] {
  return Object.keys(groupedLaws).sort((a, b) => new Date(b).getTime() - new Date(a).getTime());
}
