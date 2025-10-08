/**
 * Table layout constants for consistent sizing across components
 * These values should match the corresponding Tailwind CSS classes
 */
export const TABLE_LAYOUT = {
  ROW_HEIGHT: 48,
  HEADER_HEIGHT: 48,
  TITLEBAR_HEIGHT: 64,
  FOOTER_HEIGHT: 60,
  MODAL_PADDING: 16,

  MIN_PAGE_SIZE: 5,
  MAX_PAGE_SIZE: 50,
  DEFAULT_PAGE_SIZE: 10,
} as const;

/**
 * Calculate dynamic page size based on available height
 */
export function calculateDynamicPageSize(
  availableHeight: number,
  options: {
    titlebarHeight?: number;
    headerHeight?: number;
    footerHeight?: number;
    modalPadding?: number;
    rowHeight?: number;
    minPageSize?: number;
    maxPageSize?: number;
  } = {}
): number {
  const {
    titlebarHeight = TABLE_LAYOUT.TITLEBAR_HEIGHT,
    headerHeight = TABLE_LAYOUT.HEADER_HEIGHT,
    footerHeight = TABLE_LAYOUT.FOOTER_HEIGHT,
    modalPadding = TABLE_LAYOUT.MODAL_PADDING,
    rowHeight = TABLE_LAYOUT.ROW_HEIGHT,
    minPageSize = TABLE_LAYOUT.MIN_PAGE_SIZE,
    maxPageSize = TABLE_LAYOUT.MAX_PAGE_SIZE,
  } = options;

  if (availableHeight === 0) return TABLE_LAYOUT.DEFAULT_PAGE_SIZE;

  const usedHeight = titlebarHeight + headerHeight + footerHeight + modalPadding;
  const availableForRows = availableHeight - usedHeight;
  const calculatedRows = Math.floor(availableForRows / rowHeight);

  // Clamp between min and max values
  return Math.max(minPageSize, Math.min(maxPageSize, calculatedRows));
}
