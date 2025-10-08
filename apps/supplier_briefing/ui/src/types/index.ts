import type { ExplainedStep, SerializedPandasObject } from '@/types/api.ts';

export interface ConversationMessage {
  question: string;
  answer?: string | { data: string };
  timestamp: Date;
  status: 'pending' | 'completed' | 'failed' | 'stopped';
  pandasObjectsData?: Record<string, SerializedPandasObject> | null;
  explained_steps?: ExplainedStep[] | null;
  resultsData?: Record<string, any> | null;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ConversationMessage[];
  createdAt: Date;
  updatedAt: Date;
  isSearching: boolean;
}

export interface SavedConversation extends Conversation {
  savedAt: Date;
  folderId?: string;
}

export interface ConversationFolder {
  id: string;
  name: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ConversationHistory {
  folders: ConversationFolder[];
  savedConversations: SavedConversation[];
}

export type SearchCompleteCallback<T> = (data: T) => void;

export interface SearchCompleteData {
  question?: string;
  answer: string;
  pandasObjectsData?: Record<string, SerializedPandasObject>;
  explained_steps?: ExplainedStep[];
  resultsData?: Record<string, any>;
}

export type {
  Task,
  ToolLog,
  StartResearchAgentRequest,
  ResearchAgentResponse,
  ResearchStatusResponse,
  ExplainedStep,
  SerializedPandasObject,
  SerializedDataFrame,
  SerializedSeries,
} from './api';
