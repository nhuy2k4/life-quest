import { requestJson } from '@/services/httpClient';

export type PreferenceRequest = {
  interests: number[];
  activity_level: 'low' | 'medium' | 'high';
  location_enabled: boolean;
};

export type PreferenceResponse = {
  interests: number[];
  interest_weights: Record<string, number>;
  activity_level: 'low' | 'medium' | 'high' | null;
  location_enabled: boolean;
  notification_enabled: boolean;
};

type PreferenceDataResponse = {
  data: PreferenceResponse;
};

export async function saveMyPreferences(token: string, payload: PreferenceRequest): Promise<PreferenceResponse> {
  const response = await requestJson<PreferenceDataResponse>('/users/me/preferences', {
    method: 'POST',
    token,
    body: JSON.stringify(payload),
  });

  return response.data;
}
