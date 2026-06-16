import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View, Modal, ScrollView } from 'react-native';
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
import { getAppLocation } from '@/services/locationService';
import { useUserContext } from '@/contexts/UserContext';
import { useBadgeContext } from '@/contexts/BadgeContext';

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
  const [locationStatus, setLocationStatus] = useState<'idle' | 'checking' | 'passed' | 'failed'>('idle');
  const { currentUser } = useUserContext();
  const { badges } = useBadgeContext();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [fullLeaderboard, setFullLeaderboard] = useState<EventLeaderboardItem[]>([]);
  const [loadingFull, setLoadingFull] = useState(false);

  const handleOpenLeaderboard = useCallback(async () => {
    setIsModalVisible(true);
    if (!eventId) return;
    setLoadingFull(true);
    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (token) {
        const result = await getEventLeaderboard(token, eventId, 50);
        setFullLeaderboard(result.items);
      }
    } catch (err) {
      console.error('Failed to load full leaderboard:', err);
    } finally {
      setLoadingFull(false);
    }
  }, [eventId]);

  const timeLeft = useMemo(() => (detail ? formatTimeLeft(detail.end_at) : ''), [detail]);

  const getBadgeName = useCallback((badgeId?: string | null) => {
    if (!badgeId) return null;
    const b = badges.find((x) => x.id === badgeId);
    return b ? b.name : 'Huy hiệu';
  }, [badges]);

  const getRewardForRank = useCallback((rank: number) => {
    if (!detail?.reward_config) return null;
    return detail.reward_config.find((tier) => tier.rank_from <= rank && rank <= tier.rank_to);
  }, [detail?.reward_config]);

  const rank1Reward = useMemo(() => getRewardForRank(1), [getRewardForRank]);
  const rank2Reward = useMemo(() => getRewardForRank(2), [getRewardForRank]);
  const rank3Reward = useMemo(() => getRewardForRank(3), [getRewardForRank]);
  const hasRewards = useMemo(() => !!(rank1Reward || rank2Reward || rank3Reward), [rank1Reward, rank2Reward, rank3Reward]);

  const openQuest = useCallback((questId: string) => {
    router.push({
      pathname: ROUTES.modal.questDetail as any,
      params: { questId, isEvent: 'true' },
    });
  }, [router]);

  const handleCheckin = useCallback(async () => {
    setLocationStatus('checking');
    try {
      const loc = await getAppLocation({ forceRefresh: true, maxAgeMs: 30000 });
      if (!loc) {
        setLocationStatus('failed');
        return;
      }
      const { latitude: lat, longitude: lng } = loc;
      if (lat >= 15.90 && lat <= 16.25 && lng >= 107.80 && lng <= 108.35) {
        setLocationStatus('passed');
      } else {
        setLocationStatus('failed');
      }
    } catch {
      setLocationStatus('failed');
    }
  }, []);

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
                <View>
                  <ImageWithFallback uri={detail?.banner_url ?? undefined} height={180} borderRadius={0} fallbackText="Event banner" />
                  {detail?.status === 'ended' ? (
                    <View style={styles.endedOverlay}>
                      <Ionicons name="flag" size={20} color="#fff" />
                      <Text style={styles.endedOverlayText}>Sự kiện đã kết thúc</Text>
                    </View>
                  ) : null}
                </View>
                <View style={styles.heroText}>
                  <Text style={[styles.statusText, detail?.status === 'ended' && styles.statusTextEnded]}>
                    {detail?.status === 'ended' ? 'Đã kết thúc' : timeLeft}
                  </Text>
                  <Text style={styles.title}>{detail?.title}</Text>
                  {detail?.description ? <Text style={styles.description}>{detail.description}</Text> : null}

                  {detail?.status === 'active' && detail.quests.length > 0 ? (
                    detail.is_joined ? (
                      <View style={styles.joinedBadge}>
                        <Ionicons name="checkmark-circle" size={18} color="#10B981" />
                        <Text style={styles.joinedBadgeText}>Đã tham gia</Text>
                      </View>
                    ) : (
                      <View style={{ gap: 12, marginTop: 8 }}>
                        <Text style={styles.joinHint}>
                          Sự kiện chỉ diễn ra ở Đà Nẵng, check in để tham gia.
                        </Text>

                        {locationStatus === 'idle' && (
                          <Pressable style={styles.joinButton} onPress={handleCheckin}>
                            <Ionicons name="location" size={16} color="#fff" />
                            <Text style={styles.joinButtonText}>Check in</Text>
                          </Pressable>
                        )}

                        {locationStatus === 'checking' && (
                          <View style={[styles.joinButton, { backgroundColor: '#E5E7EB' }]}>
                            <ActivityIndicator size="small" color="#4F46E5" />
                            <Text style={[styles.joinButtonText, { color: '#4F46E5' }]}>Đang kiểm tra...</Text>
                          </View>
                        )}

                        {locationStatus === 'passed' && (
                          <Pressable style={styles.joinButton} onPress={() => openQuest(detail.quests[0].id)}>
                            <Ionicons name="flash" size={16} color="#fff" />
                            <Text style={styles.joinButtonText}>Tham gia sự kiện</Text>
                          </Pressable>
                        )}

                        {locationStatus === 'failed' && (
                          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#FEF2F2', padding: 10, borderRadius: 8 }}>
                            <Ionicons name="warning" size={16} color="#DC2626" />
                            <Text style={{ color: '#DC2626', fontSize: 13, fontWeight: '500' }}>Bạn hiện không ở Đà Nẵng</Text>
                          </View>
                        )}
                      </View>
                    )
                  ) : null}

                  {detail?.status === 'ended' && detail.is_joined ? (
                    <View style={styles.joinedBadge}>
                      <Ionicons name="trophy" size={18} color="#D97706" />
                      <Text style={[styles.joinedBadgeText, { color: '#92400E' }]}>Bạn đã tham gia sự kiện này</Text>
                    </View>
                  ) : null}
                </View>
              </View>

              {hasRewards && (
                <View style={styles.rewardsSection}>
                  <Text style={styles.sectionTitle}>Phần thưởng Top 3</Text>
                  <View style={styles.rewardsContainer}>
                    {/* Top 2 Reward */}
                    {rank2Reward ? (
                      <View style={[styles.rewardCard, styles.silverCard]}>
                        <Ionicons name="trophy" size={20} color="#9CA3AF" />
                        <Text style={styles.rewardRankText}>Top 2</Text>
                        <Text style={styles.rewardXpText}>+{rank2Reward.bonus_xp} XP</Text>
                        {rank2Reward.badge_id ? (
                          <View style={styles.rewardBadgeContainer}>
                            <Ionicons name="ribbon" size={12} color="#8B5CF6" />
                            <Text numberOfLines={1} style={styles.rewardBadgeText}>
                              {getBadgeName(rank2Reward.badge_id)}
                            </Text>
                          </View>
                        ) : null}
                      </View>
                    ) : (
                      <View style={[styles.rewardCard, { opacity: 0.4 }]}>
                        <Ionicons name="trophy-outline" size={20} color="#D1D5DB" />
                        <Text style={styles.rewardRankText}>Top 2</Text>
                        <Text style={styles.rewardXpText}>-</Text>
                      </View>
                    )}

                    {/* Top 1 Reward */}
                    {rank1Reward ? (
                      <View style={[styles.rewardCard, styles.goldCard]}>
                        <Ionicons name="trophy" size={26} color="#D97706" />
                        <Text style={[styles.rewardRankText, styles.goldRankText]}>Top 1</Text>
                        <Text style={styles.rewardXpText}>+{rank1Reward.bonus_xp} XP</Text>
                        {rank1Reward.badge_id ? (
                          <View style={styles.rewardBadgeContainer}>
                            <Ionicons name="ribbon" size={12} color="#8B5CF6" />
                            <Text numberOfLines={1} style={styles.rewardBadgeText}>
                              {getBadgeName(rank1Reward.badge_id)}
                            </Text>
                          </View>
                        ) : null}
                      </View>
                    ) : (
                      <View style={[styles.rewardCard, styles.goldCard, { opacity: 0.4 }]}>
                        <Ionicons name="trophy-outline" size={26} color="#D97706" />
                        <Text style={[styles.rewardRankText, styles.goldRankText]}>Top 1</Text>
                        <Text style={styles.rewardXpText}>-</Text>
                      </View>
                    )}

                    {/* Top 3 Reward */}
                    {rank3Reward ? (
                      <View style={[styles.rewardCard, styles.bronzeCard]}>
                        <Ionicons name="trophy" size={20} color="#B45309" />
                        <Text style={styles.rewardRankText}>Top 3</Text>
                        <Text style={styles.rewardXpText}>+{rank3Reward.bonus_xp} XP</Text>
                        {rank3Reward.badge_id ? (
                          <View style={styles.rewardBadgeContainer}>
                            <Ionicons name="ribbon" size={12} color="#8B5CF6" />
                            <Text numberOfLines={1} style={styles.rewardBadgeText}>
                              {getBadgeName(rank3Reward.badge_id)}
                            </Text>
                          </View>
                        ) : null}
                      </View>
                    ) : (
                      <View style={[styles.rewardCard, { opacity: 0.4 }]}>
                        <Ionicons name="trophy-outline" size={20} color="#D1D5DB" />
                        <Text style={styles.rewardRankText}>Top 3</Text>
                        <Text style={styles.rewardXpText}>-</Text>
                      </View>
                    )}
                  </View>
                </View>
              )}

              <View style={styles.section}>
                <View style={styles.sectionHeaderRow}>
                  <Text style={styles.sectionTitle}>Leaderboard</Text>
                  {leaderboard.length > 0 && (
                    <Pressable onPress={handleOpenLeaderboard}>
                      <Text style={styles.seeAllText}>Xem tất cả</Text>
                    </Pressable>
                  )}
                </View>
                {leaderboard.length === 0 ? (
                  <Text style={styles.emptyText}>{detail?.status === 'ended' ? 'Chưa có kết quả.' : 'Chưa có ai tham gia.'}</Text>
                ) : (
                  leaderboard.map((item) => <LeaderboardRow key={`${item.rank}-${item.user.id}`} item={item} />)
                )}
              </View>

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Event quests</Text>
                {detail?.quests.map((quest) => {
                  const isEnded = detail.status === 'ended';
                  if (isEnded) {
                    return (
                      <View key={quest.id} style={[styles.questRow, styles.questRowDisabled]}>
                        <Ionicons name="flash-outline" size={16} color="#D1D5DB" />
                        <View style={styles.questBody}>
                          <Text style={[styles.questTitle, styles.questTitleDisabled]}>{quest.title}</Text>
                          <Text style={styles.questMeta}>{`+${quest.xp_reward} XP`}</Text>
                        </View>
                        <Ionicons name="lock-closed-outline" size={14} color="#D1D5DB" />
                      </View>
                    );
                  }
                  return (
                    <Pressable key={quest.id} style={styles.questRow} onPress={() => openQuest(quest.id)}>
                      <Ionicons name="flash-outline" size={16} color="#6B7280" />
                      <View style={styles.questBody}>
                        <Text style={styles.questTitle}>{quest.title}</Text>
                        <Text style={styles.questMeta}>{`+${quest.xp_reward} XP`}</Text>
                      </View>
                      <Ionicons name="chevron-forward" size={16} color="#D1D5DB" />
                    </Pressable>
                  );
                })}
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
      <Modal
        visible={isModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setIsModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Leaderboard</Text>
              <Pressable onPress={() => setIsModalVisible(false)} style={styles.closeButton}>
                <Ionicons name="close-circle" size={24} color="#6B7280" />
              </Pressable>
            </View>

            {loadingFull ? (
              <View style={styles.modalLoading}>
                <ActivityIndicator size="small" color="#4F46E5" />
              </View>
            ) : (
              <>
                <ScrollView 
                  style={styles.modalScroll}
                  contentContainerStyle={styles.modalScrollContent}
                  showsVerticalScrollIndicator={true}
                >
                  {fullLeaderboard.length === 0 ? (
                    <Text style={styles.emptyText}>Chưa có ai tham gia.</Text>
                  ) : (
                    fullLeaderboard.map((item) => {
                      const isMe = item.user.id === currentUser?.id;
                      return (
                        <View key={`${item.rank}-${item.user.id}`} style={[styles.leaderRow, isMe && styles.myRowHighlight]}>
                          <View style={styles.rankBadge}>
                            <Text style={styles.rankText}>{item.rank}</Text>
                          </View>
                          <ImageWithFallback uri={item.post.image_url ?? undefined} width={54} height={54} borderRadius={8} fallbackText="Post" />
                          <View style={styles.leaderBody}>
                            <Text style={styles.leaderName}>{item.user.username} {isMe && <Text style={styles.meTag}> (Bạn)</Text>}</Text>
                            <Text style={styles.leaderMeta}>
                              {item.post.is_deleted ? 'Post deleted' : `${item.post.like_count.toLocaleString()} likes`}
                            </Text>
                          </View>
                        </View>
                      );
                    })
                  )}
                </ScrollView>

                {currentUser && (
                  <View style={styles.pinnedUserRow}>
                    {(() => {
                      const myRankItem = fullLeaderboard.find(item => item.user.id === currentUser.id);
                      if (myRankItem) {
                        return (
                          <View style={styles.pinnedUserRowContent}>
                            <View style={[styles.rankBadge, styles.pinnedRankBadge]}>
                              <Text style={styles.pinnedRankText}>{myRankItem.rank}</Text>
                            </View>
                            <ImageWithFallback uri={myRankItem.post.image_url ?? undefined} width={46} height={46} borderRadius={8} fallbackText="Post" />
                            <View style={styles.leaderBody}>
                              <Text style={styles.pinnedUserName}>Bạn ({currentUser.username})</Text>
                              <Text style={styles.pinnedUserMeta}>
                                {myRankItem.post.is_deleted ? 'Post deleted' : `${myRankItem.post.like_count.toLocaleString()} likes`}
                              </Text>
                            </View>
                          </View>
                        );
                      } else {
                        return (
                          <View style={styles.pinnedUserRowContent}>
                            <View style={[styles.rankBadge, styles.pinnedRankBadgeUnranked]}>
                              <Text style={styles.pinnedRankTextUnranked}>-</Text>
                            </View>
                            <View style={styles.pinnedAvatarPlaceholder}>
                              <Ionicons name="person" size={20} color="#9CA3AF" />
                            </View>
                            <View style={styles.leaderBody}>
                              <Text style={styles.pinnedUserName}>Bạn ({currentUser.username})</Text>
                              <Text style={styles.pinnedUserMeta}>Chưa xếp hạng</Text>
                            </View>
                          </View>
                        );
                      }
                    })()}
                  </View>
                )}
              </>
            )}
          </View>
        </View>
      </Modal>
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
  endedOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0,0,0,0.55)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
  },
  endedOverlayText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
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
  statusTextEnded: {
    color: '#EF4444',
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
  joinedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 10,
    backgroundColor: '#ECFDF5',
    borderColor: '#A7F3D0',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexWrap: 'wrap',
  },
  joinedBadgeText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#059669',
    flex: 1,
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
  questRowDisabled: {
    opacity: 0.45,
  },
  questBody: {
    flex: 1,
  },
  questTitle: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  questTitleDisabled: {
    color: '#9CA3AF',
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
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  seeAllText: {
    color: '#4F46E5',
    fontSize: 14,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    width: '100%',
    maxWidth: 340,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    paddingBottom: 12,
    marginBottom: 12,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#11181C',
  },
  closeButton: {
    padding: 4,
  },
  modalLoading: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalScroll: {
    maxHeight: 330,
  },
  modalScrollContent: {
    gap: 12,
    paddingBottom: 12,
  },
  myRowHighlight: {
    backgroundColor: '#EEF2FF',
    borderRadius: 8,
    padding: 6,
  },
  meTag: {
    color: '#4F46E5',
    fontSize: 12,
    fontWeight: '600',
  },
  pinnedUserRow: {
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingTop: 12,
    marginTop: 8,
  },
  pinnedUserRowContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#F5F3FF',
    borderColor: '#DDD6FE',
    borderWidth: 1,
    borderRadius: 12,
    padding: 10,
  },
  pinnedRankBadge: {
    backgroundColor: '#8B5CF6',
  },
  pinnedRankBadgeUnranked: {
    backgroundColor: '#9CA3AF',
  },
  pinnedRankText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '800',
  },
  pinnedRankTextUnranked: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '800',
  },
  pinnedUserName: {
    color: '#1F2937',
    fontSize: 14,
    fontWeight: '700',
  },
  pinnedUserMeta: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '500',
  },
  pinnedAvatarPlaceholder: {
    width: 46,
    height: 46,
    borderRadius: 8,
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
    alignItems: 'center',
  },
  rewardsSection: {
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    padding: 16,
  },
  rewardsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    gap: 8,
    marginTop: 8,
  },
  rewardCard: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    borderColor: '#E5E7EB',
    borderWidth: 1,
    height: 105,
    justifyContent: 'center',
    gap: 4,
  },
  goldCard: {
    backgroundColor: '#FFFBEB',
    borderColor: '#FDE68A',
    borderWidth: 1.5,
    height: 120,
  },
  silverCard: {
    backgroundColor: '#F3F4F6',
    borderColor: '#E5E7EB',
  },
  bronzeCard: {
    backgroundColor: '#FEF3C7',
    borderColor: '#FCD34D',
  },
  rewardRankText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#4B5563',
  },
  goldRankText: {
    fontSize: 14,
    color: '#B45309',
  },
  rewardXpText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#11181C',
  },
  rewardBadgeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    backgroundColor: '#EEF2FF',
    borderColor: '#C7D2FE',
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 4,
    paddingVertical: 2,
    maxWidth: '100%',
  },
  rewardBadgeText: {
    fontSize: 9,
    fontWeight: '600',
    color: '#4F46E5',
  },
});
