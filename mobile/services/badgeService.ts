import { requestJson } from '@/services/httpClient';
import type { BadgeItem, BadgeListResponse, FeaturedBadgeResponse } from '@/types/badge';

export async function fetchBadges(token: string, category?: string): Promise<BadgeItem[]> {
  const path = category ? `/badges?category=${encodeURIComponent(category)}` : '/badges';
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
