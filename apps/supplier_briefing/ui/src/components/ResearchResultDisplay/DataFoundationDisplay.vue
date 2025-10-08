<script setup lang="ts">
import { EnhancedDataTable } from '@/common/components';
import type { SerializedPandasObject } from '@/types';
import { isSerializedPandasObject, deserializePandasObject, prettifyKey } from '@/utils/pandas';
import { AaButton } from '@aleph-alpha/ds-components-vue';
import type { DataFrameData } from '@app-factory/shared-frontend/types';
import {
  convertDataFrameToCSV,
  convertDataFrameToExcel,
  downloadFile,
  sanitizeFilename,
} from '@app-factory/shared-frontend/utils';
import { computed, ref } from 'vue';

const props = defineProps<{
  pandasObjectsData?: Record<string, SerializedPandasObject> | null;
  resultsData?: Record<string, any> | null;
}>();

interface TableEntry {
  description: string;
  data: DataFrameData;
}

// Data display mode selection
const showAllData = ref(false);

// Get all dataframes from results repository (from present_results tool) and pandas objects repository
const getAllDataframes = computed(() => {
  const allDataframes: TableEntry[] = [];

  // First, prioritize results from present_results tool (resultsData)
  if (props.resultsData && Object.keys(props.resultsData).length > 0) {
    Object.entries(props.resultsData).forEach(([key, result]: [string, any]) => {
      // Check if this entry has dataframes (from present_results entries)
      if (
        result &&
        typeof result === 'object' &&
        result.dataframes &&
        Array.isArray(result.dataframes)
      ) {
        // Add all dataframes from this entry
        result.dataframes.forEach((dataframe: any) => {
          if (dataframe && isSerializedPandasObject(dataframe.data)) {
            try {
              const deserializedData = deserializePandasObject(dataframe.data);
              allDataframes.push({
                description: dataframe.description,
                data: deserializedData,
              });
            } catch (error) {
              console.error(
                `Error deserializing pandas object in results_data for key "${key}":`,
                error
              );
            }
          } else {
            console.error(`Cannot read data from dataframe:`, dataframe.data);
          }
        });
      }
    });
  }

  // If no results from present_results tool, fall back to pandas objects repository
  if (
    allDataframes.length === 0 &&
    props.pandasObjectsData &&
    Object.keys(props.pandasObjectsData).length > 0
  ) {
    Object.entries(props.pandasObjectsData).forEach(
      ([key, value]: [string, SerializedPandasObject]) => {
        if (isSerializedPandasObject(value)) {
          try {
            const deserializedData = deserializePandasObject(value);
            allDataframes.push({
              description: prettifyKey(key),
              data: deserializedData,
            });
          } catch (error) {
            console.error(`Error deserializing pandas object for key "${key}":`, error);
          }
        }
      }
    );
  }

  return allDataframes;
});

// Get all tables (both formatted dataframes and raw tables) from both repositories
const getAllTables = computed(() => {
  const allTables: TableEntry[] = [];

  // First, add results from present_results tool (resultsData)
  if (props.resultsData && Object.keys(props.resultsData).length > 0) {
    Object.entries(props.resultsData).forEach(([key, result]: [string, any]) => {
      // Check if this entry has dataframes (from present_results entries)
      if (
        result &&
        typeof result === 'object' &&
        result.dataframes &&
        Array.isArray(result.dataframes)
      ) {
        // Add all dataframes from this entry
        result.dataframes.forEach((dataframe_with_metadata: any) => {
          // Check if the dataframe_with_metadata.data is a serialized pandas object (new standardized format)
          if (
            dataframe_with_metadata.data &&
            isSerializedPandasObject(dataframe_with_metadata.data)
          ) {
            try {
              const deserializedData = deserializePandasObject(dataframe_with_metadata.data);
              allTables.push({
                description: dataframe_with_metadata.description || 'Dataframe',
                data: deserializedData,
              });
            } catch (error) {
              console.error(
                `Error deserializing pandas object in results_data for key "${key}":`,
                error
              );
            }
          } else {
            console.error(
              `Error deserializing pandas object in results_data for key "${key}": expected pandas object, received ${typeof dataframe_with_metadata.data} `
            );
          }
        });
      }
    });
  }

  // Then add data from sqlData repository
  if (props.pandasObjectsData && Object.keys(props.pandasObjectsData).length > 0) {
    Object.entries(props.pandasObjectsData).forEach(
      ([key, dataframe]: [string, SerializedPandasObject]) => {
        // Handle new serialized pandas format
        if (isSerializedPandasObject(dataframe)) {
          try {
            const deserializedData = deserializePandasObject(dataframe);
            allTables.push({
              description: prettifyKey(key),
              data: deserializedData,
            });
          } catch (error) {
            console.error(`Error deserializing pandas object for key "${key}":`, error);
          }
        } else {
          console.error(
            `Error deserializing pandas object in pandasObjectsData for key "${key}": expected pandas object, received ${typeof dataframe} `
          );
        }
      }
    );
  }

  return allTables;
});

