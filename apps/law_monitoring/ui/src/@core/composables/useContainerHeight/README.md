# useContainerHeight Composable

A reusable composable for calculating container height that works in both shell container and standalone modes.

## Features

- Automatically detects shell container resizing
- Handles window resize events (including fullscreen transitions)
- Calculates available height by subtracting title bar height
- Provides proper cleanup of observers
- TypeScript support with proper types

## Usage

### Basic Usage

```vue
<script setup lang="ts">
import AppTitleBar from '@/@core/components/AppTitleBar.vue';
import SkillLayout from '@/@core/components/SkillLayout.vue';
import { useContainerHeight } from '@/@core/composables';
import { ref, computed } from 'vue';

// Component refs
const skillLayoutRef = ref<InstanceType<typeof SkillLayout>>();
const titleBarRef = ref<HTMLElement>();

// Create computed ref for container
const containerRef = computed(() => skillLayoutRef.value?.containerRef);

// Use the composable
const { calculatedHeight } = useContainerHeight({
  containerRef,
  titleBarRef,
});
</script>

<template>
  <SkillLayout ref="skillLayoutRef">
    <template #title>
      <div ref="titleBarRef">
        <AppTitleBar />
      </div>
    </template>
    <template #default>
      <YourMainComponent :height="calculatedHeight" />
    </template>
  </SkillLayout>
</template>
```

### Without Title Bar

```vue
<script setup lang="ts">
import SkillLayout from '@/@core/components/SkillLayout.vue';
import { useContainerHeight } from '@/@core/composables';
import { ref, computed } from 'vue';

const skillLayoutRef = ref<InstanceType<typeof SkillLayout>>();
const containerRef = computed(() => skillLayoutRef.value?.containerRef);

// No titleBarRef needed
const { calculatedHeight } = useContainerHeight({
  containerRef,
});
</script>

<template>
  <SkillLayout ref="skillLayoutRef">
    <YourMainComponent :height="calculatedHeight" />
  </SkillLayout>
</template>
```

### Advanced Usage

```vue
<script setup lang="ts">
import { useContainerHeight } from '@/@core/composables';

const { calculatedHeight, updateHeights, setup, cleanup } = useContainerHeight({
  containerRef,
  titleBarRef,
});

// Manually trigger height recalculation
const onSomeEvent = () => {
  updateHeights();
};

// Manual setup/cleanup (useful for conditional rendering)
onMounted(() => {
  if (someCondition) {
    setup();
  }
});

onUnmounted(() => {
  cleanup();
});
</script>
```

## API

### Parameters

```typescript
interface UseContainerHeightOptions {
  containerRef: Ref<HTMLElement | undefined>;
  titleBarRef?: Ref<HTMLElement | undefined>;
}
```

- `containerRef`: Reactive reference to the container element (usually from SkillLayout)
- `titleBarRef`: Optional reactive reference to the title bar element

### Returns

```typescript
{
  calculatedHeight: Ref<number>;
  updateHeights: () => void;
  setup: () => void;
  cleanup: () => void;
}
```

- `calculatedHeight`: Reactive height value to use for your main component
- `updateHeights`: Function to manually trigger height recalculation
- `setup`: Function to manually set up observers
- `cleanup`: Function to manually clean up observers

## How It Works

1. **Container Detection**: Uses the provided `containerRef` to get the container height
2. **Title Bar Subtraction**: If `titleBarRef` is provided, subtracts its height from container height
3. **Resize Handling**: Sets up ResizeObserver for container changes and window resize listener for viewport changes
4. **Automatic Cleanup**: Automatically cleans up observers when component unmounts

## Compatibility

Works with:

- Shell container mode (when app runs inside shell)
- Standalone mode (when app runs independently)
- Fullscreen transitions (not yet fully supported)
- Window resizing
- Different screen sizes
