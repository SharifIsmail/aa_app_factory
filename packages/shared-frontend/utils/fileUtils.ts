import type { FileDownloadOptions, DataFrameData } from '../types';
import { utils as XLSXUtils, write as XLSXWrite } from 'xlsx';

/**
 * Generic file download function
 * @param content - The content to download (string, ArrayBuffer, or Blob)
 * @param filename - The filename (without extension)
 * @param options - Configuration options
 */
export const downloadFile = (
  content: string | ArrayBuffer | Blob,
  filename: string,
  options: FileDownloadOptions = {}
): void => {
  const { mimeType = 'application/octet-stream', fileExtension = '' } = options;

  try {
    // Create blob if content isn't already a blob
    const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });

    const url = window.URL.createObjectURL(blob);

    // Create temporary download link
    const link = document.createElement('a');
    link.href = url;
    link.download = fileExtension ? `${filename}.${fileExtension}` : filename;
    link.style.visibility = 'hidden';

    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Cleanup
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading file:', error);
    throw new Error(`Failed to download file: ${filename}`);
  }
};

/**
 * Convert DataFrame data to CSV format
 * @param dataframeData - The pandas DataFrame data structure
 * @returns CSV string
 */
export const convertDataFrameToCSV = (dataframeData: DataFrameData): string => {
  if (!dataframeData || !dataframeData.columns || !dataframeData.data) {
    throw new Error('Invalid dataframe structure');
  }

  const { columns, data, index, index_names } = dataframeData;
  const rows: string[] = [];

  // Check if we have MultiIndex (first index entry is an array)
  const hasMultiIndex = index.length > 0 && Array.isArray(index[0]);

  // Create header row
  let header = '';
  if (hasMultiIndex) {
    // Add index level headers
    const multiIndex = index as (string | number)[][];
    const indexLevels = multiIndex[0].length;
    for (let i = 0; i < indexLevels; i++) {
      const levelName = index_names?.[i] || `Level ${i}`;
      header += `"${levelName}",`;
    }
  } else if (index.length > 0 && index_names?.[0]) {
    // Single index header - only add if index name is provided
    header += `"${index_names[0]}",`;
  }

  // Add column headers
  header += columns.map((col: unknown) => `"${String(col).replace(/"/g, '""')}"`).join(',');
  rows.push(header);

  // Create data rows
  data.forEach((row: unknown[], rowIndex: number) => {
    let csvRow = '';

    // Add index values
    if (hasMultiIndex) {
      const multiIndex = index as (string | number)[][];
      const indexValues = multiIndex[rowIndex];
      csvRow +=
        indexValues.map((val: unknown) => `"${String(val).replace(/"/g, '""')}"`).join(',') + ',';
    } else if (index.length > 0 && index_names?.[0]) {
      const simpleIndex = index as (string | number)[];
      csvRow += `"${String(simpleIndex[rowIndex]).replace(/"/g, '""')}",`;
    }

    // Add data values
    csvRow += row
      .map((cell: unknown) => {
        if (cell === null || cell === undefined) return '""';
        return `"${String(cell).replace(/"/g, '""')}"`;
      })
      .join(',');

    rows.push(csvRow);
  });

  return rows.join('\n');
};

/**
 * Convert DataFrame data to Excel format using xlsx library
 * @param dataframeData - The pandas DataFrame data structure
 * @returns Excel file as Blob
 */
export const convertDataFrameToExcel = (dataframeData: DataFrameData): Blob => {
  if (!dataframeData || !dataframeData.columns || !dataframeData.data) {
    throw new Error('Invalid dataframe structure');
  }

  const { columns, data, index, index_names } = dataframeData;

  // Check if we have MultiIndex (first index entry is an array)
  const hasMultiIndex = index.length > 0 && Array.isArray(index[0]);

  // Convert to format xlsx expects (array of objects)
  const worksheetData = data.map((row: unknown[], rowIndex: number) => {
    const rowObj: Record<string, unknown> = {};

    // Add index values
    if (hasMultiIndex) {
      const multiIndex = index as (string | number)[][];
      const indexValues = multiIndex[rowIndex];
      indexValues.forEach((val: unknown, idx: number) => {
        const levelName = index_names?.[idx] || `Level ${idx}`;
        rowObj[levelName] = val;
      });
    } else if (index.length > 0 && index_names?.[0]) {
      const simpleIndex = index as (string | number)[];
      rowObj[index_names[0]] = simpleIndex[rowIndex];
    }

    // Add data values
    columns.forEach((col: unknown, colIdx: number) => {
      rowObj[String(col)] = row[colIdx];
    });

    return rowObj;
  });

  // Determine the correct column order
  const indexHeaders: string[] = [];
  if (hasMultiIndex) {
    const multiIndex = index as (string | number)[][];
    const indexLevels = multiIndex[0].length;
    for (let i = 0; i < indexLevels; i++) {
      const levelName = index_names?.[i] || `Level ${i}`;
      indexHeaders.push(levelName);
    }
  } else if (index.length > 0 && index_names?.[0]) {
    indexHeaders.push(index_names[0]);
  }

  // Create the correct column order: index columns first, then data columns
  const orderedColumns = [...indexHeaders, ...columns.map(String)];

  // Create workbook and worksheet with explicit column ordering
  const ws = XLSXUtils.json_to_sheet(worksheetData, { header: orderedColumns });
  const wb = XLSXUtils.book_new();
  XLSXUtils.book_append_sheet(wb, ws, 'Data');

  // Generate Excel file as array buffer
  const excelBuffer = XLSXWrite(wb, { bookType: 'xlsx', type: 'array' });

  // Return as Blob
  return new Blob([excelBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
};

/**
 * Sanitize filename to be filesystem-safe
 * @param filename - Original filename
 * @returns Sanitized filename
 */
export const sanitizeFilename = (filename: string): string => {
  return (
    filename
      // Replace filesystem-unsafe characters with underscore
      // eslint-disable-next-line no-control-regex
      .replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')
      // Replace multiple consecutive underscores/spaces/dots with single underscore
      .replace(/[_\s.]+/g, '_')
      // Remove leading/trailing underscores
      .replace(/^_|_$/g, '')
      // Keep the original case to preserve proper German capitalization
      .trim()
  );
};
