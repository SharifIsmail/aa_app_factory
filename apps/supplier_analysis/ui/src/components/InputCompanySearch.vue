<script setup lang="ts">
import { countries } from '@/data/countries';
import type { Country } from '@/data/countries';
import { companyDataService } from '@/utils/http';
import { AaText, AaButton, AaModal } from '@aleph-alpha/ds-components-vue';
import { ref, computed, onMounted } from 'vue';

// Define company data interface
interface CompanyData {
  uuid: string;
  name: string;
  hasCompanyDataReport: boolean;
  hasRisksReport: boolean;
  processingDate: string;
}

const companyName = ref('');
const selectedCountry = ref('');
const countrySearchQuery = ref('');
const isSearching = ref(false);
const isRisksSearching = ref(false);
const showCountryDropdown = ref(false);
const researchType = ref('comprehensive');
const companyNameError = ref(false);
const countryError = ref(false);
const shakeCompanyName = ref(false);
const shakeCountry = ref(false);
const previousCompanies = ref<CompanyData[]>([]);
const isLoadingCompanies = ref(false);
const showRisksMessage = ref(false);
const risksResponse = ref('');
const messageType = ref<'success' | 'error' | 'info'>('info');

const emit = defineEmits(['search-started', 'risks-search-started']);

// Fetch previously processed companies
const fetchPreviousCompanies = async () => {
  isLoadingCompanies.value = true;
  try {
    previousCompanies.value = await companyDataService.getCompaniesList();
  } catch (error) {
    console.error('Error fetching companies:', error);
  } finally {
    isLoadingCompanies.value = false;
  }
};

// Load companies on component mount
onMounted(() => {
  fetchPreviousCompanies();
});

const filteredCountries = computed(() => {
  if (!countrySearchQuery.value) return countries;
  const query = countrySearchQuery.value.toLowerCase();
  return countries.filter((country) => country.label.toLowerCase().includes(query));
});

const selectCountry = (country: Country) => {
  selectedCountry.value = country.value;
  showCountryDropdown.value = false;
};

const getSelectedCountryLabel = computed(() => {
  const country = countries.find((c) => c.value === selectedCountry.value);
  return country ? country.label : 'Select Country *';
});

const isFormValid = computed(() => {
  return companyName.value.trim() !== '' && selectedCountry.value !== '';
});

const searchCompany = async () => {
  companyNameError.value = false;
  countryError.value = false;
  shakeCompanyName.value = false;
  shakeCountry.value = false;

  if (companyName.value.trim() === '') {
    companyNameError.value = true;
    shakeCompanyName.value = true;
    setTimeout(() => (shakeCompanyName.value = false), 500);
  }

  if (selectedCountry.value === '') {
    countryError.value = true;
    shakeCountry.value = true;
    setTimeout(() => (shakeCountry.value = false), 500);
  }

  if (companyNameError.value || countryError.value) {
    return;
  }

  if (isFormValid.value) {
    isSearching.value = true;
    try {
      const data = await companyDataService.searchCompanyData(
        companyName.value,
        selectedCountry.value,
        researchType.value
      );
      emit('search-started', data.id);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      isSearching.value = false;
    }
  }
};

const showRisksPreview = async () => {
  try {
    // Check if company name is provided
    if (!companyName.value.trim()) {
      showRisksMessage.value = true;
      messageType.value = 'error';
      risksResponse.value = 'Please enter a company name in the input field';
      return;
    }

    isRisksSearching.value = true;

    // Use the company name from the input field and pass the research type
    const response = await companyDataService.researchCompanyRisks(
      companyName.value.trim(),
      researchType.value
    );
    showRisksMessage.value = true;

    // Display the response from the backend
    if (response.status === 'success') {
      messageType.value = 'success';
      risksResponse.value = `${response.message}${response.company_name ? ' for ' + response.company_name : ''}`;
      emit('risks-search-started', response.id, true);
    } else {
      messageType.value = 'error';
      // Check if the error is specifically about company data being required
      if (
        response.message &&
        response.message.includes('Company') &&
        response.message.includes('not found')
      ) {
        risksResponse.value = `You need to first conduct a company data research before performing risk analysis. Please click the "Search Company Data" button (green button) first.`;
      } else {
        risksResponse.value = response.message;
      }
    }
  } catch (error) {
    console.error('Error researching company risks:', error);
    showRisksMessage.value = true;
    messageType.value = 'error';
    risksResponse.value =
      error instanceof Error ? error.message : 'Failed to research company risks';
  } finally {
    isRisksSearching.value = false;
  }
};

const closeMessage = () => {
  showRisksMessage.value = false;
};

const showReportDialog = ref(false);
const reportHtml = ref<string | null>(null);
const loadingReport = ref(false);
const currentReportType = ref<'data' | 'risks'>('data');

