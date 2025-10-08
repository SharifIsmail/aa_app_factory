<script setup lang="ts">
import type { Citation } from '../types';
import { AaText, AaModal } from '@aleph-alpha/ds-components-vue';

// Props expected from parent component
defineProps<{
  isOpen: boolean;
  citation: Citation | null;
  citationNumber: number;
}>();

const emit = defineEmits<{
  close: [];
}>();

const handleClose = () => {
  emit('close');
};

function getChunkText(chunk: unknown): string {
  if (!chunk) return '';
  if (typeof chunk === 'string') return chunk;
  if (typeof chunk === 'object') {
    const obj = chunk as Record<string, any>;
    if (typeof obj.content === 'string') {
      return obj.content;
    }
  }
  return String(chunk);
}
</script>

<template>
  <Teleport to="body">
    <AaModal
      v-if="isOpen && citation"
      :title="`Source [${citationNumber}]`"
      with-overlay
      @close="handleClose"
    >
      <div class="flex w-[600px] flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-4">
            <!-- Chunk Text -->
            <div>
              <AaText size="sm" weight="bold" class="text-core-content-primary mb-2">
                Legal Text:
              </AaText>
              <div class="rounded-lg border-l-4 border-blue-500 bg-gray-50 p-4">
                <AaText size="sm" class="text-core-content-primary italic leading-relaxed">
                  "{{ getChunkText(citation.chunk) }}"
                </AaText>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AaModal>
  </Teleport>
</template>
