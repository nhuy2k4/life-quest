import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PropsWithChildren,
} from 'react';
import { AppState } from 'react-native';

import { BadgeUnlockCelebration } from '@/components/lifequest/badges/BadgeUnlockCelebration';
import { useAuthContext } from '@/contexts/AuthContext';
import { fetchBadgeDetail, fetchBadges, fetchFeaturedBadges } from '@/services/badgeService';
import { listNotifications, type NotificationItem } from '@/services/notificationService';
import type { BadgeItem, FeaturedBadge } from '@/types/badge';
import { getItem } from '@/utils/storage';
import { StorageKeys } from '@/utils/storage';

type BadgeContextValue = {
  badges: BadgeItem[];
  featuredBadges: FeaturedBadge[];
  isLoading: boolean;
  hasUnviewedBadge: boolean;
  newlyUnlockedBadge: BadgeItem | null;
  refreshBadges: () => Promise<void>;
  markBadgesViewed: () => void;
  dismissUnlockCelebration: () => void;
};

const BadgeContext = createContext<BadgeContextValue | undefined>(undefined);

function readString(data: Record<string, unknown> | null | undefined, key: string): string | null {
  const value = data?.[key];
  return typeof value === 'string' && value.trim().length > 0 ? value : null;
}

function buildBadgeFromNotification(item: NotificationItem): BadgeItem | null {
  const badgeId = readString(item.data, 'badge_id');
  const badgeName = readString(item.data, 'badge_name');
  if (!badgeId || !badgeName) return null;

  const rarity = readString(item.data, 'badge_rarity') ?? 'common';
  return {
    id: badgeId,
    name: badgeName,
    description: 'New achievement unlocked.',
    icon_url: readString(item.data, 'badge_icon_url') ?? 'ribbon-outline',
    rarity: ['common', 'rare', 'epic', 'legendary'].includes(rarity)
      ? (rarity as BadgeItem['rarity'])
      : 'common',
    category: 'quests',
    criteria: { type: 'notification', target: 1 },
    is_hidden: false,
    is_unlocked: true,
    unlocked_at: item.created_at,
    progress: { current: 1, target: 1 },
  };
}

