<script setup lang="ts">
import { SystemArchitectureDiagram } from './icons';
import CompanyRisksResearch from './icons/CompanyRisksResearch.vue';
import DataGatheringCycle from './icons/DataGatheringCycle.vue';
import DataSourcesArchitecture from './icons/DataSourcesArchitecture.vue';
import { ref } from 'vue';

defineEmits(['close']);

const tabs = ref([
  { id: 'overview', name: 'Overview' },
  { id: 'phases', name: 'Analysis Process' },
  { id: 'architecture', name: 'Data Sources' },
]);

const activeTab = ref('overview');

const switchSection = (section: string) => {
  activeTab.value = section;
};

const getNextTab = () => {
  const currentIndex = tabs.value.findIndex((tab) => tab.id === activeTab.value);
  if (currentIndex === -1 || currentIndex === tabs.value.length - 1) return null;
  return tabs.value[currentIndex + 1];
};

const getPreviousTab = () => {
  const currentIndex = tabs.value.findIndex((tab) => tab.id === activeTab.value);
  if (currentIndex === -1 || currentIndex === 0) return null;
  return tabs.value[currentIndex - 1];
};
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="flex max-h-[90vh] w-[900px] flex-col overflow-hidden rounded-lg bg-white shadow-xl">
      <!-- Header -->
      <div class="flex-shrink-0 border-b border-gray-200">
        <div class="flex items-center justify-between px-6 py-4">
          <h2 class="text-xl font-bold text-gray-800">How This Works</h2>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
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

      <!-- Navigation -->
      <div class="flex-shrink-0 border-b border-gray-200">
        <div class="flex gap-2 px-6 py-3">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="switchSection(tab.id)"
            class="rounded-md px-4 py-2 text-sm font-medium transition-colors"
            :class="
              activeTab === tab.id ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            "
          >
            {{ tab.name }}
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto p-6">
        <div class="tab-content">
          <div v-if="activeTab === 'overview'" class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-800">Overview</h2>

            <div class="aspect-[800/550] w-full rounded-lg bg-white p-4 shadow-sm">
              <SystemArchitectureDiagram class="h-full w-full" />
            </div>

            <div class="prose prose-sm max-w-none">
              <p>
                The Supplier Risk Assessment System combines AI-powered research capabilities with
                structured risk evaluation methodologies to deliver comprehensive supply chain due
                diligence. The system operates through specialized agents that gather, verify, and
                analyze supplier data across multiple dimensions.
              </p>

              <p>
                At its core, the system implements a two-phase approach: first establishing verified
                supplier identity through multiple authoritative sources, then conducting a
                multi-layered risk assessment examining country, industry, and supplier-specific
                factors. This approach mirrors the methodical process of expert human analysts, but
                operates at significantly greater speed and scale.
              </p>

              <p>
                The architecture employs both structured databases of metrics (like corruption
                indices and compliance ratings) and unstructured sources (such as news articles and
                NGO reports). Each finding is verified through multiple independent sources before
                contributing to the final risk score, ensuring reliability in an environment where
                information quality varies significantly across regions and industries.
              </p>

              <p>
                Designed to meet the rigorous requirements of the German Supply Chain Due Diligence
                Act (LKSG), the system produces standardized risk scores, detailed justifications,
                and specific corrective action recommendations – transforming complex global supply
                chain data into actionable intelligence for procurement decision-making.
              </p>
            </div>

            <div class="mt-6 flex justify-end">
              <button
                v-if="getNextTab()"
                @click="switchSection(getNextTab()!.id)"
                class="flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-6 py-2 text-white shadow-sm transition duration-300 hover:bg-blue-600 hover:shadow-md"
              >
                <span>Next: {{ getNextTab()!.name }}</span>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fill-rule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>

          <!-- Analysis Process Section -->
          <div v-if="activeTab === 'phases'" class="space-y-8">
            <div>
              <h3 class="mb-4 text-lg font-bold text-gray-800">Two-Phase Analysis Process</h3>

              <div class="prose prose-sm max-w-none">
                <h4 class="text-md mb-2 font-semibold text-gray-700">
                  Phase 1: Data Gathering Cycle
                </h4>
                <p class="mb-4 text-gray-600">
                  Our system employs a continuous, iterative approach to building verified supplier
                  profiles:
                </p>

                <div class="mb-8 aspect-[800/550] w-full rounded-lg bg-white p-4 shadow-sm">
                  <DataGatheringCycle class="h-full w-full" />
                </div>

                <div class="space-y-4">
                  <div>
                    <h5 class="mb-1 font-medium text-gray-700">Search</h5>
                    <ul class="list-inside list-disc space-y-1 text-gray-600">
                      <li>Collects initial company information from multiple sources</li>
                      <li>
                        Dynamically selects appropriate research tools based on company location
                      </li>
                      <li>Accesses both global databases and country-specific registries</li>
                    </ul>
                  </div>

                  <div>
                    <h5 class="mb-1 font-medium text-gray-700">Validate</h5>
                    <ul class="list-inside list-disc space-y-1 text-gray-600">
                      <li>Reviews collected data for completeness and consistency</li>
                      <li>Identifies information gaps and conflicting data points</li>
                      <li>Prioritizes missing information based on compliance requirements</li>
                    </ul>
                  </div>

                  <div>
                    <h5 class="mb-1 font-medium text-gray-700">Fix Gaps</h5>
                    <ul class="list-inside list-disc space-y-1 text-gray-600">
                      <li>Conducts targeted searches for specific missing information</li>
                      <li>Uses specialized tools to resolve identified issues</li>
                      <li>Focuses research efforts on the highest priority gaps</li>
                    </ul>
                  </div>

                  <div>
                    <h5 class="mb-1 font-medium text-gray-700">Integrate</h5>
                    <ul class="list-inside list-disc space-y-1 text-gray-600">
                      <li>Combines information from all research iterations</li>
                      <li>Resolves conflicts between different data sources</li>
                      <li>Maintains data provenance to support verification</li>
                      <li>Standardizes information format for consistent analysis</li>
                    </ul>
                  </div>
                </div>

                <p class="mt-4 text-gray-600">
                  This cyclical process continues until a complete, verified company profile is
                  established, with each agent building upon the work of others rather than
                  operating in isolation.
                </p>

                <h4 class="text-md mb-2 mt-6 font-semibold text-gray-700">
                  Phase 2: Risk Assessment
                </h4>
                <div class="mb-8 aspect-[900/600] w-full rounded-lg bg-white p-4 shadow-sm">
                  <CompanyRisksResearch class="h-full w-full" />
                </div>
                <p class="mb-4 text-gray-600">
                  Our system evaluates risk across three critical dimensions:
                </p>

                <div class="space-y-4">
                  <div>
                    <h5 class="mb-1 font-medium text-gray-700">Country Risk Analysis</h5>
                    <ul class="list-inside list-disc space-y-1 text-gray-600">
                      <li>Political stability and governance quality</li>
                      <li>Corruption metrics (Transparency International indices)</li>
                      <li>Human rights and labor standards enforcement</li>
                      <li>Operating environment challenges</li>
                    </ul>
                  </div>

                  <div>
                    <h5 class="mb-1 font-medium text-gray-700">Industry Risk Analysis</h5>
                    <ul class="list-inside list-disc space-y-1 text-gray-600">
                      <li>Sector-specific compliance challenges</li>
                      <li>Historical patterns of violations</li>
                      <li>Environmental impact factors</li>
                      <li>Standard workplace practices and safety records</li>
                    </ul>
                  </div>

                  <div>
                    <h5 class="mb-1 font-medium text-gray-700">Supplier-Specific Risk Analysis</h5>
                    <ul class="list-inside list-disc space-y-1 text-gray-600">
                      <li>Direct compliance history and incident reports</li>
                      <li>Certification status and verification</li>
                      <li>Management system maturity</li>
                      <li>Worker complaints and resolution effectiveness</li>
                    </ul>
                  </div>
                </div>

                <p class="mt-4 text-gray-600">
                  Each risk dimension is quantified on a 1-10 scale with detailed justification. The
                  final assessment combines these elements to classify suppliers into risk
                  categories (Low, Medium, High) and recommend appropriate corrective actions with
                  implementation timelines.
                </p>
              </div>

              <div class="mt-6 flex justify-between">
                <button
                  v-if="getPreviousTab()"
                  @click="switchSection(getPreviousTab()!.id)"
                  class="flex items-center justify-center gap-2 rounded-lg bg-gray-100 px-6 py-2 text-gray-700 shadow-sm transition duration-300 hover:bg-gray-200 hover:shadow-md"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  <span>Back: {{ getPreviousTab()!.name }}</span>
                </button>
                <button
                  v-if="getNextTab()"
                  @click="switchSection(getNextTab()!.id)"
                  class="flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-6 py-2 text-white shadow-sm transition duration-300 hover:bg-blue-600 hover:shadow-md"
                >
                  <span>Next: {{ getNextTab()!.name }}</span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Data Sources Section -->
          <div v-if="activeTab === 'architecture'" class="space-y-6">
            <div>
              <h3 class="mb-4 text-lg font-bold text-gray-800">Data Sources Architecture</h3>
              <p class="mb-6 text-gray-600">
                The system leverages two complementary data ecosystems to ensure comprehensive
                coverage:
              </p>

              <div class="mb-8 aspect-[900/500] w-full rounded-lg bg-white p-4 shadow-sm">
                <DataSourcesArchitecture class="h-full w-full" />
              </div>

              <div class="space-y-6">
                <div class="rounded-lg bg-gray-50 p-4">
                  <h4 class="mb-3 font-semibold text-gray-700">Human-Curated Sources Database</h4>
                  <p class="mb-3 text-gray-600">
                    A continuously maintained collection of authoritative structured data sources,
                    including but not limited to:
                  </p>
                  <ul class="list-disc space-y-1 pl-5 text-gray-600">
                    <li>Government and regulatory repositories</li>
                    <li>Global compliance and risk indices</li>
                    <li>International sanctions and watchlists</li>
                    <li>Industry certification databases</li>
                    <li>Financial and credit evaluation systems</li>
                    <li>Corporate registry archives</li>
                  </ul>
                  <p class="mt-3 text-gray-600">
                    This database expands regularly as new authoritative sources become available,
                    with each addition undergoing verification by domain experts.
                  </p>
                </div>

                <div class="rounded-lg bg-gray-50 p-4">
                  <h4 class="mb-3 font-semibold text-gray-700">Unstructured Data Sources</h4>
                  <p class="mb-3 text-gray-600">
                    A dynamic collection of unstructured data that provides context and qualitative
                    insights, encompassing:
                  </p>
                  <ul class="list-disc space-y-1 pl-5 text-gray-600">
                    <li>News media from global, regional, and local outlets</li>
                    <li>NGO publications and investigative reports</li>
                    <li>Corporate communications and disclosures</li>
                    <li>Industry analysis and trade publications</li>
                    <li>Academic research and white papers</li>
                    <li>Social responsibility monitoring platforms</li>
                    <li>Worker forums and testimonial collections</li>
                  </ul>
                </div>

                <p class="text-gray-600">
                  The system's architecture is designed for extensibility, allowing new data sources
                  to be integrated as they emerge. Each source type contributes unique insights to
                  the final risk assessment, with the human-curated database providing foundational
                  verification while internet sources offer real-time context and qualitative
                  factors.
                </p>
              </div>

              <div class="mt-6 flex justify-between">
                <button
                  v-if="getPreviousTab()"
                  @click="switchSection(getPreviousTab()!.id)"
                  class="flex items-center justify-center gap-2 rounded-lg bg-gray-100 px-6 py-2 text-gray-700 shadow-sm transition duration-300 hover:bg-gray-200 hover:shadow-md"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  <span>Back: {{ getPreviousTab()!.name }}</span>
                </button>
                <button
                  v-if="getNextTab()"
                  @click="switchSection(getNextTab()!.id)"
                  class="flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-6 py-2 text-white shadow-sm transition duration-300 hover:bg-blue-600 hover:shadow-md"
                >
                  <span>Next: {{ getNextTab()!.name }}</span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
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
