<script setup lang="ts">
import { ref, computed } from 'vue'
import { LawRelevancyApiService } from '../services/api.service'
import type { 
  ExecutionConfig, 
  ProcessedLineage,
  TeamRelevancy
} from '../types/api.types'

import LineagesList from './LineagesList.vue'
import LineageViewer from './LineageViewer.vue'

// State management
const apiService = new LawRelevancyApiService()
const bearerToken = ref(localStorage.getItem('bearerToken') || '')
const showToken = ref(false)
const executionUrl = ref(localStorage.getItem('executionUrl') || '')
const executionConfig = ref<ExecutionConfig>({
  project: '',
  benchmark: '',
  execution: ''
})

// Removed comparison functionality for simplicity

// Data state
const isLoading = ref(false)
const error = ref<string | null>(null)
const lineages = ref<ProcessedLineage[]>([])
const selectedLineage = ref<ProcessedLineage | null>(null)
const benchmarkInfo = ref<{ name: string; description: string; task_type: string } | null>(null)

// UI state
const executionUrlError = ref<string | null>(null)

// Computed properties
const canLoad = computed(() => {
  return bearerToken.value && executionConfig.value.project && 
         executionConfig.value.benchmark && executionConfig.value.execution
})

const disabledReason = computed(() => {
  if (!bearerToken.value) return 'Please enter your bearer token'
  if (!executionConfig.value.execution) return 'Please enter a valid execution URL'
  return ''
})

// URL parsing function
function parseExecutionUrl(url: string): ExecutionConfig | null {
  try {
    const cleanUrl = url.trim()
    
    const patterns = [
      /projects\/([a-fA-F0-9-]+)\/benchmarks\/([a-fA-F0-9-]+)\/executions\/([a-fA-F0-9-]+)/,
      /projects\/([a-fA-F0-9-]+)\/.*benchmarks\/([a-fA-F0-9-]+)\/executions\/([a-fA-F0-9-]+)/
    ]
    
    for (const pattern of patterns) {
      const match = cleanUrl.match(pattern)
      if (match) {
        return {
          project: match[1],
          benchmark: match[2],
          execution: match[3]
        }
      }
    }
    return null
  } catch {
    return null
  }
}

// URL update handlers
function updateConfigFromUrl(
  url: string, 
  configRef: typeof executionConfig, 
  errorRef: typeof executionUrlError
) {
  errorRef.value = null
  
  if (!url.trim()) {
    configRef.value = { project: '', benchmark: '', execution: '' }
    return
  }
  
  const parsed = parseExecutionUrl(url)
  if (parsed) {
    configRef.value = parsed
  } else {
    configRef.value = { project: '', benchmark: '', execution: '' }
    errorRef.value = 'Invalid URL format. Please paste a complete execution URL.'
  }
}

function handleExecutionUrlChange() {
  updateConfigFromUrl(executionUrl.value, executionConfig, executionUrlError)
  localStorage.setItem('executionUrl', executionUrl.value)
}

// Removed comparison URL handlers

function handleBearerTokenChange() {
  localStorage.setItem('bearerToken', bearerToken.value)
}

