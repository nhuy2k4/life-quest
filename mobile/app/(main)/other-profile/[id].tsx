import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { LevelProgressBar } from '@/components/lifequest/LevelProgressBar';
import { ProfileHeader } from '@/components/lifequest/ProfileHeader';
import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { useToast } from '@/contexts/ToastContext';
import { useUserContext } from '@/contexts/UserContext';
import { followUser, unfollowUser } from '@/services/socialService';
import { getUserProfile } from '@/services/userService';
import { BadgeGrid } from '@/components/lifequest/badges/BadgeGrid';
import { BadgeDetailModal } from '@/components/lifequest/badges/BadgeDetailModal';
import { fetchBadges } from '@/services/badgeService';
import type { BadgeItem } from '@/types/badge';
import type { UserProfile } from '@/types';
import { getLevelProgress } from '@/utils/levels';
import { getItem, StorageKeys } from '@/utils/storage';

type TabId = 'posts' | 'liked' | 'awards' | 'achievements';

function toUserProfile(data: Awaited<ReturnType<typeof getUserProfile>>): UserProfile {
  const progress = getLevelProgress(data.level_id, data.xp);

  return {
    id: data.id,
    username: data.username,
    displayName: data.display_name || data.username,
    bio: data.bio || undefined,
    avatarUrl: data.avatar_url || undefined,
    level: progress.levelId,
    currentXp: progress.currentXp,
    nextLevelXp: progress.nextLevelXp,
    isFollowing: data.is_following,
    isSelf: data.is_self,
    stats: {
      posts: data.stats.posts,
      streak: data.stats.streak,
      questsCompleted: data.stats.quests_completed,
      followers: data.stats.followers,
      following: data.stats.following,
    },
  };
}

