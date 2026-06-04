import { requestJson } from '@/services/httpClient';

export type QuestListItem = {
  id: string;
  poi_id?: string | null;
  poi_name?: string | null;
  image_url?: string | null;
  rendered_text: string;
  labels: string[];
  min_confidence: number;
  xp_reward: number;
  is_active: boolean;
  user_status: 'not_started' | 'started' | 'submitted' | 'approved' | 'rejected';
};

export type QuestDetail = {
  id: string;
  poi_id?: string | null;
  poi_name?: string | null;
  image_url?: string | null;

  rendered_text: string;
  description?: string | null;
  labels: string[];
  min_confidence: number;

  xp_reward: number;
  base_xp: number;
  poi_bonus_xp: number;
  total_xp_with_poi: number;
  poi_required: boolean;

  is_active: boolean;
  user_status: 'not_started' | 'started' | 'submitted' | 'approved' | 'rejected';
  started_at: string | null;
  expires_at: string | null;
};

type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export type StartQuestResponse = {
  user_quest_id: string;
  quest_id: string;
  poi_id?: string | null;
  status: 'started' | 'submitted' | 'approved' | 'rejected';
  started_at: string | null;
  expires_at: string | null;
};

export type SubmitQuestResponse = {
  submission_id: string;
  post_id?: string | null;
  user_quest_id: string;
  poi_id?: string | null;
  status: 'submitted' | 'approved' | 'rejected';
  submission_status: 'pending' | 'processing' | 'approved' | 'rejected' | 'manual_review';
  submitted_at: string;
  retry_count: number;
  max_retry_count: number;
  xp_granted?: number | null;
  xp_reward?: number | null;
};

export function computeFileHash(value: string): string {
  let hash = 5381;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 33) ^ value.charCodeAt(i);
  }
  return Math.abs(hash).toString(16).padStart(8, '0').repeat(4).slice(0, 32);
}

export async function listQuests(token: string, page = 1, pageSize = 20): Promise<PaginatedResponse<QuestListItem>> {
  return requestJson<PaginatedResponse<QuestListItem>>(`/quests?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });
}

export async function listQuestLog(token: string): Promise<PaginatedResponse<QuestListItem>> {
  return requestJson<PaginatedResponse<QuestListItem>>('/quests/log', {
    method: 'GET',
    token,
  });
}

export async function getQuestDetail(
  token: string,
  questId: string,
  poiId?: string | null
): Promise<QuestDetail> {
  const suffix = poiId ? `?poi_id=${encodeURIComponent(poiId)}` : '';

  return requestJson<QuestDetail>(`/quests/${questId}${suffix}`, {
    method: 'GET',
    token,
  });
}
export async function startQuest(token: string, questId: string, poiId?: string | null): Promise<StartQuestResponse> {
  const suffix = poiId ? `?poi_id=${encodeURIComponent(poiId)}` : '';
  return requestJson<StartQuestResponse>(`/quests/${questId}/start${suffix}`, {
    method: 'POST',
    token,
  });
}

export async function submitQuest(
  token: string,
  questId: string,
  payload: { imageUrl: string; cloudinaryPublicId: string; fileHash: string; lat?: number; lng?: number; poiId?: string | null; postId?: string | null }
): Promise<SubmitQuestResponse> {
  return requestJson<SubmitQuestResponse>(`/quests/${questId}/submit`, {
    method: 'POST',
    token,
    body: JSON.stringify({
      post_id: payload.postId || undefined,
      image_url: payload.imageUrl,
      cloudinary_public_id: payload.cloudinaryPublicId,
      file_hash: payload.fileHash,
      poi_id: payload.poiId || undefined,
      lat: payload.lat,
      lng: payload.lng,
    }),
  });
}

export async function recommendQuestsFromImage(
  token: string,
  imageUrl: string,
  lat?: number,
  lng?: number
): Promise<QuestListItem[]> {
  return requestJson<QuestListItem[]>('/quests/recommend-from-image', {
    method: 'POST',
    token,
    body: JSON.stringify({
      image_url: imageUrl,
      lat,
      lng,
    }),
  });
}


export function buildLocalSubmissionPayload(imageUri: string): {
  imageUrl: string;
  cloudinaryPublicId: string;
  fileHash: string;
} {
  return {
    imageUrl: imageUri,
    cloudinaryPublicId: 'local',
    fileHash: computeFileHash(imageUri),
  };
}

