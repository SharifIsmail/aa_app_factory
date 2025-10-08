import { useNotificationStore } from '@/@core/stores/useNotificationStore';
import { sanitizeFilename, downloadFile } from '@app-factory/shared-frontend/utils';
import { toBlob } from 'html-to-image';

export interface ExportOptions {
  /** The CSS selector for the widget container to export */
  containerSelector: string;
  /** Base filename for exports (without extension) */
  baseFilename: string;
  /** Export image scale for quality (default: 2) */
  scale?: number;
  /** Background color for exports (default: '#ffffff') */
  backgroundColor?: string;
  /** List of CSS class names to exclude from export */
  exclusionList?: string[];
  /** List of HTML attribute names to exclude from export */
  exclusionAttributes?: string[];
}

export type ExportFormat = {
  label: string;
  value: string;
  icon?: string;
};

export enum EXPORT_FORMAT {
  PNG = 'widget-png',
  CSV = 'widget-csv',
}

/**
 * Composable for widget export functionality
 */
export function useWidgetExport(options: ExportOptions) {
  const notificationStore = useNotificationStore();

  const {
    containerSelector,
    baseFilename,
    scale = 2,
    backgroundColor = '#ffffff',
    exclusionList = [],
    exclusionAttributes = [],
  } = options;

  /**
   * Generate a sanitized filename for exports
   */
  const generateFilename = (): string => {
    const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    const filename = `${baseFilename}_${timestamp}`;
    return sanitizeFilename(filename);
  };

  /**
   * Export widget as PNG image
   */
  const exportWidgetAsPNG = async (): Promise<void> => {
    try {
      const widgetElement = document.querySelector(containerSelector) as HTMLElement;
      if (!widgetElement) {
        throw new Error(`Widget container not found: ${containerSelector}`);
      }

      const blob = await toBlob(widgetElement, {
        backgroundColor: backgroundColor,
        pixelRatio: scale,
        filter: (node: HTMLElement) => {
          // Exclude elements with any of the specified CSS classes
          if (exclusionList.length > 0) {
            const hasExcludedClass = exclusionList.some((className) =>
              node.classList?.contains(className)
            );
            if (hasExcludedClass) {
              return false;
            }
          }

          // Exclude elements with any of the specified HTML attributes
          if (exclusionAttributes.length > 0) {
            const hasExcludedAttribute = exclusionAttributes.some((attributeName) =>
              node.hasAttribute?.(attributeName)
            );
            if (hasExcludedAttribute) {
              return false;
            }
          }

          return true;
        },
      });

      if (!blob) {
        throw new Error('Failed to generate blob from widget');
      }

      const filename = generateFilename();

      downloadFile(blob, filename, {
        fileExtension: 'png',
        mimeType: 'image/png',
      });
    } catch (error) {
      console.error('PNG export failed:', error);
      throw new Error('Failed to export as PNG');
    }
  };

  /**
   * Handle export based on format
   */
  const handleExport = async (format: string): Promise<void> => {
    try {
      if (format === EXPORT_FORMAT.PNG) {
        await exportWidgetAsPNG();
        notificationStore.addSuccessNotification('Widget exported successfully as PNG');
      } else {
        notificationStore.addErrorNotification(`Unsupported export format: ${format}`);
      }
    } catch (error) {
      console.error('Export failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to export widget';
      notificationStore.addErrorNotification(`Export failed: ${errorMessage}`);
    }
  };

  return {
    handleExport,
  };
}
