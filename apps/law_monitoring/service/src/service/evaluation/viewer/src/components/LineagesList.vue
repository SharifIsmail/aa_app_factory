<script setup lang="ts">
import type { ProcessedLineage } from '../types/api.types'

interface Props {
  lineages: ProcessedLineage[]
  selectedLineage: ProcessedLineage | null
}

interface Emits {
  (e: 'select-lineage', lineage: ProcessedLineage): void
}

defineProps<Props>()
defineEmits<Emits>()

function formatDate(dateString: string): string {
  try {
    if (!dateString) return 'Unknown'
    return new Date(dateString).toLocaleString()
  } catch (error) {
    console.warn('Error formatting date:', dateString, error)
    return 'Invalid Date'
  }
}

function getRelevantTeamsCount(lineage: ProcessedLineage): number {
  if (!lineage.team_relevancies || !Array.isArray(lineage.team_relevancies)) {
    return 0
  }
  return lineage.team_relevancies.filter(tr => tr.is_relevant).length || 0
}

function getTotalTeamsCount(lineage: ProcessedLineage): number {
  if (!lineage.team_relevancies || !Array.isArray(lineage.team_relevancies)) {
    return 0
  }
  return lineage.team_relevancies.length || 0
}

function getErrorTeamsCount(lineage: ProcessedLineage): number {
  if (!lineage.team_relevancies || !Array.isArray(lineage.team_relevancies)) {
    return 0
  }
  return lineage.team_relevancies.filter(tr => tr.error).length || 0
}

function getOverallStatus(lineage: ProcessedLineage): string {
  if (!lineage.task_spans || !Array.isArray(lineage.task_spans)) {
    console.warn('Lineage missing task_spans:', lineage.id)
    return 'unknown'
  }
  
  const failedSpans = lineage.task_spans.filter(span => span.status === 'failed')
  const runningSpans = lineage.task_spans.filter(span => span.status === 'running')
  
  if (failedSpans.length > 0) return 'failed'
  if (runningSpans.length > 0) return 'running'
  return 'completed'
}

function getTaskSpansCount(lineage: ProcessedLineage): number {
  if (!lineage.task_spans || !Array.isArray(lineage.task_spans)) {
    return 0
  }
  return lineage.task_spans.filter(span => 
    span.name.includes('Task') || span.name.includes('LawRelevancy')
  ).length
}

function getTotalChunksCount(lineage: ProcessedLineage): number {
  if (!lineage.team_relevancies || !Array.isArray(lineage.team_relevancies)) {
    return 0
  }
  return lineage.team_relevancies.reduce((sum, team) => {
    if (!team.chunk_relevancies) return sum
    return sum + team.chunk_relevancies.length
  }, 0)
}

function getRelevantChunksCount(lineage: ProcessedLineage): number {
  if (!lineage.team_relevancies || !Array.isArray(lineage.team_relevancies)) {
    return 0
  }
  return lineage.team_relevancies.reduce((sum, team) => {
    if (!team.chunk_relevancies) return sum
    return sum + team.chunk_relevancies.filter(chunk => chunk.relevancy.is_relevant).length
  }, 0)
}

function getTeamChunkSummary(lineage: ProcessedLineage): string {
  const totalChunks = getTotalChunksCount(lineage)
  const relevantChunks = getRelevantChunksCount(lineage)
  if (totalChunks === 0) return 'No chunks'
  return `${relevantChunks}/${totalChunks} chunks relevant`
}

function getClassificationLabel(lineage: ProcessedLineage): string {
  if (!lineage.classification_metrics) return 'Unknown'
  
  const metrics = lineage.classification_metrics
  if (metrics.is_true_positive) return 'True Positive'
  if (metrics.is_false_positive) return 'False Positive'
  if (metrics.is_true_negative) return 'True Negative'
  if (metrics.is_false_negative) return 'False Negative'
  return 'Unknown'
}

function getClassificationBadgeClass(lineage: ProcessedLineage): string {
  if (!lineage.classification_metrics) return 'classification-unknown'
  
  const metrics = lineage.classification_metrics
  if (metrics.is_true_positive) return 'classification-true-positive'
  if (metrics.is_false_positive) return 'classification-false-positive'
  if (metrics.is_true_negative) return 'classification-true-negative'
  if (metrics.is_false_negative) return 'classification-false-negative'
  return 'classification-unknown'
}

