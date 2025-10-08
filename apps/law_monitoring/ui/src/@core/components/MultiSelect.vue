<script setup lang="ts">
import { computed, ref, nextTick } from 'vue';

interface Props {
  modelValue: string[];
  options: string[];
  placeholder?: string;
  searchPlaceholder?: string;
  disabled?: boolean;
  loading?: boolean;
  required?: boolean;
  ariaDescribedBy?: string;
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Select options...',
  searchPlaceholder: 'Search options...',
  disabled: false,
  loading: false,
  required: false,
  ariaDescribedBy: '',
});

const emit = defineEmits<Emits>();

const searchInput = ref<string>('');
const showDropdown = ref(false);
const mainContainerRef = ref<HTMLElement>();
const searchInputRef = ref<HTMLInputElement>();
const optionsContainerRef = ref<HTMLElement>();
const currentFocusedOptionIndex = ref(-1);

const selectedOptions = computed({
  get: () => props.modelValue,
  set: (value: string[]) => emit('update:modelValue', value),
});

const filteredOptions = computed(() => {
  if (!searchInput.value.trim()) {
    return props.options.filter((option) => !selectedOptions.value.includes(option));
  }

  const searchTerm = searchInput.value.toLowerCase();
  return props.options.filter(
    (option) => option.toLowerCase().includes(searchTerm) && !selectedOptions.value.includes(option)
  );
});

const displayPlaceholder = computed(() => {
  if (props.loading) return 'Loading options...';
  if (selectedOptions.value.length > 0) return '';
  return props.placeholder;
});

function openDropdown() {
  if (props.disabled) return;
  showDropdown.value = true;
  nextTick(() => {
    searchInputRef.value?.focus();
  });
}

function closeDropdown() {
  showDropdown.value = false;
  searchInput.value = '';
  currentFocusedOptionIndex.value = -1;
}

function closeDropdownAndFocus() {
  closeDropdown();
  nextTick(() => {
    // Return focus to the main container
    mainContainerRef.value?.focus();
  });
}

function selectOption(option: string) {
  if (option && !selectedOptions.value.includes(option)) {
    selectedOptions.value = [...selectedOptions.value, option];
  }
  searchInput.value = '';
  currentFocusedOptionIndex.value = -1;
  nextTick(() => {
    searchInputRef.value?.focus();
  });
}

function removeOption(option: string) {
  selectedOptions.value = selectedOptions.value.filter((o) => o !== option);
}

function handleContainerClick(event: Event) {
  // Don't open if clicking on a remove button
  if ((event.target as HTMLElement).closest('button[data-remove]')) {
    return;
  }
  openDropdown();
}

function handleSearchKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault();
    if (filteredOptions.value.length > 0) {
      // If an option is focused via arrow keys, select it
      // Otherwise, select the first filtered option
      const targetIndex =
        currentFocusedOptionIndex.value >= 0 ? currentFocusedOptionIndex.value : 0;
      const option = filteredOptions.value[targetIndex];
      selectOption(option);
    }
  } else if (event.key === 'Escape') {
    closeDropdownAndFocus();
  } else if (event.key === 'ArrowDown') {
    event.preventDefault();
    currentFocusedOptionIndex.value = Math.min(
      currentFocusedOptionIndex.value + 1,
      filteredOptions.value.length - 1
    );
    scrollFocusedOptionIntoView();
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    currentFocusedOptionIndex.value = Math.max(currentFocusedOptionIndex.value - 1, -1);
    scrollFocusedOptionIntoView();
  } else if (event.key === 'Backspace' && !searchInput.value && selectedOptions.value.length > 0) {
    // Remove last selected option on backspace when search is empty
    removeOption(selectedOptions.value[selectedOptions.value.length - 1]);
  }
}

function handleSearchBlur(event: FocusEvent) {
  // Don't close if focus is moving to dropdown options
  if (
    event.relatedTarget &&
    mainContainerRef.value?.parentElement?.contains(event.relatedTarget as Node)
  ) {
    return;
  }
  // Delay to allow for clicks
  setTimeout(() => {
    closeDropdown();
  }, 200);
}

function scrollFocusedOptionIntoView() {
  if (currentFocusedOptionIndex.value < 0) return;

  nextTick(() => {
    const optionsContainer = optionsContainerRef.value;
    if (!optionsContainer) return;

    const focusedOption = optionsContainer.querySelector(
      `[data-option-index="${currentFocusedOptionIndex.value}"]`
    ) as HTMLElement;
    if (!focusedOption) return;

    focusedOption.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'nearest',
    });
  });
}

function handleContainerKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    openDropdown();
  } else if (event.key === 'Escape') {
    closeDropdownAndFocus();
  } else if (event.key === 'ArrowDown') {
    event.preventDefault();
    openDropdown();
  } else if (event.key === 'Backspace' && selectedOptions.value.length > 0) {
    // Remove last selected option when container is focused
    event.preventDefault();
    removeOption(selectedOptions.value[selectedOptions.value.length - 1]);
  }
}
</script>

<template>
  <div class="relative w-full">
    <!-- Main Input Container -->
    <div
      ref="mainContainerRef"
      @click="handleContainerClick"
      @keydown="handleContainerKeydown"
      :class="[
        'bg-core-bg-primary flex min-h-9 w-full flex-wrap items-center gap-1 rounded-md border px-3 text-sm transition-colors',
        'border-gray-300 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 hover:border-gray-400',
        props.disabled ? 'cursor-not-allowed opacity-50' : 'cursor-text',
        selectedOptions.length > 0 ? 'py-1.5' : 'py-2',
      ]"
      role="combobox"
      :aria-expanded="showDropdown"
      :aria-disabled="props.disabled"
      tabindex="0"
    >
      <!-- Selected Option Tags -->
      <div v-if="selectedOptions.length > 0" class="flex flex-wrap items-center gap-1">
        <span
          v-for="option in selectedOptions"
          :key="option"
          class="inline-flex items-center gap-1 rounded-md bg-blue-100 px-2 py-1 text-xs text-blue-800"
        >
          <span>{{ option }}</span>
          <button
            @click.stop="removeOption(option)"
            class="rounded-sm p-0.5 transition-colors hover:bg-blue-200 focus:outline-none"
            type="button"
            :disabled="props.disabled"
            :aria-label="`Remove ${option}`"
            tabindex="-1"
            data-remove
          >
            <div class="i-material-symbols-close size-3"></div>
          </button>
        </span>
      </div>

      <!-- Placeholder text when no selections -->
      <span v-if="selectedOptions.length === 0" class="pointer-events-none flex-1 text-gray-500">
        {{ displayPlaceholder }}
      </span>

      <!-- Spacer when there are selections to maintain layout -->
      <div v-else class="flex-1"></div>

      <!-- Dropdown arrow -->
      <div class="flex items-center">
        <div
          class="i-material-symbols-keyboard-arrow-down size-4 text-gray-400 transition-transform"
          :class="{ 'rotate-180': showDropdown }"
        ></div>
      </div>
    </div>

    <!-- Dropdown -->
    <div
      v-if="showDropdown && !props.disabled"
      class="z-100 bg-core-bg-primary absolute mt-1 w-full rounded-md border border-gray-300 shadow-lg"
      role="listbox"
    >
      <!-- Search Input in Dropdown -->
      <div class="border-b border-gray-200 p-3">
        <input
          ref="searchInputRef"
          v-model="searchInput"
          type="text"
          class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          :placeholder="props.searchPlaceholder"
          :disabled="props.disabled"
          @keydown="handleSearchKeydown"
          @blur="handleSearchBlur"
          autocomplete="off"
        />
      </div>

      <!-- Options Container -->
      <div class="max-h-48 overflow-auto" ref="optionsContainerRef" tabindex="-1">
        <!-- Loading State -->
        <div
          v-if="props.loading"
          class="p-3 text-center text-gray-500"
          role="status"
          aria-live="polite"
        >
          Loading options...
        </div>

        <!-- Options -->
        <div v-else>
          <!-- Available Options -->
          <div
            v-for="(option, index) in filteredOptions.slice(0, 50)"
            :key="option"
            :data-option-index="index"
            :class="[
              'cursor-pointer px-3 py-2 text-sm transition-colors',
              currentFocusedOptionIndex === index ? 'bg-blue-100' : 'hover:bg-gray-100',
            ]"
            @mousedown="selectOption(option)"
            @mouseenter="currentFocusedOptionIndex = index"
          >
            {{ option }}
          </div>

          <!-- No Results -->
          <div
            v-if="filteredOptions.length === 0"
            class="px-3 py-2 text-sm text-gray-500"
            role="status"
          >
            No matching options found
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
