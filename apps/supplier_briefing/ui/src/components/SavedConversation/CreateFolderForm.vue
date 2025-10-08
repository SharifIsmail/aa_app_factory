<script lang="ts" setup>
import { AaInput, AaIconButton, AaButton } from '@aleph-alpha/ds-components-vue';
import { ref } from 'vue';

export type ButtonVariant = 'icon' | 'normal';

interface Props {
  isVisible: boolean;
  buttonText?: string;
  buttonVariant?: ButtonVariant;
}

interface Emits {
  (e: 'create', folderName: string): void;
  (e: 'cancel'): void;
  (e: 'start-create'): void;
}

const props = withDefaults(defineProps<Props>(), {
  buttonText: 'New Folder',
  buttonVariant: 'icon',
});
const emit = defineEmits<Emits>();

const folderName = ref('');

function handleCreate(): void {
  if (folderName.value.trim()) {
    emit('create', folderName.value.trim());
    folderName.value = '';
  }
}

function handleCancel(): void {
  folderName.value = '';
  emit('cancel');
}

function handleKeyup(event: KeyboardEvent): void {
  if (event.key === 'Enter') {
    handleCreate();
  } else if (event.key === 'Escape') {
    handleCancel();
  }
}
</script>

<template>
  <div v-if="isVisible" class="flex items-center justify-between gap-1">
    <div class="w-3/5">
      <AaInput
        v-model="folderName"
        size="small"
        placeholder="Enter folder name"
        @keyup="handleKeyup"
      />
    </div>
    <div class="flex items-center gap-1">
      <AaButton size="small" variant="primary" @click="handleCreate" :disabled="!folderName.trim()">
        Create
      </AaButton>
      <AaButton size="small" variant="text" @click="handleCancel"> Cancel </AaButton>
    </div>
  </div>

  <AaIconButton
    v-if="props.buttonVariant === 'icon' && !isVisible"
    size="small"
    variant="ghost"
    class="justify-start"
    icon="i-material-symbols-create-new-folder-outline"
    @click="emit('start-create')"
    :label="props.buttonText"
    tooltip-text="Create New Folder"
  />
  <AaButton
    v-if="props.buttonVariant === 'normal' && !isVisible"
    size="small"
    variant="secondary"
    class="justify-start"
    prepend-icon="i-material-symbols-create-new-folder-outline"
    @click="emit('start-create')"
  >
    {{ props.buttonText }}
  </AaButton>
</template>
