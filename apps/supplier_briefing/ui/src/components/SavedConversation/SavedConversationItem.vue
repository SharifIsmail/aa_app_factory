<script lang="ts" setup>
import type { SavedConversation } from '@/types/index';
import { AaText, AaButton, AaIconButton } from '@aleph-alpha/ds-components-vue';

interface Props {
  conversation: SavedConversation;
}

interface Emits {
  (e: 'load', conversation: SavedConversation): void;
  (e: 'delete', conversationId: string): void;
}

const props = defineProps<Props>();

const emit = defineEmits<Emits>();

function handleLoad(): void {
  emit('load', props.conversation);
}

function handleDelete(): void {
  emit('delete', props.conversation.id);
}

function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}
</script>

<template>
  <div class="flex w-full items-start justify-between">
    <AaButton class="w-4/5 text-left" variant="text" @click="handleLoad">
      <div class="min-w-0 flex-1">
        <AaText weight="medium" class="text-core-content-primary truncate">
          {{ conversation.title.slice(0, 35) }}...
        </AaText>
        <AaText size="xs" class="text-core-content-secondary italic">
          Saved on {{ formatDate(conversation.savedAt) }}
        </AaText>
      </div>
    </AaButton>
    <AaIconButton
      label="Delete"
      icon="i-material-symbols-delete-outline"
      size="small"
      tooltip-text="Delete Chat"
      @click.stop="handleDelete"
    />
  </div>
</template>
