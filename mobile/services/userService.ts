import { requestJson } from '@/services/httpClient';

export type UserMeResponse = {
  id: string;
  username: string;
  email: string;
  role: string;
  level_id: number;
  xp: number;
  streak_days: number;
  trust_score: number;
  onboarding_completed: boolean;
  is_banned: boolean;
  created_at: string;
  updated_at: string;
};

type UserMeDataResponse = {
  data: UserMeResponse;
};

type UpdateProfileRequest = {
  username?: string;
  email?: string;
};

export async function getCurrentUser(token: string): Promise<UserMeResponse> {
  const response = await requestJson<UserMeDataResponse>('/users/me', {
    method: 'GET',
    token,
  });

  return response.data;
}

export async function updateProfile(token: string, payload: UpdateProfileRequest): Promise<UserMeResponse> {
  const response = await requestJson<UserMeDataResponse>('/users/me', {
    method: 'PATCH',
    token,
    body: JSON.stringify(payload),
  });

  return response.data;
}
