import axios from 'axios';
import type { TranscriptionResult, IntegrationStatus, IntegrationResults, SelectedActionItem, SelectedQuestion } from '../types';

const API_BASE = import.meta.env;

export const uploadFile = async (file: File): Promise<TranscriptionResult> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

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
