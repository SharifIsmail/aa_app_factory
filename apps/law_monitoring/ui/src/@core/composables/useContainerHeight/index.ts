import { ref, onMounted, onUnmounted, type Ref } from 'vue';

export interface UseContainerHeightOptions {
  containerRef: Ref<HTMLElement | undefined>;
  titleBarRef?: Ref<HTMLElement | undefined>;
}

export function useContainerHeight(options: UseContainerHeightOptions) {
  const { containerRef, titleBarRef } = options;

  // Reactive height value
  const calculatedHeight = ref(window.innerHeight);

  // Store observers for cleanup
  let resizeObserver: ResizeObserver | null = null;
  let windowResizeHandler: (() => void) | null = null;

  const getContainerHeight = (): number => {
    const windowHeight = window.innerHeight;

    if (containerRef.value) {
      const containerHeight = containerRef.value.clientHeight;
      return containerHeight;
    }

    // Fallback to window height if container ref is not available
    return windowHeight;
  };

  const updateHeights = () => {
    const containerHeight = getContainerHeight();

    if (titleBarRef?.value) {
      const titleBarHeight = titleBarRef.value.offsetHeight;
      const availableHeight = containerHeight - titleBarHeight;
      calculatedHeight.value = Math.max(0, availableHeight);
    } else {
      calculatedHeight.value = containerHeight;
    }
  };

  const setup = () => {
    // Initial height calculation
    updateHeights();

    // Set up ResizeObserver to detect shell container resizing
    if (containerRef.value) {
      resizeObserver = new ResizeObserver(() => {
        updateHeights();
      });

      resizeObserver.observe(containerRef.value);
    }

    // Window resize handles viewport changes
    windowResizeHandler = () => {
      updateHeights();
    };

    window.addEventListener('resize', windowResizeHandler);
  };

  const cleanup = () => {
    resizeObserver?.disconnect();
    if (windowResizeHandler) {
      window.removeEventListener('resize', windowResizeHandler);
    }
  };

  onMounted(() => {
    setup();
  });

  onUnmounted(() => {
    cleanup();
  });

  return {
    calculatedHeight,
    updateHeights,
    setup,
    cleanup,
  };
}
