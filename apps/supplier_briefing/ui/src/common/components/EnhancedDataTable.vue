<script setup lang="ts">
import type { DataFrameData } from '@app-factory/shared-frontend/types';
import { computed, onBeforeUnmount, onMounted, ref, type PropType } from 'vue';
import { VueGoodTable } from 'vue-good-table-next';
import 'vue-good-table-next/dist/vue-good-table-next.css';

const props = defineProps({
  dataframe: {
    type: Object as PropType<DataFrameData>,
    required: true,
  },
  showLineNumbers: {
    type: Boolean,
    default: false,
  },
  maxHeight: {
    type: String,
    default: 'none',
  },
  fixedHeader: {
    type: Boolean,
    default: false,
  },
  rowStyleClass: {
    type: Function as PropType<(row: any) => string>,
    default: () => '',
  },
});

const showSearchAndFilters = computed(() => {
  return props.dataframe.data.length >= 30;
});

function isEmptyValue(value: any): boolean {
  return value === null || value === undefined || value === '';
}

function normalizeNumericString(value: string): string {
  return value.replace(/,/g, '.');
}

function isNumericString(value: string): boolean {
  const normalized = normalizeNumericString(value.trim());
  return !isNaN(Number(normalized)) && value.trim() !== '';
}

function hasDecimalPoint(value: string): boolean {
  return value.includes('.') || value.includes(',');
}

function determineNumericType(hasDecimals: boolean): 'decimal' | 'number' {
  return hasDecimals ? 'decimal' : 'number';
}

function analyzeValueType(value: any): 'text' | 'number' | 'decimal' | null {
  if (isEmptyValue(value)) {
    return null;
  }

  const stringValue = String(value).trim();

  if (!isNumericString(stringValue)) {
    return 'text';
  }

  return hasDecimalPoint(stringValue) ? 'decimal' : 'number';
}

function detectTypeFromValueAccessor(totalCount: number, getValue: (index: number) => any): string {
  let hasNumbers = false;
  let hasDecimals = false;

  for (let i = 0; i < totalCount; i++) {
    const valueType = analyzeValueType(getValue(i));

    if (valueType === null) {
      continue;
    }

    if (valueType === 'text') {
      return 'text';
    }

    hasNumbers = true;
    if (valueType === 'decimal') {
      hasDecimals = true;
    }
  }

  if (!hasNumbers) {
    return 'text';
  }

  return determineNumericType(hasDecimals);
}

function detectColumnType(columnIndex: number): string {
  return detectTypeFromValueAccessor(
    props.dataframe.data.length,
    (rowIndex) => props.dataframe.data[rowIndex]?.[columnIndex]
  );
}

function detectIndexColumnType(indexValues: (string | number)[]): string {
  return detectTypeFromValueAccessor(indexValues.length, (index) => indexValues[index]);
}

const tableColumns = computed(() => {
  const columns = [];

  // Check if we have MultiIndex (first index entry is an array)
  const hasMultiIndex = props.dataframe.index.length > 0 && Array.isArray(props.dataframe.index[0]);

  if (hasMultiIndex) {
    // Create separate columns for each index level
    const multiIndex = props.dataframe.index as (string | number)[][];
    const indexLevels = multiIndex[0].length;
    for (let i = 0; i < indexLevels; i++) {
      const indexName = props.dataframe.index_names?.[i] || `#${i}`;
      const levelValues = multiIndex.map((row) => row[i]);
      columns.push({
        label: indexName,
        field: `index_level_${i}`,
        type: detectIndexColumnType(levelValues),
        sortable: true,
        filterOptions: {
          enabled: showSearchAndFilters.value,
          placeholder: 'Filter...',
        },
      });
    }
  } else if (props.dataframe.index.length > 0) {
    const simpleIndex = props.dataframe.index as (string | number)[];
    columns.push({
      label: props.dataframe.index_names?.[0] || '#',
      field: 'index',
      type: detectIndexColumnType(simpleIndex),
      sortable: true,
      filterOptions: {
        enabled: showSearchAndFilters.value,
        placeholder: 'Filter...',
      },
    });
  }

  props.dataframe.columns.forEach((col, colIndex) => {
    columns.push({
      label: String(col),
      field: String(col),
      type: detectColumnType(colIndex),
      sortable: true,
      filterOptions: {
        enabled: showSearchAndFilters.value,
        placeholder: 'Filter...',
      },
    });
  });

  return columns;
});

