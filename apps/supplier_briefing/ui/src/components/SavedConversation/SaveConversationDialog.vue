<script lang="ts" setup>
import CreateFolderForm from './CreateFolderForm.vue';
import { useConversationStore } from '@/stores/useConversationStore';
import {
  AaText,
  AaButton,
  AaModal,
  AaInput,
  AaSelect,
  type AaSelectModelValue,
} from '@aleph-alpha/ds-components-vue';
import { ref, computed } from 'vue';

interface Props {
  isOpen: boolean;
}

interface Emits {
  (e: 'close'): void;
  (e: 'saved'): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();

const conversationStore = useConversationStore();
const defaultOption = {
  label: 'Default Folder',
  value: 'default',
};

// Form state
const conversationTitle = ref<string>(conversationStore.activeConversation?.title || '');
const selectedFolder = ref<AaSelectModelValue>(defaultOption);
const isCreatingFolder = ref(false);
const isSaving = ref(false);

// Computed properties
const selectableFolders = computed(() => {
  return [
    defaultOption,
    ...conversationStore.conversationHistory.folders.map((folder) => ({
      label: folder.name,
      value: folder.id,
    })),
  ];
});

const canSave = computed(() => {
  return conversationTitle.value.trim().length > 0 && !isSaving.value && !isCreatingFolder.value;
});

const handleClose = (): void => {
  if (!isSaving.value) {
    emit('close');
  }
};

const handleCreateFolder = (folderName: string): void => {
  const existingFolder = conversationStore.conversationHistory.folders.find(
    (f) => f.name.toLowerCase() === folderName.toLowerCase()
  );

  if (existingFolder) {
    console.warn('A folder with this name already exists');
    return;
  }

  try {
    const folderId = conversationStore.createFolder(folderName);
    selectedFolder.value = {
      label: folderName,
      value: folderId,
    };
    isCreatingFolder.value = false;
  } catch (err) {
    console.error('Failed to create folder:', err);
  }
};

const handleCancelCreateFolder = (): void => {
  isCreatingFolder.value = false;
};

const handleSelectFolder = (folder: AaSelectModelValue): void => {
  selectedFolder.value = folder;
};

const handleSave = async (): Promise<void> => {
  if (!canSave.value || !conversationStore.activeConversation) {
    return;
  }

  isSaving.value = true;

  try {
    conversationStore.saveConversation(conversationTitle.value.trim(), selectedFolder.value?.value);

    emit('saved');
    emit('close');
  } catch (err) {
    console.error('Failed to save conversation:', err);
  } finally {
    isSaving.value = false;
  }
};
</script>

<template>
  <Teleport to="body">
    <AaModal
      v-if="isOpen"
      class="w-2xl max-w-2xl"
      :with-overlay="true"
      @close="handleClose"
      title="Save Conversation"
    >
      <div class="space-y-6 p-6">
        <!-- Conversation Title -->
        <div class="space-y-2">
          <AaText element="label" size="sm" weight="medium" class="text-core-content-primary">
            Conversation Title
          </AaText>
          <AaInput
            v-model="conversationTitle"
            placeholder="Enter conversation title..."
            :disabled="isSaving"
            class="w-full"
          />
        </div>

        <!-- Folder Selection -->
        <div class="space-y-2">
          <AaText element="label" size="sm" weight="medium" class="text-core-content-primary">
            {{ isCreatingFolder ? 'Create New Folder' : 'Save to Folder' }}
          </AaText>

          <div class="flex items-center gap-3">
            <AaSelect
              v-if="!isCreatingFolder"
              class="w-2/5"
              :model-value="selectedFolder"
              :disabled="isSaving"
              :options="selectableFolders"
              @update:model-value="handleSelectFolder"
            />
            <CreateFolderForm
              :is-visible="isCreatingFolder"
              @create="handleCreateFolder"
              @cancel="handleCancelCreateFolder"
              @start-create="isCreatingFolder = true"
            />
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <AaButton variant="text" @click="handleClose" :disabled="isSaving"> Cancel </AaButton>
          <AaButton variant="primary" @click="handleSave" :disabled="!canSave" :loading="isSaving">
            Save Conversation
          </AaButton>
        </div>
      </template>
    </AaModal>
  </Teleport>
</template>
