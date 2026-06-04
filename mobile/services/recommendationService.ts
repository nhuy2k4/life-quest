import { requestJson } from '@/services/httpClient';
import { mapFeedPost, type FeedPost } from '@/services/socialService';
import type { Post } from '@/types';

export type RecommendationQuestItem = {
  id: string;
  poi_id?: string | null;
  poi_name?: string | null;
  title: string;
  description?: string | null;
  rendered_text: string;
  labels?: string[];
  xp_reward: number;
  difficulty?: string | null;
  image_url?: string | null;
  final_score: number;
  reasons: string[];
  score_breakdown?: RecommendationScoreBreakdown;
};
export type RecommendationPostItem = FeedPost & {
  final_score: number;
  reasons: string[];
};

export type RecommendationScoreBreakdown = {
  interest: number;
  nearby: number;
  trending: number;
  continue: number;
  affinity: number;
  anti_repeat: number;
  exploration: number;
  freshness: number;
};

export type RecommendationSectionKey =
  | 'recommended_for_you'
  | 'trending_near_you'
  | 'continue_your_missions'
  | 'explore_new_things';

export type RecommendationSection = {
  key: RecommendationSectionKey;
  title: string;
  item_type?: 'quest' | 'post';
  items: Array<RecommendationQuestItem | RecommendationPostItem>;
};

type RecommendationApiResponse = {
  request_id: string;
  sections: RecommendationSection[];
  for_you_posts: RecommendationPostItem[];
  explore_quests: RecommendationQuestItem[];
  recommended_for_you: RecommendationPostItem[];
  trending_near_you: RecommendationQuestItem[];
  continue_your_missions: RecommendationQuestItem[];
  explore_new_things: RecommendationQuestItem[];
};

export type RecommendationResponse = Omit<RecommendationApiResponse, 'for_you_posts' | 'recommended_for_you'> & {
  for_you_posts: Post[];
  recommended_for_you: Post[];
};

export async function getRecommendedQuests(
  token: string,
  lat?: number,
  lng?: number
): Promise<RecommendationResponse> {
  let url = '/recommendations/quests?page=1&page_size=10';
  if (lat !== undefined && lng !== undefined) {
    url += `&lat=${lat}&lng=${lng}`;
  }

  const response = await requestJson<RecommendationApiResponse>(url, {
    method: 'GET',
    token,
  });

  const forYouPosts = response.for_you_posts.map(mapFeedPost);
  return {
    ...response,
    for_you_posts: forYouPosts,
    recommended_for_you: forYouPosts,
  };
}

export async function logRecommendationEvent(
  token: string,
  payload: {
    request_id: string;
    quest_id: string;
    event: 'shown' | 'clicked' | 'started' | 'completed' | 'ignored';
    section?: RecommendationSectionKey;
    rank?: number;
    final_score?: number;
    reasons?: string[];
    score_breakdown?: RecommendationScoreBreakdown;
  }
): Promise<void> {
  await requestJson('/recommendations/events', {
    method: 'POST',
    token,
    body: JSON.stringify(payload),
  });
}
