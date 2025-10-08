<script setup lang="ts">
import type { LawRelevancyExecutionItem } from '../types/api.types'

interface Props {
  executions: LawRelevancyExecutionItem[]
  selectedExecution: LawRelevancyExecutionItem | null
}

interface Emits {
  (e: 'select-execution', execution: LawRelevancyExecutionItem): void
}

defineProps<Props>()
defineEmits<Emits>()

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}

function getAccuracyColor(score: number): string {
  if (score >= 0.9) return 'text-green-600'
  if (score >= 0.7) return 'text-yellow-600'
  return 'text-red-600'
}

function getRelevantTeamsCount(execution: LawRelevancyExecutionItem): number {
  return execution.output.team_relevancies.filter(tr => tr.is_relevant).length
}

function getTotalTeamsCount(execution: LawRelevancyExecutionItem): number {
  return execution.output.team_relevancies.length
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h3>📋 Executions ({{ executions.length }})</h3>
    </div>
    <div class="card-body">
      <div class="executions-list">
        <div 
          v-for="execution in executions" 
          :key="execution.id"
          @click="$emit('select-execution', execution)"
          class="execution-item"
          :class="{ 
            selected: selectedExecution?.id === execution.id,
            'has-errors': execution.output.team_relevancies.some(tr => tr.error)
          }"
        >
          <div class="execution-header">
            <h4 class="law-title">{{ execution.input.law_title }}</h4>
            <div class="execution-meta">
              <span class="execution-id font-mono text-xs">{{ execution.id.slice(0, 8) }}...</span>
              <span class="execution-date text-xs">{{ formatDate(execution.created_at) }}</span>
            </div>
          </div>
          
          <div class="execution-metrics">
            <div class="metric">
              <span class="metric-label">Accuracy:</span>
              <span class="metric-value" :class="getAccuracyColor(execution.evaluation.accuracy_score)">
                {{ (execution.evaluation.accuracy_score * 100).toFixed(1) }}%
              </span>
            </div>
            
            <div class="metric">
              <span class="metric-label">F1 Score:</span>
              <span class="metric-value" :class="getAccuracyColor(execution.evaluation.overall_f1_score)">
                {{ (execution.evaluation.overall_f1_score * 100).toFixed(1) }}%
              </span>
            </div>
            
            <div class="metric">
              <span class="metric-label">Teams:</span>
              <span class="metric-value">
                {{ getRelevantTeamsCount(execution) }}/{{ getTotalTeamsCount(execution) }} relevant
              </span>
            </div>
            
            <div class="metric">
              <span class="metric-label">Latency:</span>
              <span class="metric-value">{{ execution.run_latency.toFixed(2) }}s</span>
            </div>
            
            <div class="metric">
              <span class="metric-label">Tokens:</span>
              <span class="metric-value">{{ execution.run_tokens.toLocaleString() }}</span>
            </div>
          </div>
          
          <div class="evaluation-summary">
            <div class="eval-badges">
              <span 
                class="eval-badge"
                :class="execution.evaluation.is_correct ? 'eval-badge-success' : 'eval-badge-error'"
              >
                {{ execution.evaluation.is_correct ? '✅ Correct' : '❌ Incorrect' }}
              </span>
              
              <span class="eval-badge eval-badge-info">
                P: {{ (execution.evaluation.precision * 100).toFixed(0) }}%
              </span>
              
              <span class="eval-badge eval-badge-info">
                R: {{ (execution.evaluation.recall * 100).toFixed(0) }}%
              </span>
            </div>
            
            <div v-if="execution.output.team_relevancies.some(tr => tr.error)" class="error-indicator">
              ⚠️ Some teams have errors
            </div>
          </div>
        </div>
        
        <div v-if="executions.length === 0" class="empty-state">
          <p>No executions found</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.executions-list {
  max-height: 600px;
  overflow-y: auto;
}

.execution-item {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.execution-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.execution-item.selected {
  border-color: #667eea;
  background-color: #f8fafc;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.execution-item.has-errors {
  border-left: 4px solid #ef4444;
}

.execution-header {
  margin-bottom: 0.75rem;
}

.law-title {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.execution-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #6b7280;
}

.execution-id {
  background-color: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.execution-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.metric-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.evaluation-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

.eval-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.eval-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.eval-badge-success {
  background-color: #dcfce7;
  color: #166534;
}

.eval-badge-error {
  background-color: #fee2e2;
  color: #dc2626;
}

.eval-badge-info {
  background-color: #dbeafe;
  color: #1d4ed8;
}

.error-indicator {
  color: #ef4444;
  font-size: 0.75rem;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.text-green-600 {
  color: #16a34a;
}

.text-yellow-600 {
  color: #ca8a04;
}

.text-red-600 {
  color: #dc2626;
}

/* Custom scrollbar */
.executions-list::-webkit-scrollbar {
  width: 6px;
}

.executions-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.executions-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.executions-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

@media (max-width: 768px) {
  .execution-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .evaluation-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .eval-badges {
    width: 100%;
  }
}
</style>
