import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react';
import { AppState, Platform, StyleSheet, Text, View } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withSequence,
  withTiming,
} from 'react-native-reanimated';

import { listNotifications, type NotificationItem } from '@/services/notificationService';
import { getItem, StorageKeys } from '@/utils/storage';

type XpGainContextValue = {
  showXpGain: (xp: number) => void;
};

type XpGainItem = {
  id: number;
  xp: number;
};

const XpGainContext = createContext<XpGainContextValue | undefined>(undefined);

function readNumber(data: Record<string, unknown> | null | undefined, key: string): number {
  const value = data?.[key];
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function extractXpFromNotification(item: Pick<NotificationItem, 'type' | 'data'>): number {
  if (item.type === 'quest_complete') {
    return readNumber(item.data, 'xp_granted');
  }
  if (item.type === 'quest_rejected') {
    return readNumber(item.data, 'consolation_xp');
  }
  if (item.type === 'xp') {
    return (
      readNumber(item.data, 'xp_granted') ||
      readNumber(item.data, 'amount') ||
      readNumber(item.data, 'xp')
    );
  }
  return 0;
}

function XpGainToast({ item, onDone }: { item: XpGainItem; onDone: (id: number) => void }) {
  const opacity = useSharedValue(0);
  const translateX = useSharedValue(34);
  const scale = useSharedValue(0.9);

  useEffect(() => {
    opacity.value = withSequence(
      withTiming(1, { duration: 400, easing: Easing.out(Easing.cubic) }),
      withDelay(280, withTiming(0, { duration: 1000, easing: Easing.inOut(Easing.quad) }))
    );
    translateX.value = withTiming(0, { duration: 400, easing: Easing.out(Easing.cubic) });
    scale.value = withSequence(
      withTiming(1.04, { duration: 220, easing: Easing.out(Easing.cubic) }),
      withTiming(1, { duration: 180, easing: Easing.out(Easing.cubic) })
    );

    const timeout = setTimeout(() => onDone(item.id), 1700);
    return () => clearTimeout(timeout);
  }, [item.id, onDone, opacity, scale, translateX]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateX: translateX.value }, { scale: scale.value }],
  }));

  return (
    <Animated.View pointerEvents="none" style={[styles.toast, animatedStyle]}>
      <View style={styles.iconWrap}>
        <Ionicons name="flash" size={18} color="#111827" />
      </View>
      <View>
        <Text style={styles.amount}>{`+${item.xp} XP`}</Text>
        <Text style={styles.caption}>Reward gained</Text>
      </View>
    </Animated.View>
  );
}

export function XpGainProvider({ children }: PropsWithChildren) {
  const [items, setItems] = useState<XpGainItem[]>([]);
  const seenNotificationIdsRef = useRef<Set<string>>(new Set());
  const hasHydratedNotificationsRef = useRef(false);

  const removeItem = useCallback((id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const showXpGain = useCallback((xp: number) => {
    if (!Number.isFinite(xp) || xp <= 0) return;

    setItems((prev) => [
      ...prev.slice(-2),
      {
        id: Date.now() + Math.random(),
        xp: Math.round(xp),
      },
    ]);
  }, []);

  const inspectNotifications = useCallback(async () => {
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      seenNotificationIdsRef.current.clear();
      hasHydratedNotificationsRef.current = false;
      return;
    }

    try {
      const response = await listNotifications(token, 1, 10);
      const seen = seenNotificationIdsRef.current;

      if (!hasHydratedNotificationsRef.current) {
        response.items.forEach((item) => seen.add(item.id));
        hasHydratedNotificationsRef.current = true;
        return;
      }

      response.items
        .slice()
        .reverse()
        .forEach((item) => {
          if (seen.has(item.id)) return;
          seen.add(item.id);
          showXpGain(extractXpFromNotification(item));
        });
    } catch {
      // XP animation is decorative; notification polling should never affect app flow.
    }
  }, [showXpGain]);

  useEffect(() => {
    void inspectNotifications();

    const interval = setInterval(() => {
      void inspectNotifications();
    }, 30000);

    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        void inspectNotifications();
      }
    });

    return () => {
      clearInterval(interval);
      subscription.remove();
    };
  }, [inspectNotifications]);

  useEffect(() => {
    if (Platform.OS === 'web') return;
    if (Platform.OS === 'android' && Constants.appOwnership === 'expo') return;

    let subscription: { remove: () => void } | null = null;
    let mounted = true;

    const attachPushListener = async () => {
      try {
        const Notifications: typeof import('expo-notifications') = await import('expo-notifications');
        if (!mounted) return;

        subscription = Notifications.addNotificationReceivedListener((notification) => {
          const request = notification.request;
          const id = request.identifier;
          if (seenNotificationIdsRef.current.has(id)) return;
          seenNotificationIdsRef.current.add(id);

          showXpGain(
            extractXpFromNotification({
              type: String(request.content.data?.type ?? request.content.categoryIdentifier ?? ''),
              data: request.content.data ?? null,
            })
          );
        });
      } catch {
        // Push listeners are unavailable in some Expo Go/runtime combinations.
      }
    };

    void attachPushListener();

    return () => {
      mounted = false;
      subscription?.remove();
    };
  }, [showXpGain]);

  const value = useMemo(() => ({ showXpGain }), [showXpGain]);

  return (
    <XpGainContext.Provider value={value}>
      {children}
      <View pointerEvents="none" style={styles.host}>
        {items.map((item, index) => (
          <View key={item.id} style={{ marginTop: index * 8 }}>
            <XpGainToast item={item} onDone={removeItem} />
          </View>
        ))}
      </View>
    </XpGainContext.Provider>
  );
}

export function useXpGain() {
  const context = useContext(XpGainContext);
  if (!context) {
    throw new Error('useXpGain must be used within an XpGainProvider');
  }
  return context;
}

const styles = StyleSheet.create({
  host: {
    alignItems: 'flex-end',
    position: 'absolute',
    right: 0,
    top: '38%',
    zIndex: 80,
  },
  toast: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderBottomLeftRadius: 18,
    borderTopLeftRadius: 18,
    flexDirection: 'row',
    gap: 10,
    minWidth: 138,
    paddingHorizontal: 12,
    paddingVertical: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.24,
    shadowRadius: 14,
  },
  iconWrap: {
    alignItems: 'center',
    backgroundColor: '#FDE68A',
    borderRadius: 999,
    height: 30,
    justifyContent: 'center',
    width: 30,
  },
  amount: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '900',
  },
  caption: {
    color: '#CBD5E1',
    fontSize: 10,
    fontWeight: '700',
  },
});
