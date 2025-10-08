<script setup lang="ts">
import {
  ref,
  onMounted,
  onUnmounted,
  type ComputedRef,
  computed,
  defineComponent,
  type CSSProperties,
} from 'vue';

defineComponent({
  name: 'BasePopover',
});

interface Props {
  /** Icon class for the trigger button */
  triggerIcon?: string;
  /** Popover placement position */
  placement?:
    | 'top'
    | 'bottom'
    | 'left'
    | 'right'
    | 'top-start'
    | 'top-end'
    | 'bottom-start'
    | 'bottom-end';
  /** Whether the popover is disabled */
  disabled?: boolean;
  /** Custom trigger button text (optional) */
  triggerText?: string;
  /** Popover width */
  width?: string;
  /** Popover custom styles */
  style?: CSSProperties;
}

interface Emits {
  (event: 'open'): void;
  (event: 'close'): void;
}

const props = withDefaults(defineProps<Props>(), {
  triggerIcon: 'i-mdi-dots-vertical',
  placement: 'bottom-start',
  disabled: false,
  triggerText: '',
  width: '200px',
  style: undefined,
});

const emit = defineEmits<Emits>();

const isOpen = ref(false);
const triggerRef = ref<HTMLElement>();
const popoverRef = ref<HTMLElement>();

const popoverClasses: ComputedRef<Record<string, boolean>> = computed(() => ({
  'popover-container': true,
  'popover-open': isOpen.value,
  'popover-closed': !isOpen.value,
}));

const triggerClasses: ComputedRef<Record<string, boolean>> = computed(() => ({
  'popover-trigger': true,
  'popover-trigger-active': isOpen.value,
  'popover-trigger-disabled': props.disabled,
}));

const contentClasses: ComputedRef<Record<string, boolean>> = computed(() => ({
  'popover-content': true,
  [`popover-${props.placement}`]: true,
}));

const togglePopover = (): void => {
  if (props.disabled) return;

  isOpen.value = !isOpen.value;

  if (isOpen.value) {
    emit('open');
  } else {
    emit('close');
  }
};

const closePopover = (): void => {
  if (isOpen.value) {
    isOpen.value = false;
    emit('close');
  }
};

const handleClickOutside = (event: MouseEvent): void => {
  if (!isOpen.value) return;

  const target = event.target as Element;

  // Check if click is inside trigger or popover
  if (
    triggerRef.value &&
    popoverRef.value &&
    !triggerRef.value.contains(target) &&
    !popoverRef.value.contains(target)
  ) {
    // Check if click is on dropdown/select related elements
    const isDropdownClick =
      target.closest('.aa-select-dropdown') ||
      target.closest('.aa-select-option') ||
      target.closest('.aa-select-menu') ||
      target.closest('[data-dropdown]') ||
      target.closest('[role="listbox"]') ||
      target.closest('[role="option"]') ||
      target.closest('.dp__menu') || // VueDatePicker dropdown
      target.closest('.dp__calendar') ||
      target.closest('.dp__overlay');

    // Don't close if clicking on dropdown elements
    if (!isDropdownClick) {
      closePopover();
    }
  }
};

const handleEscapeKey = (event: KeyboardEvent): void => {
  if (event.key === 'Escape' && isOpen.value) {
    closePopover();
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  document.addEventListener('keydown', handleEscapeKey);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  document.removeEventListener('keydown', handleEscapeKey);
});
</script>

<template>
  <div :class="popoverClasses">
    <!-- Custom trigger slot -->
    <div v-if="$slots.trigger" ref="triggerRef">
      <slot name="trigger" :is-open="isOpen" :disabled="disabled" :toggle="togglePopover" />
    </div>

    <!-- Default trigger button -->
    <button
      v-else
      ref="triggerRef"
      :class="triggerClasses"
      :disabled="disabled"
      :aria-expanded="isOpen"
      :aria-haspopup="true"
      type="button"
      @click="togglePopover"
    >
      <span v-if="triggerIcon" :class="triggerIcon" />
      <span v-if="triggerText" class="popover-trigger-text">
        {{ triggerText }}
      </span>
    </button>

    <Transition
      name="popover"
      enter-active-class="popover-enter-active"
      enter-from-class="popover-enter-from"
      enter-to-class="popover-enter-to"
      leave-active-class="popover-leave-active"
      leave-from-class="popover-leave-from"
      leave-to-class="popover-leave-to"
    >
      <div
        v-if="isOpen"
        ref="popoverRef"
        :class="contentClasses"
        :style="{ width, ...style }"
        role="dialog"
        :aria-labelledby="triggerRef?.id"
      >
        <slot />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.popover-container {
  position: relative;
  display: inline-block;
}

.popover-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
}

.popover-trigger:hover:not(.popover-trigger-disabled) {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.popover-trigger:focus {
  ring: 2px solid #3b82f6;
  ring-offset: 2px;
}

.popover-trigger-active {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.popover-trigger-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.popover-trigger-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.popover-content {
  position: absolute;
  z-index: 50;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
  padding: 0.75rem;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Positioning */
.popover-top {
  bottom: 100%;
  left: 0;
  margin-bottom: 0.5rem;
}

.popover-top-start {
  bottom: 100%;
  left: 0;
  margin-bottom: 0.5rem;
}

.popover-top-end {
  bottom: 100%;
  right: 0;
  margin-bottom: 0.5rem;
}

.popover-bottom {
  top: 100%;
  left: 0;
  margin-top: 0.5rem;
}

.popover-bottom-start {
  top: 100%;
  left: 0;
  margin-top: 0.5rem;
}

.popover-bottom-end {
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
}

.popover-left {
  right: 100%;
  top: 0;
  margin-right: 0.5rem;
}

.popover-right {
  left: 100%;
  top: 0;
  margin-left: 0.5rem;
}

/* Transitions */
.popover-enter-active,
.popover-leave-active {
  transition: all 0.2s ease;
}

.popover-enter-from {
  opacity: 0;
  transform: translateY(-0.5rem) scale(0.95);
}

.popover-enter-to {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.popover-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.popover-leave-to {
  opacity: 0;
  transform: translateY(-0.5rem) scale(0.95);
}
</style>