function getExpectedRelevantLabel(lineage: ProcessedLineage): string {
  if (!lineage.classification_metrics) return 'Unknown'
  return lineage.classification_metrics.expected_relevant ? 'Expected Relevant' : 'Expected Not Relevant'
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h3>🔗 Lineages ({{ lineages.length }})</h3>
    </div>
    <div class="card-body">
      <div class="lineages-list">
        <div 
          v-for="lineage in lineages" 
          :key="lineage.id"
          @click="$emit('select-lineage', lineage)"
          class="lineage-item"
          :class="{ 
            selected: selectedLineage?.id === lineage.id,
            'has-errors': getErrorTeamsCount(lineage) > 0,
            'has-failures': getOverallStatus(lineage) === 'failed'
          }"
        >
          <div class="lineage-header">
            <h4 class="law-title">
              {{ lineage.law_title || lineage.parsed_input?.law_title || `Lineage ${lineage.id.slice(0, 8)}` }}
            </h4>
            <div class="lineage-meta">
              <span class="lineage-id font-mono text-xs">{{ lineage.id.slice(0, 8) }}...</span>
            </div>
          </div>
          
          <div class="lineage-metrics">
            <div class="metric">
              <span class="metric-label">Teams:</span>
              <span class="metric-value">
                {{ getRelevantTeamsCount(lineage) }}/{{ getTotalTeamsCount(lineage) }} relevant
              </span>
            </div>
            
            <div class="metric">
              <span class="metric-label">Chunks:</span>
              <span class="metric-value">{{ getTeamChunkSummary(lineage) }}</span>
            </div>
            
            <div class="metric">
              <span class="metric-label">Expected:</span>
              <span class="metric-value">{{ getExpectedRelevantLabel(lineage) }}</span>
            </div>
            
            <div class="metric">
              <span class="metric-label">Classification:</span>
              <span class="metric-value">{{ getClassificationLabel(lineage) }}</span>
            </div>
          </div>
          
          <div class="lineage-summary">
            <div class="summary-badges">
              <span v-if="getTotalTeamsCount(lineage) > 0" class="summary-badge teams-badge">
                {{ getTotalTeamsCount(lineage) }} teams
              </span>
              
              <span v-if="getRelevantTeamsCount(lineage) > 0" class="summary-badge relevant-badge">
                {{ getRelevantTeamsCount(lineage) }} relevant teams
              </span>
              
              <span v-if="getRelevantChunksCount(lineage) > 0" class="summary-badge chunks-badge">
                {{ getRelevantChunksCount(lineage) }} relevant chunks
              </span>
              
              <span v-if="getErrorTeamsCount(lineage) > 0" class="summary-badge error-badge">
                {{ getErrorTeamsCount(lineage) }} errors
              </span>

              <span class="summary-badge classification-badge" :class="getClassificationBadgeClass(lineage)">
                {{ getClassificationLabel(lineage) }}
              </span>
            </div>
            
            <div class="lineage-time">
              {{ formatDate(lineage.created_at || '') }}
            </div>
          </div>
        </div>
        
        <div v-if="lineages.length === 0" class="empty-state">
          <p>No lineages found</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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

.lineages-list {
  max-height: 600px;
  overflow-y: auto;
}

.lineage-item {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.lineage-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.lineage-item.selected {
  border-color: #667eea;
  background-color: #f8fafc;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.lineage-item.has-errors {
  border-left: 4px solid #f59e0b;
}

.lineage-item.has-failures {
  border-left: 4px solid #ef4444;
}

.lineage-header {
  margin-bottom: 0.75rem;
}

.law-title {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.lineage-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #6b7280;
}

.lineage-id {
  background-color: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.lineage-status {
  font-size: 1.125rem;
}

.lineage-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
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

.lineage-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

.summary-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.summary-badge {
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.teams-badge {
  background-color: #e0e7ff;
  color: #3730a3;
}

.relevant-badge {
  background-color: #dcfce7;
  color: #166534;
}

.chunks-badge {
  background-color: #fef3c7;
  color: #92400e;
}

.error-badge {
  background-color: #fef3c7;
  color: #92400e;
}

.status-badge {
  font-weight: 600;
}

.status-completed {
  background-color: #dcfce7;
  color: #166534;
}

.status-failed {
  background-color: #fee2e2;
  color: #dc2626;
}

.status-running {
  background-color: #fef3c7;
  color: #92400e;
}

.classification-badge {
  font-weight: 600;
}

.classification-true-positive {
  background-color: #dcfce7;
  color: #166534;
}

.classification-false-positive {
  background-color: #fef3c7;
  color: #92400e;
}

.classification-true-negative {
  background-color: #f0f9ff;
  color: #0284c7;
}

.classification-false-negative {
  background-color: #fee2e2;
  color: #dc2626;
}

.classification-unknown {
  background-color: #f3f4f6;
  color: #6b7280;
}

.lineage-time {
  font-size: 0.75rem;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

/* Custom scrollbar */
.lineages-list::-webkit-scrollbar {
  width: 6px;
}

.lineages-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.lineages-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.lineages-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

@media (max-width: 768px) {
  .lineage-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .lineage-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .summary-badges {
    width: 100%;
  }
}
</style>
