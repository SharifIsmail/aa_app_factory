<script setup lang="ts">
import type { LawRelevancyExecutionItem, TeamRelevancy, ChunkRelevancy } from '../types/api.types'

interface Props {
  execution: LawRelevancyExecutionItem
}

defineProps<Props>()

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}

function getRelevancyBadgeClass(isRelevant: boolean): string {
  return isRelevant ? 'relevancy-badge-relevant' : 'relevancy-badge-not-relevant'
}

function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  if (score >= 0.4) return 'text-orange-600'
  return 'text-red-600'
}

function getMatchStatus(team: TeamRelevancy, expectedRelevancies: TeamRelevancy[]): { expected: boolean; matches: boolean } {
  const expected = expectedRelevancies.find(tr => tr.team_id === team.team_id)
  return {
    expected: expected?.is_relevant || false,
    matches: (expected?.is_relevant || false) === team.is_relevant
  }
}

function sortTeamRelevancies(teams: TeamRelevancy[]): TeamRelevancy[] {
  return [...teams].sort((a, b) => {
    // Sort by relevancy first (relevant teams first), then by score descending
    if (a.is_relevant !== b.is_relevant) {
      return a.is_relevant ? -1 : 1
    }
    return b.relevancy_score - a.relevancy_score
  })
}

function getChunkRelevancyStats(team: TeamRelevancy): { total: number; relevant: number; irrelevant: number } {
  if (!team.chunk_relevancies) {
    return { total: 0, relevant: 0, irrelevant: 0 }
  }

  const chunks = team.chunk_relevancies
  const relevant = chunks.filter(chunk => chunk.relevancy.is_relevant).length
  const irrelevant = chunks.length - relevant

  return { total: chunks.length, relevant, irrelevant }
}

function getChunkText(chunk: string | any): string {
  if (typeof chunk === 'string') {
    return chunk
  }
  if (chunk && typeof chunk === 'object') {
    if ('concatenation_of_chunk_contents' in chunk) {
      return chunk.concatenation_of_chunk_contents
    }
    if ('content' in chunk) {
      return chunk.content
    }
  }
  return String(chunk || '')
}

