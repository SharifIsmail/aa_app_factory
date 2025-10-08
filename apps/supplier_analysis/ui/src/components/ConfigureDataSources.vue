<script setup lang="ts">
import { DataSourceDiagram } from './icons';
import { AaText } from '@aleph-alpha/ds-components-vue';
import { ref } from 'vue';

defineEmits(['close']);

interface DataSource {
  name: string;
  url: string;
  description: string;
  enabled: boolean;
  implemented: boolean;
}

const dataSources = ref<DataSource[]>([
  {
    name: 'Google Search API',
    url: 'https://serper.dev',
    description:
      'Powerful Google Search API that provides structured data from Google search results, including knowledge graphs, organic results, and related searches.',
    enabled: true,
    implemented: true,
  },
  {
    name: 'Abstract API - Company Enrichment',
    url: 'https://www.abstractapi.com/api/company-enrichment',
    description:
      'Comprehensive company data enrichment service that provides detailed information about companies including size, industry, location, and social media profiles.',
    enabled: true,
    implemented: true,
  },
  {
    name: 'OpenCorporates',
    url: 'https://opencorporates.com/',
    description:
      'Largest open database of companies worldwide, covering 140+ jurisdictions with data on names, registration numbers, addresses, and directors.',
    enabled: false,
    implemented: false,
  },
  {
    name: 'European Business Register (EBR)',
    url: 'https://www.ebr.org/',
    description:
      'A network of official trade registers from 25 European countries, offering access to verified company data.',
    enabled: false,
    implemented: false,
  },
  {
    name: 'Worldwide Business Registries',
    url: 'https://ebra.be/worldwide-registers/',
    description:
      'Map-based access to national business registers globally, via the European Business Registry Association.',
    enabled: false,
    implemented: false,
  },
  {
    name: 'Data.gov',
    url: 'https://data.gov/',
    description:
      "U.S. government's open data portal with over 300,000 datasets including business and company information.",
    enabled: false,
    implemented: false,
  },
  {
    name: 'SEC EDGAR',
    url: 'https://www.sec.gov/edgar.shtml',
    description:
      'Access U.S. company filings including registration statements, periodic reports, and director information.',
    enabled: false,
    implemented: false,
  },
  {
    name: 'GEPIR (GS1)',
    url: 'https://gepir.gs1.org/',
    description:
      'Search for company details using barcodes or Global Location Numbers (GLNs), mostly for retail and manufacturing sectors.',
    enabled: false,
    implemented: false,
  },
  {
    name: 'Florida Department of State',
    url: 'https://dos.myflorida.com/sunbiz/',
    description: 'Search official business entity records registered in Florida.',
    enabled: false,
    implemented: false,
  },
  {
    name: 'New York Department of State',
    url: 'https://www.dos.ny.gov/corps/',
    description:
      'Lookup corporations and access CEO names and business addresses for New York-registered companies.',
    enabled: false,
    implemented: false,
  },
  {
    name: 'North Carolina Secretary of State',
    url: 'https://www.sosnc.gov/',
    description:
      'Provides search for business entities, including officials and registered agents in North Carolina.',
    enabled: false,
    implemented: false,
  },
  {
    name: 'Tennessee Secretary of State',
    url: 'https://sos.tn.gov/',
    description:
      'Search registered businesses in Tennessee, with access to company records and filing history.',
    enabled: false,
    implemented: false,
  },
]);

const showNotification = ref(false);
const notificationMessage = ref('');
const activeTab = ref('configure'); // 'configure' or 'learn'

const toggleSource = (source: DataSource) => {
  // If trying to enable a non-implemented source, show notification
  if (!source.enabled && !source.implemented) {
    notificationMessage.value = `The ${source.name} data source is not yet available. We're working to add more data sources soon.`;
    showNotification.value = true;
    return;
  }

  // Allow toggling for all sources (enabling only if implemented)
  source.enabled = !source.enabled;
};

const closeNotification = () => {
  showNotification.value = false;
};

const showCustomSourceNotification = () => {
  notificationMessage.value =
    "We're working on adding support for custom data sources. This feature will be available soon.";
  showNotification.value = true;
};

