import { Ionicons } from '@expo/vector-icons';
import { type Href, useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { LevelProgressBar } from '@/components/lifequest/LevelProgressBar';
import { ProfileHeader } from '@/components/lifequest/ProfileHeader';
import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { useUserContext } from '@/contexts/UserContext';

type TabId = 'photos' | 'liked' | 'achievements';

export default function ProfileScreen() {
  const router = useRouter();
  const { currentUser, isLoadingCurrentUser } = useUserContext();
  const { posts } = usePostContext();
  const [activeTab, setActiveTab] = useState<TabId>('photos');

  const profile = currentUser;

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

  const myPhotos = posts.filter((p) => p.author.id === profile.id);
  const myLikedPhotos = posts.filter((p) => p.isLiked);
  const completedQuests = myPhotos.filter((p) => Boolean(p.submissionId)).length;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
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

        <View style={styles.tabBar}>
          <Pressable style={styles.tabButton} onPress={() => setActiveTab('photos')}>
            <Ionicons name="grid-outline" size={18} color={activeTab === 'photos' ? '#11181C' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'photos' ? styles.tabIndicatorActive : null]} />
          </Pressable>
          <Pressable style={styles.tabButton} onPress={() => setActiveTab('liked')}>
            <Ionicons name="heart-outline" size={18} color={activeTab === 'liked' ? '#11181C' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'liked' ? styles.tabIndicatorActive : null]} />
          </Pressable>
          <Pressable style={styles.tabButton} onPress={() => setActiveTab('achievements')}>
            <Ionicons name="ribbon-outline" size={18} color={activeTab === 'achievements' ? '#11181C' : '#9CA3AF'} />
            <View style={[styles.tabIndicator, activeTab === 'achievements' ? styles.tabIndicatorActive : null]} />
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

        {activeTab === 'achievements' ? (
          <View style={styles.emptyTab}>
            <Ionicons name="ribbon-outline" size={32} color="#D1D5DB" />
            <Text style={styles.emptyTabText}>Chưa có thành tích nào</Text>
          </View>
        ) : null}

      </ScrollView>

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
  rewardToggle: {
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    padding: 12,
  },
  rewardIconWrap: {
    alignItems: 'center',
    backgroundColor: '#fff',
    borderColor: '#E5E7EB',
    borderRadius: 10,
    borderWidth: 1,
    height: 34,
    justifyContent: 'center',
    width: 34,
  },
  rewardTextWrap: {
    flex: 1,
  },
  rewardTitle: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  rewardSubtitle: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  rewardList: {
    gap: 8,
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
  emptyTab: {
    alignItems: 'center',
    gap: 10,
    paddingVertical: 48,
  },
  emptyTabText: {
    color: '#9CA3AF',
    fontSize: 14,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  achievementList: {
    gap: 8,
    padding: 14,
  },
  achievementItem: {
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    padding: 10,
  },
  achievementIconWrap: {
    alignItems: 'center',
    backgroundColor: '#E5E7EB',
    borderRadius: 10,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  achievementTextWrap: {
    flex: 1,
  },
  achievementTitle: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  achievementDesc: {
    color: '#6B7280',
    fontSize: 12,
  },
  achievementAgo: {
    color: '#9CA3AF',
    fontSize: 11,
  },
});
