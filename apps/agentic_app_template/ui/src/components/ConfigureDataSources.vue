<script setup lang="ts">
import { AaModal, AaSelect, AaCheckbox, type AaSelectOption } from '@aleph-alpha/ds-components-vue';
import { ref } from 'vue';

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const lorem1 = ref(false);
const lorem2 = ref(false);

const loremSelectOptions = [
  { value: 'ipsum1', label: 'Ipsum 1' },
  { value: 'ipsum2', label: 'Ipsum 2' },
  { value: 'ipsum3', label: 'Ipsum 3' },
];

const selectedLorem = ref<AaSelectOption>({
  value: loremSelectOptions[0].value,
  label: loremSelectOptions[0].label,
});

function handleLoremSelectChange(option: AaSelectOption | null) {
  if (option) {
    selectedLorem.value = option;
  }
}
</script>

<template>
  <Teleport to="body">
    <AaModal title="Settings" with-overlay @close="emit('close')">
      <div class="flex w-[400px] max-w-full flex-col">
        <div class="space-y-6 p-6">
          <div class="flex items-center justify-between pr-3">
            <span>Lorem ipsum dolor</span>
            <AaCheckbox name="lorem1" v-model="lorem1" />
          </div>
          <div class="flex items-center justify-between pr-3">
            <span>Sit amet consectetur</span>
            <AaCheckbox name="lorem2" v-model="lorem2" />
          </div>
          <div class="flex items-center justify-between">
            <span>Adipiscing elit</span>
            <AaSelect
              :model-value="selectedLorem"
              :options="loremSelectOptions"
              size="medium"
              variant="text"
              placeholder=""
              @update:model-value="handleLoremSelectChange"
            />
          </div>
        </div>
      </div>
    </AaModal>
  </Teleport>
</template>
