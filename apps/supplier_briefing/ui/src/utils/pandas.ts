import type { SerializedDataFrame, SerializedSeries, SerializedPandasObject } from '@/types';
import type { DataFrameData } from '@app-factory/shared-frontend/types';

/**
 * Type guard to check if an object is a serialized DataFrame
 */
export function isSerializedDataFrame(obj: any): obj is SerializedDataFrame {
  return obj && typeof obj === 'object' && obj.type === 'DataFrame' && obj.data && obj.dtypes;
}

/**
 * Type guard to check if an object is a serialized Series
 */
export function isSerializedSeries(obj: any): obj is SerializedSeries {
  return obj && typeof obj === 'object' && obj.type === 'Series' && obj.data && obj.dtype;
}

/**
 * Type guard to check if an object is a serialized pandas object (DataFrame or Series)
 */
export function isSerializedPandasObject(obj: any): obj is SerializedPandasObject {
  return isSerializedDataFrame(obj) || isSerializedSeries(obj);
}

/**
 * Convert a serialized DataFrame to the format expected by EnhancedDataTable
 */
export function deserializeDataFrame(obj: SerializedDataFrame): DataFrameData {
  const result: DataFrameData = {
    columns: obj.data.columns.map((col) => String(col)),
    data: obj.data.data,
    index: obj.data.index,
    index_names: obj.index_names,
  };

  return result;
}

/**
 * Convert a serialized Series to the format expected by EnhancedDataTable
 * Series are converted to two-column DataFrames: Attribute | Value
 */
export function deserializeSeries(obj: SerializedSeries): DataFrameData {
  const data: string[][] = obj.data.data.map((value) => [value]);

  return {
    columns: ['Wert'],
    data: data,
    index: obj.data.index,
    index_names: ['Attribut'],
  };
}
/**
 * Convert any serialized pandas object to the format expected by EnhancedDataTable
 */
export function deserializePandasObject(obj: SerializedPandasObject): DataFrameData {
  if (isSerializedDataFrame(obj)) {
    return deserializeDataFrame(obj);
  } else if (isSerializedSeries(obj)) {
    return deserializeSeries(obj);
  } else {
    throw new Error(`Unsupported pandas object type: ${(obj as any).type}`);
  }
}

/**
 * Create a pretty display name from a key
 */
export function prettifyKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}
