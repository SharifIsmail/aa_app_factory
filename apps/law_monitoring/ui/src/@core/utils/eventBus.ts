import type { Notification } from '@/@core/stores/useNotificationStore.ts';
import { useEventBus } from '@vueuse/core';

export const notificationEventBus = useEventBus<Notification>('assistant-notification');
