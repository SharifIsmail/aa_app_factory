<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ProcessedLineage, TeamRelevancy, ChunkRelevancy } from '../types/api.types'
import ChipToggleButtons from './ChipToggleButtons.vue'

// Tooltip state
const clickedChunk = ref<ColoredChunk | null>(null)
const tooltipPosition = ref({ x: 0, y: 0 })
const showTooltip = ref(false)

interface Props {
  lineage: ProcessedLineage
}

const props = defineProps<Props>()

// View state management
const currentView = ref<'hierarchical' | 'markdown'>('hierarchical')

// View toggle options
const viewOptions = [
  { value: 'hierarchical', label: 'Hierarchical', prependIcon: 'i-material-symbols-account-tree' },
  { value: 'markdown', label: 'Document', prependIcon: 'i-material-symbols-description' }
] as const

interface ColoredChunk {
  text: string
  isRelevant: boolean
  teamName?: string
  reasoning?: string
  originalIndex: number
  // Support for multiple teams
  teamRelevancies?: Array<{
    teamName: string
    reasoning: string
    isRelevant: boolean
  }>
}

// Simple markdown renderer - basic implementation without external dependency
function renderMarkdown(text: string): string {
  if (!text) return ''

  // Convert text to basic HTML with some common markdown patterns
  let html = text
    // Headers
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.*?)__/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/_(.*?)_/g, '<em>$1</em>')
    // Code blocks (triple backticks)
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    // Inline code
    .replace(/`(.*?)`/g, '<code>$1</code>')
    // Line breaks
    .replace(/\n\n/g, '</p><p>')
    // Unordered lists
    .replace(/^\* (.+$)/gim, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    // Ordered lists
    .replace(/^\d+\. (.+$)/gim, '<li>$1</li>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    // Escape any remaining newlines to <br>
    .replace(/\n/g, '<br>')

  // Wrap in paragraph if not already wrapped
  if (!html.includes('<p>') && !html.includes('<h1>') && !html.includes('<h2>') && !html.includes('<h3>') && !html.includes('<ul>') && !html.includes('<ol>') && !html.includes('<pre>')) {
    html = `<p>${html}</p>`
  }

  return html
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}



function getRelevancyBadgeClass(isRelevant: boolean): string {
  return isRelevant ? 'relevancy-badge-relevant' : 'relevancy-badge-not-relevant'
}

function getScoreColor(score: number | undefined | null): string {
  if (score == null) return 'text-gray-600'
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  if (score >= 0.4) return 'text-orange-600'
  return 'text-red-600'
}



function formatJson(obj: any): string {
  if (typeof obj === 'string') {
    try {
      return JSON.stringify(JSON.parse(obj), null, 2)
    } catch {
      return obj
    }
  }
  return JSON.stringify(obj, null, 2)
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

function expandAllChunks(event: Event): void {
  const target = event.target as HTMLElement
  const chunkAnalysis = target.closest('.chunk-analysis')
  if (chunkAnalysis) {
    const details = chunkAnalysis.querySelectorAll('details')
    details.forEach((d: any) => d.open = true)
  }
}

function collapseAllChunks(event: Event): void {
  const target = event.target as HTMLElement
  const chunkAnalysis = target.closest('.chunk-analysis')
  if (chunkAnalysis) {
    const details = chunkAnalysis.querySelectorAll('details')
    details.forEach((d: any) => d.open = false)
  }
}

// Markdown document view functions
const coloredChunks = computed((): ColoredChunk[] => {
  if (!props.lineage.team_relevancies || !props.lineage.parsed_input?.law_text) {
    return []
  }

  const chunks: ColoredChunk[] = []
  const lawText = props.lineage.parsed_input.law_text

  // Collect all chunks from all teams with their relevancy info
  const chunkMap = new Map<string, {
    isRelevant: boolean;
    teamName: string;
    reasoning: string;
    teamRelevancies: Array<{
      teamName: string;
      reasoning: string;
      isRelevant: boolean;
    }>
  }>()

  props.lineage.team_relevancies.forEach((team: TeamRelevancy) => {
    if (team.chunk_relevancies) {
      team.chunk_relevancies.forEach((chunkRelevancy: ChunkRelevancy) => {
        // Handle different chunk formats - API service should have already converted to string
        let chunkText: string
        if (typeof chunkRelevancy.chunk === 'string') {
          chunkText = chunkRelevancy.chunk.trim()
        } else if (chunkRelevancy.chunk && typeof chunkRelevancy.chunk === 'object') {
          // Fallback if API service didn't convert properly
          if ('concatenation_of_chunk_contents' in chunkRelevancy.chunk) {
            chunkText = chunkRelevancy.chunk.concatenation_of_chunk_contents.trim()
          } else if ('content' in chunkRelevancy.chunk) {
            chunkText = chunkRelevancy.chunk.content.trim()
          } else {
            chunkText = String(chunkRelevancy.chunk).trim()
          }
        } else {
          chunkText = String(chunkRelevancy.chunk || '').trim()
        }

        const teamRelevancyInfo = {
          teamName: team.team_name,
          reasoning: chunkRelevancy.relevancy.reasoning,
          isRelevant: chunkRelevancy.relevancy.is_relevant
        }

        if (!chunkMap.has(chunkText)) {
          chunkMap.set(chunkText, {
            isRelevant: chunkRelevancy.relevancy.is_relevant,
            teamName: team.team_name,
            reasoning: chunkRelevancy.relevancy.reasoning,
            teamRelevancies: [teamRelevancyInfo]
          })
        } else {
          // Add this team's relevancy to the existing chunk
          const existing = chunkMap.get(chunkText)!
          existing.teamRelevancies.push(teamRelevancyInfo)

          // If chunk is relevant for any team, mark it as relevant
          if (chunkRelevancy.relevancy.is_relevant) {
            // Update primary team info only if this is the first relevant team we found
            if (!existing.isRelevant) {
              existing.isRelevant = true
              existing.teamName = team.team_name
              existing.reasoning = chunkRelevancy.relevancy.reasoning
            }
          }
        }
      })
    }
  })

  // Try to map chunks back to their positions in the original text
  let lastPosition = 0
  const processedChunks: ColoredChunk[] = []

  // Sort chunks by their position in the text for better mapping
  const sortedChunks = Array.from(chunkMap.entries()).sort(([chunkA], [chunkB]) => {
    const posA = lawText.indexOf(chunkA)
    const posB = lawText.indexOf(chunkB)
    return posA - posB
  })

  sortedChunks.forEach(([chunkText, relevancyInfo]) => {
    // Try exact match first
    let position = lawText.indexOf(chunkText, lastPosition)

    // If exact match fails, try with normalized whitespace
    if (position === -1) {
      const normalizedChunk = chunkText.replace(/\s+/g, ' ').trim()
      const normalizedLawText = lawText.replace(/\s+/g, ' ')
      const normalizedPosition = normalizedLawText.indexOf(normalizedChunk, lastPosition)
      if (normalizedPosition !== -1) {
        // Find the original position by counting characters
        let charCount = 0
        for (let i = 0; i < lawText.length && charCount < normalizedPosition; i++) {
          if (lawText[i] !== ' ' || lawText[i-1] !== ' ') {
            charCount++
          }
          position = i
        }
      }
    }

    // If still no match, try finding the chunk anywhere in the remaining text
    if (position === -1) {
      position = lawText.indexOf(chunkText.substring(0, 50), lastPosition)
    }

    if (position !== -1) {
      // Add any text between last position and current chunk as non-relevant
      if (position > lastPosition) {
        const betweenText = lawText.substring(lastPosition, position)
        if (betweenText.trim()) {
          processedChunks.push({
            text: betweenText,
            isRelevant: false,
            originalIndex: processedChunks.length
          })
        }
      }

      // Add the current chunk
      processedChunks.push({
        text: chunkText,
        isRelevant: relevancyInfo.isRelevant,
        teamName: relevancyInfo.teamName,
        reasoning: relevancyInfo.reasoning,
        teamRelevancies: relevancyInfo.teamRelevancies,
        originalIndex: processedChunks.length
      })

      lastPosition = position + chunkText.length
    } else {
      // If chunk cannot be found in the document, add it as a separate item
      processedChunks.push({
        text: `[CHUNK NOT FOUND IN DOCUMENT]: ${chunkText.substring(0, 100)}...`,
        isRelevant: relevancyInfo.isRelevant,
        teamName: relevancyInfo.teamName,
        reasoning: relevancyInfo.reasoning,
        teamRelevancies: relevancyInfo.teamRelevancies,
        originalIndex: processedChunks.length
      })
    }
  })

  // Add any remaining text
  if (lastPosition < lawText.length) {
    const remainingText = lawText.substring(lastPosition)
    if (remainingText.trim()) {
      processedChunks.push({
        text: remainingText,
        isRelevant: false,
        originalIndex: processedChunks.length
      })
    }
  }

  // If no chunks were successfully mapped, create a simple fallback view
  if (processedChunks.length === 0 && chunkMap.size > 0) {
    // Create a simple alternating pattern with chunks from the chunk map
    const chunkArray = Array.from(chunkMap.entries())
    chunkArray.forEach(([chunkText, relevancyInfo], index) => {
      processedChunks.push({
        text: chunkText,
        isRelevant: relevancyInfo.isRelevant,
        teamName: relevancyInfo.teamName,
        reasoning: relevancyInfo.reasoning,
        teamRelevancies: relevancyInfo.teamRelevancies,
        originalIndex: index
      })

      // Add separator
      if (index < chunkArray.length - 1) {
        processedChunks.push({
          text: '\n\n---\n\n',
          isRelevant: false,
          originalIndex: index + 0.5
        })
      }
    })
  }

  return processedChunks.length > 0 ? processedChunks : [
    {
      text: lawText,
      isRelevant: false,
      originalIndex: 0
    }
  ]
})

function handleViewChange(view: string): void {
  currentView.value = view as 'hierarchical' | 'markdown'
}

function getChunkTooltip(chunk: ColoredChunk): string {
  if (!chunk.isRelevant) {
    return 'This chunk was not identified as relevant for any team.'
  }

  if (chunk.teamRelevancies && chunk.teamRelevancies.length > 0) {
    const relevantTeams = chunk.teamRelevancies.filter(tr => tr.isRelevant)
    if (relevantTeams.length > 1) {
      return `Multiple Teams Found This Relevant (${relevantTeams.length} teams)\n\nClick to see detailed reasoning for each team.`
    } else if (relevantTeams.length === 1) {
      const team = relevantTeams[0]
      return `Team: ${team.teamName}\n\nRelevancy Reasoning:\n${team.reasoning}\n\nThis chunk was identified as relevant for the ${team.teamName} team.`
    }
  }

  // Fallback to old format for backward compatibility
  if (chunk.teamName && chunk.reasoning) {
    return `Team: ${chunk.teamName}\n\nRelevancy Reasoning:\n${chunk.reasoning}\n\nThis chunk was identified as relevant for the ${chunk.teamName} team.`
  } else if (chunk.teamName) {
    return `Team: ${chunk.teamName}\n\nThis chunk was identified as relevant for the ${chunk.teamName} team.\n(No detailed reasoning available)`
  }

  return 'This chunk was identified as relevant.\n(No team or reasoning information available)'
}

function handleChunkClick(event: MouseEvent, chunk: ColoredChunk): void {
  if (!chunk.isRelevant) return

  // If clicking the same chunk, close the tooltip
  if (clickedChunk.value === chunk) {
    showTooltip.value = false
    clickedChunk.value = null
    return
  }

  // Set new chunk and position tooltip
  clickedChunk.value = chunk
  updateTooltipPosition(event)
  showTooltip.value = true
}

function updateTooltipPosition(event: MouseEvent): void {
  const tooltipWidth = 400 // max-width of tooltip
  const tooltipHeight = 300 // estimated max height
  const offset = 20

  let x = event.clientX + offset
  let y = event.clientY - 10

  // Adjust if tooltip would go off the right edge
  if (x + tooltipWidth > window.innerWidth) {
    x = event.clientX - tooltipWidth - offset
  }

  // Adjust if tooltip would go off the bottom edge
  if (y + tooltipHeight > window.innerHeight) {
    y = window.innerHeight - tooltipHeight - 10
  }

  // Ensure tooltip doesn't go above the top
  if (y < 10) {
    y = 10
  }

  tooltipPosition.value = { x, y }
}

function closeTooltip(): void {
  showTooltip.value = false
  clickedChunk.value = null
}
</script>

<template>
  <div class="lineage-viewer">
    <!-- View Toggle -->
    <div class="view-toggle-section">
      <ChipToggleButtons
        title="View Mode"
        :model-value="currentView"
        :options="viewOptions"
        @update:model-value="handleViewChange"
        :mandatory="true"
      />
    </div>

    <!-- Lineage Overview -->
    <div class="section">
      <h4>🔗 Lineage Overview</h4>
      <div class="lineage-info">
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">ID:</span>
            <span class="info-value font-mono">{{ props.lineage.id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Example ID:</span>
            <span class="info-value font-mono">{{ props.lineage.example_id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Trace ID:</span>
            <span class="info-value font-mono">{{ props.lineage.trace_id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Created:</span>
            <span class="info-value">{{ formatDate(props.lineage.created_at) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Created By:</span>
            <span class="info-value">{{ props.lineage.created_by }}</span>
          </div>

        </div>
      </div>
    </div>

    <!-- Law Information (if parsed) -->
    <div v-if="props.lineage.parsed_input" class="section">
      <h4>⚖️ Law Information</h4>
      <div class="law-info">
        <div class="law-item">
          <strong>Title:</strong>
          <p>{{ props.lineage.parsed_input.law_title }}</p>
        </div>
        <div v-if="props.lineage.parsed_input.metadata.expression_url" class="law-item">
          <strong>URL:</strong>
          <a
            :href="props.lineage.parsed_input.metadata.expression_url"
            target="_blank"
            class="law-url"
          >
            {{ props.lineage.parsed_input.metadata.expression_url }}
          </a>
        </div>
        <div class="law-item">
          <strong>Text Preview:</strong>
          <div class="law-text-preview">
            {{ props.lineage.parsed_input.law_text.substring(0, 300) }}
            <span v-if="props.lineage.parsed_input.law_text.length > 300">... ({{ props.lineage.parsed_input.law_text.length - 300 }} more characters)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Expected Output and Classification Metrics -->
    <div v-if="props.lineage.classification_metrics" class="section">
      <h4>📊 Classification Analysis</h4>
      <div class="classification-info">
        <div class="classification-summary-horizontal">
          <div class="classification-item-horizontal">
            <span class="classification-label">Expected Relevance:</span>
            <span class="classification-value" :class="{
              'expected-relevant': props.lineage.classification_metrics.expected_relevant,
              'expected-not-relevant': !props.lineage.classification_metrics.expected_relevant
            }">
              {{ props.lineage.classification_metrics.expected_relevant ? '✅ Relevant' : '❌ Not Relevant' }}
            </span>
          </div>

          <div class="classification-item-horizontal">
            <span class="classification-label">Actual Classification:</span>
            <span class="classification-value" :class="{
              'actual-relevant': props.lineage.classification_metrics.actual_relevant,
              'actual-not-relevant': !props.lineage.classification_metrics.actual_relevant
            }">
              {{ props.lineage.classification_metrics.actual_relevant ? '⚠️ Relevant' : 'Not Relevant' }}
            </span>
          </div>

          <div class="classification-item-horizontal">
            <span class="classification-label">Classification Result:</span>
            <span class="classification-badge" :class="{
              'badge-true-positive': props.lineage.classification_metrics.is_true_positive,
              'badge-false-positive': props.lineage.classification_metrics.is_false_positive,
              'badge-true-negative': props.lineage.classification_metrics.is_true_negative,
              'badge-false-negative': props.lineage.classification_metrics.is_false_negative
            }">
              <span v-if="props.lineage.classification_metrics.is_true_positive">🎯 True Positive</span>
              <span v-else-if="props.lineage.classification_metrics.is_false_positive">⚠️ False Positive</span>
              <span v-else-if="props.lineage.classification_metrics.is_true_negative">✅ True Negative</span>
              <span v-else-if="props.lineage.classification_metrics.is_false_negative">❌ False Negative</span>
              <span v-else>❓ Unknown</span>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Expected Output Details -->
    <div v-if="props.lineage.parsed_expected_output" class="section">
      <h4>🎯 Expected Output</h4>
      <div class="expected-output-info">
        <div class="expected-teams-summary">
          <div class="summary-stat">
            <span class="summary-label">Expected Relevant Teams:</span>
            <span class="summary-value text-green-600">
              {{ props.lineage.parsed_expected_output.team_relevancies?.filter(tr => tr.is_relevant).length || 0 }}
            </span>
          </div>
          <div class="summary-stat">
            <span class="summary-label">Expected Not Relevant:</span>
            <span class="summary-value text-gray-600">
              {{ props.lineage.parsed_expected_output.team_relevancies?.filter(tr => !tr.is_relevant).length || 0 }}
            </span>
          </div>
        </div>

        <div v-if="props.lineage.parsed_expected_output.team_relevancies && props.lineage.parsed_expected_output.team_relevancies.length > 0" class="expected-teams-list">
          <h6>Expected Team Relevancies:</h6>
          <div class="expected-teams-grid">
            <div
              v-for="expectedTeam in props.lineage.parsed_expected_output.team_relevancies"
              :key="expectedTeam.team_name"
              class="expected-team-item"
              :class="{ 'expected-relevant': expectedTeam.is_relevant }"
            >
              <div class="expected-team-header">
                <span class="expected-team-name">{{ expectedTeam.team_name }}</span>
                <span class="expected-relevancy-badge" :class="{
                  'expected-relevant-badge': expectedTeam.is_relevant,
                  'expected-not-relevant-badge': !expectedTeam.is_relevant
                }">
                  {{ expectedTeam.is_relevant ? 'Should be Relevant' : 'Should be Not Relevant' }}
                </span>
              </div>
              <div v-if="expectedTeam.reasoning" class="expected-team-reasoning">
                <strong>Expected Reasoning:</strong>
                <p>{{ expectedTeam.reasoning }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Markdown Document View -->
    <div v-if="currentView === 'markdown' && props.lineage.parsed_input?.law_text && props.lineage.team_relevancies && props.lineage.team_relevancies.length > 0" class="section">
      <h4>📄 Law Document with Relevancy Highlights</h4>

      <!-- Debug Information -->
      <div class="debug-info">
        <details style="margin-bottom: 1rem; background: #f0f9ff; padding: 0.5rem; border-radius: 0.25rem;">
          <summary style="cursor: pointer; font-weight: bold;">🔍 Debug Information</summary>
          <div style="font-size: 0.75rem; margin-top: 0.5rem;">
            <p><strong>Total chunks processed:</strong> {{ coloredChunks.length }}</p>
            <p><strong>Relevant chunks:</strong> {{ coloredChunks.filter(c => c.isRelevant).length }}</p>
            <p><strong>Non-relevant chunks:</strong> {{ coloredChunks.filter(c => !c.isRelevant).length }}</p>
            <p><strong>Teams with chunk data:</strong> {{ props.lineage.team_relevancies.filter(t => t.chunk_relevancies && t.chunk_relevancies.length > 0).length }}</p>
            <p><strong>Sample chunks from teams:</strong></p>
            <ul style="max-height: 150px; overflow-y: auto; font-size: 0.7rem;">
              <li v-for="(team, teamIndex) in props.lineage.team_relevancies.slice(0, 2)" :key="teamIndex">
                <strong>{{ team.team_name }}:</strong> {{ team.chunk_relevancies?.length || 0 }} chunks
                <ul v-if="team.chunk_relevancies && team.chunk_relevancies.length > 0" style="margin-left: 1rem;">
                  <li v-for="(chunkRel, chunkIndex) in team.chunk_relevancies.slice(0, 2)" :key="chunkIndex">
                    <span :style="{ color: chunkRel.relevancy.is_relevant ? '#dc2626' : '#374151' }">
                      {{ chunkRel.relevancy.is_relevant ? '⚠️' : '' }}
                      "{{ getChunkText(chunkRel.chunk).substring(0, 80) }}{{ getChunkText(chunkRel.chunk).length > 80 ? '...' : '' }}"
                    </span>
                  </li>
                </ul>
              </li>
            </ul>
            <p><strong>Sample relevant chunks in processed view:</strong></p>
            <ul style="max-height: 100px; overflow-y: auto;">
              <li v-for="chunk in coloredChunks.filter(c => c.isRelevant).slice(0, 3)" :key="chunk.originalIndex">
                "{{ chunk.text.substring(0, 100) }}{{ chunk.text.length > 100 ? '...' : '' }}" (Team: {{ chunk.teamName }})
              </li>
            </ul>
          </div>
        </details>
      </div>

      <div class="markdown-legend">
        <div class="legend-item">
          <span class="legend-color relevant-color"></span>
          <span class="legend-text">Relevant chunks (click for details)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color multi-team-color"></span>
          <span class="legend-text">Multi-team relevant chunks (gradient + number indicator)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color not-relevant-color"></span>
          <span class="legend-text">Not relevant chunks</span>
        </div>
      </div>

      <div class="markdown-document">
        <h5 class="document-title">{{ props.lineage.parsed_input.law_title || 'Law Document' }}</h5>
        <div class="document-content">
          <span
            v-for="chunk in coloredChunks"
            :key="chunk.originalIndex"
            :class="{
              'chunk-relevant': chunk.isRelevant,
              'chunk-not-relevant': !chunk.isRelevant,
              'chunk-active': chunk.isRelevant && clickedChunk === chunk,
              'chunk-multi-team': chunk.isRelevant && chunk.teamRelevancies && chunk.teamRelevancies.filter(tr => tr.isRelevant).length > 1
            }"
            class="document-chunk"
            @click="(event) => handleChunkClick(event, chunk)"
            :title="chunk.isRelevant && chunk.teamRelevancies && chunk.teamRelevancies.filter(tr => tr.isRelevant).length > 1
              ? `Relevant for ${chunk.teamRelevancies.filter(tr => tr.isRelevant).length} teams: ${chunk.teamRelevancies.filter(tr => tr.isRelevant).map(tr => tr.teamName).join(', ')}`
              : getChunkTooltip(chunk)"
          >{{ chunk.text }}<span
              v-if="chunk.isRelevant && chunk.teamRelevancies && chunk.teamRelevancies.filter(tr => tr.isRelevant).length > 1"
              class="multi-team-indicator"
            >{{ chunk.teamRelevancies.filter(tr => tr.isRelevant).length }}</span></span>
        </div>
      </div>
    </div>

    <!-- Custom Tooltip -->
    <div
      v-if="showTooltip && clickedChunk"
      class="custom-tooltip"
      :style="{
        left: tooltipPosition.x + 'px',
        top: tooltipPosition.y + 'px'
      }"
    >
      <div class="tooltip-content">
        <div class="tooltip-header">
          <div class="tooltip-title">
            <strong v-if="clickedChunk.teamRelevancies && clickedChunk.teamRelevancies.filter(tr => tr.isRelevant).length > 1">
              Multiple Teams ({{ clickedChunk.teamRelevancies.filter(tr => tr.isRelevant).length }})
            </strong>
            <strong v-else>
              {{ clickedChunk.teamName }}
            </strong>
          </div>
          <button class="tooltip-close" @click="closeTooltip" title="Close tooltip">
            ✕
          </button>
        </div>

        <!-- Show all relevant teams if multiple teams found this chunk relevant -->
        <div v-if="clickedChunk.teamRelevancies && clickedChunk.teamRelevancies.filter(tr => tr.isRelevant).length > 1">
          <div
            v-for="(teamRelevancy, index) in clickedChunk.teamRelevancies.filter(tr => tr.isRelevant)"
            :key="index"
            class="team-relevancy-section"
          >
            <div class="team-relevancy-header">
              <strong>{{ teamRelevancy.teamName }}</strong>
            </div>
            <div v-if="teamRelevancy.reasoning" class="tooltip-reasoning">
              <div class="tooltip-section-title">Relevancy Reasoning:</div>
              <div class="tooltip-text">{{ teamRelevancy.reasoning }}</div>
            </div>
            <div v-if="index < clickedChunk.teamRelevancies.filter(tr => tr.isRelevant).length - 1" class="team-separator"></div>
          </div>
        </div>

        <!-- Show single team info (backward compatibility) -->
        <div v-else>
          <div v-if="clickedChunk.reasoning" class="tooltip-reasoning">
            <div class="tooltip-section-title">Relevancy Reasoning:</div>
            <div class="tooltip-text">{{ clickedChunk.reasoning }}</div>
          </div>
        </div>

        <div class="tooltip-footer">
          <span v-if="clickedChunk.teamRelevancies && clickedChunk.teamRelevancies.filter(tr => tr.isRelevant).length > 1">
            This chunk was identified as relevant by {{ clickedChunk.teamRelevancies.filter(tr => tr.isRelevant).length }} teams.
          </span>
          <span v-else>
            This chunk was identified as relevant for the {{ clickedChunk.teamName }} team.
          </span>
        </div>
        <!-- Scroll indicator -->
        <div class="scroll-indicator">
          <span class="scroll-hint">↕ Scroll for more content</span>
        </div>
      </div>
    </div>

    <!-- Team Relevancies (Task Output) - Hierarchical View -->
    <div v-if="currentView === 'hierarchical' && props.lineage.team_relevancies && props.lineage.team_relevancies.length > 0" class="section">
      <h4>👥 Team Relevancy Analysis</h4>

      <div class="teams-summary">
        <div class="summary-stat">
          <span class="summary-label">Relevant Teams:</span>
          <span class="summary-value text-red-600">
            {{ props.lineage.team_relevancies.filter(tr => tr.is_relevant).length }}
          </span>
        </div>
        <div class="summary-stat">
          <span class="summary-label">Not Relevant:</span>
          <span class="summary-value text-gray-600">
            {{ props.lineage.team_relevancies.filter(tr => !tr.is_relevant).length }}
          </span>
        </div>
        <div class="summary-stat">
          <span class="summary-label">Errors:</span>
          <span class="summary-value text-red-600">
            {{ props.lineage.team_relevancies.filter(tr => tr.error).length }}
          </span>
        </div>
      </div>

      <div class="teams-list">
        <details
          v-for="team in [...props.lineage.team_relevancies].sort((a, b) => {
            // Sort relevant teams first, then non-relevant teams
            if (a.is_relevant && !b.is_relevant) return -1;
            if (!a.is_relevant && b.is_relevant) return 1;
            return 0;
          })"
          :key="team.team_id"
          class="team-item-expanded"
          :class="{ 'team-item-error': team.error }"
          open
        >
          <summary class="team-header-expanded">
            <div class="team-info">
              <h5 class="team-name">{{ team.team_name }}</h5>
              <span class="team-id font-mono">{{ team.team_id }}</span>
            </div>
            <div class="team-badges-expanded">
              <span
                class="relevancy-badge"
                :class="getRelevancyBadgeClass(team.is_relevant)"
              >
                {{ team.is_relevant ? '⚠️ Relevant' : 'Not Relevant' }}
              </span>
              <span class="score-badge" :class="getScoreColor(team.relevancy_score || 0)">
                Score: {{ team.relevancy_score != null ? team.relevancy_score.toFixed(3) : 'N/A' }}
              </span>
            </div>
          </summary>

          <div v-if="team.error" class="team-error">
            <strong>⚠️ Error:</strong> {{ team.error }}
          </div>

          <div v-else class="team-content-expanded">
            <!-- Overall Team Reasoning -->
            <div class="team-reasoning-expanded">
              <h6>📋 Overall Assessment</h6>
              <div
                class="team-reasoning-content markdown-content"
                v-html="renderMarkdown(team.reasoning || 'No reasoning provided')"
              ></div>
            </div>

            <!-- Chunk-level Analysis -->
            <div v-if="team.chunk_relevancies && team.chunk_relevancies.length > 0" class="chunk-analysis">
              <h6>🧩 Chunk-by-Chunk Analysis (<span class="stat-icon">📊</span> <span class="stat-text">{{ getChunkRelevancyStats(team).relevant }} / {{ getChunkRelevancyStats(team).total }} relevant chunks</span>)</h6>
              <div class="chunk-controls" style="margin-bottom: 1rem;">
                <button
                  @click="expandAllChunks"
                  class="btn-expand-chunks"
                >
                  📂 Expand All Chunks
                </button>
                <button
                  @click="collapseAllChunks"
                  class="btn-collapse-chunks"
                >
                  📁 Collapse All Chunks
                </button>
              </div>

              <div class="chunks-list">
                <details
                  v-for="(chunkRelevancy, index) in team.chunk_relevancies"
                  :key="index"
                  class="chunk-item"
                  :class="{ 'chunk-relevant': chunkRelevancy.relevancy.is_relevant }"
                  :open="false"
                >
                  <summary class="chunk-summary">
                    <div class="chunk-header">
                      <span class="chunk-status-icon">
                        {{ chunkRelevancy.relevancy.is_relevant ? '⚠️' : '' }}
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
                      <div
                        class="chunk-reasoning-content markdown-content"
                        v-html="renderMarkdown(chunkRelevancy.relevancy.reasoning)"
                      ></div>
                    </div>
                  </div>
                </details>
              </div>
            </div>

            <!-- No Chunks Section -->
            <div v-else class="no-chunks-section">
              <h6>📝 Chunk Analysis</h6>
              <div class="no-chunks-message">
                <p style="color: #6b7280; font-style: italic;">
                  No chunk-level analysis available for this team.
                  <br>
                  <span style="font-size: 0.75rem;">
                    This may indicate that the analysis was done at the document level only,
                    or chunk data wasn't captured during processing.
                  </span>
                </p>
              </div>
            </div>
          </div>
        </details>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lineage-viewer {
  max-height: 80vh;
  overflow-y: auto;
}

/* View Toggle Styles */
.view-toggle-section {
  margin-bottom: 0.75rem;
  padding: 0.75rem 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

/* Markdown Document View Styles */
.markdown-legend {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background-color: #f8fafc;
  border-radius: 0.375rem;
  border: 1px solid #e2e8f0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-color {
  width: 1rem;
  height: 1rem;
  border-radius: 0.25rem;
  border: 1px solid #d1d5db;
}

.relevant-color {
  background-color: #dc2626;
}

.multi-team-color {
  background: linear-gradient(135deg, #dc2626, #7c2d12);
  border: 1px solid #991b1b;
}

.not-relevant-color {
  background-color: #374151;
}

.legend-text {
  font-size: 0.875rem;
  color: #374151;
  font-weight: 500;
}

.markdown-document {
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
  max-height: 70vh;
  overflow-y: auto;
}

.document-title {
  margin: 0 0 1.5rem 0;
  color: #374151;
  font-weight: 700;
  font-size: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f1f5f9;
}

.document-content {
  line-height: 1.8;
  font-size: 0.95rem;
  color: #374151;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.document-chunk {
  border-radius: 0.25rem;
  padding: 0.125rem 0.25rem;
  margin: 0;
  transition: all 0.2s;
  position: relative;
  display: inline;
}

.document-chunk.chunk-relevant {
  cursor: pointer;
}

.document-chunk.chunk-not-relevant {
  cursor: default;
}

.chunk-relevant {
  background-color: #dc2626;
  color: #fef2f2;
  border: 1px solid #b91c1c;
  font-weight: 500;
}

.chunk-relevant:hover {
  background-color: #b91c1c;
  box-shadow: 0 2px 8px rgba(185, 28, 28, 0.4);
  transform: translateY(-1px);
  z-index: 10;
  border-color: #991b1b;
}

.chunk-active {
  background-color: #991b1b !important;
  color: #fef2f2 !important;
  border-color: #7f1d1d !important;
  box-shadow: 0 4px 12px rgba(127, 29, 29, 0.6) !important;
  transform: translateY(-1px) !important;
}

.chunk-not-relevant {
  background-color: transparent;
  color: #374151;
  border: 1px solid transparent;
}

.chunk-not-relevant:hover {
  background-color: #f3f4f6;
  box-shadow: 0 1px 3px rgba(107, 114, 128, 0.1);
}

.chunk-multi-team {
  background: linear-gradient(135deg, #dc2626, #7c2d12) !important;
  border: 2px solid #991b1b !important;
  position: relative;
}

.chunk-multi-team:hover {
  background: linear-gradient(135deg, #b91c1c, #92400e) !important;
  box-shadow: 0 3px 10px rgba(185, 28, 28, 0.5) !important;
}

.multi-team-indicator {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #fbbf24;
  color: #1f2937;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #f3f4f6;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  z-index: 5;
}

/* Custom Tooltip Styles */
.custom-tooltip {
  position: fixed;
  z-index: 1000;
  pointer-events: none;
  max-width: 500px;
  min-width: 300px;
  max-height: 400px;
}

.tooltip-content {
  background: #1f2937;
  color: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
  border: 1px solid #374151;
  font-size: 0.875rem; /* 14px at default browser font size - scales with browser zoom */
  line-height: 1.5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  pointer-events: all; /* Allow interaction with tooltip content */
}

.tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid #374151;
  padding-bottom: 0.5rem;
}

.tooltip-title strong {
  color: #fbbf24;
  font-size: 1rem; /* 16px at default - scales with browser zoom */
  font-weight: 600;
}

.tooltip-close {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
  border: 1px solid #4b5563;
  border-radius: 0.25rem;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
  flex-shrink: 0;
}

.tooltip-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border-color: #f87171;
}

.tooltip-section-title {
  color: #d1d5db;
  font-size: 0.8125rem; /* 13px at default - scales with browser zoom */
  font-weight: 500;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.tooltip-text {
  color: #f3f4f6;
  margin-bottom: 0.75rem;
  white-space: pre-line;
  word-wrap: break-word;
  font-size: 0.875rem; /* 14px at default - scales with browser zoom */
  line-height: 1.6;
}

.tooltip-footer {
  color: #9ca3af;
  font-size: 0.75rem; /* 12px at default - scales with browser zoom */
  font-style: italic;
  border-top: 1px solid #374151;
  padding-top: 0.5rem;
  margin-top: 0.75rem;
}

/* Custom scrollbar for tooltip */
.tooltip-content::-webkit-scrollbar {
  width: 6px;
}

.tooltip-content::-webkit-scrollbar-track {
  background: #374151;
  border-radius: 3px;
}

.tooltip-content::-webkit-scrollbar-thumb {
  background: #6b7280;
  border-radius: 3px;
}

.tooltip-content::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Ensure scrollbar is visible on hover */
.tooltip-content:hover::-webkit-scrollbar-thumb {
  background: #9ca3af;
}

/* Multi-team tooltip styles */
.team-relevancy-section {
  margin-bottom: 1rem;
}

.team-relevancy-header {
  color: #fbbf24;
  font-size: 0.9375rem; /* 15px at default - scales with browser zoom */
  font-weight: 600;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
  padding-bottom: 0.25rem;
}

.team-separator {
  border-top: 1px solid #4b5563;
  margin: 1rem 0;
  height: 1px;
}

/* Scroll indicator */
.scroll-indicator {
  position: sticky;
  bottom: 0;
  right: 0;
  text-align: right;
  padding: 0.25rem 0;
  background: linear-gradient(transparent, #1f2937 50%);
  pointer-events: none;
}

.scroll-hint {
  font-size: 0.625rem; /* 10px at default - scales with browser zoom */
  color: #6b7280;
  opacity: 0.7;
  font-style: italic;
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

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.info-value {
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
}

.teams-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
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
  cursor: pointer;
  list-style: none;
}

.team-header-expanded::-webkit-details-marker {
  display: none;
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

.relevancy-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.relevancy-badge-relevant {
  background-color: #fee2e2;
  color: #dc2626;
}

.relevancy-badge-not-relevant {
  background-color: #dcfce7;
  color: #166534;
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

.team-content-expanded {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-height: 50px; /* Ensure content area is visible */
  padding-top: 0.5rem;
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
  border-left: 4px solid #dc2626;
  background-color: #fef2f2;
}

.chunk-item:not(.chunk-relevant) {
  border-left: 4px solid #6b7280;
  background-color: #fafafa;
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
  background-color: #fee2e2;
  color: #dc2626;
}

.chunk-relevancy-label.not-relevant {
  background-color: #f3f4f6;
  color: #374151;
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

/* Markdown content styling */
.markdown-content {
  color: #4b5563;
  font-size: 0.875rem;
  line-height: 1.6;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  color: #374151;
  font-weight: 600;
  margin: 1rem 0 0.5rem 0;
  line-height: 1.4;
}

.markdown-content h1 { font-size: 1.5rem; }
.markdown-content h2 { font-size: 1.25rem; }
.markdown-content h3 { font-size: 1.125rem; }
.markdown-content h4 { font-size: 1rem; }
.markdown-content h5 { font-size: 0.875rem; }
.markdown-content h6 { font-size: 0.75rem; }

.markdown-content p {
  margin: 0.5rem 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content li {
  margin: 0.25rem 0;
}

.markdown-content strong {
  font-weight: 600;
  color: #374151;
}

.markdown-content em {
  font-style: italic;
}

.markdown-content code {
  background-color: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;
  padding: 0.125rem 0.375rem;
  font-family: 'SF Mono', Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 0.75rem;
  color: #374151;
}

.markdown-content pre {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  padding: 0.75rem;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.markdown-content pre code {
  background-color: transparent;
  border: none;
  padding: 0;
  font-size: 0.75rem;
  line-height: 1.4;
}

.markdown-content blockquote {
  border-left: 4px solid #e2e8f0;
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: #6b7280;
  font-style: italic;
}

.markdown-content a {
  color: #2563eb;
  text-decoration: underline;
}

.markdown-content a:hover {
  color: #1d4ed8;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75rem 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid #e2e8f0;
  padding: 0.5rem;
  text-align: left;
}

.markdown-content th {
  background-color: #f8fafc;
  font-weight: 600;
}

.markdown-content hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 1rem 0;
}

.no-chunks-section {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem;
}

.no-chunks-section h6 {
  margin: 0 0 0.75rem 0;
  color: #374151;
  font-weight: 600;
  font-size: 1rem;
}

.no-chunks-message {
  text-align: center;
  padding: 1rem;
}

.btn-expand-chunks, .btn-collapse-chunks {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  margin-right: 0.5rem;
  transition: background-color 0.2s;
}

.btn-expand-chunks:hover, .btn-collapse-chunks:hover {
  background-color: #2563eb;
}

.btn-collapse-chunks {
  background-color: #6b7280;
}

.btn-collapse-chunks:hover {
  background-color: #4b5563;
}

.spans-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.span-item {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  background: white;
}

.span-task {
  border-left: 4px solid #3b82f6;
  background-color: #f0f9ff;
}

.span-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.span-name {
  margin: 0;
  color: #374151;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.span-id {
  font-size: 0.75rem;
  color: #6b7280;
  background-color: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.span-meta {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.span-status {
  font-weight: 600;
  font-size: 0.875rem;
}

.span-duration {
  font-size: 0.875rem;
  color: #6b7280;
  font-family: monospace;
}

.span-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.span-times {
  display: flex;
  gap: 2rem;
  font-size: 0.875rem;
  color: #4b5563;
}

.task-output {
  background-color: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 0.375rem;
  padding: 1rem;
}

.task-output-json {
  background-color: #f8fafc;
  padding: 0.75rem;
  border-radius: 0.25rem;
  overflow-x: auto;
  font-size: 0.75rem;
  line-height: 1.4;
  margin-top: 0.5rem;
}

.span-attributes,
.span-events {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  padding: 1rem;
}

.attributes-list,
.events-list {
  margin-top: 0.5rem;
}

.attribute-item,
.event-attribute {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.attribute-key {
  color: #6b7280;
  font-weight: 500;
  min-width: 100px;
}

.attribute-value {
  color: #374151;
  font-family: monospace;
  word-break: break-all;
}

.event-item {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f1f5f9;
}

.event-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.event-name {
  font-weight: 600;
  color: #374151;
}

.event-time {
  font-size: 0.75rem;
  color: #6b7280;
  font-family: monospace;
}

.raw-data-details {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem;
}

.raw-data-details summary {
  cursor: pointer;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
}

.raw-data {
  background-color: #1f2937;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  font-size: 0.75rem;
  line-height: 1.4;
  max-height: 400px;
  overflow-y: auto;
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

/* Classification Analysis Styles */
.classification-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.classification-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.classification-summary-horizontal {
  display: flex;
  gap: 1.5rem;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
  flex-wrap: nowrap;
  align-items: flex-start;
}

.classification-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.classification-item-horizontal {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 0 1 auto;
  min-width: 150px;
}

.classification-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.classification-value {
  font-size: 1rem;
  font-weight: 600;
}

.expected-relevant {
  color: #16a34a;
}

.expected-not-relevant {
  color: #dc2626;
}

.actual-relevant {
  color: #f59e0b;
}

.actual-not-relevant {
  color: #6b7280;
}

.classification-badge {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.badge-true-positive {
  background-color: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.badge-false-positive {
  background-color: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.badge-true-negative {
  background-color: #dbeafe;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

.badge-false-negative {
  background-color: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.classification-explanation {
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 0.5rem;
  padding: 1rem;
}

.explanation-item h6 {
  margin: 0 0 0.75rem 0;
  color: #0369a1;
  font-weight: 600;
}

.explanation-item ul {
  margin: 0;
  padding-left: 1.5rem;
}

.explanation-item li {
  margin-bottom: 0.5rem;
  color: #4b5563;
  line-height: 1.5;
}

/* Expected Output Styles */
.expected-output-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.expected-teams-summary {
  display: flex;
  gap: 2rem;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.expected-teams-list h6 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-weight: 600;
  font-size: 1rem;
}

.expected-teams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.expected-team-item {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  background: white;
}

.expected-team-item.expected-relevant {
  border-left: 4px solid #16a34a;
  background-color: #f0fdf4;
}

.expected-team-item:not(.expected-relevant) {
  border-left: 4px solid #6b7280;
  background-color: #fafafa;
}

.expected-team-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.expected-team-name {
  font-weight: 600;
  color: #374151;
}

.expected-relevancy-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.expected-relevant-badge {
  background-color: #dcfce7;
  color: #166534;
}

.expected-not-relevant-badge {
  background-color: #f3f4f6;
  color: #374151;
}

.expected-team-reasoning {
  margin-top: 0.75rem;
}

.expected-team-reasoning strong {
  color: #374151;
  font-size: 0.875rem;
  display: block;
  margin-bottom: 0.5rem;
}

.expected-team-reasoning p {
  color: #4b5563;
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.6;
}

/* Custom scrollbars */
.lineage-viewer::-webkit-scrollbar,
.teams-list::-webkit-scrollbar,
.raw-data::-webkit-scrollbar {
  width: 6px;
}

.lineage-viewer::-webkit-scrollbar-track,
.teams-list::-webkit-scrollbar-track,
.raw-data::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.lineage-viewer::-webkit-scrollbar-thumb,
.teams-list::-webkit-scrollbar-thumb,
.raw-data::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.lineage-viewer::-webkit-scrollbar-thumb:hover,
.teams-list::-webkit-scrollbar-thumb:hover,
.raw-data::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .teams-summary {
    flex-direction: column;
    gap: 1rem;
  }

  .team-header {
    flex-direction: column;
    gap: 0.75rem;
  }

  .span-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .span-times {
    flex-direction: column;
    gap: 0.5rem;
  }

  .classification-summary-horizontal {
    flex-direction: column;
    gap: 1rem;
  }

  .classification-item-horizontal {
    min-width: unset;
  }
}
</style>
