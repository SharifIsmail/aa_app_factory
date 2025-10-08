export interface FileDownloadOptions {
  filename?: string;
  mimeType?: string;
  fileExtension?: string;
}

export interface DataFrameData {
  filename?: string;
  mimeType?: string;
  fileExtension?: string;
}

export interface DataFrameData {
  columns: string[];
  data: unknown[][];
  index: (string | number)[] | (string | number)[][];
  index_names?: string[];
}
