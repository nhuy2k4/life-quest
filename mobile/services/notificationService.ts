import Constants from 'expo-constants';
import { Platform } from 'react-native';

import { requestJson } from '@/services/httpClient';
import { getItem, setItem, StorageKeys } from '@/utils/storage';

export type NotificationItem = {
  id: string;
  type: string;
  data: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
};

export type NotificationListResponse = {
  items: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export type UnreadCountResponse = {
  unread_count: number;
};

export async function listNotifications(token: string, page = 1, pageSize = 30): Promise<NotificationListResponse> {
  return requestJson<NotificationListResponse>(`/notifications?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });
}

export async function getUnreadNotificationCount(token: string): Promise<number> {
  const response = await requestJson<UnreadCountResponse>('/notifications/unread-count', {
    method: 'GET',
    token,
  });
  return response.unread_count;
}

export async function markNotificationRead(token: string, notificationId: string): Promise<void> {
  await requestJson(`/notifications/${notificationId}/read`, {
    method: 'PATCH',
    token,
  });
}

export async function markAllNotificationsRead(token: string): Promise<void> {
  await requestJson('/notifications/read-all', {
    method: 'PATCH',
    token,
  });
}

export async function registerPushToken(token: string): Promise<string | null> {
  if (Platform.OS === 'web') {
    return null;
  }

  if (Platform.OS === 'android' && Constants.appOwnership === 'expo') {
    // Expo Go SDK 53+ removed Android remote push support from expo-notifications.
    // Use a development build for push; keep in-app notifications active in Expo Go.
    return null;
  }

  try {
    const Notifications: typeof import('expo-notifications') = await import('expo-notifications');

    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldShowBanner: true,
        shouldShowList: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
      }),
    });

    const existingStatus = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus.status;

    if (finalStatus !== 'granted') {
      const requested = await Notifications.requestPermissionsAsync();
      finalStatus = requested.status;
    }

    if (finalStatus !== 'granted') {
      return null;
    }

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.DEFAULT,
      });
    }

    const projectId =
      Constants.expoConfig?.extra?.eas?.projectId ??
      Constants.easConfig?.projectId;

    const pushToken = (await Notifications.getExpoPushTokenAsync(projectId ? { projectId } : undefined)).data;
    const previous = await getItem<string>(StorageKeys.pushToken);

    const platform = Platform.OS === 'ios' || Platform.OS === 'android' ? Platform.OS : 'unknown';

    if (previous !== pushToken) {
      await requestJson('/notifications/push-tokens', {
        method: 'POST',
        token,
        body: JSON.stringify({
          token: pushToken,
          provider: 'expo',
          platform,
        }),
      });
      await setItem(StorageKeys.pushToken, pushToken);
    }

    if (Platform.OS === 'android') {
      const nativeToken = await Notifications.getDevicePushTokenAsync();
      if (nativeToken.data) {
        await requestJson('/notifications/push-tokens', {
          method: 'POST',
          token,
          body: JSON.stringify({
            token: String(nativeToken.data),
            provider: 'fcm',
            platform: 'android',
          }),
        });
      }
    }

    return pushToken;
  } catch {
    // Expo Go SDK 53+ no longer supports Android remote notifications.
    // In-app notifications still work; push requires a development build.
    return null;
  }
}
