<script setup lang="ts">
import { AaButton, AaInfoBadge } from '@aleph-alpha/ds-components-vue';
import { ref } from 'vue';

defineProps<{
  structuredData: Record<string, any> | null;
  extractedData: string | null;
  searchStatus: string | null;
}>();

const isDataPanelExpanded = ref(false);

const makeUrlsClickable = (text: string) => {
  if (!text) return text;
  const urlRegex = /(https?:\/\/[\w\-._~:/?#[\]@!$&'()*+,;=%]+[\w\-_/])/g;
  return text.replace(
    urlRegex,
    (url) =>
      `<a href="${url}" target="_blank" class="text-blue-500 hover:text-blue-700 hover:underline">${url}</a>`
  );
};

const renderStructuredValue = (value: any) => {
  const raw = value && typeof value === 'object' ? value.value : value;
  if (isDataPanelExpanded.value) {
    return makeUrlsClickable(
      raw
        ?.replace(/(^|[^<br>\n])Source URL:/g, (match: string, p1: string) =>
          p1 === '' || p1 === '\n' || p1.endsWith('<br>')
            ? p1 + 'Source URL:'
            : p1 + '<br>Source URL:'
        )
        ?.replace(/\n/g, '<br>')
    );
  }
  return makeUrlsClickable(raw);
};
</script>

<template>
  <div
    v-if="structuredData && Object.keys(structuredData).length > 0 && searchStatus !== 'COMPLETED'"
    class="research-data-panel relative mb-4 flex-shrink-0 rounded-lg bg-white text-sm shadow-md"
    :style="{
      height: isDataPanelExpanded ? 'auto' : '300px',
      padding: '8px',
      overflowY: 'scroll',
    }"
  >
    <div
      class="sticky top-0 z-20 flex items-center justify-between border-b border-gray-200 bg-white shadow-sm"
      :class="{ 'mb-2 px-2 py-3': !isDataPanelExpanded, 'mb-3 p-2': isDataPanelExpanded }"
    >
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Data found so far</span>
        <AaInfoBadge :soft="true" variant="success">
          {{ Object.keys(structuredData).length }} entries
        </AaInfoBadge>
      </div>
      <AaButton
        @click="isDataPanelExpanded = !isDataPanelExpanded"
        variant="outline"
        size="small"
        :prepend-icon="
          isDataPanelExpanded ? 'i-material-symbols-close' : 'i-material-symbols-grid-view'
        "
      >
        {{ isDataPanelExpanded ? 'Collapse' : 'Expand' }}
      </AaButton>
    </div>

    <!-- Display structured data when available -->
    <div
      v-if="structuredData && Object.keys(structuredData).length > 0"
      :class="[
        'p-4',
        isDataPanelExpanded ? 'space-y-4' : 'grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3',
      ]"
    >
      <div
        v-for="(value, key) in structuredData"
        :key="key"
        :class="{
          'flex items-center overflow-hidden whitespace-nowrap rounded-md border border-gray-200 p-3 shadow-sm transition-shadow hover:shadow-md':
            !isDataPanelExpanded,
          'flex flex-col border-b border-gray-100 pb-3': isDataPanelExpanded,
        }"
        :title="
          !isDataPanelExpanded ? key + ': ' + (typeof value === 'object' ? value.value : value) : ''
        "
      >
        <div
          :class="[
            'font-medium text-blue-600',
            isDataPanelExpanded ? 'mb-2' : 'w-18 mr-2 shrink-0 truncate',
          ]"
        >
          {{ key.replace('_', ' ').replace(/^./, (c) => c.toUpperCase()) }}
        </div>
        <div
          :class="[
            'text-gray-700',
            isDataPanelExpanded ? 'break-words' : 'flex flex-1 items-center overflow-hidden',
          ]"
        >
          <span
            :class="[isDataPanelExpanded ? '' : 'inline-block max-w-[calc(100%-45px)] truncate']"
            v-html="renderStructuredValue(value)"
          >
          </span>
          <a
            v-if="value && typeof value === 'object' && value.source_url"
            :href="value.source_url"
            target="_blank"
            :class="[
              'text-xs text-gray-500 hover:text-blue-500 hover:underline',
              isDataPanelExpanded ? 'mt-1 block' : 'ml-1 inline-flex shrink-0 items-center',
            ]"
            :title="'Source: ' + value.source_url"
          >
            [source]
          </a>
        </div>
      </div>
    </div>

    <!-- Fallback to plain text display when structured data is not available -->
    <div v-else :class="['text-gray-700', isDataPanelExpanded ? 'p-4' : 'mt-2']">
      <div v-if="isDataPanelExpanded">
        <!-- In expanded view: preserve formatting and show full URLs -->
        <div v-for="(line, index) in extractedData?.split('\n') || []" :key="index" class="mb-2">
          <template v-if="line.includes('(SOURCE URL:')">
            <!-- Handle lines with source URLs -->
            <div>
              {{ line.split('(SOURCE URL:')[0].trim() }}
              <a
                v-if="line.includes('(SOURCE URL:')"
                :href="line.split('(SOURCE URL:')[1].replace(')', '').trim()"
                target="_blank"
                class="ml-2 text-xs text-gray-500 hover:text-blue-500 hover:underline"
              >
                [source]
              </a>
            </div>
          </template>
          <template v-else>
            <!-- Regular lines without source URLs -->
            <div v-html="makeUrlsClickable(line)"></div>
          </template>
        </div>
      </div>
      <div v-else>
        <!-- In collapsed view: process each line to handle source URLs -->
        <div
          v-for="(line, index) in extractedData?.split('\n') || []"
          :key="index"
          class="truncate"
        >
          <template v-if="line.includes('(SOURCE URL:')">
            <span class="inline-block max-w-[calc(100%-45px)] truncate">
              {{ line.split('(SOURCE URL:')[0].trim() }}
            </span>
            <a
              :href="line.split('(SOURCE URL:')[1].replace(')', '').trim()"
              target="_blank"
              class="ml-1 inline-flex items-center text-xs text-gray-500 hover:text-blue-500 hover:underline"
            >
              [source]
            </a>
          </template>
          <template v-else>
            <span v-html="makeUrlsClickable(line)"></span>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
