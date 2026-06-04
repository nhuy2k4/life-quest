import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

export const StorageKeys = {
  newPost: 'lq_new_post',
  cameraMode: 'lq_camera_mode',
  attachedQuest: 'lq_attached_quest',
  suggestionFrom: 'lq_suggestion_from',
  feedCache: 'lq_feed_cache',
  lastLocation: 'lq_last_location',
  searchHistory: 'lq_search_history',
  accessToken: 'lq_access_token',
  refreshToken: 'lq_refresh_token',
  pushToken: 'lq_push_token',
  onboardingCompleted: 'lq_onboarding_completed',
} as const;

const memoryStore = new Map<string, string>();
const isWeb = Platform.OS === 'web';

function webSave(key: string, value: string): void {
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.setItem(key, value);
    return;
  }
  memoryStore.set(key, value);
}

function webGet(key: string): string | null {
  if (typeof window !== 'undefined' && window.localStorage) {
    return window.localStorage.getItem(key);
  }
  return memoryStore.get(key) ?? null;
}

function webRemove(key: string): void {
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.removeItem(key);
    return;
  }
  memoryStore.delete(key);
}

function webClear(keys: string[]): void {
  if (typeof window !== 'undefined' && window.localStorage) {
    keys.forEach((key) => window.localStorage.removeItem(key));
    return;
  }
  keys.forEach((key) => memoryStore.delete(key));
}

type StorageService = {
  save: <T>(key: string, value: T) => Promise<boolean>;
  get: <T>(key: string) => Promise<T | null>;
  remove: (key: string) => Promise<boolean>;
  clear: (keys: string[]) => Promise<boolean>;
};

export const storageService: StorageService = {
  async save<T>(key: string, value: T): Promise<boolean> {
    const serialized = JSON.stringify(value);

    try {
      if (isWeb) {
        webSave(key, serialized);
        return true;
      }

      await AsyncStorage.setItem(key, serialized);
      return true;
    } catch {
      if (!isWeb) {
        webSave(key, serialized);
        return true;
      }
      return false;
    }
  },

  async get<T>(key: string): Promise<T | null> {
    let raw: string | null = null;

    try {
      raw = isWeb ? webGet(key) : await AsyncStorage.getItem(key);
    } catch {
      raw = webGet(key);
    }

    if (!raw) return null;

    try {
      return JSON.parse(raw) as T;
    } catch {
      return null;
    }
  },

  async remove(key: string): Promise<boolean> {
    try {
      if (isWeb) {
        webRemove(key);
        return true;
      }

      await AsyncStorage.removeItem(key);
      return true;
    } catch {
      webRemove(key);
      return true;
    }
  },

  async clear(keys: string[]): Promise<boolean> {
    try {
      if (isWeb) {
        webClear(keys);
        return true;
      }

      await AsyncStorage.multiRemove(keys);
      return true;
    } catch {
      webClear(keys);
      return true;
    }
  },
};

export async function saveItem<T>(key: string, value: T): Promise<boolean> {
  return storageService.save(key, value);
}

export async function getItem<T>(key: string): Promise<T | null> {
  return storageService.get<T>(key);
}

export async function removeItem(key: string): Promise<boolean> {
  return storageService.remove(key);
}

export async function clearItems(keys: string[]): Promise<boolean> {
  return storageService.clear(keys);
}

export async function setItem<T>(key: string, value: T): Promise<boolean> {
  return storageService.save(key, value);
}
