<script lang="ts" setup>
import { AaText, AaButton, AaModal } from '@aleph-alpha/ds-components-vue';

interface Props {
  isVisible: boolean;
  title: string;
  message: string;
}

interface Emits {
  (e: 'confirm'): void;
  (e: 'cancel'): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();
</script>

<template>
  <Teleport to="body">
    <AaModal
      v-if="isVisible"
      class="max-w-md"
      :with-overlay="true"
      @close="emit('cancel')"
      :title="title"
    >
      <div class="p-4">
        <AaText class="text-core-content-secondary">
          {{ message }}
        </AaText>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <AaButton variant="text" @click="emit('cancel')">Cancel</AaButton>
          <AaButton variant="primary" @click="emit('confirm')">Delete</AaButton>
        </div>
      </template>
    </AaModal>
  </Teleport>
</template>
