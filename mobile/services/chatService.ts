import { buildApiWebSocketUrl } from '@/constants/api';
import { requestJson } from '@/services/httpClient';

export type ChatUser = {
  id: string;
  username: string;
  avatar_url?: string | null;
  level_id: number;
  xp: number;
  streak_days: number;
};

export type ChatMessage = {
  id: string;
  conversation_id: string;
  sender: ChatUser;
  content: string;
  message_type: string;
  read_at?: string | null;
  created_at: string;
  is_mine: boolean;
};

export type Conversation = {
  id: string;
  other_user: ChatUser;
  is_friend: boolean;
  last_message?: ChatMessage | null;
  unread_count: number;
  created_at: string;
  updated_at: string;
  last_message_at?: string | null;
};

type ConversationListResponse = {
  items: Conversation[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

type MessageListResponse = {
  items: ChatMessage[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export async function listConversations(token: string, page = 1, pageSize = 20): Promise<ConversationListResponse> {
  return requestJson<ConversationListResponse>(`/chat/conversations?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });
}

export async function getOrCreateConversation(token: string, targetUserId: string): Promise<Conversation> {
  return requestJson<Conversation>('/chat/conversations', {
    method: 'POST',
    token,
    body: JSON.stringify({ target_user_id: targetUserId }),
  });
}

export async function listMessages(token: string, conversationId: string, page = 1, pageSize = 50): Promise<MessageListResponse> {
  return requestJson<MessageListResponse>(`/chat/conversations/${conversationId}/messages?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });
}

export async function sendChatMessage(token: string, conversationId: string, content: string): Promise<ChatMessage> {
  return requestJson<ChatMessage>(`/chat/conversations/${conversationId}/messages`, {
    method: 'POST',
    token,
    body: JSON.stringify({ content }),
  });
}

export async function markConversationRead(token: string, conversationId: string): Promise<void> {
  await requestJson(`/chat/conversations/${conversationId}/read`, {
    method: 'POST',
    token,
  });
}

export function createChatSocket(token: string): WebSocket {
  return new WebSocket(buildApiWebSocketUrl(`/chat/ws?token=${encodeURIComponent(token)}`));
}