async function viewReport(uuid: string, type: 'data' | 'risks') {
  currentReportType.value = type;
  loadingReport.value = true;
  try {
    reportHtml.value = await companyDataService.getReport(uuid, type);
    showReportDialog.value = true;
  } finally {
    loadingReport.value = false;
  }
}
</script>

<template>
  <div
    class="rounded-lg border border-gray-100 bg-white bg-opacity-90 p-4 shadow-md backdrop-blur-sm"
  >
    <AaText class="mb-3"
      >Enter a company name to analyze potential supply chain risks and compliance issues.
    </AaText>

    <div class="flex flex-col gap-3">
      <div class="flex gap-2">
        <input
          type="text"
          v-model="companyName"
          class="text-core-content-secondary flex-grow rounded-lg border bg-gray-50 p-3 outline-none transition-all duration-300 focus:bg-white focus:ring-2 focus:ring-blue-300"
          placeholder="Company name *"
          :class="{ 'animate-shake border-red-500': companyNameError && shakeCompanyName }"
        />

        <div class="relative w-64 min-w-40">
          <div
            @click="showCountryDropdown = !showCountryDropdown"
            :class="[
              'flex w-full cursor-pointer items-center justify-between truncate rounded-lg border bg-gray-50 p-3 pr-10 transition-all duration-300 hover:bg-gray-100',
              selectedCountry ? 'text-core-content-secondary' : 'text-gray-400',
              { 'animate-shake border-red-500': countryError && shakeCountry },
            ]"
          >
            <span class="truncate">{{ getSelectedCountryLabel }}</span>
            <svg
              class="ml-2 h-4 w-4 flex-shrink-0 fill-current"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
            >
              <path
                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"
              />
            </svg>
          </div>

          <div
            v-if="showCountryDropdown"
            class="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-lg border bg-white shadow-lg"
          >
            <div class="sticky top-0 border-b bg-white p-2">
              <input
                type="text"
                v-model="countrySearchQuery"
                class="w-full rounded border p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                placeholder="Search"
                @click.stop
                autofocus
              />
            </div>
            <div class="py-1">
              <div
                v-for="country in filteredCountries"
                :key="country.value"
                @click="selectCountry(country)"
                class="cursor-pointer px-4 py-2 text-sm hover:bg-gray-100"
              >
                {{ country.label }}
              </div>
              <div v-if="filteredCountries.length === 0" class="px-4 py-2 text-sm text-gray-500">
                No countries found
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between">
        <div class="mb-1 mt-1">
          <div class="flex gap-4">
            <label class="flex cursor-pointer items-center">
              <input
                type="radio"
                v-model="researchType"
                value="comprehensive"
                class="h-4 w-4 text-blue-600"
              />
              <span class="ml-2 text-sm font-medium"
                >Comprehensive Assessment
                <span class="text-xs font-semibold text-green-600">(Recommended)</span></span
              >
            </label>
            <label class="flex cursor-pointer items-center">
              <input
                type="radio"
                v-model="researchType"
                value="quick"
                class="h-4 w-4 text-blue-600"
              />
              <span class="ml-2 text-sm font-medium"
                >Fast Company Scan <span class="text-xs text-gray-500">(Basic)</span></span
              >
            </label>
          </div>
        </div>

        <div class="flex gap-2">
          <AaButton
            :append-icon="
              isSearching
                ? 'i-material-symbols-progress-activity animate-spin'
                : 'i-material-symbols-search'
            "
            @click="searchCompany"
            class="w-64 border-2 bg-gradient-to-r from-green-500 to-green-600 px-8 py-2 text-lg text-white shadow-lg transition-all hover:from-green-600 hover:to-green-700 hover:shadow-xl"
            :class="{
              'border-green-400': isFormValid,
              'border-gray-400 bg-gradient-to-r from-green-500 to-green-600 opacity-85':
                !isFormValid,
            }"
          >
            {{ isSearching ? 'Searching...' : 'Search Company Data' }}
          </AaButton>
          <AaButton
            :append-icon="
              isRisksSearching
                ? 'i-material-symbols-progress-activity animate-spin'
                : 'i-material-symbols-warning'
            "
            @click="showRisksPreview"
            class="w-64 border-2 bg-gradient-to-r from-blue-400 to-blue-500 px-8 py-2 text-lg text-white shadow-lg transition-all hover:from-blue-500 hover:to-blue-600 hover:shadow-xl"
            :class="{
              'border-blue-400': isFormValid,
              'border-gray-400 bg-gradient-to-r from-blue-400 to-blue-500 opacity-85': !isFormValid,
            }"
          >
            {{ isRisksSearching ? 'Researching...' : 'Research Company Risks' }}
          </AaButton>
        </div>
      </div>

      <div
        v-if="showRisksMessage"
        :class="[
          'rounded-lg border p-4 shadow-sm',
          messageType === 'success'
            ? 'border-green-200 bg-green-50'
            : messageType === 'error'
              ? 'border-red-200 bg-red-50'
              : 'border-blue-200 bg-blue-50',
        ]"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-grow">
            <h3 class="mb-2 text-lg font-semibold text-gray-900">
              <span v-if="messageType === 'success'">Company Risks Research</span>
              <span
                v-else-if="
                  messageType === 'error' && risksResponse && risksResponse.includes('not found')
                "
                >Company Data Required</span
              >
              <span v-else-if="messageType === 'error'">Error</span>
              <span v-else>Company Risks Research</span>
            </h3>
            <p
              :class="[
                'text-base',
                messageType === 'success'
                  ? 'text-green-700'
                  : messageType === 'error'
                    ? 'text-gray-900'
                    : 'text-gray-700',
              ]"
              v-if="risksResponse"
            >
              {{ risksResponse }}
            </p>
            <p class="text-gray-700" v-else>
              This feature is in development. The backend has been set up to receive requests.
            </p>
          </div>
          <button @click="closeMessage" class="text-gray-400 hover:text-gray-600">
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

      <div
        v-if="researchType === 'quick'"
        class="rounded-md border border-gray-200 bg-white p-3 text-sm shadow-sm transition-all duration-300"
      >
        <p>
          <strong>It's just fast. It's NOT comprehensive or detailed.</strong><br />
          The Fast Company Scan provides a rapid assessment by gathering basic company information.
          This approach is suitable for initial exploration but may not provide complete data
          coverage. Use this for a quick overview, keeping in mind that a Comprehensive Assessment
          will provide more reliable insights.
        </p>
      </div>

      <div
        v-if="researchType === 'comprehensive'"
        class="rounded-md border border-gray-200 bg-white p-3 text-sm shadow-sm transition-all duration-300"
      >
        <p>
          <strong>It's comprehensive, detailed and trustworthy. It's not fast.</strong><br />
          The Comprehensive Assessment performs a thorough multi-stage analysis. First, it conducts
          standard data collection, then employs an advanced agent to identify gaps,
          inconsistencies, and potential red flags. For each detected issue, the system initiates
          targeted follow-up research. All findings are integrated into a complete report, providing
          an accurate risk profile you can rely on.
        </p>
      </div>

      <!-- Previously Processed Companies Table -->
      <div class="mt-6">
        <h3 class="mb-2 text-lg font-semibold">Previously Processed Companies</h3>

        <div v-if="isLoadingCompanies" class="py-4 text-center">
          <div
            class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-green-600"
          ></div>
          <p class="mt-2 text-sm text-gray-600">Loading previous companies...</p>
        </div>

        <div
          v-else-if="previousCompanies.length === 0"
          class="rounded-md border bg-gray-50 py-4 text-center"
        >
          <p class="text-gray-500">No companies have been processed yet.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 rounded-lg border">
            <thead class="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Company Name
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Processing Date
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Reports
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr v-for="company in previousCompanies" :key="company.uuid" class="hover:bg-gray-50">
                <td class="whitespace-nowrap px-6 py-4">
                  <div class="text-sm font-medium text-gray-900">{{ company.name }}</div>
                </td>
                <td class="whitespace-nowrap px-6 py-4">
                  <div class="text-sm text-gray-500">{{ company.processingDate }}</div>
                </td>
                <td class="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                  <div class="space-x-3">
                    <button
                      v-if="company.hasCompanyDataReport"
                      @click="viewReport(company.uuid, 'data')"
                      class="text-blue-600 underline hover:text-blue-800"
                    >
                      CompanyData
                    </button>
                    <button
                      v-if="company.hasRisksReport"
                      @click="viewReport(company.uuid, 'risks')"
                      class="text-blue-600 underline hover:text-blue-800"
                      :class="{
                        'rounded border-2 border-blue-400 bg-blue-50 px-2 py-1': showRisksMessage,
                      }"
                    >
                      RiskReport
                    </button>
                    <span
                      v-if="!company.hasCompanyDataReport && !company.hasRisksReport"
                      class="text-gray-400"
                    >
                      No reports available
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <Teleport to="body">
      <AaModal
        v-if="showReportDialog"
        class="h-[90vh] w-[70vw]"
        :with-overlay="true"
        @close="showReportDialog = false"
      >
        <div v-if="loadingReport" class="py-8 text-center">Loading report…</div>
        <div v-else class="prose h-max-100 max-w-none" v-html="reportHtml"></div>
      </AaModal>
    </Teleport>
  </div>
</template>

<style>
.animate-shake {
  animation: shake 0.5s;
}

@keyframes shake {
  0% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(5px);
  }
  50% {
    transform: translateX(-5px);
  }
  75% {
    transform: translateX(5px);
  }
  100% {
    transform: translateX(0);
  }
}

.animate-slide-in {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Target all text and icons inside the button */
.bg-gradient-to-r.from-blue-500.to-blue-600 * {
  color: white !important;
}
</style>
