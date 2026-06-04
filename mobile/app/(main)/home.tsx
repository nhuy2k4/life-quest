import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, Keyboard, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { CommentSheet } from '@/components/lifequest/CommentSheet';
import { PostCard } from '@/components/lifequest/PostCard';
import { QuestCard } from '@/components/lifequest/QuestCard';
import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { useUserContext } from '@/contexts/UserContext';
import { useToast } from '@/contexts/ToastContext';
import { HttpError } from '@/services/httpClient';
import {
  getRecommendedQuests,
  logRecommendationEvent,
  type RecommendationQuestItem,
  type RecommendationSection,
  type RecommendationSectionKey,
} from '@/services/recommendationService';
import { getAppLocation } from '@/services/locationService';
import { getActiveEvents, getFeed, type EventListItem } from '@/services/socialService';
import type { Post, Quest } from '@/types';
import { StorageKeys, getItem, removeItem, setItem } from '@/utils/storage';

type FeedItem = {
  id: string;
  post: Post;
  attachedQuest?: Pick<Quest, 'title' | 'xpReward'> | null;
};

type HomeTab = 'for_you' | 'explore' | 'active';
type RecommendationQuestEntry = {
  key: string;
  item: RecommendationQuestItem;
  sectionKey: RecommendationSectionKey;
  rank: number;
};

const RECENT_POST_WINDOW_MS = 10 * 60 * 1000;
const OLD_POST_BOOST_SCORE = 50;
const OLD_POST_ENGAGEMENT_BOOST = 25;

function mergePostsById(primary: Post[], secondary: Post[]): Post[] {
  const merged = [...primary];

  const findMatchIndex = (candidate: Post) =>
    merged.findIndex((item) => {
      if (item.id === candidate.id) return true;
      if (item.submissionId && candidate.submissionId && item.submissionId === candidate.submissionId) return true;
      return false;
    });

  secondary.forEach((item) => {
    const existingIndex = findMatchIndex(item);
    if (existingIndex !== -1) {
      const existing = merged[existingIndex];
      const sameSubmissionWithDifferentPost =
        Boolean(existing.submissionId && item.submissionId && existing.submissionId === item.submissionId && existing.id !== item.id);

      merged[existingIndex] = {
        ...item,
        ...existing,
        id: sameSubmissionWithDifferentPost ? item.id : existing.id,
        createdAt: sameSubmissionWithDifferentPost ? item.createdAt : existing.createdAt,
      };
      return;
    }
    merged.push(item);
  });

  return merged;
}

function isNearbyRecommendedPost(post: Post): boolean {
  return post.recommendationReasons?.some((reason) => reason.toLowerCase().includes('near')) ?? false;
}

function getPostTimestamp(post: Post): number {
  const created = Date.parse(post.createdAt);
  return Number.isNaN(created) ? 0 : created;
}

function isPostedToday(post: Post): boolean {
  const created = getPostTimestamp(post);
  if (created === 0) return false;

  const createdDate = new Date(created);
  const now = new Date();
  return (
    createdDate.getFullYear() === now.getFullYear() &&
    createdDate.getMonth() === now.getMonth() &&
    createdDate.getDate() === now.getDate()
  );
}

function getEngagementScore(post: Post): number {
  return (post.likesCount ?? 0) * 3 + (post.commentsCount ?? 0) * 5;
}

function getMixScore(post: Post, seed: number): number {
  const source = `${post.id}:${seed}`;
  let hash = 2166136261;

  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
}

function isBoostedOldPost(post: Post): boolean {
  if (isPostedToday(post)) return false;
  return (post.recommendationScore ?? 0) >= OLD_POST_BOOST_SCORE || getEngagementScore(post) >= OLD_POST_ENGAGEMENT_BOOST;
}

