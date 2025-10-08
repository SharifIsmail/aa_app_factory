import type { PreprocessedLaw } from '@/modules/monitoring/types';
import { type Category } from '@/modules/monitoring/types';
import type { Http } from '@aleph-alpha/lib-http';

export class ManualLawAnalysisService {
  constructor(readonly httpClient: Http) {}

  async startLawSummary(lawUrl: string): Promise<any> {
    try {
      const response = await this.httpClient.post<any>('summary-start', {
        body: {
          law_url: lawUrl,
        },
      });

      // Check if the response indicates an error
      if (response.data && response.data.status === 'ERROR') {
        // Create an error object with the structured error response
        const error: any = new Error(response.data.message || 'An error occurred');
        error.response = {
          data: response.data,
        };
        throw error;
      }

      return response.data;
    } catch (error: any) {
      console.error('Error in startLawSummary:', error);

      // If the error has a response with data, use that
      if (error.response && error.response.data) {
        // If the error has a message field, use that
        if (error.response.data.message) {
          error.message = error.response.data.message;
        }
      }

      // Re-throw the error to be handled by the component
      throw error;
    }
  }

  async getSummaryStatus(uuid: string): Promise<any> {
    return (await this.httpClient.get<any>(`summary-status/${uuid}`)).data;
  }

  async stopSummary(uuid: string): Promise<any> {
    return (await this.httpClient.delete<any>(`summary-stop/${uuid}`)).data;
  }

  async getReport(
    uuid: string,
    download: boolean = false,
    reportType: 'html' | 'json' | 'docx' | 'pdf' = 'html',
    returnBinary: boolean = false
  ): Promise<any> {
    const endpoint = `reports/${uuid}`;
    const params: any = { report_type: reportType };

    if (download) {
      params.download = 'true';
    }

    // For binary return (Word and PDF documents), use base64 format
    if (returnBinary && (reportType === 'docx' || reportType === 'pdf')) {
      params.format = 'base64';

      const response = await this.httpClient.get<string>(endpoint, { params });

      // Decode base64 string back to ArrayBuffer
      const binaryString = atob(response.data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      return bytes.buffer;
    }

    // For text content (HTML/JSON), return as usual
    const response = await this.httpClient.get<any>(endpoint, { params });
    return response.data;
  }

  async updateLawCategory(lawId: string, category: Category): Promise<PreprocessedLaw | void> {
    try {
      const response = await this.httpClient.put<PreprocessedLaw>(`law/update/${lawId}`, {
        body: {
          category,
        },
      });

      // Backend now returns 200 with updated law data instead of 204
      if (response.status === 200) {
        return response.data;
      } else if (response.status === 204) {
        // For backward compatibility if backend returns 204
        return;
      } else {
        throw new Error(`Unexpected response status: ${response.status}`);
      }
    } catch (error: any) {
      console.error('Error updating law category:', error);
      throw error;
    }
  }
}
