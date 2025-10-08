import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { notificationEventBus } from '@/@core/utils/eventBus.ts';
import { defineStore } from 'pinia';

export interface Notification {
  type: 'success' | 'error' | 'info';
  message: string;
  timeout?: number;
  action?: {
    label: string;
    callback: () => void;
  };
}

export function isNotification(value: unknown): value is Notification {
  return (
    typeof value === 'object' &&
    value !== null &&
    'type' in value &&
    ['success', 'error', 'info'].includes((value as Notification).type) &&
    'message' in value
  );
}

export const useNotificationStore = defineStore(createStoreId('notifications'), () => {
  const addNotification = (payload: Notification) => {
    notificationEventBus.emit({
      type: payload.type,
      message: payload.message,
      timeout: 5000,
      action: payload.action
        ? {
            label: payload.action.label,
            callback: payload.action.callback,
          }
        : undefined,
    });
  };

  const addInfoNotification = (message: string) => {
    addNotification({
      type: 'info',
      message,
    });
  };
  const addSuccessNotification = (message: string) => {
    addNotification({
      type: 'success',
      message,
    });
  };

  const addErrorNotification = (
    message: string,
    action?: {
      label: string;
      callback: () => void;
    }
  ) => {
    addNotification({
      type: 'error',
      message,
      action,
    });
  };

  return {
    addNotification,
    addErrorNotification,
    addInfoNotification,
    addSuccessNotification,
  };
});
