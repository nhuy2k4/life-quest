import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { CommentSheet } from '@/components/lifequest/CommentSheet';
import { PostCard } from '@/components/lifequest/PostCard';
import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { useToast } from '@/contexts/ToastContext';
import { HttpError } from '@/services/httpClient';
import { getRecommendedQuests, type RecommendationQuestItem } from '@/services/recommendationService';
import { getFeed } from '@/services/socialService';
import type { Post, Quest } from '@/types';
import { StorageKeys, getItem, removeItem } from '@/utils/storage';

type FeedItem = {
  id: string;
  post: Post;
  attachedQuest?: Pick<Quest, 'title' | 'xpReward'> | null;
};



function HomeHeader({ onOpenComments }: { onOpenComments: () => void }) {
  return (
    <View style={styles.headerWrap}>
      <View style={styles.headerRow}>
        <Text style={styles.headerTitle}>LifeQuest</Text>
        <View style={styles.headerActions}>
          <Pressable style={styles.iconButton}>
            <Ionicons name="search-outline" size={20} color="#11181C" />
          </Pressable>
          <Pressable style={styles.iconButton} onPress={onOpenComments}>
            <Ionicons name="chatbubble-outline" size={20} color="#11181C" />
          </Pressable>
        </View>
      </View>
      <Text style={styles.headerSubtitle}>Discover quests and progress from your community.</Text>
    </View>
  );
}

function EndOfFeed() {
  return (
    <View style={styles.endWrap}>
      <View style={styles.endLine} />
      <Text style={styles.endText}>You&apos;re all caught up</Text>
    </View>
  );
}

import { ScrollView } from 'react-native';
import { QuestCard } from '@/components/lifequest/QuestCard';