const tableRows = computed(() => {
  const hasMultiIndex = props.dataframe.index.length > 0 && Array.isArray(props.dataframe.index[0]);

  return props.dataframe.data.map((row, rowIndex) => {
    const rowObj: any = {
      originalIndex: rowIndex,
    };

    if (hasMultiIndex) {
      // MultiIndex: create separate fields for each level
      const multiIndex = props.dataframe.index as (string | number)[][];
      const indexValues = multiIndex[rowIndex];
      indexValues.forEach((value, levelIndex) => {
        rowObj[`index_level_${levelIndex}`] = value;
      });
    } else if (props.dataframe.index.length > 0) {
      const simpleIndex = props.dataframe.index as (string | number)[];
      rowObj.index = simpleIndex[rowIndex];
    }

    props.dataframe.columns.forEach((col, colIndex) => {
      rowObj[String(col)] = row[colIndex];
    });

    return rowObj;
  });
});

// Manage horizontal overflow indicators on the inner vue-good-table container
const tableRootEl = ref<HTMLElement | null>(null);
const showLeftShadow = ref<boolean>(false);
const showRightShadow = ref<boolean>(false);
let responsiveEl: HTMLElement | null = null;
let resizeObserver: ResizeObserver | null = null;

function updateShadows(): void {
  if (!responsiveEl) return;
  const hasOverflow = responsiveEl.scrollWidth > responsiveEl.clientWidth + 1;
  if (!hasOverflow) {
    showLeftShadow.value = false;
    showRightShadow.value = false;
    return;
  }
  const atStart = responsiveEl.scrollLeft <= 0;
  const atEnd =
    Math.ceil(responsiveEl.scrollLeft + responsiveEl.clientWidth) >= responsiveEl.scrollWidth;
  showLeftShadow.value = !atStart;
  showRightShadow.value = !atEnd;
}

function onScroll(): void {
  updateShadows();
}

onMounted(() => {
  // Find the inner horizontal scroller produced by vue-good-table-next
  responsiveEl = tableRootEl.value?.querySelector('.vgt-responsive') as HTMLElement | null;
  if (responsiveEl) {
    responsiveEl.addEventListener('scroll', onScroll, { passive: true } as AddEventListenerOptions);
    // Observe size/content changes to recompute overflow state
    resizeObserver = new ResizeObserver(() => updateShadows());
    resizeObserver.observe(responsiveEl);
    // Initial state
    updateShadows();
  }
});

onBeforeUnmount(() => {
  if (responsiveEl) {
    responsiveEl.removeEventListener('scroll', onScroll as EventListener);
  }
  if (resizeObserver && responsiveEl) {
    resizeObserver.unobserve(responsiveEl);
  }
  resizeObserver = null;
  responsiveEl = null;
});
</script>

<template>
  <div class="enhanced-data-table" ref="tableRootEl">
    <VueGoodTable
      :columns="tableColumns"
      :rows="tableRows"
      :search-options="{
        enabled: showSearchAndFilters,
        placeholder: 'Search in table...',
      }"
      :pagination-options="{
        enabled: true,
        mode: 'records',
        perPage: 50,
        position: 'bottom',
        perPageDropdown: [10, 25, 50, 100],
        dropdownAllowAll: false,
        nextLabel: 'Next',
        prevLabel: 'Previous',
        rowsPerPageLabel: 'Rows per page',
        ofLabel: 'of',
        allLabel: 'All',
      }"
      :sort-options="{
        enabled: true,
        multipleColumns: false,
      }"
      style-class="vgt-table striped bordered"
      :line-numbers="showLineNumbers"
      :max-height="maxHeight !== 'none' ? maxHeight : undefined"
      :fixed-header="fixedHeader"
      :row-style-class="rowStyleClass"
      theme="default"
    >
      <template #emptystate>
        <div class="py-4 text-center text-gray-500">No data available</div>
      </template>
      <template #table-row="tableProps">
        <span> {{ tableProps.formattedRow[tableProps.column.field] }} </span>
      </template>
    </VueGoodTable>
    <div v-show="showLeftShadow" class="h-shadow left" aria-hidden="true">
      <div class="h-shadow-arrow left-arrow">‹</div>
    </div>

    <div v-show="showRightShadow" class="h-shadow right" aria-hidden="true">
      <div class="h-shadow-arrow right-arrow">›</div>
    </div>
  </div>
