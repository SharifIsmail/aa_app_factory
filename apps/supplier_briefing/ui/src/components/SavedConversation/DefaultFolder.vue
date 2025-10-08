<script lang="ts" setup>
import SavedConversationItem from './SavedConversationItem.vue';
import type { SavedConversation } from '@/types/index';
import { AaText } from '@aleph-alpha/ds-components-vue';

interface Props {
  conversations: SavedConversation[];
}

interface Emits {
  (e: 'load-conversation', conversation: SavedConversation): void;
  (e: 'delete-conversation', conversationId: string): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();
</script>

<template>
  <div v-if="conversations.length > 0" class="space-y-2">
    <div class="flex flex-1 items-center gap-2">
      <AaText weight="medium" class="text-core-content-primary flex items-center gap-2">
        <span class="i-material-symbols-folder-outline text-core-content-secondary"></span>
        Default Folder
      </AaText>
      <AaText size="sm" class="text-core-content-tertiary"> ({{ conversations.length }}) </AaText>
    </div>

    <div class="ml-6 space-y-2">
      <SavedConversationItem
        v-for="conversation in conversations"
        :key="conversation.id"
        :conversation="conversation"
        @load="emit('load-conversation', $event)"
        @delete="emit('delete-conversation', $event)"
      />
    </div>
  </div>
</template>
