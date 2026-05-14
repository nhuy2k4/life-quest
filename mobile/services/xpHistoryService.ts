import { requestJson } from '@/services/httpClient';

export type XpHistoryItem = {
  id: string;
  amount: number;
  source: string;
  submission_id: string | null;
  created_at: string;
};

export type XpHistoryResponse = {
  items: XpHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export async function getXpHistory(token: string, page = 1, pageSize = 20): Promise<XpHistoryResponse> {
  return requestJson<XpHistoryResponse>(`/gamification/xp-history?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });
}
