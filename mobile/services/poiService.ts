import { requestJson } from '@/services/httpClient';

export type PoiSuggestion = {
  poi_id: string | null;
  name: string | null;
  poi_type: string | null;
  latitude: number | null;
  longitude: number | null;
  radius_m: number | null;
  distance_m: number | null;
};

export async function suggestPoi(lat: number, lng: number, accuracyM?: number | null): Promise<PoiSuggestion> {
  const accuracy = typeof accuracyM === 'number' && Number.isFinite(accuracyM)
    ? `&accuracy_m=${encodeURIComponent(String(Math.max(0, accuracyM)))}`
    : '';

  return requestJson<PoiSuggestion>(`/pois/suggest?lat=${lat}&lng=${lng}${accuracy}`, {
    method: 'GET',
  });
}
