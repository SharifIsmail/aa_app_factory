<script lang="ts" setup>
import CreateFolderForm from './CreateFolderForm.vue';
import DefaultFolder from './DefaultFolder.vue';
import DeleteConfirmationModal from './DeleteConfirmationModal.vue';
import EmptyState from './EmptyState.vue';
import FolderList from './FolderList.vue';
import SearchInput from './SearchInput.vue';
import { useConversationStore } from '@/stores/useConversationStore';
import type { SavedConversation } from '@/types/index';
import { AaText, AaIconButton } from '@aleph-alpha/ds-components-vue';
import { ref, computed } from 'vue';

enum SidePanelEntity {
  Conversation = 'conversation',
  Folder = 'folder',
}

interface Emits {
  (e: 'conversationLoaded'): void;
}

const emit = defineEmits<Emits>();

const conversationStore = useConversationStore();

// State management
const showDeleteConfirmation = ref<string | null>(null);
const deletingType = ref<SidePanelEntity>(SidePanelEntity.Conversation);
const isCreatingFolder = ref(false);
const searchTerm = ref('');

const isSearching = computed(() => {
  return searchTerm.value.trim().length > 0;
});

const filteredConversationsByFolder = computed(() => {
  if (!isSearching.value) {
    return conversationStore.savedConversationsByFolder;
  }

  const searchQuery = searchTerm.value.toLowerCase().trim();
  const filtered: Record<string, SavedConversation[]> = {};

  Object.entries(conversationStore.savedConversationsByFolder).forEach(
    ([folderId, conversations]) => {
      const matchingConversations = conversations.filter((conversation) => {
        if (conversation.title.toLowerCase().includes(searchQuery)) {
          return true;
        }
      });

      if (matchingConversations.length > 0) {
        filtered[folderId] = matchingConversations;
      }
    }
  );

  return filtered;
});

const filteredFolders = computed(() => {
  const allFolders = conversationStore.conversationHistory.folders;
  if (!isSearching.value) {
    return allFolders;
  }

  return allFolders.filter((folder) => filteredConversationsByFolder.value[folder.id]?.length > 0);
});

const hasFilteredContent = computed(() => {
  if (!isSearching.value) {
    return conversationStore.hasAnyContent;
  }

  return Object.keys(filteredConversationsByFolder.value).length > 0;
});

// Delete confirmation computed properties
const deleteModalTitle = computed(() => {
  return deletingType.value === SidePanelEntity.Folder ? 'Delete Folder?' : 'Delete Chat?';
});

const deleteModalMessage = computed(() => {
  if (deletingType.value === SidePanelEntity.Folder) {
    return 'Are you sure you want to delete the folder? This will delete the folder and all chats in it. This action cannot be undone.';
  }
  return 'Are you sure you want to delete the chat? This action cannot be undone.';
});

// Event handlers
function handleLoadConversation(conversation: SavedConversation): void {
  conversationStore.loadSavedConversation(conversation.id);
  emit('conversationLoaded');
}

function handleDeleteConversation(conversationId: string): void {
  showDeleteConfirmation.value = conversationId;
  deletingType.value = SidePanelEntity.Conversation;
}

function handleFolderDelete(folderId: string): void {
  showDeleteConfirmation.value = folderId;
  deletingType.value = SidePanelEntity.Folder;
}

function handleDelete(): void {
  if (!showDeleteConfirmation.value) return;

  if (deletingType.value === SidePanelEntity.Folder) {
    conversationStore.deleteFolder(showDeleteConfirmation.value);
  } else {
    conversationStore.deleteSavedConversation(showDeleteConfirmation.value);
  }

  showDeleteConfirmation.value = null;
}

function cancelDelete(): void {
  showDeleteConfirmation.value = null;
}

// Create folder handlers
function handleCreateFolder(folderName: string): void {
  conversationStore.createFolder(folderName);
  isCreatingFolder.value = false;
}

function handleCancelCreateFolder(): void {
  isCreatingFolder.value = false;
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Header -->
    <div class="border-b p-4">
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-2">
          <AaText element="h3" size="lg" weight="bold" class="text-core-content-primary">
            Saved Chats
          </AaText>
          <AaText size="sm" class="text-core-content-secondary mt-1">
            {{ conversationStore.conversationHistory.savedConversations.length }} saved chat(s)
          </AaText>
        </div>
        <AaIconButton
          label="Close"
          icon="i-material-symbols-close"
          size="small"
          @click="emit('conversationLoaded')"
        />
      </div>

      <div class="mt-3">
        <SearchInput v-model="searchTerm" placeholder="Search chats by title..." />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div v-if="!hasFilteredContent" class="flex h-full flex-col">
        <EmptyState :is-searching="isSearching" />

        <div v-if="!isSearching" class="px-4 pb-4">
          <CreateFolderForm
            :is-visible="isCreatingFolder"
            button-variant="normal"
            @create="handleCreateFolder"
            @cancel="handleCancelCreateFolder"
            @start-create="() => (isCreatingFolder = true)"
          />
        </div>
      </div>

      <div v-else class="space-y-4 p-4">
        <!-- Custom folders -->
        <FolderList
          :folders="filteredFolders"
          :conversations-by-folder="filteredConversationsByFolder"
          @load-conversation="handleLoadConversation"
          @delete-conversation="handleDeleteConversation"
          @delete-folder="handleFolderDelete"
        />
        <!-- Default folder conversations -->
        <DefaultFolder
          :conversations="filteredConversationsByFolder.default || []"
          @load-conversation="handleLoadConversation"
          @delete-conversation="handleDeleteConversation"
        />

        <!-- Create Folder Section -->
        <div v-if="!isSearching" class="mt-4 pb-4">
          <CreateFolderForm
            :is-visible="isCreatingFolder"
            button-variant="normal"
            @create="handleCreateFolder"
            @cancel="handleCancelCreateFolder"
            @start-create="isCreatingFolder = true"
          />
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmationModal
      :is-visible="!!showDeleteConfirmation"
      :title="deleteModalTitle"
      :message="deleteModalMessage"
      @confirm="handleDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>