function sortPostsForFeed(posts: Post[], pinnedPostId?: string | null, mixSeed = 0): Post[] {
  return [...posts].sort((a, b) => {
    const bPinned = pinnedPostId && b.id === pinnedPostId ? 1 : 0;
    const aPinned = pinnedPostId && a.id === pinnedPostId ? 1 : 0;
    if (bPinned !== aPinned) return bPinned - aPinned;

    const bTodayOrBoosted = isPostedToday(b) || isBoostedOldPost(b) ? 1 : 0;
    const aTodayOrBoosted = isPostedToday(a) || isBoostedOldPost(a) ? 1 : 0;
    if (bTodayOrBoosted !== aTodayOrBoosted) return bTodayOrBoosted - aTodayOrBoosted;

    const bNearby = isNearbyRecommendedPost(b) ? 1 : 0;
    const aNearby = isNearbyRecommendedPost(a) ? 1 : 0;
    if (bNearby !== aNearby) return bNearby - aNearby;

    const bMix = getMixScore(b, mixSeed);
    const aMix = getMixScore(a, mixSeed);
    if (bMix !== aMix) return bMix - aMix;

    const bScore = b.recommendationScore ?? 0;
    const aScore = a.recommendationScore ?? 0;
    if (bScore !== aScore) return bScore - aScore;

    const bEngagement = getEngagementScore(b);
    const aEngagement = getEngagementScore(a);
    if (bEngagement !== aEngagement) return bEngagement - aEngagement;

    return getPostTimestamp(b) - getPostTimestamp(a);
  });
}


function EndOfFeed() {
  return (
    <View style={styles.endWrap}>
      <View style={styles.endLine} />
      <Text style={styles.endText}>You&apos;re all caught up</Text>
    </View>
  );
}