function RecommendationHeader({
  recommendations,
  isLoading,
  error,
}: {
  recommendations: RecommendationQuestItem[];
  isLoading: boolean;
  error: string | null;
}) {
  if (isLoading) {
    return (
      <View style={styles.recommendationWrap}>
        <Text style={styles.recommendationTitle}>Recommended for You</Text>
        <ActivityIndicator size="small" color="#6366F1" style={{ alignSelf: 'flex-start', marginTop: 12 }} />
      </View>
    );
  }

  if (error || recommendations.length === 0) {
    return null; 
  }

  return (
    <View style={styles.recommendationWrap}>
      <Text style={styles.recommendationTitle}>Recommended for You</Text>
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingRight: 20, gap: 12, paddingTop: 4 }}
      >
        {recommendations.slice(0, 5).map((item) => {
          const normalizedDifficulty = item.difficulty?.toLowerCase();
          const difficulty =
            normalizedDifficulty === 'easy' || normalizedDifficulty === 'medium' || normalizedDifficulty === 'hard'
              ? normalizedDifficulty
              : undefined;
          // Adapt schema model into dynamic view compatible props
          const questAdapter: Quest = {
            id: item.id,
            title: item.title,
            description: item.description || item.rendered_text,
            xpReward: item.xp_reward,
            difficulty,
            imageUrl: item.image_url ?? undefined,
          };

          return (
            <View key={item.id} style={{ width: 260 }}>
              <QuestCard 
                quest={questAdapter} 
                onPress={(id) => router.push({ pathname: ROUTES.modal.questDetail, params: { questId: id } })} 
              />
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
}


import * as Location from 'expo-location';

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const { posts, setPosts } = usePostContext();
  const { showToast } = useToast();
  const [globalCommentOpen, setGlobalCommentOpen] = useState(false);
  const [recommendations, setRecommendations] = useState<RecommendationQuestItem[]>([]);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [feedPage, setFeedPage] = useState(1);
  const [hasNext, setHasNext] = useState(true);

  const contentPaddingBottom = useMemo(
    () => Layout.bottomNavHeight + Math.max(insets.bottom, Layout.bottomSafeAreaPadding) + 16,
    [insets.bottom]
  );

  const feedItems = useMemo<FeedItem[]>(() => {
    return posts.map((post) => ({ id: post.id, post }));
  }, [posts]);


  useEffect(() => {
    const hydratePendingPost = async () => {
      const pendingPost = await getItem<Post>(StorageKeys.newPost);
      if (!pendingPost) return;

      setPosts((prev) => {
        if (prev.some((item) => item.id === pendingPost.id)) {
          return prev;
        }
        return [pendingPost, ...prev];
      });

      await removeItem(StorageKeys.newPost);
    };

    void hydratePendingPost();
  }, [setPosts]);

  useEffect(() => {
    const loadRecommendations = async () => {
      setRecommendationError(null);
      setIsLoadingRecommendations(true);

      try {
        const token = await getItem<string>(StorageKeys.accessToken);
        if (!token) {
          setRecommendations([]);
          return;
        }

        let lat: number | undefined;
        let lng: number | undefined;

        // Attempt to dynamically capture physical hardware GPS coordinates to boost nearby results
        try {
          const { status } = await Location.requestForegroundPermissionsAsync();
          if (status === 'granted') {
            // Using balanced accuracy for blazing fast loading speed without battery drain
            // PERFORMANCE OPTIMIZATION: Use cache first for instant UI render
            let currentLocation = await Location.getLastKnownPositionAsync({});
            if (!currentLocation) {
              currentLocation = await Location.getCurrentPositionAsync({
                accuracy: Location.Accuracy.Low,
              });
            }

            if (currentLocation) {
              lat = currentLocation.coords.latitude;
              lng = currentLocation.coords.longitude;
            }

          }
        } catch (locErr) {
          console.log('Could not acquire location permissions or coords, defaulting to global recommendation.', locErr);
        }

        const items = await getRecommendedQuests(token, lat, lng);
        setRecommendations(items);

      } catch (error) {
        if (error instanceof HttpError) {
          setRecommendationError(error.message);
        } else {
          setRecommendationError('Could not load recommendations.');
        }
      } finally {
        setIsLoadingRecommendations(false);
      }
    };

    void loadRecommendations();
  }, []);

  const loadFeedPage = async (page: number, mode: 'refresh' | 'more') => {
    try {
      if (mode === 'refresh') {
        setIsRefreshing(true);
      } else {
        setIsLoadingMore(true);
      }

      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) {
        setPosts([]);
        setHasNext(false);
        return;
      }

      const response = await getFeed(token, page);
      setHasNext(response.hasNext);
      setFeedPage(response.page);

      setPosts((prev) => {
        if (page === 1) {
          return response.items;
        }

        const seen = new Set(prev.map((item) => item.id));
        const merged = [...prev];
        response.items.forEach((item) => {
          if (!seen.has(item.id)) {
            merged.push(item);
          }
        });
        return merged;
      });
    } catch (error) {
      showToast(error instanceof HttpError ? error.message : 'Could not load feed.');
    } finally {
      setIsRefreshing(false);
      setIsLoadingMore(false);
    }
  };

  useEffect(() => {
    void loadFeedPage(1, 'refresh');
  }, [setPosts]);

  return (
    <View style={styles.container}>
      <FlatList
        data={feedItems}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <PostCard post={item.post} attachedQuest={item.attachedQuest ?? null} />}
        refreshing={isRefreshing}
        onRefresh={() => loadFeedPage(1, 'refresh')}
        onEndReached={() => {
          if (!isLoadingMore && hasNext) {
            void loadFeedPage(feedPage + 1, 'more');
          }
        }}
        onEndReachedThreshold={0.3}
        ListHeaderComponent={
          <>
            <HomeHeader onOpenComments={() => setGlobalCommentOpen(true)} />
            <RecommendationHeader
              recommendations={recommendations}
              isLoading={isLoadingRecommendations}
              error={recommendationError}
            />
          </>
        }
        ListFooterComponent={
          isLoadingMore ? (
            <View style={styles.loadingMore}>
              <ActivityIndicator size="small" color="#11181C" />
            </View>
          ) : hasNext ? null : (
            <EndOfFeed />
          )
        }
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.listContent, { paddingBottom: contentPaddingBottom }]}
      />

      <BottomNav showNotificationDot />

      <CommentSheet
        open={globalCommentOpen}
        onClose={() => setGlobalCommentOpen(false)}
        totalComments={48}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flex: 1,
  },
  listContent: {
    paddingTop: 8,
  },
  loadingMore: {
    paddingVertical: 16,
  },
  headerWrap: {
    backgroundColor: '#fff',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    paddingBottom: 10,
    paddingHorizontal: 12,
    paddingTop: 6,
  },
  headerRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 24,
    fontWeight: '700',
  },
  headerActions: {
    flexDirection: 'row',
    gap: 6,
  },
  iconButton: {
    alignItems: 'center',
    borderRadius: 16,
    height: 32,
    justifyContent: 'center',
    width: 32,
  },
  headerSubtitle: {
    color: '#6B7280',
    fontSize: 12,
    marginTop: 4,
  },
  recommendationWrap: {
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  recommendationTitle: {
    color: '#11181C',
    fontSize: 15,
    fontWeight: '700',
  },
  recommendationCard: {
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
    borderRadius: 10,
    borderWidth: 1,
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  recommendationRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  recommendationCardTitle: {
    color: '#11181C',
    flex: 1,
    fontSize: 13,
    fontWeight: '600',
    marginRight: 8,
  },
  recommendationXp: {
    color: '#11181C',
    fontSize: 12,
    fontWeight: '700',
  },
  recommendationMeta: {
    color: '#6B7280',
    fontSize: 12,
  },
  recommendationError: {
    color: '#B91C1C',
    fontSize: 12,
  },
  endWrap: {
    alignItems: 'center',
    gap: 8,
    paddingVertical: 28,
  },
  endLine: {
    backgroundColor: '#E5E7EB',
    height: 1,
    width: 32,
  },
  endText: {
    color: '#9CA3AF',
    fontSize: 12,
  },
});
