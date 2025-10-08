<script lang="ts" setup>
import SavedConversationItem from './SavedConversationItem.vue';
import type { ConversationFolder, SavedConversation } from '@/types/index';
import { AaText, AaButton, AaInput, AaIconButton } from '@aleph-alpha/ds-components-vue';
import { ref, watch, computed } from 'vue';

interface Props {
  folder: ConversationFolder;
  conversations: SavedConversation[];
  isCollapsed: boolean;
  isEditing: boolean;
}

interface Emits {
  (e: 'toggle-collapse'): void;
  (e: 'start-edit'): void;
  (e: 'save-edit', folderName: string): void;
  (e: 'cancel-edit'): void;
  (e: 'delete'): void;
  (e: 'load-conversation', conversation: SavedConversation): void;
  (e: 'delete-conversation', conversationId: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const editingName = ref('');

// Update editing name when editing starts
watch(
  () => props.isEditing,
  (isEditing) => {
    if (isEditing) {
      editingName.value = props.folder.name;
    }
  }
);

const hasConversations = computed(() => props.conversations.length > 0);

function handleSaveEdit(): void {
  if (editingName.value.trim()) {
    emit('save-edit', editingName.value.trim());
  }
}

function handleCancelEdit(): void {
  editingName.value = '';
  emit('cancel-edit');
}

function handleKeyup(event: KeyboardEvent): void {
  if (event.key === 'Enter') {
    handleSaveEdit();
  } else if (event.key === 'Escape') {
    handleCancelEdit();
  }
}

function handleToggleCollapse(): void {
  if (hasConversations.value) {
    emit('toggle-collapse');
  }
}
</script>

<template>
  <div class="space-y-2">
    <div class="group flex items-center justify-between">
      <!-- Editing Mode -->
      <div v-if="isEditing" class="flex flex-1 items-center justify-between gap-2">
        <div class="w-4/5">
          <AaInput v-model="editingName" size="small" class="flex-1" @keyup="handleKeyup" />
        </div>
        <div class="flex items-center gap-1">
          <AaButton size="small" variant="primary" @click="handleSaveEdit"> Save </AaButton>
          <AaButton size="small" variant="text" @click="handleCancelEdit"> Cancel </AaButton>
        </div>
      </div>

      <!-- Display Mode -->
      <div
        v-else
        class="flex flex-1 items-center gap-2"
        :class="hasConversations ? 'cursor-pointer' : 'cursor-default'"
        @click="handleToggleCollapse"
      >
        <span
          v-if="hasConversations"
          class="text-core-content-secondary transition-transform duration-200"
          :class="isCollapsed ? 'i-material-symbols-folder' : 'i-material-symbols-folder-outline'"
        ></span>
        <span v-else class="i-material-symbols-folder-outline text-core-content-secondary"></span>

        <AaText
          weight="medium"
          :class="hasConversations ? 'text-core-content-primary' : 'text-core-content-secondary'"
        >
          {{ folder.name }}
        </AaText>

        <AaText size="sm" class="text-core-content-tertiary"> ({{ conversations.length }}) </AaText>
      </div>

      <!-- Folder Actions -->
      <div
        v-if="!isEditing"
        class="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100"
      >
        <AaIconButton
          label="Edit"
          size="small"
          tooltip-text="Edit Folder Name"
          icon="i-material-symbols-edit-outline"
          @click="emit('start-edit')"
        />
        <AaIconButton
          label="Delete"
          size="small"
          tooltip-text="Delete Folder"
          icon="i-material-symbols-delete-outline"
          @click="emit('delete')"
        />
      </div>
    </div>

    <!-- Conversations in folder -->
    <div v-if="hasConversations && !isCollapsed" class="ml-6 space-y-2">
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
