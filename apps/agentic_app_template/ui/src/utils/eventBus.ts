import type { Notification } from '@/stores/useNotificationStore';
import { useEventBus } from '@vueuse/core';

export const notificationEventBus = useEventBus<Notification>('assistant-notification');
