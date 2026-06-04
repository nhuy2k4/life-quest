import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { PostCard } from '@/components/lifequest/PostCard';
import { ROUTES } from '@/constants/routes';
import { HttpError } from '@/services/httpClient';
import {
  getEventDetail,
  getEventLeaderboard,
  getEventPosts,
  type EventDetail,
  type EventLeaderboardItem,
} from '@/services/socialService';
import type { Post } from '@/types';
import { getItem, StorageKeys } from '@/utils/storage';

const LEADERBOARD_POLL_MS = 15000;

function formatTimeLeft(endAt: string): string {
  const diffMs = new Date(endAt).getTime() - Date.now();
  if (diffMs <= 0) return 'Ended';
  const hours = Math.floor(diffMs / (60 * 60 * 1000));
  const minutes = Math.ceil((diffMs % (60 * 60 * 1000)) / (60 * 1000));
  if (hours >= 24) return `${Math.ceil(hours / 24)}d left`;
  if (hours > 0) return `${hours}h ${minutes}m left`;
  return `${minutes}m left`;
}

function LeaderboardRow({ item }: { item: EventLeaderboardItem }) {
  return (
    <View style={styles.leaderRow}>
      <View style={styles.rankBadge}>
        <Text style={styles.rankText}>{item.rank}</Text>
      </View>
      <ImageWithFallback uri={item.post.image_url ?? undefined} width={54} height={54} borderRadius={8} fallbackText="Post" />
      <View style={styles.leaderBody}>
        <Text style={styles.leaderName}>{item.user.username}</Text>
        <Text style={styles.leaderMeta}>
          {item.post.is_deleted ? 'Post deleted' : `${item.post.like_count.toLocaleString()} likes`}
        </Text>
      </View>
    </View>
  );
}

