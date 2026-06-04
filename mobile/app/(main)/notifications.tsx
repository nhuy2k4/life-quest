import { Ionicons } from '@expo/vector-icons';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { Avatar } from '@/components/ui/avatar';
import { Layout } from '@/constants/layout';
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationItem,
} from '@/services/notificationService';
import { getItem, StorageKeys } from '@/utils/storage';

type NotifType = 'like' | 'comment' | 'follow' | 'quest_complete' | 'quest_rejected' | 'quest_suggest' | 'xp' | 'system' | 'badge_unlocked';

function asNotifType(value: string): NotifType {
  if (
    value === 'like' ||
    value === 'comment' ||
    value === 'follow' ||
    value === 'quest_complete' ||
    value === 'quest_rejected' ||
    value === 'quest_suggest' ||
    value === 'xp' ||
    value === 'badge_unlocked'
  ) {
    return value;
  }
  return 'system';
}

function timeAgo(value: string): string {
  const created = new Date(value).getTime();
  const diffSeconds = Math.max(1, Math.floor((Date.now() - created) / 1000));
  if (diffSeconds < 60) return 'just now';
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function readString(data: Record<string, unknown> | null, key: string): string | undefined {
  const value = data?.[key];
  return typeof value === 'string' ? value : undefined;
}

function notificationCopy(item: NotificationItem): { actor?: string; preview: string; meta?: string } {
  const type = asNotifType(item.type);
  const actor = readString(item.data, 'actor_username');

  if (type === 'like') {
    return { actor, preview: 'liked your post.' };
  }
  if (type === 'comment') {
    return {
      actor,
      preview: 'commented on your post.',
      meta: readString(item.data, 'comment_preview'),
    };
  }
  if (type === 'follow') {
    return { actor, preview: 'started following you.' };
  }
  if (type === 'quest_complete') {
    const xp = item.data?.xp_granted;
    return {
      preview: 'Quest approved',
      meta: typeof xp === 'number' ? `+${xp} XP added` : 'XP added to your profile',
    };
  }
  if (type === 'quest_rejected') {
    const consolation = typeof item.data?.consolation_xp === 'number' ? item.data.consolation_xp : 0;
    const previews = ['Nice try!', 'Almost there!', 'Keep exploring!'];
    const preview = previews[Math.floor(Math.random() * previews.length)];
    const bonusText = consolation > 0 ? ` +${consolation} XP exploration bonus earned.` : '';
    const reason = readString(item.data, 'reason') ?? 'You can update the photo and try again.';
    return {
      preview: `${preview}${bonusText}`,
      meta: reason,
    };
  }
  if (type === 'badge_unlocked') {
    const rarity = readString(item.data, 'badge_rarity');
    const rarityText = rarity ? `[${rarity.toUpperCase()}] ` : '';
    return {
      preview: 'You unlocked a new badge!',
      meta: `${rarityText}${readString(item.data, 'badge_name') ?? 'Check it out in your profile.'}`,
    };
  }
  return { preview: 'You have a new notification.' };
}

function NotifIcon({ type }: { type: NotifType }) {
  if (type === 'like') return <Ionicons name="heart-outline" size={16} color="#4B5563" />;
  if (type === 'comment') return <Ionicons name="chatbubble-outline" size={16} color="#4B5563" />;
  if (type === 'follow') return <Ionicons name="person-add-outline" size={16} color="#4B5563" />;
  if (type === 'quest_complete') return <Ionicons name="trophy-outline" size={16} color="#fff" />;
  if (type === 'quest_rejected') return <Ionicons name="alert-circle-outline" size={16} color="#fff" />;
  if (type === 'badge_unlocked') return <Ionicons name="ribbon-outline" size={16} color="#fff" />;
  if (type === 'quest_suggest') return <Ionicons name="flash-outline" size={16} color="#fff" />;
  return <Ionicons name="notifications-outline" size={16} color="#4B5563" />;
}

function NotificationRow({
  item,
  onRead,
}: {
  item: NotificationItem;
  onRead: (id: string) => void;
}) {
  const type = asNotifType(item.type);
  const isSystem = type === 'quest_complete' || type === 'quest_rejected' || type === 'quest_suggest' || type === 'xp' || type === 'system' || type === 'badge_unlocked';
  const iconBg = type === 'quest_complete' ? '#11181C' : type === 'quest_rejected' ? '#7F1D1D' : type === 'badge_unlocked' ? '#8B5CF6' : '#1F2937';
  const copy = notificationCopy(item);

  return (
    <Pressable onPress={() => onRead(item.id)} style={[styles.row, item.is_read ? styles.rowRead : styles.rowUnread]}>
      <View style={styles.leftWrap}>
        {isSystem ? (
          <View style={[styles.systemIconWrap, { backgroundColor: iconBg }]}>
            <NotifIcon type={type} />
          </View>
        ) : (
          <>
            <Avatar size={40} label={(copy.actor ?? 'U').charAt(0)} />
            <View style={styles.typeBadge}>
              <NotifIcon type={type} />
            </View>
          </>
        )}
      </View>

      <View style={styles.textWrap}>
        <Text style={styles.previewText}>
          {copy.actor ? <Text style={styles.actorText}>{`${copy.actor} `}</Text> : null}
          <Text style={styles.previewMuted}>{copy.preview}</Text>
        </Text>
        {copy.meta ? <Text style={styles.metaText}>{copy.meta}</Text> : null}
        <Text style={styles.timeText}>{timeAgo(item.created_at)}</Text>
      </View>

      {!item.is_read ? <View style={styles.unreadDot} /> : null}
    </Pressable>
  );
}

export default function NotificationsScreen() {
  const [notifs, setNotifs] = useState<NotificationItem[]>([]);
  const [isRefreshing, setRefreshing] = useState(false);
  const [isLoading, setLoading] = useState(true);

  const unreadCount = useMemo(() => notifs.filter((item) => !item.is_read).length, [notifs]);

  const loadNotifications = useCallback(async () => {
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      setNotifs([]);
      setLoading(false);
      return;
    }

    try {
      const response = await listNotifications(token, 1, 50);
      setNotifs(response.items);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  const markAllRead = async () => {
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) return;
    setNotifs((prev) => prev.map((item) => ({ ...item, is_read: true })));
    await markAllNotificationsRead(token);
  };

  const markRead = async (id: string) => {
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) return;
    setNotifs((prev) => prev.map((item) => (item.id === id ? { ...item, is_read: true } : item)));
    await markNotificationRead(token, id);
  };

  const today = notifs;
  const earlier: NotificationItem[] = [];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <Text style={styles.headerTitle}>Notifications</Text>
          <View style={styles.headerActions}>
            {unreadCount > 0 ? (
              <View style={styles.unreadCount}>
                <Text style={styles.unreadCountText}>{unreadCount}</Text>
              </View>
            ) : null}
            {unreadCount > 0 ? (
              <Pressable onPress={markAllRead} style={styles.readAllButton}>
                <Ionicons name="checkmark-done" size={14} color="#6B7280" />
                <Text style={styles.readAllText}>All read</Text>
              </Pressable>
            ) : null}
          </View>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => {
              setRefreshing(true);
              void loadNotifications();
            }}
          />
        }>
        {isLoading ? (
          <View style={styles.emptyWrap}>
            <ActivityIndicator size="small" color="#11181C" />
          </View>
        ) : null}

        {!isLoading && notifs.length === 0 ? (
          <View style={styles.emptyWrap}>
            <Ionicons name="notifications-outline" size={36} color="#9CA3AF" />
            <Text style={styles.emptyText}>No notifications yet</Text>
          </View>
        ) : null}

        {today.length > 0 ? <Text style={styles.sectionLabel}>TODAY</Text> : null}
        {today.map((item) => (
          <NotificationRow key={item.id} item={item} onRead={markRead} />
        ))}

        {earlier.length > 0 ? <Text style={styles.sectionLabel}>EARLIER</Text> : null}
        {earlier.map((item) => (
          <NotificationRow key={item.id} item={item} onRead={markRead} />
        ))}
      </ScrollView>

      <BottomNav showNotificationDot={unreadCount > 0} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  headerTop: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 20,
    fontWeight: '700',
  },
  headerActions: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  unreadCount: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderRadius: 10,
    height: 20,
    justifyContent: 'center',
    minWidth: 20,
    paddingHorizontal: 5,
  },
  unreadCountText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  readAllButton: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 4,
  },
  readAllText: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '500',
  },
  content: {
    paddingBottom: Layout.bottomNavHeight + 24,
  },
  sectionLabel: {
    color: '#9CA3AF',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 8,
  },
  row: {
    alignItems: 'center',
    borderBottomColor: '#F9FAFB',
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  rowRead: {
    backgroundColor: '#fff',
  },
  rowUnread: {
    backgroundColor: '#F9FAFB',
  },
  leftWrap: {
    position: 'relative',
  },
  typeBadge: {
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderColor: '#fff',
    borderRadius: 10,
    borderWidth: 2,
    bottom: -2,
    height: 20,
    justifyContent: 'center',
    position: 'absolute',
    right: -2,
    width: 20,
  },
  systemIconWrap: {
    alignItems: 'center',
    borderRadius: 20,
    height: 40,
    justifyContent: 'center',
    width: 40,
  },
  textWrap: {
    flex: 1,
    gap: 2,
  },
  previewText: {
    fontSize: 14,
    lineHeight: 20,
  },
  actorText: {
    color: '#11181C',
    fontWeight: '700',
  },
  previewMuted: {
    color: '#374151',
  },
  metaText: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  timeText: {
    color: '#D1D5DB',
    fontSize: 11,
  },
  unreadDot: {
    backgroundColor: '#11181C',
    borderRadius: 4,
    height: 8,
    width: 8,
  },
  emptyWrap: {
    alignItems: 'center',
    gap: 8,
    paddingVertical: 80,
  },
  emptyText: {
    color: '#9CA3AF',
    fontSize: 14,
  },
});
