<script setup lang="ts">
import ChipToggleButtons from '@/@core/components/ChipToggleButtons.vue';
import EurovocMultiSelect from '@/@core/components/EurovocMultiSelect.vue';
import Popover from '@/@core/components/Popover.vue';
import { useCompanyConfigStore } from '@/@core/stores/companyConfigStore.ts';
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { downloadContentAsFile } from '@/@core/utils/fileUtils.ts';
import {
  categoryOptions,
  aiClassificationOptions,
  searchTypeOptions,
  documentTypeOptions,
  journalSeriesOptions,
  DATE_RANGE_RESET,
} from '@/modules/monitoring/constants';
import { useLawCoordinatorStore } from '@/modules/monitoring/stores/lawCoordinatorStore.ts';
import { useLawDataStore } from '@/modules/monitoring/stores/lawDataStore.ts';
import { DisplayMode } from '@/modules/monitoring/stores/lawDisplayStore.ts';
import { useLawDisplayStore } from '@/modules/monitoring/stores/lawDisplayStore.ts';
import {
  SearchType,
  OfficialJournalSeries,
  DocumentTypeLabel,
  type DateRange,
  AiClassification,
  Category,
} from '@/modules/monitoring/types';
import { ExportScope } from '@/modules/monitoring/types';
import {
  AaButton,
  AaInput,
  AaSelect,
  AaTooltip,
  AaText,
  AaIconButton,
  type AaSelectOption,
} from '@aleph-alpha/ds-components-vue';
import VueDatePicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';
import { computed, onMounted, ref } from 'vue';

interface Props {
  selectedDateRange?: DateRange;
  dateSelectionMessage: string;
}

interface Emits {
  (e: 'date-range-change', dateRange: DateRange | null | typeof DATE_RANGE_RESET): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();
const lawCoordinatorStore = useLawCoordinatorStore();
const lawDataStore = useLawDataStore();
const companyConfigStore = useCompanyConfigStore();
const notificationStore = useNotificationStore();
const lawDisplayStore = useLawDisplayStore();

const localSearch = ref<string>('');
const selectedEurovocDescriptors = ref<string[]>([]);
const selectedDocumentType = ref<AaSelectOption<string>>();
const selectedJournalSeries = ref<AaSelectOption<string>>();
const exportRelevantButtonRef = ref();
const selectedDepartment = ref<AaSelectOption<string>>();

const selectedSearchType = ref<AaSelectOption<string>>({
  value: searchTypeOptions[0].value,
  label: searchTypeOptions[0].label,
});

const isTitleSearch = computed(() => {
  return selectedSearchType.value?.value === SearchType.TITLE;
});

const isEurovocSearch = computed(() => {
  return selectedSearchType.value?.value === SearchType.EUROVOC;
});

const isDocumentTypeSearch = computed(() => {
  return selectedSearchType.value?.value === SearchType.DOCUMENT_TYPE;
});

const isJournalSeriesSearch = computed(() => {
  return selectedSearchType.value?.value === SearchType.JOURNAL_SERIES;
});

const isDepartmentSearch = computed(() => {
  return selectedSearchType.value?.value === SearchType.DEPARTMENT;
});

const searchValidators: Record<SearchType, () => boolean> = {
  [SearchType.TITLE]: () => localSearch.value.trim().length > 0,
  [SearchType.EUROVOC]: () => selectedEurovocDescriptors.value.length > 0,
  [SearchType.DOCUMENT_TYPE]: () => selectedDocumentType.value?.value !== undefined,
  [SearchType.JOURNAL_SERIES]: () => selectedJournalSeries.value?.value !== undefined,
  [SearchType.DEPARTMENT]: () => selectedDepartment.value?.value !== undefined,
};

const canSearch = computed(() => {
  if (!selectedSearchType.value?.value) return false;

  const validator = searchValidators[selectedSearchType.value.value as SearchType];
  return validator ? validator() : false;
});

function resetFilters() {
  localSearch.value = '';
  selectedEurovocDescriptors.value = [];
  selectedDocumentType.value = undefined;
  selectedJournalSeries.value = undefined;
  selectedDepartment.value = undefined;
  lawDisplayStore.isInitialFilterApplied = false;
}

function handleDateRangeChange(dateRange: DateRange | null) {
  const currentRange = props.selectedDateRange;
  const newRange = dateRange;

  // Check if the ranges are the same
  if (
    currentRange &&
    newRange &&
    currentRange.length === newRange.length &&
    currentRange.every((date, index) => date.getTime() === newRange[index].getTime())
  ) {
    return;
  }

  if (!currentRange && !newRange) {
    return;
  }

  resetFilters();
  emit('date-range-change', dateRange);
}

function handleSearchTypeChange(option: AaSelectOption<string> | null) {
  if (option) {
    selectedSearchType.value = option;

    resetFilters();
  }
}

function handleDocumentTypeChange(option: AaSelectOption<string> | null) {
  if (option) {
    selectedDocumentType.value = option;
  } else {
    selectedDocumentType.value = undefined;
  }
}

function handleJournalSeriesChange(option: AaSelectOption<string> | null) {
  if (option) {
    selectedJournalSeries.value = option;
  } else {
    selectedJournalSeries.value = undefined;
  }
}

function handleDepartmentChange(option: AaSelectOption<string> | null) {
  if (option) {
    selectedDepartment.value = option;
  } else {
    selectedDepartment.value = undefined;
  }
}

const searchExecutors: Record<SearchType, () => void> = {
  [SearchType.TITLE]: () => lawCoordinatorStore.searchLawsByTitle(localSearch.value.trim()),
  [SearchType.EUROVOC]: () =>
    lawCoordinatorStore.searchLawsByEurovoc(selectedEurovocDescriptors.value),
  [SearchType.DOCUMENT_TYPE]: () =>
    selectedDocumentType.value?.value &&
    lawCoordinatorStore.searchLawsByDocumentType(
      selectedDocumentType.value.value as DocumentTypeLabel
    ),
  [SearchType.JOURNAL_SERIES]: () =>
    selectedJournalSeries.value?.value &&
    lawCoordinatorStore.searchLawsByJournalSeries(
      selectedJournalSeries.value.value as OfficialJournalSeries
    ),
  [SearchType.DEPARTMENT]: () =>
    selectedDepartment.value?.value &&
    lawCoordinatorStore.searchLawsByDepartment(selectedDepartment.value.value),
};

function executeSearch() {
  if (!canSearch.value || !selectedSearchType.value?.value) return;

  emit('date-range-change', DATE_RANGE_RESET); // reset date range

  const executor = searchExecutors[selectedSearchType.value.value as SearchType];
  executor?.();
}

async function resetSearch() {
  resetFilters();
  await lawCoordinatorStore.resetSearch();
}

function handleSearchKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    executeSearch();
  }
}

