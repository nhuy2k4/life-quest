import { requestJson } from '@/services/httpClient';
import type { BadgeItem, BadgeListResponse, FeaturedBadgeResponse } from '@/types/badge';

export async function fetchBadges(token: string, category?: string, userId?: string): Promise<BadgeItem[]> {
  let path = '/badges';
  const params: string[] = [];
  if (category) params.push(`category=${encodeURIComponent(category)}`);
  if (userId) params.push(`user_id=${encodeURIComponent(userId)}`);
  if (params.length > 0) path += `?${params.join('&')}`;

  const response = await requestJson<BadgeListResponse>(path, { method: 'GET', token });
  return response.data;
}

export async function fetchFeaturedBadges(token: string): Promise<FeaturedBadgeResponse['data']> {
  const response = await requestJson<FeaturedBadgeResponse>('/badges/featured', { method: 'GET', token });
  return response.data;
}

export async function fetchBadgeDetail(token: string, badgeId: string): Promise<BadgeItem> {
  return requestJson<BadgeItem>(`/badges/${badgeId}`, { method: 'GET', token });
}