function truncateChunkText(text: string, maxLength: number = 150): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h3>📄 Execution Details</h3>
    </div>
    <div class="card-body">
      <!-- Execution Overview -->
      <div class="section">
        <h4>🔍 Overview</h4>
        <div class="overview-grid">
          <div class="overview-item">
            <span class="overview-label">Execution ID:</span>
            <span class="overview-value font-mono">{{ execution.id }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">Created:</span>
            <span class="overview-value">{{ formatDate(execution.created_at) }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">Created By:</span>
            <span class="overview-value">{{ execution.created_by }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">Latency:</span>
            <span class="overview-value">{{ execution.run_latency.toFixed(2) }}s</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">Tokens:</span>
            <span class="overview-value">{{ execution.run_tokens.toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <!-- Law Information -->
      <div class="section">
        <h4>⚖️ Law Information</h4>
        <div class="law-info">
          <div class="law-item">
            <strong>Title:</strong>
            <p>{{ execution.input.law_title }}</p>
          </div>
          <div class="law-item">
            <strong>URL:</strong>
            <a
              :href="execution.input.metadata.expression_url"
              target="_blank"
              class="law-url"
            >
              {{ execution.input.metadata.expression_url }}
            </a>
          </div>
          <div class="law-item">
            <strong>Text Preview:</strong>
            <div class="law-text-preview">
              {{ execution.input.law_text.substring(0, 500) }}
              <span v-if="execution.input.law_text.length > 500">... ({{ execution.input.law_text.length - 500 }} more characters)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Evaluation Results -->
      <div class="section">
        <h4>📊 Evaluation Results</h4>
        <div class="evaluation-grid">
          <div class="eval-metric">
            <div class="eval-metric-label">Overall Result</div>
            <div class="eval-metric-value" :class="execution.evaluation.is_correct ? 'text-green-600' : 'text-red-600'">
              {{ execution.evaluation.is_correct ? '✅ Correct' : '❌ Incorrect' }}
            </div>
          </div>
          <div class="eval-metric">
            <div class="eval-metric-label">Accuracy Score</div>
            <div class="eval-metric-value" :class="getScoreColor(execution.evaluation.accuracy_score)">
              {{ (execution.evaluation.accuracy_score * 100).toFixed(1) }}%
            </div>
          </div>
          <div class="eval-metric">
            <div class="eval-metric-label">F1 Score</div>
            <div class="eval-metric-value" :class="getScoreColor(execution.evaluation.overall_f1_score)">
              {{ (execution.evaluation.overall_f1_score * 100).toFixed(1) }}%
            </div>
          </div>
          <div class="eval-metric">
            <div class="eval-metric-label">Precision</div>
            <div class="eval-metric-value" :class="getScoreColor(execution.evaluation.precision)">
              {{ (execution.evaluation.precision * 100).toFixed(1) }}%
            </div>
          </div>
          <div class="eval-metric">
            <div class="eval-metric-label">Recall</div>
            <div class="eval-metric-value" :class="getScoreColor(execution.evaluation.recall)">
              {{ (execution.evaluation.recall * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
      </div>

      <!-- Team Relevancies -->
      <div class="section">
        <h4>👥 Team Relevancy Analysis ({{ execution.output.team_relevancies.length }} teams)</h4>

        <div class="teams-summary">
          <div class="summary-stat">
            <span class="summary-label">Relevant Teams:</span>
            <span class="summary-value text-red-600">
              {{ execution.output.team_relevancies.filter(tr => tr.is_relevant).length }}
            </span>
          </div>
          <div class="summary-stat">
            <span class="summary-label">Not Relevant:</span>
            <span class="summary-value text-gray-600">
              {{ execution.output.team_relevancies.filter(tr => !tr.is_relevant).length }}
            </span>
          </div>
          <div class="summary-stat">
            <span class="summary-label">Errors:</span>
            <span class="summary-value text-red-600">
              {{ execution.output.team_relevancies.filter(tr => tr.error).length }}
            </span>
          </div>
          <div class="summary-stat">
            <span class="summary-label">Total Chunks:</span>
            <span class="summary-value text-blue-600">
              {{ execution.output.team_relevancies.reduce((sum, team) => sum + getChunkRelevancyStats(team).total, 0) }}
            </span>
          </div>
        </div>

        <div class="teams-list">
          <div
            v-for="team in sortTeamRelevancies(execution.output.team_relevancies)"
            :key="team.team_id"
            class="team-item-expanded"
            :class="{ 'team-item-error': team.error }"
          >
            <div class="team-header-expanded">
              <div class="team-info">
                <h5 class="team-name">{{ team.team_name }}</h5>
                <span class="team-id font-mono">{{ team.team_id }}</span>
              </div>
              <div class="team-badges-expanded">
                <span
                  class="relevancy-badge"
                  :class="getRelevancyBadgeClass(team.is_relevant)"
                >
                  {{ team.is_relevant ? '✅ Relevant' : '❌ Not Relevant' }}
                </span>
                <span class="score-badge" :class="getScoreColor(team.relevancy_score)">
                  Score: {{ team.relevancy_score.toFixed(3) }}
                </span>
                <span v-if="getChunkRelevancyStats(team).total > 0" class="chunks-badge">
                  📝 {{ getChunkRelevancyStats(team).total }} chunks
                </span>
              </div>
            </div>

            <div v-if="team.error" class="team-error">
              <strong>⚠️ Error:</strong> {{ team.error }}
            </div>

            <div v-else class="team-content-expanded">
              <!-- Overall Team Reasoning -->
              <div class="team-reasoning-expanded">
                <h6>📋 Overall Assessment</h6>
                <p>{{ team.reasoning }}</p>
              </div>

              <!-- Chunk-level Analysis -->
              <div v-if="team.chunk_relevancies && team.chunk_relevancies.length > 0" class="chunk-analysis">
                <h6>🧩 Chunk-by-Chunk Analysis</h6>

                <div class="chunk-stats">
                  <div class="chunk-stat">
                    <span class="stat-icon">📊</span>
                    <span class="stat-text">{{ getChunkRelevancyStats(team).total }} total chunks</span>
                  </div>
                  <div class="chunk-stat relevant">
                    <span class="stat-icon">✅</span>
                    <span class="stat-text">{{ getChunkRelevancyStats(team).relevant }} relevant</span>
                  </div>
                  <div class="chunk-stat irrelevant">
                    <span class="stat-icon">❌</span>
                    <span class="stat-text">{{ getChunkRelevancyStats(team).irrelevant }} not relevant</span>
                  </div>
                </div>

                <div class="chunks-list">
                  <details
                    v-for="(chunkRelevancy, index) in team.chunk_relevancies"
                    :key="index"
                    class="chunk-item"
                    :class="{ 'chunk-relevant': chunkRelevancy.relevancy.is_relevant }"
                  >
                    <summary class="chunk-summary">
                      <div class="chunk-header">
                        <span class="chunk-status-icon">
                          {{ chunkRelevancy.relevancy.is_relevant ? '✅' : '❌' }}
                        </span>
                        <span class="chunk-preview">
                          {{ truncateChunkText(getChunkText(chunkRelevancy.chunk)) }}
                        </span>
                        <span class="chunk-relevancy-label" :class="{
                          'relevant': chunkRelevancy.relevancy.is_relevant,
                          'not-relevant': !chunkRelevancy.relevancy.is_relevant
                        }">
                          {{ chunkRelevancy.relevancy.is_relevant ? 'Relevant' : 'Not Relevant' }}
                        </span>
                      </div>
                    </summary>
                    <div class="chunk-details">
                      <div class="chunk-text">
                        <strong>Full Chunk Text:</strong>
                        <div class="chunk-text-content">{{ getChunkText(chunkRelevancy.chunk) }}</div>
                      </div>
                      <div class="chunk-reasoning">
                        <strong>Reasoning:</strong>
                        <p>{{ chunkRelevancy.relevancy.reasoning }}</p>
                      </div>
                    </div>
                  </details>
                </div>
              </div>

              <!-- Expected vs Actual comparison -->
              <div
                v-if="execution.expected_output.team_relevancies.find(tr => tr.team_id === team.team_id)"
                class="team-comparison"
              >
                <div class="comparison-row">
                  <span class="comparison-label">Expected:</span>
                  <span
                    class="comparison-value"
                    :class="getMatchStatus(team, execution.expected_output.team_relevancies).expected ? 'text-green-600' : 'text-gray-600'"
                  >
                    {{ getMatchStatus(team, execution.expected_output.team_relevancies).expected ? 'Relevant' : 'Not Relevant' }}
                  </span>
                  <span
                    class="comparison-match"
                    :class="getMatchStatus(team, execution.expected_output.team_relevancies).matches ? 'text-green-600' : 'text-red-600'"
                  >
                    {{ getMatchStatus(team, execution.expected_output.team_relevancies).matches ? '✅ Match' : '❌ Mismatch' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Subject Matter Summary -->
      <div v-if="execution.output.subject_matter_summary" class="section">
        <h4>📝 Subject Matter Summary</h4>
        <div class="subject-matter">
          <p>{{ execution.output.subject_matter_summary }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.overview-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.overview-value {
  font-size: 0.875rem;
  color: #374151;
  font-weight: 600;
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

.law-text-preview {
  background-color: #f8fafc;
  padding: 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #4b5563;
  border: 1px solid #e2e8f0;
}

.evaluation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.eval-metric {
  text-align: center;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.eval-metric-label {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.eval-metric-value {
  font-size: 1.25rem;
  font-weight: 700;
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

.teams-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 500px;
  overflow-y: auto;
}

.team-item-expanded {
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  background: white;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.team-item-error {
  border-left: 4px solid #ef4444;
  background-color: #fef2f2;
}

.team-header-expanded {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f1f5f9;
}

.team-info h5 {
  margin: 0;
  color: #374151;
  font-weight: 700;
  font-size: 1.125rem;
  margin-bottom: 0.5rem;
}

.team-id {
  font-size: 0.75rem;
  color: #6b7280;
  background-color: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-family: monospace;
}

.team-badges-expanded {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: center;
}

.chunks-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  background-color: #e0f2fe;
  color: #0284c7;
  border: 1px solid #bae6fd;
}

.team-content-expanded {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.team-reasoning-expanded {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem;
}

.team-reasoning-expanded h6 {
  margin: 0 0 0.75rem 0;
  color: #374151;
  font-weight: 600;
  font-size: 1rem;
}

.team-reasoning-expanded p {
  color: #4b5563;
  margin: 0;
  line-height: 1.6;
}

.chunk-analysis {
  background-color: #fefbf7;
  border: 1px solid #fed7aa;
  border-radius: 0.5rem;
  padding: 1.25rem;
}

.chunk-analysis h6 {
  margin: 0 0 1rem 0;
  color: #9a3412;
  font-weight: 600;
  font-size: 1rem;
}

.chunk-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.chunk-stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #f3f4f6;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.chunk-stat.relevant {
  background-color: #dcfce7;
  color: #166534;
}

.chunk-stat.irrelevant {
  background-color: #fee2e2;
  color: #dc2626;
}

.stat-icon {
  font-size: 1rem;
}

.chunks-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chunk-item {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  overflow: hidden;
}

.chunk-item.chunk-relevant {
  border-left: 4px solid #16a34a;
  background-color: #f6fff8;
}

.chunk-item:not(.chunk-relevant) {
  border-left: 4px solid #dc2626;
  background-color: #fefbfb;
}

.chunk-summary {
  padding: 0.75rem 1rem;
  cursor: pointer;
  list-style: none;
  background-color: inherit;
  transition: background-color 0.2s;
}

.chunk-summary:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.chunk-summary::-webkit-details-marker {
  display: none;
}

.chunk-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.chunk-status-icon {
  font-size: 1.125rem;
  flex-shrink: 0;
}

.chunk-preview {
  flex: 1;
  font-size: 0.875rem;
  color: #4b5563;
  line-height: 1.4;
}

.chunk-relevancy-label {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.chunk-relevancy-label.relevant {
  background-color: #dcfce7;
  color: #166534;
}

.chunk-relevancy-label.not-relevant {
  background-color: #fee2e2;
  color: #dc2626;
}

.chunk-details {
  padding: 1rem;
  border-top: 1px solid #f1f5f9;
  background-color: #fafafa;
}

.chunk-text {
  margin-bottom: 1rem;
}

.chunk-text strong {
  color: #374151;
  font-size: 0.875rem;
  display: block;
  margin-bottom: 0.5rem;
}

.chunk-text-content {
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  padding: 0.75rem;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #374151;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.chunk-reasoning strong {
  color: #374151;
  font-size: 0.875rem;
  display: block;
  margin-bottom: 0.5rem;
}

.chunk-reasoning p {
  color: #4b5563;
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.6;
}

.relevancy-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.relevancy-badge-relevant {
  background-color: #dcfce7;
  color: #166534;
}

.relevancy-badge-not-relevant {
  background-color: #fee2e2;
  color: #dc2626;
}

.score-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  background-color: #dbeafe;
  color: #1d4ed8;
}

.team-error {
  background-color: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 0.375rem;
  padding: 0.75rem;
  color: #dc2626;
  font-size: 0.875rem;
}

.team-comparison {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f1f5f9;
}

.comparison-row {
  display: flex;
  gap: 1rem;
  align-items: center;
  font-size: 0.875rem;
}

.comparison-label {
  color: #6b7280;
  font-weight: 500;
}

.comparison-value {
  font-weight: 600;
}

.comparison-match {
  font-weight: 600;
  font-size: 0.75rem;
}

.subject-matter {
  background-color: #f8fafc;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.subject-matter p {
  line-height: 1.6;
  color: #4b5563;
  margin: 0;
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

.text-gray-600 {
  color: #4b5563;
}

.text-blue-600 {
  color: #2563eb;
}

/* Custom scrollbar for teams list */
.teams-list::-webkit-scrollbar {
  width: 6px;
}

.teams-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.teams-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.teams-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

@media (max-width: 768px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .evaluation-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .teams-summary {
    flex-direction: column;
    gap: 1rem;
  }

  .team-header {
    flex-direction: column;
    gap: 0.75rem;
  }

  .comparison-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>