</template>

<style scoped>
.enhanced-data-table {
  @apply w-full;
}

:deep(.vgt-wrap) {
  @apply w-full;
}

:deep(.vgt-table) {
  @apply w-full table-auto text-xs;
}

:deep(.vgt-table thead th) {
  @apply whitespace-nowrap bg-gray-100 px-1 py-1;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: #4b5563 !important;
}

:deep(.vgt-table tbody td) {
  @apply border-b border-gray-200 px-1 py-1;
  font-size: 0.75rem !important;
  color: #4b5563 !important;
}

:deep(.vgt-table tbody tr:hover) {
  @apply bg-gray-50;
}

:deep(.vgt-global-search) {
  @apply mb-2;
}

:deep(.vgt-global-search__input) {
  @apply w-full rounded-md border border-gray-300 px-3 py-1 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500;
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.vgt-pagination) {
  @apply mt-2 flex items-center justify-between;
}

:deep(.vgt-pagination__info) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.vgt-pagination__page-btn) {
  @apply mx-0.5 cursor-pointer rounded border border-gray-300 px-1 py-0.5 hover:bg-gray-100;
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.vgt-pagination__page-btn.disabled) {
  @apply cursor-not-allowed opacity-50 hover:bg-white;
}

:deep(.vgt-pagination__page-btn.active) {
  @apply border-blue-500 bg-blue-500 text-white hover:bg-blue-600;
}

:deep(.footer__row-count__select) {
  @apply rounded border border-gray-300 px-1 py-0.5 focus:outline-none focus:ring-2 focus:ring-blue-500;
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.footer__row-count__label) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.footer__row-count) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.footer__navigation) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.footer__navigation__page-info) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.footer__navigation__page-btn) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.footer__navigation__page-btn span) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.page-info) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.page-info__label) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.footer__navigation__page-info__current-entry) {
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

:deep(.vgt-table th.sortable) {
  @apply cursor-pointer select-none;
}

:deep(.vgt-table th.sortable:hover) {
  @apply bg-gray-200;
}

:deep(.vgt-table th.sorting-asc::after) {
  content: ' ↑';
  @apply text-blue-500;
}

:deep(.vgt-table th.sorting-desc::after) {
  content: ' ↓';
  @apply text-blue-500;
}

:deep(.vgt-filter-row) {
  @apply bg-gray-50;
}

:deep(.vgt-filter-row td) {
  @apply py-1.5;
}

:deep(.vgt-filter-row input) {
  @apply w-full rounded border border-gray-300 px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-500;
  font-size: 0.75rem !important;
  color: #6b7280 !important;
}

/* Horizontal overflow hint shadows */
.h-shadow {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 18px;
  pointer-events: none;
  z-index: 5;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 8px;
}
.h-shadow.left {
  left: 0;
  background: linear-gradient(to right, rgba(0, 0, 0, 0.08), rgba(0, 0, 0, 0));
}
.h-shadow.right {
  right: 0;
  background: linear-gradient(to left, rgba(0, 0, 0, 0.08), rgba(0, 0, 0, 0));
}

/* Arrow indicators within shadows */
.h-shadow-arrow {
  font-size: 18px;
  font-weight: bold;
  color: rgba(75, 85, 99, 0.7);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  user-select: none;
  animation: pulse-arrow 2s ease-in-out infinite;
}

.h-shadow-arrow.left-arrow {
  margin-left: -2px;
}

.h-shadow-arrow.right-arrow {
  margin-right: -2px;
}

@keyframes pulse-arrow {
  0%,
  100% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
}
</style>
