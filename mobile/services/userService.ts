import { requestJson } from '@/services/httpClient';

export type UserMeResponse = {
  id: string;
  username: string;
  display_name?: string | null;
  bio?: string | null;
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

export type PublicUserProfileResponse = {
  id: string;
  username: string;
  display_name?: string | null;
  bio?: string | null;
  level_id: number;
  xp: number;
  streak_days: number;
  is_following: boolean;
  is_self: boolean;
  stats: {
    posts: number;
    streak: number;
    quests_completed: number;
    followers: number;
    following: number;
  };
};

type UserMeDataResponse = {
  data: UserMeResponse;
};

type PublicUserProfileDataResponse = {
  data: PublicUserProfileResponse;
};

type UpdateProfileRequest = {
  username?: string;
  display_name?: string | null;
  bio?: string | null;
  email?: string;
};

export async function getCurrentUser(token: string): Promise<UserMeResponse> {
  const response = await requestJson<UserMeDataResponse>('/users/me', {
    method: 'GET',
    token,
  });

  return response.data;
}

export async function getUserProfile(token: string, userId: string): Promise<PublicUserProfileResponse> {
  const response = await requestJson<PublicUserProfileDataResponse>(`/users/${userId}`, {
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