// Get tables to display based on selection
const tablesToDisplay = computed(() => {
  return showAllData.value ? getAllTables.value : getAllDataframes.value;
});

const downloadAsCSV = (dataframe: TableEntry, filename: string) => {
  try {
    const csvContent = convertDataFrameToCSV(dataframe.data);
    downloadFile(csvContent, filename, {
      mimeType: 'text/csv;charset=utf-8;',
      fileExtension: 'csv',
    });
  } catch (error) {
    console.error('Error downloading CSV:', error);
  }
};

const downloadAsExcel = (dataframe: TableEntry, filename: string) => {
  try {
    const excelBlob = convertDataFrameToExcel(dataframe.data);
    downloadFile(excelBlob, filename, {
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      fileExtension: 'xlsx',
    });
  } catch (error) {
    console.error('Error downloading Excel:', error);
  }
};
</script>

<template>
  <!-- Data Tables Section -->
  <div v-if="tablesToDisplay.length > 0" class="mt-6">
    <!-- Display supporting dataframes -->
    <div class="space-y-6">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-700">Datengrundlage</h3>
        <div class="flex items-center gap-1 rounded-lg border border-gray-200 p-1">
          <button
            @click="showAllData = false"
            :class="[
              'rounded px-3 py-1 text-sm font-medium transition-colors',
              !showAllData ? 'bg-blue-500 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100',
            ]"
          >
            Relevante Daten
          </button>
          <button
            @click="showAllData = true"
            :class="[
              'rounded px-3 py-1 text-sm font-medium transition-colors',
              showAllData ? 'bg-blue-500 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100',
            ]"
          >
            Alle verfügbaren Daten
          </button>
        </div>
      </div>
      <div
        v-for="(dataframe, index) in tablesToDisplay"
        :key="index"
        class="border-core-border-default bg-core-bg-primary overflow-hidden rounded-lg border shadow-sm"
      >
        <div
          class="border-core-border-default bg-core-bg-primary flex items-center justify-between border-b px-6 py-4"
        >
          <h5 class="text-core-content-primary text-sm font-semibold">
            {{ dataframe.description }}
          </h5>
          <div class="flex items-center gap-2">
            <AaButton
              @click="
                downloadAsCSV(
                  dataframe,
                  sanitizeFilename(dataframe.description || `table_${index}`)
                )
              "
              variant="text"
              size="small"
              prepend-icon="i-material-symbols-download"
            >
              CSV
            </AaButton>
            <AaButton
              @click="
                downloadAsExcel(
                  dataframe,
                  sanitizeFilename(dataframe.description || `table_${index}`)
                )
              "
              variant="text"
              size="small"
              prepend-icon="i-material-symbols-download"
            >
              XLSX
            </AaButton>
          </div>
        </div>

        <!-- Use EnhancedDataTable component -->
        <div class="relative">
          <div class="overflow-x-auto">
            <EnhancedDataTable :dataframe="dataframe.data" :fixed-header="false" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