// Data loading functions
async function loadLineages() {
  if (!canLoad.value) return
  
  isLoading.value = true
  error.value = null
  lineages.value = []
  selectedLineage.value = null
  benchmarkInfo.value = null
  
  try {
    // Load lineages and benchmark info in parallel
    const [lineagesData, benchmarkData] = await Promise.all([
      apiService.fetchAllLineages(executionConfig.value, bearerToken.value),
      apiService.fetchBenchmarkInfo(executionConfig.value, bearerToken.value)
    ])
    
    lineages.value = lineagesData
    benchmarkInfo.value = benchmarkData
    
    console.log('Loaded lineages:', lineages.value.length)
    console.log('Sample lineage:', lineages.value[0])
    
    if (lineages.value.length === 0) {
      error.value = 'No lineages found for this execution'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'An error occurred while loading data'
    console.error('Error loading lineages:', err)
  } finally {
    isLoading.value = false
  }
}

// Removed comparison functionality

// Event handlers
function selectLineage(lineage: ProcessedLineage) {
  selectedLineage.value = lineage
}

// Load config from URL on mount
if (executionUrl.value) {
  updateConfigFromUrl(executionUrl.value, executionConfig, executionUrlError)
}
</script>

<template>
  <div class="benchmark-viewer">
    <!-- Main Content -->
      <div class="card">
        <div class="card-header">
          <h2>🔧 Configuration</h2>
        </div>
        <div class="card-body">
          <!-- Bearer Token -->
          <div class="form-group">
            <label class="form-label">Bearer Token:</label>
            <div class="token-input-wrapper">
              <input 
                v-model="bearerToken"
                @input="handleBearerTokenChange"
                :type="showToken ? 'text' : 'password'"
                placeholder="Enter your Pharia Studio bearer token..."
                class="form-input font-mono"
              />
              <button 
                @click="showToken = !showToken"
                type="button"
                class="btn btn-secondary"
              >
                {{ showToken ? 'Hide' : 'Show' }}
              </button>
            </div>
          </div>

          <!-- Execution URL -->
          <div class="form-group">
            <label class="form-label">Execution URL:</label>
            <input 
              v-model="executionUrl"
              @input="handleExecutionUrlChange"
              placeholder="Paste execution URL from Pharia Studio..."
              type="text"
              class="form-input font-mono"
            />
            <div class="text-xs text-gray-500 mt-1">
              Example: https://pharia-studio.customer.pharia.com/projects/.../benchmarks/.../executions/...
            </div>
            <div v-if="executionUrlError" class="alert alert-error mt-2">
              {{ executionUrlError }}
            </div>
          </div>

          <!-- Parsed Config Display -->
          <div v-if="executionConfig.project" class="parsed-config">
            <h4>📋 Parsed Configuration:</h4>
            <div class="config-grid">
              <div><strong>Project:</strong> <span class="font-mono">{{ executionConfig.project }}</span></div>
              <div><strong>Benchmark:</strong> <span class="font-mono">{{ executionConfig.benchmark }}</span></div>
              <div><strong>Execution:</strong> <span class="font-mono">{{ executionConfig.execution }}</span></div>
            </div>
          </div>

          <!-- Load Button -->
          <div class="text-center mt-4">
            <button 
              @click="loadLineages" 
              :disabled="!canLoad || isLoading"
              :title="disabledReason"
              class="btn btn-primary"
            >
              {{ isLoading ? '⏳ Loading...' : '📥 Load Lineages' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="alert alert-error">
        {{ error }}
      </div>

      <!-- Debug Information -->
      <div v-if="benchmarkInfo" class="card">
        <div class="card-header">
          <h3>📊 Load Results</h3>
        </div>
        <div class="card-body">
          <div class="debug-info">
            <div><strong>Benchmark Name:</strong> {{ benchmarkInfo.name }}</div>
            <div><strong>Task Type:</strong> {{ benchmarkInfo.task_type }}</div>
            <div v-if="benchmarkInfo.description"><strong>Description:</strong> {{ benchmarkInfo.description }}</div>
            <div><strong>Lineages Loaded:</strong> {{ lineages.length }}</div>
            <div v-if="lineages.length > 0"><strong>Sample Lineage ID:</strong> {{ lineages[0]?.id?.slice(0, 8) }}...</div>
            <div v-if="lineages.length > 0"><strong>Sample Lineage Law Title:</strong> {{ lineages[0]?.law_title || lineages[0]?.parsed_input?.law_title || 'Not parsed' }}</div>
            <div v-if="lineages.length > 0"><strong>Has Team Relevancies:</strong> {{ lineages[0]?.team_relevancies ? `Yes (${lineages[0].team_relevancies.length} teams)` : 'No' }}</div>
            <div v-if="lineages.length > 0 && lineages[0]?.team_relevancies"><strong>Sample Team:</strong> {{ lineages[0].team_relevancies[0]?.team_name || 'Unknown' }}</div>
            <div v-if="lineages.length > 0 && lineages[0]?.team_relevancies && lineages[0].team_relevancies[0]"><strong>Sample Team Has Chunks:</strong> {{ lineages[0].team_relevancies[0].chunk_relevancies ? `Yes (${lineages[0].team_relevancies[0].chunk_relevancies.length})` : 'No' }}</div>
            <div v-if="lineages.length > 0"><strong>Total Chunks Across All Lineages:</strong> {{ lineages.reduce((total, lineage) => total + (lineage.team_relevancies?.reduce((sum, team) => sum + (team.chunk_relevancies ? team.chunk_relevancies.length : 0), 0) || 0), 0) }}</div>
            <div v-if="lineages.length === 0" class="warning-message">
              ⚠️ No lineages found for this execution. This might indicate:
              <ul>
                <li>The execution has no lineages data</li>
                <li>The execution is still running</li>
                <li>There was an API error (check console)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Results Debug -->
      <div v-if="lineages.length > 0" class="card">
        <div class="card-header">
          <h3>🔍 Results Debug</h3>
        </div>
        <div class="card-body">
          <div><strong>Should show results:</strong> {{ lineages.length > 0 ? 'YES' : 'NO' }}</div>
          <div><strong>Results section rendered:</strong> {{ lineages.length > 0 ? 'This text proves the section is rendering' : 'NO' }}</div>
        </div>
      </div>

      <!-- Results -->
      <div v-if="lineages.length > 0" class="results-section">
        <div class="card">
          <div class="card-header">
            <h3>📋 Lineages List Component</h3>
          </div>
          <div class="card-body">
            <div><strong>About to render LineagesList with:</strong></div>
            <div>• lineages.length: {{ lineages.length }}</div>
            <div>• selectedLineage: {{ selectedLineage?.id?.slice(0, 8) || 'none' }}</div>
          </div>
        </div>
        
        <div class="grid grid-cols-2 gap-6 mt-4">
          <LineagesList 
            :lineages="lineages"
            :selected-lineage="selectedLineage"
            @select-lineage="selectLineage"
          />
          
          <LineageViewer 
            v-if="selectedLineage"
            :lineage="selectedLineage"
          />
        </div>
      </div>
  </div>
</template>

<style scoped>
.benchmark-viewer {
  width: 100%;
}

/* Removed unused tab styling */

.token-input-wrapper {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.token-input-wrapper .form-input {
  flex: 1;
}

.parsed-config {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  padding: 1rem;
  margin-top: 1rem;
}

.parsed-config h4 {
  margin-bottom: 0.75rem;
  color: #374151;
}

.config-grid {
  display: grid;
  gap: 0.5rem;
}

.config-grid > div {
  font-size: 0.875rem;
}

.debug-info {
  display: grid;
  gap: 0.75rem;
}

.debug-info > div {
  padding: 0.5rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.debug-info > div:last-child {
  border-bottom: none;
}

.warning-message {
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 0.375rem;
  padding: 1rem;
  color: #92400e;
  margin-top: 0.5rem;
}

.warning-message ul {
  margin: 0.5rem 0 0 1.5rem;
  padding: 0;
}

.warning-message li {
  margin-bottom: 0.25rem;
}

.results-section {
  margin-top: 2rem;
}

/* Responsive design */
@media (max-width: 768px) {
  .token-input-wrapper {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
