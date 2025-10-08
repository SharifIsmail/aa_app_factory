<script lang="ts" setup>
import FolderItem from './FolderItem.vue';
import { useConversationStore } from '@/stores/useConversationStore';
import type { ConversationFolder, SavedConversation } from '@/types/index';
import { ref } from 'vue';

interface Props {
  folders: ConversationFolder[];
  conversationsByFolder: Record<string, SavedConversation[]>;
}

interface Emits {
  (e: 'load-conversation', conversation: SavedConversation): void;
  (e: 'delete-conversation', conversationId: string): void;
  (e: 'delete-folder', folderId: string): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();

const conversationStore = useConversationStore();
const editingFolderId = ref<string | null>(null);
const collapsedFolders = ref<Set<string>>(new Set());

function toggleFolderCollapse(folderId: string): void {
  if (collapsedFolders.value.has(folderId)) {
    collapsedFolders.value.delete(folderId);
  } else {
    collapsedFolders.value.add(folderId);
  }
}

function isFolderCollapsed(folderId: string): boolean {
  return collapsedFolders.value.has(folderId);
}

function startEditingFolder(folderId: string): void {
  editingFolderId.value = folderId;
}

function saveEditingFolder(folderId: string, folderName: string): void {
  conversationStore.updateFolder(folderId, folderName);
  editingFolderId.value = null;
}

function cancelEditingFolder(): void {
  editingFolderId.value = null;
}

function isEditingFolder(folderId: string): boolean {
  return editingFolderId.value === folderId;
}

function handleFolderDelete(folderId: string): void {
  emit('delete-folder', folderId);
}

function handleLoadConversation(conversation: SavedConversation): void {
  emit('load-conversation', conversation);
}

function handleDeleteConversation(conversationId: string): void {
  emit('delete-conversation', conversationId);
}
</script>

<template>
  <div class="space-y-4">
    <FolderItem
      v-for="folder in folders"
      :key="folder.id"
      :folder="folder"
      :conversations="conversationsByFolder[folder.id] || []"
      :is-collapsed="isFolderCollapsed(folder.id)"
      :is-editing="isEditingFolder(folder.id)"
      @toggle-collapse="toggleFolderCollapse(folder.id)"
      @start-edit="startEditingFolder(folder.id)"
      @save-edit="saveEditingFolder(folder.id, $event)"
      @cancel-edit="cancelEditingFolder"
      @delete="handleFolderDelete(folder.id)"
      @load-conversation="handleLoadConversation"
      @delete-conversation="handleDeleteConversation"
    />
  </div>
</template>