export default function EventDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const eventId = typeof params.eventId === 'string' ? params.eventId : undefined;
  const [detail, setDetail] = useState<EventDetail | null>(null);
  const [leaderboard, setLeaderboard] = useState<EventLeaderboardItem[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const timeLeft = useMemo(() => (detail ? formatTimeLeft(detail.end_at) : ''), [detail]);

  const openQuest = useCallback((questId: string) => {
    router.push({
      pathname: ROUTES.modal.questDetail as any,
      params: { questId },
    });
  }, [router]);

  const loadEvent = useCallback(async (mode: 'initial' | 'refresh' = 'initial') => {
    if (!eventId) return;
    if (mode === 'refresh') setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) {
        setDetail(null);
        setLeaderboard([]);
        setPosts([]);
        return;
      }

      const [detailResult, leaderboardResult, postsResult] = await Promise.all([
        getEventDetail(token, eventId),
        getEventLeaderboard(token, eventId, 5),
        getEventPosts(token, eventId, 1, 30),
      ]);

      setDetail(detailResult);
      setLeaderboard(leaderboardResult.items);
      setPosts(postsResult.items);
    } catch (loadError) {
      setError(loadError instanceof HttpError ? loadError.message : 'Could not load event.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [eventId]);

  useEffect(() => {
    void loadEvent('initial');
  }, [loadEvent]);

  useEffect(() => {
    if (!eventId || detail?.status === 'ended') return;
    const timer = setInterval(() => void loadEvent('refresh'), LEADERBOARD_POLL_MS);
    return () => clearInterval(timer);
  }, [detail?.status, eventId, loadEvent]);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.iconButton}>
          <Ionicons name="arrow-back" size={20} color="#11181C" />
        </Pressable>
        <Text style={styles.headerTitle}>Event</Text>
        <View style={styles.iconButton} />
      </View>

      {loading ? (
        <View style={styles.centerPanel}>
          <ActivityIndicator size="small" color="#11181C" />
        </View>
      ) : error ? (
        <View style={styles.centerPanel}>
          <Ionicons name="alert-circle-outline" size={28} color="#D1D5DB" />
          <Text style={styles.emptyText}>{error}</Text>
        </View>
      ) : (
        <FlatList
          data={posts}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <PostCard post={item} />}
          refreshing={refreshing}
          onRefresh={() => void loadEvent('refresh')}
          ListHeaderComponent={
            <>
              <View style={styles.hero}>
                <ImageWithFallback uri={detail?.banner_url ?? undefined} height={180} borderRadius={0} fallbackText="Event banner" />
                <View style={styles.heroText}>
                  <Text style={styles.statusText}>{detail?.status === 'ended' ? 'Ended' : timeLeft}</Text>
                  <Text style={styles.title}>{detail?.title}</Text>
                  {detail?.description ? <Text style={styles.description}>{detail.description}</Text> : null}
                  {detail?.status === 'active' && detail.quests.length > 0 ? (
                    <Pressable style={styles.joinButton} onPress={() => openQuest(detail.quests[0].id)}>
                      <Ionicons name="flash" size={16} color="#fff" />
                      <Text style={styles.joinButtonText}>Join Event</Text>
                    </Pressable>
                  ) : null}
                  {detail?.status === 'active' ? (
                    <Text style={styles.joinHint}>Complete any event quest and post it to enter the leaderboard.</Text>
                  ) : null}
                </View>
              </View>

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Top 5</Text>
                {leaderboard.length === 0 ? (
                  <Text style={styles.emptyText}>No entries yet.</Text>
                ) : (
                  leaderboard.map((item) => <LeaderboardRow key={`${item.rank}-${item.user.id}`} item={item} />)
                )}
              </View>

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Event quests</Text>
                {detail?.quests.map((quest) => (
                  <Pressable key={quest.id} style={styles.questRow} onPress={() => openQuest(quest.id)}>
                    <Ionicons name="flash-outline" size={16} color="#6B7280" />
                    <View style={styles.questBody}>
                      <Text style={styles.questTitle}>{quest.title}</Text>
                      <Text style={styles.questMeta}>{`+${quest.xp_reward} XP`}</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={16} color="#D1D5DB" />
                  </Pressable>
                ))}
              </View>

              <View style={styles.postsHeader}>
                <Text style={styles.sectionTitle}>Entries</Text>
              </View>
            </>
          }
          ListEmptyComponent={<Text style={styles.emptyPosts}>No event posts yet.</Text>}
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flex: 1,
  },
  header: {
    alignItems: 'center',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  iconButton: {
    alignItems: 'center',
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 16,
    fontWeight: '600',
  },
  centerPanel: {
    alignItems: 'center',
    flex: 1,
    gap: 8,
    justifyContent: 'center',
    padding: 24,
  },
  hero: {
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
  },
  heroText: {
    gap: 6,
    padding: 16,
  },
  statusText: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  title: {
    color: '#11181C',
    fontSize: 24,
    fontWeight: '800',
  },
  description: {
    color: '#6B7280',
    fontSize: 14,
    lineHeight: 20,
  },
  joinButton: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderRadius: 12,
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    marginTop: 8,
    paddingVertical: 12,
  },
  joinButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '800',
  },
  joinHint: {
    color: '#9CA3AF',
    fontSize: 12,
    lineHeight: 17,
  },
  section: {
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    gap: 10,
    padding: 16,
  },
  sectionTitle: {
    color: '#11181C',
    fontSize: 16,
    fontWeight: '800',
  },
  leaderRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  rankBadge: {
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 999,
    height: 28,
    justifyContent: 'center',
    width: 28,
  },
  rankText: {
    color: '#11181C',
    fontSize: 12,
    fontWeight: '800',
  },
  leaderBody: {
    flex: 1,
  },
  leaderName: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  leaderMeta: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  questRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  questBody: {
    flex: 1,
  },
  questTitle: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  questMeta: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  postsHeader: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  emptyText: {
    color: '#9CA3AF',
    fontSize: 13,
  },
  emptyPosts: {
    color: '#9CA3AF',
    fontSize: 13,
    padding: 16,
    textAlign: 'center',
  },
});
