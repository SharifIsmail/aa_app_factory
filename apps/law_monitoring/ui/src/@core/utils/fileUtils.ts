export interface FileUtilsOptions {
  filename?: string;
  mimeType?: string;
}

/**
 * Opens content in a new browser window
 * @param content - The content to display
 * @param options - Configuration options
 */
export const openContentInNewWindow = (content: string, options: FileUtilsOptions = {}): void => {
  const { mimeType = 'text/html' } = options;

  try {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
    // Note: We don't revoke the URL immediately since the new window needs it
  } catch (error) {
    console.error('Failed to open content in new window:', error);
    throw new Error('Failed to open content. Please try again.');
  }
};

/**
 * Downloads content as a file
 * @param content - The content to download (string or ArrayBuffer)
 * @param filename - The filename for the download
 * @param options - Configuration options
 */
export const downloadContentAsFile = (
  content: string | ArrayBuffer,
  filename: string,
  options: FileUtilsOptions = {}
): void => {
  const { mimeType = 'text/html charset=utf-8' } = options;

  try {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);

    // Create a temporary link for download
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Clean up the blob URL
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to download content:', error);
    throw new Error('Failed to download file. Please try again.');
  }
};

/**
 * Utility to handle both opening and downloading content based on action type
 * @param content - The content to handle (string for opening, string or ArrayBuffer for downloading)
 * @param action - Whether to 'open' or 'download'
 * @param options - Configuration options including filename for downloads
 */
export const handleContent = (
  content: string | ArrayBuffer,
  action: 'open' | 'download',
  options: FileUtilsOptions & { filename?: string } = {}
): void => {
  if (action === 'open') {
    if (typeof content !== 'string') {
      throw new Error('Opening content requires string data');
    }
    openContentInNewWindow(content, options);
  } else if (action === 'download' && options.filename) {
    downloadContentAsFile(content, options.filename, options);
  } else {
    throw new Error('Invalid action or missing filename for download');
  }
};
