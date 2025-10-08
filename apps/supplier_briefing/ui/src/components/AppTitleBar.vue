<script lang="ts" setup>
import SaveConversationDialog from '@/components/SavedConversation/SaveConversationDialog.vue';
import SavedConversationSidePanel from '@/components/SavedConversation/SavedConversationSidePanel.vue';
import { useConversationStore } from '@/stores/useConversationStore.ts';
import { AaText, AaButton, AaModal } from '@aleph-alpha/ds-components-vue';
import { ref, computed } from 'vue';

const conversationStore = useConversationStore();
const showConfirmationModal = ref(false);
const showSaveDialog = ref(false);
const showHistoryPanel = ref(false);

const activeConversation = computed(() => conversationStore.activeConversation);

const hasActiveConversation = computed(() => {
  return activeConversation.value && activeConversation.value.messages.length > 0;
});

const isSearching = computed(() => {
  return activeConversation.value && activeConversation.value.isSearching;
});

const handleNewConversationClick = () => {
  if (hasActiveConversation.value) {
    showConfirmationModal.value = true;
  } else {
    conversationStore.startNewConversation();
  }
};

const confirmNewConversation = () => {
  conversationStore.startNewConversation();
  showConfirmationModal.value = false;
};

const cancelNewConversation = () => {
  showConfirmationModal.value = false;
};

const handleSaveConversation = () => {
  showSaveDialog.value = true;
};

const handleSaveDialogClose = () => {
  showSaveDialog.value = false;
};

const handleConversationSaved = () => {
  // Could show a success message here if needed
  console.log('Conversation saved successfully');
};

const toggleHistoryPanel = () => {
  showHistoryPanel.value = !showHistoryPanel.value;
};

const handleConversationLoaded = () => {
  showHistoryPanel.value = false;
};
</script>

<template>
  <div class="px-XL flex w-full items-center justify-between gap-6 border-b py-2.5">
    <AaText element="h2" class="text-core-content-primary" size="sm" weight="bold">
      Supplier Briefing
    </AaText>

    <div class="flex items-center gap-3">
      <AaButton
        variant="text"
        :disabled="
          isSearching ||
          !conversationStore.canSaveCurrentConversation ||
          conversationStore.isCurrentConversationSaved
        "
        @click="handleSaveConversation"
        :class="{ 'text-green-600': conversationStore.isCurrentConversationSaved }"
        :append-icon="
          conversationStore.isCurrentConversationSaved ? 'i-material-symbols-check' : ''
        "
        :prepend-icon="
          !conversationStore.isCurrentConversationSaved ? 'i-material-symbols-bookmark-outline' : ''
        "
      >
        {{ conversationStore.isCurrentConversationSaved ? 'Auto-Saving' : 'Save Chat' }}
      </AaButton>
      <AaButton
        variant="secondary"
        prepend-icon="i-material-symbols-schedule-outline"
        @click="toggleHistoryPanel"
        >Saved Chats</AaButton
      >
      <AaButton
        variant="primary"
        :disabled="!hasActiveConversation"
        @click="handleNewConversationClick"
        prepend-icon="i-material-symbols-add"
      >
        New Chat
      </AaButton>
    </div>
  </div>

  <!-- Confirmation Modal -->
  <Teleport to="body">
    <AaModal
      v-if="showConfirmationModal"
      class="max-w-4xl"
      :with-overlay="true"
      @close="cancelNewConversation"
      title="Start New Conversation?"
    >
      <AaText class="text-core-content-secondary p-4">
        Are you sure you want to start a new chat? Any ongoing research will be stopped and unsaved
        chats will be lost permanently. This action cannot be undone.
      </AaText>

      <template #footer>
        <div class="flex justify-end gap-3">
          <AaButton variant="text" @click="cancelNewConversation"> Cancel </AaButton>
          <AaButton variant="primary" @click="confirmNewConversation"> Confirm </AaButton>
        </div>
      </template>
    </AaModal>
  </Teleport>

  <SaveConversationDialog
    v-if="showSaveDialog"
    :is-open="showSaveDialog"
    @close="handleSaveDialogClose"
    @saved="handleConversationSaved"
  />

  <Teleport to="body">
    <div v-if="showHistoryPanel" class="fixed inset-0 z-20 flex" @click.self="toggleHistoryPanel">
      <div class="absolute inset-0 bg-black bg-opacity-25" @click="toggleHistoryPanel"></div>
      <div class="relative ml-auto h-full w-96 bg-white shadow-xl">
        <SavedConversationSidePanel @conversation-loaded="handleConversationLoaded" />
      </div>
    </div>
  </Teleport>
</template>
