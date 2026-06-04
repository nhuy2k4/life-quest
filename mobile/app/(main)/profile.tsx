import { Ionicons } from '@expo/vector-icons';
import { type Href, useRouter, useFocusEffect } from 'expo-router';
import { useState, useCallback, useMemo } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { LevelProgressBar } from '@/components/lifequest/LevelProgressBar';
import { ProfileHeader } from '@/components/lifequest/ProfileHeader';
import { AchievementFilterBar, type StatusFilter, type RarityFilter } from '@/components/lifequest/badges/AchievementFilterBar';
import { BadgeDetailModal } from '@/components/lifequest/badges/BadgeDetailModal';
import { BadgeGrid } from '@/components/lifequest/badges/BadgeGrid';
import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { useBadgeContext } from '@/contexts/BadgeContext';
import { usePostContext } from '@/contexts/PostContext';
import { useUserContext } from '@/contexts/UserContext';
import type { BadgeItem } from '@/types/badge';

type TabId = 'photos' | 'liked' | 'achievements';

export default function ProfileScreen() {
  const router = useRouter();
  const { currentUser, isLoadingCurrentUser, refreshCurrentUser } = useUserContext();
  const { posts } = usePostContext();
  const {
    badges,
    isLoading: isBadgesLoading,
    hasUnviewedBadge,
    newlyUnlockedBadge,
    markBadgesViewed,
    refreshBadges,
  } = useBadgeContext();

  const [activeTab, setActiveTab] = useState<TabId>('photos');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [rarityFilter, setRarityFilter] = useState<RarityFilter>('all');
  const [selectedBadge, setSelectedBadge] = useState<BadgeItem | null>(null);
  const profile = currentUser;

  const myPhotos = profile ? posts.filter((p) => p.author.id === profile.id) : [];
  const myLikedPhotos = posts.filter((p) => p.isLiked);
  const completedQuests = myPhotos.filter((p) => Boolean(p.submissionId)).length;

  // Filter badges by status and rarity
  const filteredBadges = useMemo(() => {
    return badges.filter((b) => {
      if (statusFilter === 'completed' && !b.is_unlocked) return false;
      if (statusFilter === 'locked' && b.is_unlocked) return false;
      if (statusFilter === 'in_progress' && (b.is_unlocked || (b.progress?.current || 0) === 0)) return false;
      if (rarityFilter !== 'all' && b.rarity !== rarityFilter) return false;
      return true;
    });
  }, [badges, statusFilter, rarityFilter]);

  const unlockedCount = badges.filter((b) => b.is_unlocked).length;

  useFocusEffect(
    useCallback(() => {
      void refreshCurrentUser();
    }, [refreshCurrentUser])
  );

  // Mark badges as viewed when switching to the achievements tab
  const handleTabChange = useCallback(
    (tab: TabId) => {
      setActiveTab(tab);
      if (tab === 'achievements' && hasUnviewedBadge) {
        markBadgesViewed();
      }
      if (tab === 'achievements') {
        void refreshBadges();
      }
    },
    [hasUnviewedBadge, markBadgesViewed, refreshBadges]
  );

  if (isLoadingCurrentUser && !currentUser) {
    return (
      <SafeAreaView style={styles.loadingContainer} edges={['top']}>
        <ActivityIndicator size="small" color="#11181C" />
      </SafeAreaView>
    );
  }

  if (!profile) {
    return (
      <SafeAreaView style={styles.loadingContainer} edges={['top']}>
        <Text style={styles.emptyTabText}>Profile data is not available.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
        stickyHeaderIndices={[]} // allow tab bar to scroll up with content
      >
        <ProfileHeader
          user={profile}
          isSelf
          onSettings={() => router.push(ROUTES.main.settings as Href)}
          onEdit={() => router.push(ROUTES.main.editProfile as Href)}
        />

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
              <Text style={styles.statValue}>{myPhotos.length}</Text>
              <Text style={styles.statLabel}>Posts</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="calendar-outline" size={18} color="#6B7280" />
              <Text style={styles.statValue}>{profile.stats.streak}</Text>
              <Text style={styles.statLabel}>Streak</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="trophy-outline" size={18} color="#6B7280" />
              <Text style={styles.statValue}>{completedQuests}</Text>
              <Text style={styles.statLabel}>Quests</Text>
            </View>
          </View>
        </View>

        {/* Tab bar */}
        <View style={styles.tabBar}>
          <Pressable style={styles.tabButton} onPress={() => handleTabChange('photos')}>
            <Ionicons name="grid-outline" size={18} color={activeTab === 'photos' ? '#11181C' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'photos' ? styles.tabIndicatorActive : null]} />
          </Pressable>
          <Pressable style={styles.tabButton} onPress={() => handleTabChange('liked')}>
            <Ionicons name="heart-outline" size={18} color={activeTab === 'liked' ? '#11181C' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'liked' ? styles.tabIndicatorActive : null]} />
          </Pressable>
          <Pressable style={styles.tabButton} onPress={() => handleTabChange('achievements')}>
            <View style={styles.tabIconWrap}>
              <Ionicons name="ribbon-outline" size={18} color={activeTab === 'achievements' ? '#6366F1' : '#9CA3AF'} />
              {hasUnviewedBadge && activeTab !== 'achievements' ? (
                <View style={styles.notifDot} />
              ) : null}
            </View>
            <View style={[styles.tabIndicator, activeTab === 'achievements' ? styles.tabIndicatorAchievements : null]} />
          </Pressable>
        </View>

        {/* Photos Tab */}
        {activeTab === 'photos' && myPhotos.length > 0 ? (
          <View style={styles.grid}>
            {myPhotos.map((post) => (
              <Pressable
                key={post.id}
                style={{ width: '33.33%' }}
                onPress={() => router.push({ pathname: ROUTES.modal.postDetail as any, params: { postId: post.id } })}
              >
                <ImageWithFallback uri={post.imageUrl || ''} width="100%" height={132} borderRadius={0} fallbackText="Photo" />
              </Pressable>
            ))}
          </View>
        ) : null}

        {activeTab === 'photos' && myPhotos.length === 0 ? (
          <View style={styles.emptyTab}>
            <Ionicons name="images-outline" size={32} color="#D1D5DB" />
            <Text style={styles.emptyTabText}>Chưa có bài đăng nào</Text>
          </View>
        ) : null}

        {/* Liked Tab */}
        {activeTab === 'liked' && myLikedPhotos.length > 0 ? (
          <View style={styles.grid}>
            {myLikedPhotos.map((post) => (
              <Pressable
                key={post.id}
                style={{ width: '33.33%' }}
                onPress={() => router.push({ pathname: ROUTES.modal.postDetail as any, params: { postId: post.id } })}
              >
                <ImageWithFallback uri={post.imageUrl || ''} width="100%" height={132} borderRadius={0} fallbackText="Liked" />
              </Pressable>
            ))}
          </View>
        ) : null}

        {activeTab === 'liked' && myLikedPhotos.length === 0 ? (
          <View style={styles.emptyTab}>
            <Ionicons name="heart-outline" size={32} color="#D1D5DB" />
            <Text style={styles.emptyTabText}>Chưa thích bài nào</Text>
          </View>
        ) : null}

        {/* Achievements / Badges Tab */}
        {activeTab === 'achievements' ? (
          <View style={styles.achievementsContainer}>
            <AchievementFilterBar
              statusFilter={statusFilter}
              rarityFilter={rarityFilter}
              onStatusChange={setStatusFilter}
              onRarityChange={setRarityFilter}
              totalCount={badges.length}
              unlockedCount={unlockedCount}
            />

            {/* Loading state */}
            {isBadgesLoading && badges.length === 0 ? (
              <View style={styles.emptyTab}>
                <ActivityIndicator size="small" color="#6366F1" />
                <Text style={styles.emptyTabText}>Loading badges…</Text>
              </View>
            ) : filteredBadges.length === 0 ? (
              <View style={styles.emptyTab}>
                <Ionicons name="ribbon-outline" size={32} color="#D1D5DB" />
                <Text style={styles.emptyTabTextLight}>No achievements found</Text>
              </View>
            ) : (
              <BadgeGrid
                badges={filteredBadges}
                newlyUnlockedIds={new Set(newlyUnlockedBadge ? [newlyUnlockedBadge.id] : [])}
                onPressBadge={setSelectedBadge}
              />
            )}
          </View>
        ) : null}
      </ScrollView>

      {/* Badge Detail Modal */}
      <BadgeDetailModal
        badge={selectedBadge}
        onClose={() => setSelectedBadge(null)}
      />

      <BottomNav />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
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
  tabIconWrap: {
    position: 'relative',
  },
  notifDot: {
    backgroundColor: '#EF4444',
    borderColor: '#fff',
    borderRadius: 5,
    borderWidth: 1.5,
    height: 9,
    position: 'absolute',
    right: -4,
    top: -2,
    width: 9,
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
  tabIndicatorAchievements: {
    backgroundColor: '#6366F1',
  },
  emptyTab: {
    alignItems: 'center',
    gap: 10,
    paddingVertical: 48,
  },
  emptyTabText: {
    color: '#9CA3AF',
    fontSize: 14,
  },
  emptyTabTextLight: {
    color: '#6B7280',
    fontSize: 14,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  // Achievements
  achievementsContainer: {
    backgroundColor: '#FAFAFA',
    minHeight: 300,
  },
});
