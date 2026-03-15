import axios from 'axios';
import type { TranscriptionResult, IntegrationStatus, IntegrationResults, SelectedActionItem, SelectedQuestion, ProcessingStep } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5001';

export const uploadFile = async (file: File): Promise<{ job_id: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  return response.data;
};

export const subscribeToJob = (
  jobId: string,
  callbacks: {
    onStep: (step: ProcessingStep, progress: number) => void;
    onComplete: (result: TranscriptionResult) => void;
    onError: (error: string) => void;
  }
): (() => void) => {
  const es = new EventSource(`${API_BASE}/jobs/${jobId}/stream`);

  es.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.step === 'error') {
      callbacks.onError(data.error || 'Processing failed');
      es.close();
      return;
    }

    callbacks.onStep(data.step as ProcessingStep, data.progress);

    if (data.step === 'complete' && data.result) {
      callbacks.onComplete(data.result);
      es.close();
    }
  };

  es.onerror = () => {
    es.close();
    // Fallback: try polling the result endpoint
    getJobResult(jobId)
      .then((result) => {
        if ('transcript' in result) {
          callbacks.onComplete(result as TranscriptionResult);
        } else {
          callbacks.onError('Connection lost. Please try again.');
        }
      })
      .catch(() => {
        callbacks.onError('Connection lost. Please try again.');
      });
  };

  return () => es.close();
};

export const getJobResult = async (jobId: string): Promise<TranscriptionResult | { status: string }> => {
  const response = await axios.get(`${API_BASE}/jobs/${jobId}/result`);
  return response.data;
};

export const getIntegrationStatus = async (): Promise<IntegrationStatus> => {
  const response = await axios.get(`${API_BASE}/integration-status`);
  return response.data;
};

export const createIntegrations = async (
  actionItems: SelectedActionItem[],
  openQuestions: SelectedQuestion[]
): Promise<IntegrationResults> => {
  const response = await axios.post(`${API_BASE}/create-integrations`, {
    action_items: actionItems,
    open_questions: openQuestions
  });

  return response.data;
};