async function downloadRelevantCsv() {
  try {
    const csvContent = await lawDataStore.downloadRelevantCsv();
    if (!csvContent) {
      notificationStore.addErrorNotification('CSV download failed, please try again.');
      return;
    }
    const today = new Date().toISOString().split('T')[0];
    const filename = `relevant_legal_acts_${today}.csv`;
    downloadContentAsFile(csvContent, filename, { mimeType: 'text/csv' });
    notificationStore.addSuccessNotification('CSV export completed successfully.');
  } catch (error: any) {
    console.error('CSV download failed:', error);
    notificationStore.addErrorNotification('CSV download failed, please try again.');
  }
}

async function downloadAllEvaluatedCsv() {
  try {
    const csvContent = await lawDataStore.downloadRelevantCsv(ExportScope.AllEvaluated);
    if (!csvContent) {
      notificationStore.addErrorNotification('CSV download failed, please try again.');
      return;
    }
    const today = new Date().toISOString().split('T')[0];
    const filename = `evaluated_legal_acts_${today}.csv`;
    downloadContentAsFile(csvContent, filename, { mimeType: 'text/csv' });
    notificationStore.addSuccessNotification('CSV export completed successfully.');
  } catch (error: any) {
    console.error('CSV download failed:', error);
    notificationStore.addErrorNotification('CSV download failed, please try again.');
  }
}

function setDefaultFilters() {
  lawDisplayStore.isInitialFilterApplied = true;

  selectedSearchType.value = {
    value: SearchType.JOURNAL_SERIES,
    label: 'Journal Series',
  };

  handleJournalSeriesChange({
    value: OfficialJournalSeries.L_SERIES,
    label: 'L-Series',
  });

  if (isJournalSeriesSearch.value && selectedJournalSeries.value) {
    executeSearch();
  }
}

onMounted(async () => {
  if (companyConfigStore.companyConfig.teams.length === 0) {
    companyConfigStore.fetchCompanyConfig();
  }
  if (lawDisplayStore.isInitialFilterApplied) {
    setDefaultFilters();
  }
});
</script>

