<script setup lang="ts">
import { AaText } from '@aleph-alpha/ds-components-vue';

defineEmits(['close']);
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="max-h-[80vh] w-[600px] overflow-hidden rounded-lg bg-white shadow-xl">
      <div class="p-6">
        <div class="mb-4 flex items-center justify-between">
          <AaText size="lg" weight="bold">Configure data sources</AaText>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <div class="rounded-lg bg-gray-50 p-4">
            <AaText weight="medium" class="mb-2">Settings will be available soon</AaText>
            <AaText size="sm" class="text-gray-600">This feature is under development.</AaText>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
