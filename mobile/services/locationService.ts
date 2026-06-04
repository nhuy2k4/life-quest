import * as Location from 'expo-location';

import { getItem, setItem, StorageKeys } from '@/utils/storage';

export type AppLocation = {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  capturedAt: number;
};

type LocationOptions = {
  forceRefresh?: boolean;
  maxAgeMs?: number;
  accuracy?: Location.LocationAccuracy;
};

const DEFAULT_MAX_AGE_MS = 2 * 60 * 1000;

function isUsable(location: AppLocation | null, maxAgeMs: number): location is AppLocation {
  if (!location) return false;
  return Date.now() - location.capturedAt <= maxAgeMs;
}

async function readCachedLocation(maxAgeMs: number): Promise<AppLocation | null> {
  const cached = await getItem<AppLocation>(StorageKeys.lastLocation);
  return isUsable(cached, maxAgeMs) ? cached : null;
}

async function requestCurrentLocation(accuracy: Location.LocationAccuracy): Promise<AppLocation | null> {
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== 'granted') {
    return null;
  }

  const current = await Location.getCurrentPositionAsync({ accuracy });
  const next: AppLocation = {
    latitude: current.coords.latitude,
    longitude: current.coords.longitude,
    accuracy: current.coords.accuracy ?? null,
    capturedAt: Date.now(),
  };
  await setItem(StorageKeys.lastLocation, next);
  return next;
}

export async function getAppLocation(options: LocationOptions = {}): Promise<AppLocation | null> {
  const maxAgeMs = options.maxAgeMs ?? DEFAULT_MAX_AGE_MS;
  if (!options.forceRefresh) {
    const cached = await readCachedLocation(maxAgeMs);
    if (cached) return cached;
  }

  try {
    return await requestCurrentLocation(options.accuracy ?? Location.Accuracy.Balanced);
  } catch {
    return readCachedLocation(Number.POSITIVE_INFINITY);
  }
}

export async function warmLocationCache(): Promise<void> {
  await getAppLocation({ maxAgeMs: DEFAULT_MAX_AGE_MS }).catch(() => null);
}