<template>
  <div>
    <div class="flex justify-between py-4">
      <div class="w-100 flex items-center">
        <AaText size="sm" weight="bold" class="text-core-content-tertiary block w-40"
          >Date of release</AaText
        >
        <VueDatePicker
          auto-apply
          range
          :model-value="props.selectedDateRange"
          :enable-time-picker="false"
          :min-date="lawDataStore.firstDate"
          :max-date="lawDataStore.lastDate"
          :disabled-dates="lawDataStore.disabledDates"
          @update:model-value="handleDateRangeChange"
          placeholder="Select date range"
          format="dd.MM.yyyy"
          range-separator=" - "
          clearable
          :disabled="lawCoordinatorStore.isLoadingDates"
          :loading="lawCoordinatorStore.isLoadingDates"
        />
        <div v-if="dateSelectionMessage" class="text-semantic-content-warning text-sm">
          {{ dateSelectionMessage }}
        </div>
      </div>
      <div class="flex items-center gap-4">
        <Popover placement="bottom-end" width="400px">
          <template #trigger="{ disabled, toggle }">
            <AaButton
              :variant="
                lawCoordinatorStore.displayMode === DisplayMode.SEARCH ? 'secondary' : 'outline'
              "
              :disabled="disabled"
              @click="toggle"
              prepend-icon="i-material-symbols-filter-alt-outline"
              append-icon="i-material-symbols-arrow-drop-down"
            >
              Filter
            </AaButton>
          </template>

          <AaText weight="bold">Filter By</AaText>
          <AaSelect
            :model-value="selectedSearchType"
            :options="searchTypeOptions"
            @update:model-value="handleSearchTypeChange"
            placeholder="Search Type"
            class="searchType"
            size="medium"
          />
          <AaInput
            v-if="isTitleSearch"
            v-model="localSearch"
            placeholder="Type title"
            @keydown="handleSearchKeydown"
            class="h-9"
          />
          <EurovocMultiSelect
            v-if="isEurovocSearch"
            v-model="selectedEurovocDescriptors"
            placeholder="Select Eurovoc descriptors"
          />
          <AaSelect
            v-if="isDocumentTypeSearch"
            :model-value="selectedDocumentType"
            :options="documentTypeOptions"
            @update:model-value="handleDocumentTypeChange"
            placeholder="Select Document Type"
            size="medium"
          />
          <AaSelect
            v-if="isJournalSeriesSearch"
            :model-value="selectedJournalSeries"
            :options="journalSeriesOptions"
            @update:model-value="handleJournalSeriesChange"
            placeholder="Select Journal Series"
            size="medium"
          />
          <AaSelect
            v-if="isDepartmentSearch"
            :model-value="selectedDepartment"
            :options="companyConfigStore.departmentOptions"
            :loading="companyConfigStore.isLoading"
            @update:model-value="handleDepartmentChange"
            placeholder="Select Department"
            size="medium"
          />
          <AaButton
            variant="primary"
            :disabled="!canSearch"
            @click="executeSearch"
            prepend-icon="i-material-symbols-search"
            class="h-10 justify-center"
          >
            Search
          </AaButton>
          <AaButton
            :disabled="lawCoordinatorStore.displayMode !== DisplayMode.SEARCH"
            variant="secondary"
            @click="resetSearch"
            prepend-icon="i-material-symbols-close"
            class="h-10 justify-center"
          >
            Reset
          </AaButton>
        </Popover>
        <div class="flex items-center gap-2">
          <!-- Main export action -->
          <AaButton
            ref="exportRelevantButtonRef"
            variant="outline"
            :loading="lawDataStore.isDownloadingRelevantCsv"
            :disabled="lawDataStore.isDownloadingRelevantCsv"
            @click="downloadRelevantCsv"
            prepend-icon="i-material-symbols-download"
          >
            Export Relevant
          </AaButton>
          <Popover placement="bottom-end" width="180px" :style="{ minHeight: 'revert' }">
            <template #trigger="{ disabled, toggle }">
              <AaIconButton
                :disabled="disabled || lawDataStore.isDownloadingRelevantCsv"
                variant="outline"
                icon="i-material-symbols-more-vert"
                label="More actions"
                aria-label="More actions"
                @click="toggle"
              />
            </template>

            <div class="flex flex-col gap-2">
              <AaButton
                variant="text"
                :loading="lawDataStore.isDownloadingAllEvaluatedCsv"
                :disabled="lawDataStore.isDownloadingAllEvaluatedCsv"
                class="justify-start"
                @click="downloadAllEvaluatedCsv"
              >
                Export Evaluated
              </AaButton>
            </div>
          </Popover>

          <AaTooltip :anchor="exportRelevantButtonRef">
            Download all legal acts marked as relevant to CSV.
          </AaTooltip>
        </div>
      </div>
    </div>
    <div class="flex justify-between py-4">
      <div class="flex items-center gap-12">
        <ChipToggleButtons
          title="AI Classification"
          :model-value="lawCoordinatorStore.aiClassificationFilter"
          :options="aiClassificationOptions"
          @update:model-value="
            (value) =>
              lawCoordinatorStore.setAiClassificationFilter(value as 'ALL' | AiClassification)
          "
        />
        <ChipToggleButtons
          title="Human Decision"
          :model-value="lawCoordinatorStore.categoryFilter"
          :options="categoryOptions"
          @update:model-value="
            (value) => lawCoordinatorStore.setCategoryFilter(value as 'ALL' | Category)
          "
        />
      </div>

      <AaText size="sm" weight="bold" class="text-core-content-tertiary">
        Displaying {{ lawCoordinatorStore.displayedLaws.length }} of
        {{ lawDataStore.paginationMetadata?.total_items }} total legal acts
      </AaText>
    </div>
  </div>
</template>

<style scoped>
.dp__main :deep(.dp__theme_light) {
  --dp-primary-color: #e9f781;
  --dp-primary-text-color: #1e1e24;
}

.dp__main :deep(.dp__input)::placeholder {
  color: #1e1e24;
}

.dp__main :deep(.dp__input:focus) {
  outline: 2px solid #555cf9;
  outline-offset: 2px;
  border-color: #555cf9;
}

.dp__main :deep(.dp__input:focus-visible) {
  outline: 2px solid #555cf9;
  outline-offset: 2px;
  border-color: #555cf9;
}

/* Base view might override this style */
.searchType :deep(.aa-button) {
  border-color: #d1d5db !important;
}
</style>
