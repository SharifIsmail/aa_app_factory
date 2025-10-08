<script setup lang="ts">
import type { LawComparisonItem, TeamComparisonResult } from '../types/api.types'

interface Props {
  comparisons: LawComparisonItem[]
  selectedComparison: LawComparisonItem | null
  hasDifferences: (comparison: LawComparisonItem) => boolean
}

interface Emits {
  (e: 'select-comparison', comparison: LawComparisonItem): void
}

defineProps<Props>()
defineEmits<Emits>()

function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  if (score >= 0.4) return 'text-orange-600'
  return 'text-red-600'
}

function getTeamDifferencesCount(comparison: LawComparisonItem): number {
  return comparison.teamComparisons.filter(tc => !tc.matches).length
}

function formatScoreDifference(diff: number): string {
  return diff > 0 ? `+${diff.toFixed(3)}` : diff.toFixed(3)
}

function getRelevancyIcon(isRelevant: boolean): string {
  return isRelevant ? '✅' : '❌'
}

function getMatchIcon(matches: boolean): string {
  return matches ? '✅' : '❌'
}

function sortTeamComparisons(teams: TeamComparisonResult[]): TeamComparisonResult[] {
  return [...teams].sort((a, b) => {
    // Sort by mismatches first, then by score difference descending
    if (a.matches !== b.matches) {
      return a.matches ? 1 : -1
    }
    return b.score_difference - a.score_difference
  })
}
</script>

