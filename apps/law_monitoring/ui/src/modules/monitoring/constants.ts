import {
  AiClassification,
  Category,
  DocumentTypeLabel,
  OfficialJournalSeries,
  SearchType,
} from '@/modules/monitoring/types';

const searchTypeLabels: Record<SearchType, string> = {
  [SearchType.TITLE]: 'Title',
  [SearchType.EUROVOC]: 'Eurovoc',
  [SearchType.DOCUMENT_TYPE]: 'Document Type',
  [SearchType.JOURNAL_SERIES]: 'Journal Series',
  [SearchType.DEPARTMENT]: 'Department',
};

export const searchTypeOptions = Object.entries(searchTypeLabels).map(([value, label]) => ({
  value: value as SearchType,
  label,
}));

export const categoryOptions = [
  { value: 'ALL', label: 'All' },
  { value: Category.OPEN, label: 'No Decision' },
  { value: Category.RELEVANT, label: 'Relevant' },
  { value: Category.NOT_RELEVANT, label: 'Not Relevant' },
];

export const aiClassificationOptions = [
  { value: 'ALL', label: 'All' },
  { value: AiClassification.LIKELY_RELEVANT, label: 'Likely Relevant' },
  { value: AiClassification.LIKELY_IRRELEVANT, label: 'Likely Not Relevant' },
];

export const documentTypeOptions = Object.values(DocumentTypeLabel)
  .filter((type) => type !== DocumentTypeLabel.UNKNOWN)
  .map((type) => ({
    value: type,
    label: type,
  }));

export const journalSeriesOptions = Object.values(OfficialJournalSeries)
  .filter((type) => type !== OfficialJournalSeries.UNKNOWN)
  .map((type) => ({
    value: type,
    label: type,
  }));

// Shared sentinel values
export const DATE_RANGE_RESET = 'reset' as const;
export type DateRangeReset = typeof DATE_RANGE_RESET;
