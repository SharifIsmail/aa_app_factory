<script setup lang="ts">
import { researchAgentService } from '@/utils/http';
import { AaButton, AaSelect, AaInput, type AaSelectOption } from '@aleph-alpha/ds-components-vue';
import { ref, computed } from 'vue';

const researchTopic = ref('');
const isSearching = ref(false);

const researchTypeOptions = [
  { value: 'basic', label: 'Basic' },
  { value: 'comprehensive', label: 'Comprehensive' },
];

const researchType = ref<AaSelectOption>({
  value: researchTypeOptions[0].value,
  label: researchTypeOptions[0].label,
});

const emit = defineEmits<{
  (e: 'search-started', researchId: string): void;
}>();

const isFormValid = computed(() => {
  return researchTopic.value.trim() !== '';
});

function handleResearchTypeChange(option: AaSelectOption | null) {
  if (option) {
    researchType.value = option;
  }
}

const startResearchingTopic = async () => {
  if (isFormValid.value) {
    isSearching.value = true;
    try {
      const data = await researchAgentService.startResearchAgent(
        researchTopic.value,
        researchType.value.value
      );
      emit('search-started', data.id);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      isSearching.value = false;
    }
  }
};
</script>

<template>
  <div
    class="mx-auto w-full max-w-[600px] rounded-lg border border-gray-100 bg-white bg-opacity-90 p-4 shadow-md backdrop-blur-sm"
  >
    What do you want to research today?
    <div class="mt-4 flex flex-col gap-4">
      <AaInput
        v-model="researchTopic"
        placeholder="Enter your research topic *"
        size="medium"
        @keydown.enter="startResearchingTopic"
      />
      <div class="flex items-center gap-2">
        Research type:
        <AaSelect
          :model-value="researchType"
          :options="researchTypeOptions"
          size="medium"
          placeholder=""
          @update:model-value="handleResearchTypeChange"
        />
      </div>
      <div class="flex justify-end">
        <AaButton
          size="medium"
          :disabled="!isFormValid"
          :append-icon="
            isSearching
              ? 'i-material-symbols-progress-activity animate-spin'
              : 'i-material-symbols-search'
          "
          @click="startResearchingTopic"
        >
          {{ isSearching ? 'Researching...' : 'Research topic' }}
        </AaButton>
      </div>
    </div>
  </div>
</template>