const switchTab = (tab: string) => {
  activeTab.value = tab;
};
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="flex max-h-[80vh] w-[800px] flex-col overflow-hidden rounded-lg bg-white shadow-xl">
      <!-- Header with tabs -->
      <div class="flex-shrink-0 border-b border-gray-200">
        <div class="flex">
          <button
            @click="switchTab('configure')"
            class="px-6 py-4 text-sm font-medium transition-colors focus:outline-none"
            :class="
              activeTab === 'configure'
                ? 'border-b-2 border-blue-600 bg-blue-50 text-blue-600'
                : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
            "
          >
            Configure Data Sources
          </button>
          <div class="relative">
            <button
              @click="switchTab('learn')"
              class="flex items-center gap-2 rounded-t-md border-l border-r border-t px-6 py-4 text-sm font-medium transition-colors focus:outline-none"
              :class="
                activeTab === 'learn'
                  ? 'border-b-2 border-blue-200 border-blue-600 bg-blue-50 text-blue-600'
                  : 'border-indigo-200 text-indigo-700 shadow-sm hover:bg-indigo-50 hover:text-indigo-800'
              "
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>Understand how data sources work</span>
            </button>
          </div>
          <div class="flex-grow"></div>
          <button @click="$emit('close')" class="p-4 text-gray-400 hover:text-gray-600">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto">
        <!-- Configure Tab Content -->
        <div v-if="activeTab === 'configure'" class="p-6">
          <div class="mb-5 flex items-center justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-800">Available Data Sources</h2>
              <p class="mt-1 text-sm text-gray-600">
                Enable or disable the data sources used by the AI agent system
              </p>
            </div>
            <div class="rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800">
              {{ dataSources.filter((s) => s.enabled).length }} active
            </div>
          </div>

          <div class="mb-6 space-y-4">
            <div
              v-for="source in dataSources"
              :key="source.name"
              class="rounded-lg border p-4 transition-colors"
              :class="
                source.enabled ? 'border-blue-200 bg-white shadow-sm' : 'border-gray-200 bg-gray-50'
              "
            >
              <div class="flex items-start justify-between gap-4">
                <div class="flex-grow">
                  <div class="mb-1 flex items-center gap-2">
                    <AaText
                      weight="medium"
                      :class="source.enabled ? 'text-blue-900' : 'text-gray-500'"
                    >
                      {{ source.name }}
                    </AaText>
                    <span
                      class="rounded-full px-2 py-0.5 text-xs font-medium"
                      :class="
                        source.enabled ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-500'
                      "
                    >
                      {{ source.enabled ? 'Enabled' : 'Disabled' }}
                    </span>
                    <span
                      v-if="!source.implemented"
                      class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700"
                    >
                      Coming Soon
                    </span>
                  </div>
                  <AaText size="sm" class="mb-1 text-gray-500">{{ source.url }}</AaText>
                  <AaText size="sm" class="text-gray-600">{{ source.description }}</AaText>
                </div>
                <button
                  @click="toggleSource(source)"
                  class="relative h-7 w-14 flex-shrink-0 rounded-full transition-colors"
                  :class="source.enabled ? 'bg-blue-600' : 'bg-gray-300'"
                >
                  <div
                    class="absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition-transform"
                    :class="source.enabled ? 'left-8' : 'left-1'"
                  ></div>
                </button>
              </div>
            </div>
          </div>

          <div class="flex justify-center gap-4">
            <button
              @click="showCustomSourceNotification"
              class="flex items-center gap-2 rounded-md bg-blue-600 px-5 py-2 text-white transition-colors hover:bg-blue-700"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>Add Custom Data Source</span>
            </button>
            <button
              @click="$emit('close')"
              class="px-5 py-2 text-gray-600 transition-colors hover:text-gray-800"
            >
              Close
            </button>
          </div>
        </div>

        <!-- Learn Tab Content -->
        <div v-if="activeTab === 'learn'" class="p-6">
          <!-- Diagram at the top -->
          <div class="mb-8 flex justify-center">
            <DataSourceDiagram />
          </div>

          <!-- Info content -->
          <div class="mx-auto max-w-2xl space-y-6">
            <div>
              <h3 class="mb-2 font-bold text-gray-800">What are Data Sources?</h3>
              <p class="text-gray-600">
                Data sources are specialized tools and APIs that our AI agents use to gather
                comprehensive information about suppliers. Each data source provides unique
                information that contributes to a complete risk assessment.
              </p>
            </div>

            <div>
              <h3 class="mb-2 font-bold text-gray-800">How Our Agent System Works</h3>
              <p class="mb-2 text-gray-600">
                Our supplier risk assessment system uses specialized AI agents that work together to
                discover, validate, and evaluate supplier information:
              </p>
              <ul class="list-disc space-y-1 pl-5 text-gray-600">
                <li>
                  <strong>Search Agent</strong> collects initial supplier data using these
                  configured data sources
                </li>
                <li>
                  <strong>Validate Data Agent</strong> identifies information gaps and
                  inconsistencies
                </li>
                <li>
                  <strong>Fix Gaps Agent</strong> addresses specific feedback issues through
                  targeted searches
                </li>
                <li>
                  <strong>Integration Agent</strong> combines all data into a comprehensive report
                </li>
              </ul>
            </div>

            <div>
              <h3 class="mb-2 font-bold text-gray-800">Types of Data Sources</h3>
              <ul class="list-disc space-y-1 pl-5 text-gray-600">
                <li>
                  <strong>Global Data Sources</strong> (Google Search, OpenCorporates): Used for all
                  suppliers regardless of location
                </li>
                <li>
                  <strong>Regional Data Sources</strong> (European Business Register): Provide
                  specialized information for specific countries
                </li>
                <li>
                  <strong>Specialized APIs</strong> (Company Enrichment): Offer detailed business
                  metrics and analytics
                </li>
              </ul>
            </div>

            <div>
              <h3 class="mb-2 font-bold text-gray-800">Assessment Framework</h3>
              <p class="mb-2 text-gray-600">
                Our system evaluates risks across three key dimensions:
              </p>
              <ul class="list-disc space-y-1 pl-5 text-gray-600">
                <li>
                  <strong>Country-Level Risks</strong>: Corruption, human rights issues, labor
                  practices
                </li>
                <li>
                  <strong>Industry-Level Risks</strong>: Child labor, forced labor, workplace safety
                </li>
                <li>
                  <strong>Supplier-Specific Risks</strong>: Previous violations, fines, worker
                  complaints
                </li>
              </ul>
            </div>

            <div class="mt-4 flex justify-center">
              <button
                @click="$emit('close')"
                class="px-5 py-2 text-gray-600 transition-colors hover:text-gray-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Notification popup -->
    <div
      v-if="showNotification"
      class="fixed left-1/2 top-1/2 z-[60] -translate-x-1/2 -translate-y-1/2 transform rounded-lg bg-blue-500 px-6 py-3 text-white shadow-lg"
    >
      <div class="flex items-center gap-3">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
            clip-rule="evenodd"
          />
        </svg>
        <span>{{ notificationMessage }}</span>
        <button @click="closeNotification" class="ml-2 text-white hover:text-gray-200">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>