<template>
  <div class="comparison-layout">
    <!-- Comparisons List -->
    <div class="comparisons-list card">
      <div class="card-header">
        <h3>🔍 Law Comparisons ({{ comparisons.length }})</h3>
        <div class="legend">
          <span class="legend-item">
            <span class="legend-icon">🔴</span> = Has Differences
          </span>
          <span class="legend-item">
            <span class="legend-icon">🟢</span> = Identical Results
          </span>
        </div>
      </div>
      <div class="card-body">
        <div class="comparisons-scroll">
          <template v-for="(comparison, index) in comparisons" :key="comparison.lawId">
            <!-- Section divider between different and same results -->
            <div 
              v-if="index > 0 && hasDifferences(comparisons[index - 1]) && !hasDifferences(comparison)"
              class="section-divider"
            >
              <span>Laws with identical results</span>
            </div>
            
            <div 
              @click="$emit('select-comparison', comparison)"
              class="comparison-item"
              :class="{ 
                selected: selectedComparison?.lawId === comparison.lawId,
                'has-differences': hasDifferences(comparison)
              }"
            >
              <div class="comparison-header">
                <h4 class="law-title">{{ comparison.lawTitle }}</h4>
                <div class="comparison-indicators">
                  <span 
                    class="difference-indicator"
                    :class="hasDifferences(comparison) ? 'indicator-different' : 'indicator-same'"
                  >
                    {{ hasDifferences(comparison) ? '🔴' : '🟢' }}
                  </span>
                  <span class="team-count">
                    {{ getTeamDifferencesCount(comparison) }}/{{ comparison.teamComparisons.length }} teams differ
                  </span>
                </div>
              </div>
              
              <div class="execution-summary">
                <div class="execution-info">
                  <span class="execution-label">Exec 1:</span>
                  <span class="accuracy-score" :class="getScoreColor(comparison.execution1.evaluation.accuracy_score)">
                    {{ (comparison.execution1.evaluation.accuracy_score * 100).toFixed(1) }}%
                  </span>
                  <span class="f1-score">
                    F1: {{ (comparison.execution1.evaluation.overall_f1_score * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="execution-info">
                  <span class="execution-label">Exec 2:</span>
                  <span class="accuracy-score" :class="getScoreColor(comparison.execution2.evaluation.accuracy_score)">
                    {{ (comparison.execution2.evaluation.accuracy_score * 100).toFixed(1) }}%
                  </span>
                  <span class="f1-score">
                    F1: {{ (comparison.execution2.evaluation.overall_f1_score * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Comparison Details -->
    <div v-if="selectedComparison" class="comparison-details card">
      <div class="card-header">
        <h3>📊 Comparison Details: {{ selectedComparison.lawTitle }}</h3>
      </div>
      <div class="card-body">
        <!-- Overall Metrics Comparison -->
        <div class="section">
          <h4>📈 Overall Metrics</h4>
          <div class="metrics-comparison">
            <div class="metrics-side">
              <h5>Execution 1</h5>
              <div class="metrics-grid">
                <div class="metric-item">
                  <span class="metric-label">Accuracy:</span>
                  <span class="metric-value" :class="getScoreColor(selectedComparison.execution1.evaluation.accuracy_score)">
                    {{ (selectedComparison.execution1.evaluation.accuracy_score * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">F1 Score:</span>
                  <span class="metric-value" :class="getScoreColor(selectedComparison.execution1.evaluation.overall_f1_score)">
                    {{ (selectedComparison.execution1.evaluation.overall_f1_score * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Precision:</span>
                  <span class="metric-value" :class="getScoreColor(selectedComparison.execution1.evaluation.precision)">
                    {{ (selectedComparison.execution1.evaluation.precision * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Recall:</span>
                  <span class="metric-value" :class="getScoreColor(selectedComparison.execution1.evaluation.recall)">
                    {{ (selectedComparison.execution1.evaluation.recall * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Latency:</span>
                  <span class="metric-value">{{ selectedComparison.execution1.latency.toFixed(2) }}s</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Tokens:</span>
                  <span class="metric-value">{{ selectedComparison.execution1.tokens.toLocaleString() }}</span>
                </div>
              </div>
            </div>
            
            <div class="metrics-side">
              <h5>Execution 2</h5>
              <div class="metrics-grid">
                <div class="metric-item">
                  <span class="metric-label">Accuracy:</span>
                  <span class="metric-value" :class="getScoreColor(selectedComparison.execution2.evaluation.accuracy_score)">
                    {{ (selectedComparison.execution2.evaluation.accuracy_score * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">F1 Score:</span>
                  <span class="metric-value" :class="getScoreColor(selectedComparison.execution2.evaluation.overall_f1_score)">
                    {{ (selectedComparison.execution2.evaluation.overall_f1_score * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Precision:</span>
                  <span class="metric-value" :class="getScoreColor(selectedComparison.execution2.evaluation.precision)">
                    {{ (selectedComparison.execution2.evaluation.precision * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Recall:</span>
                  <span class="metric-value" :class="getScoreColor(selectedComparison.execution2.evaluation.recall)">
                    {{ (selectedComparison.execution2.evaluation.recall * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Latency:</span>
                  <span class="metric-value">{{ selectedComparison.execution2.latency.toFixed(2) }}s</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Tokens:</span>
                  <span class="metric-value">{{ selectedComparison.execution2.tokens.toLocaleString() }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Team-by-Team Comparison -->
        <div class="section">
          <h4>👥 Team-by-Team Comparison</h4>
          
          <div class="teams-summary">
            <div class="summary-stat">
              <span class="summary-label">Total Teams:</span>
              <span class="summary-value">{{ selectedComparison.teamComparisons.length }}</span>
            </div>
            <div class="summary-stat">
              <span class="summary-label">Matching Results:</span>
              <span class="summary-value text-green-600">
                {{ selectedComparison.teamComparisons.filter(tc => tc.matches).length }}
              </span>
            </div>
            <div class="summary-stat">
              <span class="summary-label">Different Results:</span>
              <span class="summary-value text-red-600">
                {{ selectedComparison.teamComparisons.filter(tc => !tc.matches).length }}
              </span>
            </div>
          </div>

          <div class="teams-comparison-list">
            <div 
              v-for="team in sortTeamComparisons(selectedComparison.teamComparisons)" 
              :key="team.team_id"
              class="team-comparison-item"
              :class="{ 'team-mismatch': !team.matches }"
            >
              <div class="team-comparison-header">
                <div class="team-info">
                  <h5 class="team-name">{{ team.team_name }}</h5>
                  <span class="team-id font-mono">{{ team.team_id }}</span>
                </div>
                <div class="match-indicator">
                  <span :class="team.matches ? 'text-green-600' : 'text-red-600'">
                    {{ getMatchIcon(team.matches) }} {{ team.matches ? 'Match' : 'Mismatch' }}
                  </span>
                </div>
              </div>
              
              <div class="team-comparison-content">
                <div class="comparison-table">
                  <div class="comparison-row">
                    <div class="comparison-label">Expected:</div>
                    <div class="comparison-value">
                      {{ getRelevancyIcon(team.expected_relevant) }} {{ team.expected_relevant ? 'Relevant' : 'Not Relevant' }}
                    </div>
                    <div class="comparison-score">
                      Score: {{ team.expected_score.toFixed(3) }}
                    </div>
                  </div>
                  
                  <div class="comparison-row">
                    <div class="comparison-label">Execution 1:</div>
                    <div class="comparison-value" :class="team.actual_relevant === team.expected_relevant ? 'text-green-600' : 'text-red-600'">
                      {{ getRelevancyIcon(team.actual_relevant) }} {{ team.actual_relevant ? 'Relevant' : 'Not Relevant' }}
                    </div>
                    <div class="comparison-score">
                      Score: {{ team.actual_score.toFixed(3) }}
                      <span class="score-diff" :class="team.score_difference > 0.1 ? 'text-red-600' : 'text-gray-500'">
                        ({{ formatScoreDifference(team.actual_score - team.expected_score) }})
                      </span>
                    </div>
                  </div>
                </div>
                
                <div v-if="team.actual_reasoning" class="reasoning-section">
                  <div class="reasoning-header">
                    <strong>Reasoning (Execution 1):</strong>
                  </div>
                  <div class="reasoning-text">
                    {{ team.actual_reasoning }}
                  </div>
                </div>
                
                <div v-if="team.expected_reasoning" class="reasoning-section">
                  <div class="reasoning-header">
                    <strong>Expected Reasoning:</strong>
                  </div>
                  <div class="reasoning-text expected-reasoning">
                    {{ team.expected_reasoning }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Law Information -->
        <div class="section">
          <h4>⚖️ Law Information</h4>
          <div class="law-info">
            <div class="law-item">
              <strong>Title:</strong>
              <p>{{ selectedComparison.input.law_title }}</p>
            </div>
            <div class="law-item">
              <strong>URL:</strong>
              <a :href="selectedComparison.input.metadata.expression_url" target="_blank" class="law-url">
                {{ selectedComparison.input.metadata.expression_url }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comparison-layout {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 1.5rem;
  height: calc(100vh - 300px);
}

.comparisons-list {
  height: fit-content;
  max-height: 100%;
  overflow: hidden;
}

.legend {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.legend-icon {
  font-size: 0.875rem;
}

.comparisons-scroll {
  max-height: 500px;
  overflow-y: auto;
}

.section-divider {
  margin: 1rem 0;
  padding: 0.75rem 0;
  text-align: center;
  position: relative;
}

.section-divider span {
  background: white;
  padding: 0 1rem;
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  position: relative;
  z-index: 1;
}

.section-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e5e7eb;
}

.comparison-item {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.comparison-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.comparison-item.selected {
  border-color: #667eea;
  background-color: #f8fafc;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.comparison-item.has-differences {
  border-left: 4px solid #ef4444;
}

.comparison-header {
  margin-bottom: 0.75rem;
}

.law-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.comparison-indicators {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.difference-indicator {
  font-size: 1.25rem;
}

.team-count {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.execution-summary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.execution-info {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  font-size: 0.875rem;
}

.execution-label {
  color: #6b7280;
  font-weight: 500;
  width: 60px;
}

.accuracy-score {
  font-weight: 600;
}

.f1-score {
  color: #4b5563;
  font-size: 0.75rem;
}

.comparison-details {
  height: fit-content;
  max-height: 100%;
  overflow-y: auto;
}

.section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.section h4 {
  color: #374151;
  margin-bottom: 1rem;
  font-size: 1.125rem;
  font-weight: 600;
}

.metrics-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.metrics-side {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
}

.metrics-side h5 {
  color: #374151;
  margin-bottom: 1rem;
  text-align: center;
}

.metrics-grid {
  display: grid;
  gap: 0.75rem;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #f8fafc;
  border-radius: 0.25rem;
}

.metric-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 0.875rem;
  font-weight: 600;
}

.teams-summary {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  align-items: center;
}

.summary-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.summary-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #374151;
}

.teams-comparison-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.team-comparison-item {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  background: white;
}

.team-comparison-item.team-mismatch {
  border-left: 4px solid #ef4444;
  background-color: #fef2f2;
}

.team-comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.team-name {
  margin: 0;
  color: #374151;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.team-id {
  font-size: 0.75rem;
  color: #6b7280;
  background-color: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.match-indicator {
  font-weight: 600;
  font-size: 0.875rem;
}

.comparison-table {
  margin-bottom: 1rem;
}

.comparison-row {
  display: grid;
  grid-template-columns: 100px 1fr 120px;
  gap: 1rem;
  align-items: center;
  padding: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.comparison-row:last-child {
  border-bottom: none;
}

.comparison-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.comparison-value {
  font-size: 0.875rem;
  font-weight: 600;
}

.comparison-score {
  font-size: 0.875rem;
  font-weight: 500;
  text-align: right;
}

.score-diff {
  font-size: 0.75rem;
  margin-left: 0.25rem;
}

.reasoning-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
}

.reasoning-header {
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.reasoning-text {
  font-size: 0.875rem;
  line-height: 1.6;
  color: #4b5563;
  background-color: #f8fafc;
  padding: 0.75rem;
  border-radius: 0.375rem;
  border: 1px solid #e2e8f0;
}

.expected-reasoning {
  background-color: #fef3c7;
  border-color: #fbbf24;
}

.law-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.law-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.law-item strong {
  color: #374151;
  font-weight: 600;
}

.law-url {
  color: #2563eb;
  text-decoration: underline;
  word-break: break-all;
}

.text-green-600 {
  color: #16a34a;
}

.text-yellow-600 {
  color: #ca8a04;
}

.text-orange-600 {
  color: #ea580c;
}

.text-red-600 {
  color: #dc2626;
}

.text-gray-500 {
  color: #6b7280;
}

/* Custom scrollbars */
.comparisons-scroll::-webkit-scrollbar,
.comparison-details::-webkit-scrollbar,
.teams-comparison-list::-webkit-scrollbar {
  width: 6px;
}

.comparisons-scroll::-webkit-scrollbar-track,
.comparison-details::-webkit-scrollbar-track,
.teams-comparison-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.comparisons-scroll::-webkit-scrollbar-thumb,
.comparison-details::-webkit-scrollbar-thumb,
.teams-comparison-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.comparisons-scroll::-webkit-scrollbar-thumb:hover,
.comparison-details::-webkit-scrollbar-thumb:hover,
.teams-comparison-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

@media (max-width: 1200px) {
  .comparison-layout {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .comparisons-scroll {
    max-height: 300px;
  }
}

@media (max-width: 768px) {
  .metrics-comparison {
    grid-template-columns: 1fr;
  }
  
  .teams-summary {
    flex-direction: column;
    gap: 1rem;
  }
  
  .team-comparison-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .comparison-row {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .comparison-score {
    text-align: left;
  }
}
</style>