function HomeTabs({
  activeTab,
  onChange,
  onSearch,
  onMessages,
}: {
  activeTab: HomeTab;
  onChange: (tab: HomeTab) => void;
  onSearch: () => void;
  onMessages: () => void;
}) {
  const tabs: { key: HomeTab; label: string }[] = [
    { key: 'for_you', label: 'For You' },
    { key: 'explore', label: 'Explore' },
    { key: 'active', label: 'Following' },
  ];

  return (
    <View style={styles.homeHeaderWrap}>
      <View style={styles.homeTopBar}>
        <Pressable accessibilityLabel="Search posts" onPress={onSearch} style={styles.headerIconButton}>
          <Ionicons name="search-outline" size={28} color="#11181C" />
        </Pressable>
        <Text style={styles.homeTitle}>LifeQuest</Text>
        <Pressable accessibilityLabel="Messages" onPress={onMessages} style={styles.headerIconButton}>
          <Ionicons name="chatbubble-ellipses-outline" size={28} color="#11181C" />
        </Pressable>
      </View>

      <View style={styles.homeTabsWrap}>
        {tabs.map((tab) => {
          const isActive = tab.key === activeTab;
          return (
            <Pressable
              key={tab.key}
              onPress={() => onChange(tab.key)}
              style={[styles.homeTab, isActive ? styles.homeTabActive : null]}
            >
              <Text style={[styles.homeTabText, isActive ? styles.homeTabTextActive : null]}>{tab.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function ActiveEventStrip({ events }: { events: EventListItem[] }) {
  if (events.length === 0) return null;

  return (
    <View style={styles.eventStrip}>
      <Text style={styles.eventStripTitle}>Live events</Text>
      <FlatList
        data={events}
        horizontal
        keyExtractor={(item) => item.id}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.eventStripList}
        renderItem={({ item }) => {
          const endTime = new Date(item.end_at).getTime();
          const hoursLeft = Math.max(0, Math.ceil((endTime - Date.now()) / (60 * 60 * 1000)));
          return (
            <Pressable
              style={styles.eventPill}
              onPress={() =>
                router.push({
                  pathname: ROUTES.modal.eventDetail as any,
                  params: { eventId: item.id },
                })
              }
            >
              <Ionicons name="trophy-outline" size={15} color="#11181C" />
              <View style={styles.eventPillTextWrap}>
                <Text style={styles.eventPillTitle} numberOfLines={1}>{item.title}</Text>
                <Text style={styles.eventPillMeta}>{hoursLeft > 0 ? `${hoursLeft}h left` : 'Ending soon'}</Text>
              </View>
            </Pressable>
          );
        }}
      />
    </View>
  );
}

function RecommendationQuestList({
  requestId,
  entries,
  emptyText,
}: {
  requestId: string | null;
  entries: RecommendationQuestEntry[];
  emptyText: string;
}) {
  if (entries.length === 0) {
    return (
      <View style={styles.emptyPanel}>
        <Ionicons name="compass-outline" size={28} color="#D1D5DB" />
        <Text style={styles.emptyPanelText}>{emptyText}</Text>
      </View>
    );
  }

  return (
    <View style={styles.questList}>
      {entries.map(({ key, item, sectionKey, rank }) => {
              const normalizedDifficulty = item.difficulty?.toLowerCase();
              const difficulty =
                normalizedDifficulty === 'easy' || normalizedDifficulty === 'medium' || normalizedDifficulty === 'hard'
                  ? normalizedDifficulty
                  : undefined;
              const questAdapter: Quest = {
                id: item.id,
                title: item.title,
                description: item.reasons[0] || item.description || item.rendered_text,
                xpReward: item.xp_reward,
                difficulty,
                imageUrl: item.image_url ?? undefined,
              };

              return (
                <View key={key} style={styles.questListItem}>
                  <QuestCard
                    quest={questAdapter}
                    onPress={async (id) => {
                      const token = await getItem<string>(StorageKeys.accessToken);
                      if (token && requestId) {
                        try {
                          await logRecommendationEvent(token, {
                            request_id: requestId,
                            quest_id: id,
                            event: 'clicked',
                            section: sectionKey,
                            rank,
                            final_score: item.final_score,
                            reasons: item.reasons,
                            score_breakdown: item.score_breakdown,
                          });
                        } catch {
                          // Recommendation analytics should never block navigation.
                        }
                      }
                      router.push({
                        pathname: ROUTES.modal.questDetail,
                        params: {
                          questId: id,
                          poiId: item.poi_id ?? undefined,
                          poiName: item.poi_name ?? undefined,

                          recommendationRequestId: requestId ?? undefined,
                          recommendationSection: sectionKey,
                          recommendationRank: String(rank),
                          recommendationScore: String(item.final_score),
                          recommendationReasons: JSON.stringify(item.reasons),
                          recommendationBreakdown: JSON.stringify(item.score_breakdown),
                        },
                      });
                    }}
                  />
                </View>
              );
            })}
    </View>
  );
}

function extractHashtags(text: string): string[] {
  const matches = text.match(/#[A-Za-z0-9_-]+/g);
  if (!matches) return [];
  return matches.map((tag) => tag.toLowerCase());
}

function buildSuggestions(posts: Post[], query: string): string[] {
  const trimmed = query.trim().toLowerCase();
  if (trimmed.length === 0) return [];

  const pool: string[] = [];
  posts.forEach((post) => {
    if (post.quest?.title) pool.push(post.quest.title);
    if (post.location) pool.push(post.location);
    extractHashtags(post.caption ?? '').forEach((tag) => pool.push(tag));
  });

  const seen = new Set<string>();
  const suggestions: string[] = [];
  pool.forEach((item) => {
    const text = item.trim();
    if (!text) return;
    const lower = text.toLowerCase();
    if (!lower.includes(trimmed)) return;
    if (seen.has(lower)) return;
    seen.add(lower);
    suggestions.push(text);
  });

  return suggestions.slice(0, 8);
}

function SearchModal({
  visible,
  onClose,
  sourcePosts,
}: {
  visible: boolean;
  onClose: () => void;
  sourcePosts: Post[];
}) {
  const [query, setQuery] = useState('');
  const [committedQuery, setCommittedQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'top' | 'users' | 'quests' | 'locations' | 'hashtags'>('top');
  const [history, setHistory] = useState<string[]>([]);
  const inputRef = useRef<TextInput | null>(null);

  useEffect(() => {
    if (!visible) {
      setQuery('');
      setCommittedQuery('');
    }
  }, [visible]);

  useEffect(() => {
    if (!visible) return;
    const loadHistory = async () => {
      const stored = await getItem<string[]>(StorageKeys.searchHistory);
      setHistory(stored ?? []);
    };
    void loadHistory();
  }, [visible]);

  useEffect(() => {
    if (query.trim().length === 0) {
      setCommittedQuery('');
    }
  }, [query]);

  useEffect(() => {
    setActiveTab('top');
  }, [committedQuery]);

  const commitSearch = (value: string) => {
    const trimmed = value.trim();
    setCommittedQuery(trimmed);
    inputRef.current?.blur();
    Keyboard.dismiss();
    if (trimmed.length < 2) return;

    setHistory((prev) => {
      const normalized = trimmed.toLowerCase();
      const next = [trimmed, ...prev.filter((item) => item.toLowerCase() !== normalized)].slice(0, 8);
      void setItem(StorageKeys.searchHistory, next);
      return next;
    });
  };

  const clearHistory = async () => {
    setHistory([]);
    await removeItem(StorageKeys.searchHistory);
  };

  const removeHistoryItem = async (value: string) => {
    setHistory((prev) => {
      const next = prev.filter((item) => item !== value);
      void setItem(StorageKeys.searchHistory, next);
      return next;
    });
  };

  const suggestions = useMemo(() => buildSuggestions(sourcePosts, query), [query, sourcePosts]);

  const results = useMemo(() => {
    const trimmed = committedQuery.trim();
    if (!visible || trimmed.length < 2) return [];

    const terms = trimmed.split(/\s+/).map((term) => term.toLowerCase()).filter(Boolean);
    if (terms.length === 0) return [];

    return sourcePosts.filter((post) => {
      const caption = post.caption ?? '';
      const questTitle = post.quest?.title ?? '';
      const questDesc = post.quest?.description ?? '';
      const location = post.location ?? '';
      const hashtags = extractHashtags(caption);
      const tagText = hashtags.map((tag) => tag.slice(1)).join(' ');
      const searchable = [caption, questTitle, questDesc, location, tagText].join(' ').toLowerCase();

      return terms.some((term) => {
        if (term.startsWith('#')) {
          return hashtags.includes(term);
        }
        return searchable.includes(term);
      });
    });
  }, [committedQuery, sourcePosts, visible]);

  const filteredResults = useMemo(() => {
    const trimmed = committedQuery.trim();
    if (!visible || trimmed.length < 2) return [];
    if (activeTab === 'top') return results;

    const terms = trimmed
      .split(/\s+/)
      .map((term) => term.toLowerCase())
      .filter(Boolean)
      .map((term) => (term.startsWith('#') ? term.slice(1) : term));

    return results.filter((post) => {
      const caption = post.caption ?? '';
      const questTitle = post.quest?.title ?? '';
      const questDesc = post.quest?.description ?? '';
      const location = post.location ?? '';
      const hashtags = extractHashtags(caption).map((tag) => tag.slice(1));
      const username = post.author?.username ?? '';

      const haystack = (text: string) => text.toLowerCase();

      switch (activeTab) {
        case 'users':
          return terms.some((term) => haystack(username).includes(term));
        case 'quests':
          return terms.some((term) =>
            haystack(`${questTitle} ${questDesc}`).includes(term)
          );
        case 'locations':
          return terms.some((term) => haystack(location).includes(term));
        case 'hashtags':
          return terms.some((term) => hashtags.some((tag) => tag.toLowerCase().includes(term)));
        default:
          return false;
      }
    });
  }, [activeTab, committedQuery, results, visible]);

  if (!visible) return null;

  return (
    <View style={styles.searchModal}>
      <View style={styles.searchHeader}>
        <Pressable onPress={onClose} style={styles.searchBack}>
          <Ionicons name="arrow-back" size={20} color="#11181C" />
        </Pressable>
        <View style={styles.searchInputWrap}>
          <TextInput
              ref={inputRef}
            value={query}
            onChangeText={setQuery}
            placeholder="Search current feed"
            placeholderTextColor="#9CA3AF"
            autoCapitalize="none"
            autoFocus
            returnKeyType="search"
            onSubmitEditing={() => commitSearch(query)}
            style={styles.searchInput}
          />
            {query.trim().length > 0 ? (
              <Pressable onPress={() => setQuery('')} style={styles.clearButton}>
                <Ionicons name="close-circle" size={18} color="#9CA3AF" />
              </Pressable>
            ) : null}
        </View>
          <Pressable onPress={() => commitSearch(query)} style={styles.searchCancel}>
          <Text style={styles.searchCancelText}>Tìm kiếm</Text>
        </Pressable>
      </View>

      {committedQuery.trim().length < 2 ? (
        <View style={styles.suggestionList}>
          {query.trim().length === 0 ? (
            history.length === 0 ? (
              <View style={styles.emptyPanel}>
                <Ionicons name="time-outline" size={28} color="#D1D5DB" />
                <Text style={styles.emptyPanelText}>Chưa có lịch sử tìm kiếm.</Text>
              </View>
            ) : (
              <>
                <View style={styles.historyHeader}>
                  <Text style={styles.historyTitle}>Tìm kiếm gần đây</Text>
                  <Pressable onPress={clearHistory} style={styles.historyClear}>
                    <Text style={styles.historyClearText}>Xóa lịch sử</Text>
                  </Pressable>
                </View>
                {history.map((item) => (
                  <View key={item} style={styles.historyRow}>
                    <Pressable
                      onPress={() => {
                        setQuery(item);
                        commitSearch(item);
                      }}
                      style={styles.suggestionRow}
                    >
                      <Ionicons name="time-outline" size={18} color="#9CA3AF" />
                      <Text style={styles.suggestionText}>{item}</Text>
                    </Pressable>
                    <Pressable onPress={() => removeHistoryItem(item)} style={styles.historyDelete}>
                      <Ionicons name="close" size={16} color="#9CA3AF" />
                    </Pressable>
                  </View>
                ))}
              </>
            )
          ) : suggestions.length === 0 ? (
            <View style={styles.emptyPanel}>
              <Ionicons name="sparkles-outline" size={28} color="#D1D5DB" />
              <Text style={styles.emptyPanelText}>No suggestions yet.</Text>
            </View>
          ) : (
            suggestions.map((item) => (
              <Pressable
                key={item}
                onPress={() => {
                  setQuery(item);
                    commitSearch(item);
                }}
                style={styles.suggestionRow}
              >
                <Ionicons name="search-outline" size={18} color="#9CA3AF" />
                <Text style={styles.suggestionText}>{item}</Text>
              </Pressable>
            ))
          )}
        </View>
      ) : (
        <>
          <View style={styles.searchTabs}>
            {(
              [
                { key: 'top', label: 'Top' },
                { key: 'users', label: 'Người dùng' },
                { key: 'quests', label: 'Nhiệm vụ' },
                { key: 'locations', label: 'Địa điểm' },
                { key: 'hashtags', label: 'Hashtag' },
              ] as const
            ).map((tab) => {
              const isActive = tab.key === activeTab;
              return (
                <Pressable
                  key={tab.key}
                  onPress={() => setActiveTab(tab.key)}
                  style={[styles.searchTab, isActive ? styles.searchTabActive : null]}
                >
                  <Text style={[styles.searchTabText, isActive ? styles.searchTabTextActive : null]}>{tab.label}</Text>
                </Pressable>
              );
            })}
          </View>
          <FlatList
            data={filteredResults}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => <PostCard post={item} />}
            ListEmptyComponent={
              <View style={styles.emptyPanel}>
                <Ionicons name="file-tray-outline" size={28} color="#D1D5DB" />
                <Text style={styles.emptyPanelText}>No matching posts.</Text>
              </View>
            }
            showsVerticalScrollIndicator={false}
          />
        </>
      )}
    </View>
  );
}

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const { posts, setPosts } = usePostContext();
  const { currentUser } = useUserContext();
  const { showToast } = useToast();
  const [globalCommentOpen, setGlobalCommentOpen] = useState(false);
  const [recommendationRequestId, setRecommendationRequestId] = useState<string | null>(null);
  const [recommendationSections, setRecommendationSections] = useState<RecommendationSection[]>([]);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [feedPage, setFeedPage] = useState(1);
  const [hasNext, setHasNext] = useState(true);
  const [activeTab, setActiveTab] = useState<HomeTab>('for_you');
  const [followingPosts, setFollowingPosts] = useState<Post[]>([]);
  const [isLoadingFollowing, setIsLoadingFollowing] = useState(false);
  const [followingError, setFollowingError] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeEvents, setActiveEvents] = useState<EventListItem[]>([]);
  const [pinnedPostId, setPinnedPostId] = useState<string | null>(null);
  const feedMixSeedRef = useRef(Date.now());

  const contentPaddingBottom = useMemo(
    () => Layout.bottomNavHeight + Math.max(insets.bottom, Layout.bottomSafeAreaPadding) + 16,
    [insets.bottom]
  );

  const feedItems = useMemo<FeedItem[]>(() => {
    return posts.map((post) => ({ id: post.id, post }));
  }, [posts]);

  const sectionMap = useMemo(
    () => new Map(recommendationSections.map((section) => [section.key, section])),
    [recommendationSections]
  );

  const exploreEntries = useMemo<RecommendationQuestEntry[]>(
    () =>
      (sectionMap.get('explore_new_things')?.items.filter((item): item is RecommendationQuestItem => 'xp_reward' in item) ?? []).map((item, index) => ({
        key: `explore_new_things-${item.id}-${index}`,
        item,
        sectionKey: 'explore_new_things',
        rank: index + 1,
      })),
    [sectionMap]
  );

  const followingItems = useMemo<FeedItem[]>(
    () => followingPosts.map((post) => ({ id: post.id, post })),
    [followingPosts]
  );

  const homeItems = activeTab === 'for_you' ? feedItems : activeTab === 'active' ? followingItems : [];
  const searchSourcePosts = useMemo(
    () => (activeTab === 'for_you' ? posts : activeTab === 'active' ? followingPosts : []),
    [activeTab, followingPosts, posts]
  );


  const hydratePendingPost = useCallback(async () => {
    const pendingPost = await getItem<Post>(StorageKeys.newPost);
    if (!pendingPost) return;

    setPinnedPostId(pendingPost.id);
    setPosts((prev) => sortPostsForFeed(mergePostsById([pendingPost], prev), pendingPost.id, feedMixSeedRef.current));
    await removeItem(StorageKeys.newPost);
  }, [setPosts]);

  useFocusEffect(
    useCallback(() => {
      void hydratePendingPost();
    }, [hydratePendingPost])
  );

  const preserveRecentPosts = useCallback(
    (prev: Post[], incoming: Post[]) => {
      const currentUserId = currentUser?.id;
      if (!currentUserId) return incoming;

      const now = Date.now();
      const incomingIds = new Set(incoming.map((post) => post.id));
      const incomingSubmissionIds = new Set(incoming.map((post) => post.submissionId).filter(Boolean));
      const recentLocal = prev.filter((post) => {
        if (post.author.id !== currentUserId) return false;
        if (incomingIds.has(post.id)) return false;
        if (post.submissionId && incomingSubmissionIds.has(post.submissionId)) return false;
        const created = Date.parse(post.createdAt);
        if (Number.isNaN(created)) return false;
        return now - created <= RECENT_POST_WINDOW_MS;
      });

      if (recentLocal.length === 0) return incoming;
      return [...recentLocal, ...incoming];
    },
    [currentUser?.id]
  );

  const loadRecommendations = useCallback(async (mode: 'initial' | 'refresh' = 'initial') => {
    setRecommendationError(null);
    const nextMixSeed = mode === 'refresh' ? Date.now() : feedMixSeedRef.current;
    if (mode === 'refresh') {
      setPinnedPostId(null);
      feedMixSeedRef.current = nextMixSeed;
      setIsRefreshing(true);
    } else {
      setIsLoadingRecommendations(true);
    }

    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) {
        setRecommendationSections([]);
        setActiveEvents([]);
        setPosts([]);
        return;
      }

      const activeEventsPromise = getActiveEvents(token);

      const currentLocation = await getAppLocation({
        maxAgeMs: mode === 'refresh' ? 30 * 1000 : 2 * 60 * 1000,
      });
      const lat = currentLocation?.latitude;
      const lng = currentLocation?.longitude;

      const [recommendationResult, feedResult, activeEventsResult] = await Promise.allSettled([
        getRecommendedQuests(token, lat, lng),
        getFeed(token, 1, 20),
        activeEventsPromise,
      ]);

      setActiveEvents(activeEventsResult.status === 'fulfilled' ? activeEventsResult.value : []);

      if (recommendationResult.status === 'fulfilled') {
        setRecommendationRequestId(recommendationResult.value.request_id);
        setRecommendationSections(recommendationResult.value.sections);
      } else {
        setRecommendationRequestId(null);
        setRecommendationSections([]);
        setRecommendationError(
          recommendationResult.reason instanceof HttpError
            ? recommendationResult.reason.message
            : 'Could not load recommendations.'
        );
      }

      if (feedResult.status === 'rejected' && recommendationResult.status === 'rejected') {
        throw feedResult.reason;
      }

      const recommendationPosts =
        recommendationResult.status === 'fulfilled' ? recommendationResult.value.for_you_posts : [];
      const feedPosts = feedResult.status === 'fulfilled' ? feedResult.value.items : [];
      const uniquePosts = mergePostsById(recommendationPosts, feedPosts);
      setPosts((prev) => sortPostsForFeed(preserveRecentPosts(prev, uniquePosts), pinnedPostId, nextMixSeed));
      setHasNext(feedResult.status === 'fulfilled' ? feedResult.value.hasNext : false);
      setFeedPage(1);

    } catch (error) {
      if (error instanceof HttpError) {
        setRecommendationError(error.message);
      } else {
        setRecommendationError('Could not load recommendations.');
      }
    } finally {
      if (mode === 'refresh') {
        setIsRefreshing(false);
      } else {
        setIsLoadingRecommendations(false);
      }
    }
  }, [pinnedPostId, preserveRecentPosts, setPosts]);

  useEffect(() => {
    void loadRecommendations('initial');
  }, [loadRecommendations]);

  const loadFeedPage = async (page: number, mode: 'refresh' | 'more') => {
    try {
      const nextMixSeed = mode === 'refresh' ? Date.now() : feedMixSeedRef.current;
      if (mode === 'refresh') {
        setPinnedPostId(null);
        feedMixSeedRef.current = nextMixSeed;
        setIsRefreshing(true);
      } else {
        setIsLoadingMore(true);
      }

      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) {
        setPosts([]);
        setActiveEvents([]);
        setHasNext(false);
        return;
      }

      const [feedResult, activeEventsResult] = await Promise.allSettled([
        getFeed(token, page),
        page === 1 ? getActiveEvents(token) : Promise.resolve(null),
      ]);

      if (feedResult.status === 'rejected') {
        throw feedResult.reason;
      }

      if (page === 1) {
        setActiveEvents(activeEventsResult.status === 'fulfilled' && activeEventsResult.value ? activeEventsResult.value : []);
      }
      const response = feedResult.value;
      setHasNext(response.hasNext);
      setFeedPage(response.page);

      setPosts((prev) => {
        if (page === 1) {
          const uniquePosts = Array.from(new Map(response.items.map((post) => [post.id, post])).values());
          return sortPostsForFeed(
            preserveRecentPosts(prev, uniquePosts),
            mode === 'refresh' ? null : pinnedPostId,
            nextMixSeed
          );
        }

        return sortPostsForFeed(mergePostsById(prev, response.items), pinnedPostId, nextMixSeed);
      });
    } catch (error) {
      showToast(error instanceof HttpError ? error.message : 'Could not load feed.');
    } finally {
      setIsRefreshing(false);
      setIsLoadingMore(false);
    }
  };

  const loadFollowingPosts = async () => {
    setIsLoadingFollowing(true);
    setFollowingError(null);
    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) {
        setFollowingPosts([]);
        return;
      }
      const response = await getFeed(token, 1, 20, 'following');
      setFollowingPosts(response.items);
    } catch (error) {
      setFollowingError(error instanceof HttpError ? error.message : 'Could not load following feed.');
    } finally {
      setIsLoadingFollowing(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'active') {
      void loadFollowingPosts();
    }
  }, [activeTab]);

  return (
    <View style={styles.container}>
      <FlatList
        data={homeItems}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <PostCard post={item.post} attachedQuest={item.attachedQuest ?? null} />}
        refreshing={activeTab === 'for_you' ? isRefreshing : activeTab === 'active' ? isLoadingFollowing : isLoadingRecommendations}
        onRefresh={() => {
          if (activeTab === 'for_you') {
            setRecommendationSections([]);
            setRecommendationRequestId(null);
            void loadRecommendations('refresh');
          } else if (activeTab === 'active') {
            void loadFollowingPosts();
          }
        }}
        onEndReached={() => {
          if (activeTab === 'for_you' && !isLoadingMore && hasNext) {
            void loadFeedPage(feedPage + 1, 'more');
          }
        }}
        onEndReachedThreshold={0.3}
        ListHeaderComponent={
          <>
            <HomeTabs
              activeTab={activeTab}
              onChange={setActiveTab}
              onSearch={() => setSearchOpen(true)}
              onMessages={() => router.push(ROUTES.main.chat as any)}
            />
            {activeTab === 'for_you' ? <ActiveEventStrip events={activeEvents} /> : null}
            {activeTab !== 'for_you' && isLoadingRecommendations ? (
              <View style={styles.loadingPanel}>
                <ActivityIndicator size="small" color="#11181C" />
              </View>
            ) : null}
            {activeTab !== 'for_you' && recommendationError ? (
              <View style={styles.emptyPanel}>
                <Ionicons name="alert-circle-outline" size={28} color="#D1D5DB" />
                <Text style={styles.emptyPanelText}>{recommendationError}</Text>
              </View>
            ) : null}
            {activeTab === 'explore' && !isLoadingRecommendations && !recommendationError ? (
              <RecommendationQuestList
                requestId={recommendationRequestId}
                entries={exploreEntries}
                emptyText="No system quests available yet."
              />
            ) : null}
            {activeTab === 'active' && isLoadingFollowing ? (
              <View style={styles.loadingPanel}>
                <ActivityIndicator size="small" color="#11181C" />
              </View>
            ) : null}
            {activeTab === 'active' && followingError ? (
              <View style={styles.emptyPanel}>
                <Ionicons name="alert-circle-outline" size={28} color="#D1D5DB" />
                <Text style={styles.emptyPanelText}>{followingError}</Text>
              </View>
            ) : null}
            {activeTab === 'active' && followingItems.length === 0 && !isLoadingFollowing && !followingError ? (
              <View style={styles.emptyPanel}>
                <Ionicons name="people-outline" size={28} color="#D1D5DB" />
                <Text style={styles.emptyPanelText}>Follow people to see their posts here.</Text>
              </View>
            ) : null}
            {activeTab === 'for_you' && feedItems.length === 0 && !isRefreshing ? (
              <View style={styles.emptyPanel}>
                <Ionicons name="images-outline" size={28} color="#D1D5DB" />
                <Text style={styles.emptyPanelText}>No posts yet.</Text>
              </View>
            ) : null}
          </>
        }
        ListFooterComponent={
          activeTab !== 'for_you' ? null : isLoadingMore ? (
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
      <SearchModal visible={searchOpen} onClose={() => setSearchOpen(false)} sourcePosts={searchSourcePosts} />

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
  homeHeaderWrap: {
    backgroundColor: '#fff',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
  },
  homeTopBar: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingTop: 14,
    paddingBottom: 8,
  },
  homeTitle: {
    color: '#11181C',
    fontSize: 28,
    fontWeight: '800',
  },
  headerIconButton: {
    alignItems: 'center',
    height: 42,
    justifyContent: 'center',
    width: 42,
  },
  homeTabsWrap: {
    alignItems: 'center',
    backgroundColor: '#fff',
    flexDirection: 'row',
  },
  homeTab: {
    alignItems: 'center',
    flex: 1,
    paddingBottom: 12,
    paddingTop: 6,
  },
  homeTabActive: {
    borderBottomColor: '#11181C',
    borderBottomWidth: 2,
  },
  homeTabText: {
    color: '#6B7280',
    fontSize: 15,
    fontWeight: '700',
  },
  homeTabTextActive: {
    color: '#11181C',
  },
  questList: {
    backgroundColor: '#fff',
    gap: 12,
    padding: 12,
  },
  questListItem: {
    width: '100%',
  },
  loadingPanel: {
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingVertical: 30,
  },
  emptyPanel: {
    alignItems: 'center',
    backgroundColor: '#fff',
    gap: 8,
    paddingHorizontal: 20,
    paddingVertical: 42,
  },
  eventStrip: {
    backgroundColor: '#fff',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    paddingBottom: 10,
    paddingTop: 10,
  },
  eventStripTitle: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '700',
    paddingHorizontal: 12,
    textTransform: 'uppercase',
  },
  eventStripList: {
    gap: 10,
    paddingHorizontal: 12,
    paddingTop: 8,
  },
  eventPill: {
    alignItems: 'center',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 8,
    maxWidth: 220,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  eventPillTextWrap: {
    minWidth: 120,
  },
  eventPillTitle: {
    color: '#11181C',
    fontSize: 13,
    fontWeight: '700',
  },
  eventPillMeta: {
    color: '#9CA3AF',
    fontSize: 11,
    marginTop: 2,
  },
  emptyPanelText: {
    color: '#9CA3AF',
    fontSize: 13,
    textAlign: 'center',
  },
  searchModal: {
    backgroundColor: '#fff',
    flex: 1,
    paddingTop: 48,
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    zIndex: 50,
  },
  searchHeader: {
    alignItems: 'center',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: 10,
    paddingBottom: 10,
    paddingHorizontal: 12,
  },
  searchInputWrap: {
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    flex: 1,
    flexDirection: 'row',
    minHeight: 40,
    paddingHorizontal: 12,
  },
  searchInput: {
    color: '#11181C',
    flex: 1,
    fontSize: 15,
  },
  clearButton: {
    alignItems: 'center',
    height: 24,
    justifyContent: 'center',
    width: 24,
  },
  searchBack: {
    alignItems: 'center',
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  searchCancel: {
    paddingHorizontal: 2,
    paddingVertical: 8,
  },
  searchCancelText: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '600',
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
  suggestionList: {
    paddingHorizontal: 12,
    paddingTop: 16,
  },
  suggestionRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
    paddingVertical: 10,
  },
  suggestionText: {
    color: '#11181C',
    fontSize: 15,
  },
  historyRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  historyDelete: {
    alignItems: 'center',
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  historyHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  historyTitle: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  historyClear: {
    paddingVertical: 4,
  },
  historyClearText: {
    color: '#11181C',
    fontSize: 12,
    fontWeight: '600',
  },
  searchTabs: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  searchTab: {
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#F3F4F6',
  },
  searchTabActive: {
    backgroundColor: '#11181C',
  },
  searchTabText: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '600',
  },
  searchTabTextActive: {
    color: '#fff',
  },
});
