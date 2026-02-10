export interface ActionItem {
  task: string;
  owner?: string;
  deadline?: string;
}

export interface OpenQuestion {
  question: string;
  context?: string;
}

export interface Decision {
  decision: string;
  context?: string;
}

export interface Insights {
  summary?: string;
  decisions?: Decision[];
  action_items?: ActionItem[];
  open_questions?: OpenQuestion[];
}

export interface TranscriptionResult {
  transcript: string;
  insights: Insights;
}

export interface IntegrationStatus {
  github_enabled: boolean;
  github_repo?: string;
  calendar_enabled: boolean;
  calendar_type?: string;
}

export interface SelectedActionItem extends ActionItem {
  create_github: boolean;
}

export interface SelectedQuestion extends OpenQuestion {
  create_github: boolean;
  create_calendar: boolean;
}

export interface IntegrationResult {
  type: string;
  title: string;
  url?: string;
  issue_number?: number;
  event_id?: string;
  attendees?: string[];
  error?: string;
}

export interface IntegrationResults {
  success: boolean;
  results: {
    github_issues: IntegrationResult[];
    calendar_events: IntegrationResult[];
  };
}

export const AppState = {
  UPLOAD: 'UPLOAD',
  PROCESSING: 'PROCESSING',
  RESULTS: 'RESULTS',
  ERROR: 'ERROR'
} as const;

export type AppState = (typeof AppState [keyof typeof AppState])