export function BadgeProvider({ children }: PropsWithChildren) {
  const { isAuthenticated } = useAuthContext();
  const [badges, setBadges] = useState<BadgeItem[]>([]);
  const [featuredBadges, setFeaturedBadges] = useState<FeaturedBadge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasUnviewedBadge, setHasUnviewedBadge] = useState(false);
  const [newlyUnlockedBadge, setNewlyUnlockedBadge] = useState<BadgeItem | null>(null);

  // Track previously known unlocked badge IDs to diff for new unlocks
  const prevUnlockedIds = useRef<Set<string>>(new Set());
  // Prevent initial mount from triggering "new unlock" celebration
  const isFirstLoad = useRef(true);
  const seenNotificationIdsRef = useRef<Set<string>>(new Set());
  const announcedBadgeIdsRef = useRef<Set<string>>(new Set());
  const hasHydratedNotificationsRef = useRef(false);

  const loadBadges = useCallback(
    async (silent = false) => {
      if (!isAuthenticated) return;

      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      if (!silent) setIsLoading(true);

      try {
        const [allBadges, featured] = await Promise.all([
          fetchBadges(token),
          fetchFeaturedBadges(token),
        ]);

        const currentUnlockedIds = new Set(allBadges.filter((b) => b.is_unlocked).map((b) => b.id));

        if (!isFirstLoad.current) {
          // Detect newly unlocked since last fetch
          const newUnlocked = allBadges.filter(
            (b) => b.is_unlocked && !prevUnlockedIds.current.has(b.id)
          );

          if (newUnlocked.length > 0) {
            setHasUnviewedBadge(true);
            // Show celebration for the highest rarity newly unlocked badge
            const rarityOrder: Record<string, number> = {
              legendary: 0,
              epic: 1,
              rare: 2,
              common: 3,
            };
            const topNew = [...newUnlocked].sort(
              (a, b) => (rarityOrder[a.rarity] ?? 99) - (rarityOrder[b.rarity] ?? 99)
            )[0];
            if (!announcedBadgeIdsRef.current.has(topNew.id)) {
              announcedBadgeIdsRef.current.add(topNew.id);
              setNewlyUnlockedBadge(topNew);
            }
          }
        }

        prevUnlockedIds.current = currentUnlockedIds;
        isFirstLoad.current = false;

        setBadges(allBadges);
        setFeaturedBadges(featured);
      } catch (error) {
        console.warn('[BadgeContext] Failed to load badges', error);
      } finally {
        if (!silent) setIsLoading(false);
      }
    },
    [isAuthenticated]
  );

  const showBadgeFromNotification = useCallback(async (token: string, item: NotificationItem) => {
    if (item.type !== 'badge_unlocked') return;

    const fallbackBadge = buildBadgeFromNotification(item);
    const badgeId = fallbackBadge?.id ?? readString(item.data, 'badge_id');
    if (!badgeId || announcedBadgeIdsRef.current.has(badgeId)) return;

    announcedBadgeIdsRef.current.add(badgeId);
    setHasUnviewedBadge(true);

    try {
      const detail = await fetchBadgeDetail(token, badgeId);
      setNewlyUnlockedBadge(detail);
    } catch {
      if (fallbackBadge) {
        setNewlyUnlockedBadge(fallbackBadge);
      }
    }

    void loadBadges(true);
  }, [loadBadges]);

  const inspectNotifications = useCallback(async () => {
    if (!isAuthenticated) {
      seenNotificationIdsRef.current.clear();
      hasHydratedNotificationsRef.current = false;
      return;
    }

    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) return;

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
          void showBadgeFromNotification(token, item);
        });
    } catch {
      // Badge notifications are decorative; failures should not affect app flow.
    }
  }, [isAuthenticated, showBadgeFromNotification]);

  // Load badges when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      void loadBadges();
    } else {
      setBadges([]);
      setFeaturedBadges([]);
      prevUnlockedIds.current = new Set();
      announcedBadgeIdsRef.current = new Set();
      seenNotificationIdsRef.current = new Set();
      hasHydratedNotificationsRef.current = false;
      isFirstLoad.current = true;
    }
  }, [isAuthenticated, loadBadges]);

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
    if (!isAuthenticated) return;

    const interval = setInterval(() => {
      void loadBadges(true);
    }, 10000);

    return () => clearInterval(interval);
  }, [isAuthenticated, loadBadges]);

  const refreshBadges = useCallback(async () => {
    await loadBadges(true);
  }, [loadBadges]);

  const markBadgesViewed = useCallback(() => {
    setHasUnviewedBadge(false);
  }, []);

  const dismissUnlockCelebration = useCallback(() => {
    setNewlyUnlockedBadge(null);
  }, []);

  const value = useMemo(
    () => ({
      badges,
      featuredBadges,
      isLoading,
      hasUnviewedBadge,
      newlyUnlockedBadge,
      refreshBadges,
      markBadgesViewed,
      dismissUnlockCelebration,
    }),
    [
      badges,
      featuredBadges,
      isLoading,
      hasUnviewedBadge,
      newlyUnlockedBadge,
      refreshBadges,
      markBadgesViewed,
      dismissUnlockCelebration,
    ]
  );

  return (
    <BadgeContext.Provider value={value}>
      {children}
      <BadgeUnlockCelebration
        badge={newlyUnlockedBadge}
        onDismiss={dismissUnlockCelebration}
      />
    </BadgeContext.Provider>
  );
}

export function useBadgeContext() {
  const context = useContext(BadgeContext);
  if (!context) {
    throw new Error('useBadgeContext must be used within a BadgeProvider');
  }
  return context;
}