export default function OtherProfileScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id: string | string[] }>();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const { posts, setPosts } = usePostContext();
  const { showToast } = useToast();
  const { currentUser, setCurrentUser } = useUserContext();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>('posts');
  const [awards, setAwards] = useState<Post[]>([]);
  const [isLoadingAwards, setIsLoadingAwards] = useState(false);
  const [badges, setBadges] = useState<BadgeItem[]>([]);
  const [isLoadingBadges, setIsLoadingBadges] = useState(false);
  const [selectedBadge, setSelectedBadge] = useState<BadgeItem | null>(null);

  const userPosts = useMemo(
    () => posts.filter((post) => post.author.id === id),
    [id, posts]
  );

  useEffect(() => {
    let mounted = true;

    const loadProfile = async () => {
      if (!id) return;
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      setIsLoading(true);
      try {
        const data = await getUserProfile(token, id);
        if (!mounted) return;
        const mapped = toUserProfile(data);
        setProfile(mapped);
        setIsFollowing(Boolean(mapped.isFollowing));
      } catch {
        if (mounted) {
          showToast('Could not load profile.');
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    void loadProfile();

    return () => {
      mounted = false;
    };
  }, [id]);

  useEffect(() => {
    let mounted = true;
    const loadAwards = async () => {
      if (!id || activeTab !== 'awards') return;
      setIsLoadingAwards(true);
      try {
        const token = await getItem<string>(StorageKeys.accessToken);
        if (!token) return;
        const { getUserAwards } = await import('@/services/socialService');
        const res = await getUserAwards(token, id, 1, 100);
        if (mounted) {
          setAwards(res.items);
        }
      } catch (err) {
        console.error('Failed to load awards', err);
      } finally {
        if (mounted) {
          setIsLoadingAwards(false);
        }
      }
    };
    void loadAwards();
    return () => {
      mounted = false;
    };
  }, [id, activeTab]);

  useEffect(() => {
    let mounted = true;
    const loadBadges = async () => {
      if (!id || activeTab !== 'achievements') return;
      setIsLoadingBadges(true);
      try {
        const token = await getItem<string>(StorageKeys.accessToken);
        if (!token) return;
        const res = await fetchBadges(token, undefined, id);
        if (mounted) {
          setBadges(res);
        }
      } catch (err) {
        console.error('Failed to load badges', err);
      } finally {
        if (mounted) {
          setIsLoadingBadges(false);
        }
      }
    };
    void loadBadges();
    return () => {
      mounted = false;
    };
  }, [id, activeTab]);

  const syncFeedFollowState = (nextFollowing: boolean) => {
    if (!id) return;
    setPosts((prev) =>
      prev.map((item) =>
        item.author.id === id
          ? {
              ...item,
              followedByMe: nextFollowing,
            }
          : item
      )
    );
  };

  const handleToggleFollow = async () => {
    if (!id || !profile || currentUser?.id === id) return;
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      showToast('Bạn chưa đăng nhập.');
      return;
    }

    const nextFollowing = !isFollowing;
    setIsFollowing(nextFollowing);
    setProfile((prev) =>
      prev
        ? {
            ...prev,
            isFollowing: nextFollowing,
            stats: {
              ...prev.stats,
              followers: Math.max(0, prev.stats.followers + (nextFollowing ? 1 : -1)),
            },
          }
        : prev
    );
    syncFeedFollowState(nextFollowing);
    setCurrentUser(
      currentUser
        ? {
            ...currentUser,
            stats: {
              ...currentUser.stats,
              following: Math.max(0, currentUser.stats.following + (nextFollowing ? 1 : -1)),
            },
          }
        : currentUser
    );

    try {
      if (nextFollowing) {
        await followUser(token, id);
      } else {
        await unfollowUser(token, id);
      }
    } catch {
      setIsFollowing(!nextFollowing);
      setProfile((prev) =>
        prev
          ? {
              ...prev,
              isFollowing: !nextFollowing,
              stats: {
                ...prev.stats,
                followers: Math.max(0, prev.stats.followers + (nextFollowing ? -1 : 1)),
              },
            }
          : prev
      );
      syncFeedFollowState(!nextFollowing);
      setCurrentUser(
        currentUser
          ? {
              ...currentUser,
              stats: {
                ...currentUser.stats,
                following: Math.max(0, currentUser.stats.following + (nextFollowing ? -1 : 1)),
              },
            }
          : currentUser
      );
      showToast('Follow failed.');
    }
  };

  if (isLoading && !profile) {
    return (
      <SafeAreaView style={styles.center} edges={['top']}>
        <ActivityIndicator size="small" color="#11181C" />
      </SafeAreaView>
    );
  }

  if (!profile) {
    return (
      <SafeAreaView style={styles.center} edges={['top']}>
        <Text style={styles.emptyText}>Profile data is not available.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <ProfileHeader
          user={profile}
          isSelf={Boolean(profile.isSelf)}
          isFollowing={isFollowing}
          onBack={() => router.back()}
          onToggleFollow={handleToggleFollow}
        />

        {!profile.isSelf ? (
          <View style={styles.messageActionWrap}>
            <Pressable
              style={styles.messageButton}
              onPress={() =>
                router.push({
                  pathname: ROUTES.modal.chatDetail as any,
                  params: { targetUserId: profile.id, username: profile.username },
                })
              }
            >
              <Ionicons name="chatbubble-outline" size={16} color="#fff" />
              <Text style={styles.messageButtonText}>Message</Text>
            </Pressable>
          </View>
        ) : null}

        <View style={styles.innerWrap}>
          <View style={styles.progressCard}>
            <LevelProgressBar
              level={profile.level}
              currentXp={profile.currentXp}
              nextLevelXp={profile.nextLevelXp}
            />
          </View>

          <View style={styles.statsRow}>
            <View style={styles.statCard}>
              <Ionicons name="camera-outline" size={18} color="#6B7280" />
              <Text style={styles.statValue}>{profile.stats.posts}</Text>
              <Text style={styles.statLabel}>Posts</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="trophy-outline" size={18} color="#6B7280" />
              <Text style={styles.statValue}>{profile.stats.questsCompleted}</Text>
              <Text style={styles.statLabel}>Quests</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="flame-outline" size={18} color="#6B7280" />
              <Text style={styles.statValue}>{profile.stats.streak}</Text>
              <Text style={styles.statLabel}>Streak</Text>
            </View>
          </View>
        </View>

        <View style={styles.tabBar}>
          <Pressable style={styles.tabButton} onPress={() => setActiveTab('posts')}>
            <Ionicons name="grid-outline" size={18} color={activeTab === 'posts' ? '#11181C' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'posts' ? styles.tabIndicatorActive : null]} />
          </Pressable>
          <Pressable style={styles.tabButton} onPress={() => setActiveTab('liked')}>
            <Ionicons name="heart-outline" size={18} color={activeTab === 'liked' ? '#11181C' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'liked' ? styles.tabIndicatorActive : null]} />
          </Pressable>
          <Pressable style={styles.tabButton} onPress={() => setActiveTab('awards')}>
            <Ionicons name="medal-outline" size={18} color={activeTab === 'awards' ? '#F59E0B' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'awards' ? styles.tabIndicatorActive : null]} />
          </Pressable>
          <Pressable style={styles.tabButton} onPress={() => setActiveTab('achievements')}>
            <Ionicons name="ribbon-outline" size={18} color={activeTab === 'achievements' ? '#11181C' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'achievements' ? styles.tabIndicatorActive : null]} />
          </Pressable>
        </View>

        {activeTab === 'posts' ? (
          userPosts.length > 0 ? (
            <View style={styles.grid}>
              {userPosts.map((post) => (
                <Pressable
                  key={post.id}
                  style={styles.gridItem}
                  onPress={() => router.push({ pathname: ROUTES.modal.postDetail as any, params: { postId: post.id } })}
                >
                  <ImageWithFallback uri={post.imageUrl || ''} width="100%" height={132} borderRadius={0} fallbackText="Photo" />
                </Pressable>
              ))}
            </View>
          ) : (
            <View style={styles.emptyWrap}>
              <Ionicons name="images-outline" size={32} color="#D1D5DB" />
              <Text style={styles.emptyText}>Chưa có bài đăng nào</Text>
            </View>
          )
        ) : null}

        {activeTab === 'liked' ? (
          <View style={styles.emptyWrap}>
            <Ionicons name="heart-outline" size={32} color="#D1D5DB" />
            <Text style={styles.emptyText}>Chưa có bài đã thích</Text>
          </View>
        ) : null}

        {activeTab === 'awards' && isLoadingAwards ? (
          <View style={styles.emptyWrap}>
            <ActivityIndicator size="small" color="#F59E0B" />
          </View>
        ) : null}

        {activeTab === 'awards' && !isLoadingAwards && awards.length > 0 ? (
          <View style={styles.grid}>
            {awards.map((post) => (
              <Pressable
                key={post.id}
                style={styles.gridItem}
                onPress={() => router.push({ pathname: ROUTES.modal.postDetail as any, params: { postId: post.id } })}
              >
                <ImageWithFallback uri={post.imageUrl || ''} width="100%" height={132} borderRadius={0} fallbackText="Award" />
                <View style={{ position: 'absolute', top: 4, right: 4, backgroundColor: 'rgba(0,0,0,0.5)', borderRadius: 12, padding: 4 }}>
                  <Ionicons name="medal" size={16} color="#F59E0B" />
                </View>
              </Pressable>
            ))}
          </View>
        ) : null}

        {activeTab === 'awards' && !isLoadingAwards && awards.length === 0 ? (
          <View style={styles.emptyWrap}>
            <Ionicons name="medal-outline" size={32} color="#D1D5DB" />
            <Text style={styles.emptyText}>Chưa có bài nào đoạt giải</Text>
          </View>
        ) : null}

        {activeTab === 'achievements' && isLoadingBadges ? (
          <View style={styles.emptyWrap}>
            <ActivityIndicator size="small" color="#6366F1" />
          </View>
        ) : null}

        {activeTab === 'achievements' && !isLoadingBadges && (
          (() => {
            const unlockedBadges = badges.filter((b) => b.is_unlocked);
            if (unlockedBadges.length === 0) {
              return (
                <View style={styles.emptyWrap}>
                  <Ionicons name="ribbon-outline" size={32} color="#D1D5DB" />
                  <Text style={styles.emptyText}>Chưa hoàn thành thành tựu nào</Text>
                </View>
              );
            }
            return (
              <BadgeGrid
                badges={unlockedBadges}
                onPressBadge={(badge) => setSelectedBadge(badge)}
              />
            );
          })()
        )}
      </ScrollView>

      <BottomNav />
      <BadgeDetailModal
        badge={selectedBadge}
        onClose={() => setSelectedBadge(null)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
  },
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    paddingBottom: Layout.bottomNavHeight + 20,
  },
  innerWrap: {
    gap: 12,
    paddingHorizontal: 16,
    paddingTop: 14,
  },
  messageActionWrap: {
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  messageButton: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderRadius: 12,
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    paddingVertical: 11,
  },
  messageButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
  },
  progressCard: {
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  statCard: {
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    flex: 1,
    gap: 2,
    paddingVertical: 10,
  },
  statValue: {
    color: '#11181C',
    fontSize: 16,
    fontWeight: '700',
  },
  statLabel: {
    color: '#6B7280',
    fontSize: 12,
  },
  tabBar: {
    borderBottomColor: '#E5E7EB',
    borderBottomWidth: 1,
    borderTopColor: '#E5E7EB',
    borderTopWidth: 1,
    flexDirection: 'row',
    marginTop: 16,
  },
  tabButton: {
    alignItems: 'center',
    flex: 1,
    gap: 6,
    paddingVertical: 10,
  },
  tabIndicator: {
    backgroundColor: 'transparent',
    borderRadius: 2,
    height: 2,
    width: 24,
  },
  tabIndicatorActive: {
    backgroundColor: '#11181C',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 16,
  },
  gridItem: {
    width: '33.33%',
  },
  emptyWrap: {
    alignItems: 'center',
    gap: 10,
    paddingVertical: 48,
  },
  emptyText: {
    color: '#9CA3AF',
    fontSize: 14,
  },
});
