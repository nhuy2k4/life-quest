import { requestJson } from '@/services/httpClient';

export type RecommendationQuestItem = {
  id: string;
  rendered_text: string;
  title: string;
  description: string | null;
  difficulty: string;
  image_url?: string | null;
  labels: string[];
  min_confidence: number;
  poi_required: boolean;
  xp_reward: number;
  user_status: 'not_started' | 'started' | 'submitted' | 'approved' | 'rejected';
  recommendation_score: number;
  ml_score?: number | null;
};


type RecommendationResponse = {
  items: RecommendationQuestItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export async function getRecommendedQuests(
  token: string,
  lat?: number,
  lng?: number
): Promise<RecommendationQuestItem[]> {
  let url = '/recommendations/quests?page=1&page_size=10';
  if (lat !== undefined && lng !== undefined) {
    url += `&lat=${lat}&lng=${lng}`;
  }

  const response = await requestJson<RecommendationResponse>(url, {
    method: 'GET',
    token,
  });

  return response.items;
}

