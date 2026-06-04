import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { useToast } from '@/contexts/ToastContext';
import { listQuestLog, type QuestListItem } from '@/services/questService';
import { getItem, StorageKeys } from '@/utils/storage';

type TabKey = 'available' | 'inprogress' | 'completed' | 'failed';

type QuestItem = {
  id: string;
  poiId?: string | null;
  poiName?: string | null;
  title: string;
  desc: string;
  xp: number;
  category: string;
  image?: string;
  user_status: 'not_started' | 'started' | 'submitted' | 'approved' | 'rejected';
  progress?: number;
  total?: number;
  failReason?: string;
};

type TabDef = {
  key: TabKey;
  label: string;
  data: QuestItem[];
  unseen: number;
};

function mapQuest(item: QuestListItem): QuestItem {
  return {
    id: item.id,
    poiId: item.poi_id ?? null,
    poiName: item.poi_name ?? null,
    title: item.rendered_text,
    desc: item.poi_name ?? item.labels?.join(', ') ?? '',
    xp: item.xp_reward,
    category: item.poi_name ?? item.labels?.[0] ?? 'General',
    image: item.image_url ?? undefined,
    user_status: item.user_status,
  };
}

function EmptyState({ activeTab }: { activeTab: TabKey }) {
  const icon =
    activeTab === 'available'
      ? 'list-outline'
      : activeTab === 'completed'
        ? 'checkmark-circle-outline'
        : activeTab === 'failed'
          ? 'close-circle-outline'
          : 'time-outline';
  const label = activeTab === 'inprogress' ? 'No active quests' : `No ${activeTab} quests`;

  return (
    <View style={styles.emptyWrap}>
      <View style={styles.emptyIconWrap}>
        <Ionicons name={icon} size={26} color="#9CA3AF" />
      </View>
      <Text style={styles.emptyText}>{label}</Text>
    </View>
  );
}

function QuestLogCard({ quest, tab, onPress }: { quest: QuestItem; tab: TabKey; onPress: () => void }) {
  const pct = quest.progress && quest.total ? Math.round((quest.progress / quest.total) * 100) : 0;

  if (tab === 'available') {
    return (
      <Pressable onPress={onPress} style={styles.savedCard}>
        <ImageWithFallback uri={quest.image} width={64} height={64} borderRadius={12} fallbackText="Quest" />

        <View style={styles.savedBody}>
          <View style={styles.savedTopMeta}>
            <Text style={styles.metaMuted}>{quest.category}</Text>
          </View>
          <Text style={styles.cardTitle} numberOfLines={1}>{quest.title}</Text>
          <View style={styles.savedBottomMeta}>
            <View style={styles.inlineRow}>
              <Ionicons name="flash" size={12} color="#9CA3AF" />
              <Text style={styles.metaMuted}>{`+${quest.xp} XP`}</Text>
            </View>
          </View>
        </View>

        <View style={styles.savedTail}>
          <Ionicons name="chevron-forward" size={14} color="#D1D5DB" />
        </View>
      </Pressable>
    );
  }

  if (tab === 'completed') {
    return (
      <Pressable onPress={onPress} style={styles.completedCard}>
        <View>
          <ImageWithFallback uri={quest.image} width={56} height={56} borderRadius={12} fallbackText="Quest" />
          <View style={styles.completedBadge}>
            <Ionicons name="checkmark" size={10} color="#fff" />
          </View>
        </View>

        <View style={styles.completedBody}>
          <Text style={styles.cardTitle} numberOfLines={1}>{quest.title}</Text>
          <Text style={styles.metaMuted}>{quest.category}</Text>
          <Text style={styles.completedXp}>{`+${quest.xp} XP earned`}</Text>
        </View>

        <Ionicons name="chevron-forward" size={16} color="#D1D5DB" />
      </Pressable>
    );
  }

  if (tab === 'failed') {
    return (
      <Pressable onPress={onPress} style={styles.progressCard}>
        <View style={styles.progressHeader}>
          <ImageWithFallback uri={quest.image} width={56} height={56} borderRadius={12} fallbackText="Quest" />
          <View style={styles.progressBody}>
            <Text style={styles.failedTitle} numberOfLines={1}>{quest.title}</Text>
            {quest.failReason ? <Text style={styles.metaMuted}>{quest.failReason}</Text> : null}
          </View>
          <View style={styles.inlineRow}>
            <Ionicons name="flash" size={12} color="#9CA3AF" />
            <Text style={styles.metaMuted}>{`0/${quest.xp}`}</Text>
          </View>
        </View>

        <View style={styles.progressWrap}>
          <View style={styles.progressMeta}>
            <Text style={styles.metaMuted}>{`Reached ${quest.progress ?? 0}/${quest.total ?? 0}`}</Text>
            <Text style={styles.metaMuted}>{`${pct}%`}</Text>
          </View>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFillFailed, { width: `${pct}%` }]} />
          </View>
        </View>
      </Pressable>
    );
  }

  return (
    <Pressable onPress={onPress} style={styles.progressCard}>
      <View style={styles.progressHeader}>
        <ImageWithFallback uri={quest.image} width={56} height={56} borderRadius={12} fallbackText="Quest" />
        <View style={styles.progressBody}>
          <Text style={styles.cardTitle} numberOfLines={1}>{quest.title}</Text>
          <Text style={styles.metaMuted} numberOfLines={1}>{quest.desc}</Text>
        </View>
        <View style={quest.user_status === 'started' ? styles.continuePill : styles.reviewPill}>
          <Text style={quest.user_status === 'started' ? styles.continuePillText : styles.reviewPillText}>
            {quest.user_status === 'started' ? 'Continue' : 'Reviewing'}
          </Text>
        </View>
      </View>

      <View style={styles.progressWrap}>
        <View style={styles.progressMeta}>
          <Text style={styles.metaMuted}>
            {quest.user_status === 'started' ? 'Progressing' : 'Waiting for approval'}
          </Text>
          <Text style={styles.inlineStrong}>{`+${quest.xp} XP`}</Text>
        </View>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: quest.user_status === 'started' ? '35%' : '70%' }]} />
        </View>
      </View>
    </Pressable>
  );
}

export default function QuestLogScreen() {
  const router = useRouter();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<TabKey>('inprogress');
  const [rawQuests, setRawQuests] = useState<QuestListItem[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasNext, setHasNext] = useState(true);

  useEffect(() => {
    void loadQuests(false);
  }, []);

  const loadQuests = async (isRefresh: boolean) => {
    if (isRefresh) {
      setRefreshing(true);
    }

    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      const response = await listQuestLog(token);
      setRawQuests(response.items);
      setHasNext(response.has_next);
    } catch {
      showToast('Could not refresh quests.');
    } finally {
      setRefreshing(false);
    }
  };

  const loadMore = async () => {
    if (isLoadingMore || !hasNext) return;

    setIsLoadingMore(true);
    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      const response = await listQuestLog(token);
      setHasNext(response.has_next);
      setRawQuests((prev) => {
        const seen = new Set(prev.map((item) => `${item.id}:${item.poi_id ?? 'base'}`));
        const merged = [...prev];
        response.items.forEach((item) => {
          const key = `${item.id}:${item.poi_id ?? 'base'}`;
          if (!seen.has(key)) {
            merged.push(item);
            seen.add(key);
          }
        });
        return merged;
      });
    } catch {
      showToast('Could not load more quests.');
    } finally {
      setIsLoadingMore(false);
    }
  };

  const mappedQuests = useMemo(() => rawQuests.map(mapQuest), [rawQuests]);
  const availableQuests = useMemo(
    () => mappedQuests.filter((item) => item.user_status === 'not_started'),
    [mappedQuests]
  );
  const inProgressQuests = useMemo(
    () => mappedQuests.filter((item) => item.user_status === 'started' || item.user_status === 'submitted'),
    [mappedQuests]
  );
  const completedQuests = useMemo(
    () => mappedQuests.filter((item) => item.user_status === 'approved'),
    [mappedQuests]
  );
  const failedQuests = useMemo(
    () => mappedQuests.filter((item) => item.user_status === 'rejected'),
    [mappedQuests]
  );

  const tabs = useMemo<TabDef[]>(
    () => [
      { key: 'available', label: 'Available', data: availableQuests, unseen: 0 },
      { key: 'inprogress', label: 'In Progress', data: inProgressQuests, unseen: 0 },
      { key: 'completed', label: 'Completed', data: completedQuests, unseen: 0 },
      { key: 'failed', label: 'Failed', data: failedQuests, unseen: 0 },
    ],
    [availableQuests, inProgressQuests, completedQuests, failedQuests]
  );

  const currentTab = useMemo(() => tabs.find((tab) => tab.key === activeTab) ?? tabs[0], [activeTab, tabs]);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Quests</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabRow}>
          {tabs.map((tab) => {
            const active = tab.key === activeTab;
            return (
              <Pressable
                key={tab.key}
                onPress={() => setActiveTab(tab.key)}
                style={[styles.tabButton, active ? styles.tabButtonActive : null]}>
                <Text style={[styles.tabLabel, active ? styles.tabLabelActive : styles.tabLabelInactive]}>{tab.label}</Text>
                <View style={[styles.tabCount, tab.unseen > 0 ? styles.tabCountUnseen : styles.tabCountSeen]}>
                  <Text style={[styles.tabCountText, tab.unseen > 0 ? styles.tabCountTextUnseen : styles.tabCountTextSeen]}>
                    {tab.data.length}
                  </Text>
                </View>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => loadQuests(true)} />}
      >
        {currentTab.data.length === 0 ? <EmptyState activeTab={activeTab} /> : null}
        {currentTab.data.map((quest) => (
          <QuestLogCard
            key={`${quest.id}:${quest.poiId ?? 'base'}`}
            quest={quest}
            tab={activeTab}
            onPress={() => router.push({ pathname: ROUTES.modal.questDetail, params: { questId: quest.id, poiId: quest.poiId ?? undefined } })}
          />
        ))}
        {hasNext ? (
          <Pressable style={styles.loadMoreButton} onPress={loadMore} disabled={isLoadingMore}>
            <Text style={styles.loadMoreText}>{isLoadingMore ? 'Loading...' : 'Load more quests'}</Text>
            {isLoadingMore ? <ActivityIndicator size="small" color="#11181C" /> : null}
          </Pressable>
        ) : null}
      </ScrollView>

      <BottomNav />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 28,
    fontWeight: '800',
    paddingBottom: 12,
  },
  tabRow: {
    gap: 6,
    paddingBottom: 2,
  },
  tabButton: {
    alignItems: 'center',
    borderBottomWidth: 2,
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 12,
  },
  tabButtonActive: {
    borderBottomColor: '#11181C',
  },
  tabLabel: {
    fontSize: 14,
  },
  tabLabelActive: {
    color: '#11181C',
    fontWeight: '700',
  },
  tabLabelInactive: {
    color: '#9CA3AF',
  },
  tabCount: {
    alignItems: 'center',
    borderRadius: 999,
    justifyContent: 'center',
    minWidth: 18,
    paddingHorizontal: 6,
    height: 18,
  },
  tabCountSeen: {
    backgroundColor: '#F3F4F6',
  },
  tabCountUnseen: {
    backgroundColor: '#11181C',
  },
  tabCountText: {
    fontSize: 11,
    fontWeight: '600',
  },
  tabCountTextSeen: {
    color: '#6B7280',
  },
  tabCountTextUnseen: {
    color: '#fff',
  },
  content: {
    gap: 10,
    padding: 16,
    paddingBottom: Layout.bottomNavHeight + 28,
  },
  savedCard: {
    alignItems: 'center',
    backgroundColor: '#fff',
    borderColor: '#F3F4F6',
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    padding: 12,
  },
  savedBody: {
    flex: 1,
    gap: 4,
  },
  savedTopMeta: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  savedBottomMeta: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  savedTail: {
    alignItems: 'center',
    gap: 8,
  },
  cardTitle: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  metaMuted: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  inlineRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 3,
  },
  inlineStrong: {
    color: '#11181C',
    fontSize: 12,
    fontWeight: '700',
  },
  progressCard: {
    backgroundColor: '#fff',
    borderColor: '#F3F4F6',
    borderRadius: 16,
    borderWidth: 1,
    overflow: 'hidden',
    padding: 12,
    gap: 8,
  },
  progressHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  progressBody: {
    flex: 1,
    gap: 2,
  },
  progressWrap: {
    gap: 4,
  },
  progressMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressTrack: {
    backgroundColor: '#F3F4F6',
    borderRadius: 999,
    height: 6,
    overflow: 'hidden',
  },
  progressFill: {
    backgroundColor: '#11181C',
    borderRadius: 999,
    height: '100%',
  },
  progressFillFailed: {
    backgroundColor: '#D1D5DB',
    borderRadius: 999,
    height: '100%',
  },
  continuePill: {
    backgroundColor: '#11181C',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  continuePillText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  reviewPill: {
    backgroundColor: '#F3F4F6',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  reviewPillText: {
    color: '#6B7280',
    fontSize: 11,
    fontWeight: '700',
  },
  completedCard: {
    alignItems: 'center',
    backgroundColor: '#fff',
    borderColor: '#F3F4F6',
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    opacity: 0.85,
    padding: 12,
  },
  completedBody: {
    flex: 1,
    gap: 2,
  },
  completedBadge: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderColor: '#fff',
    borderRadius: 10,
    borderWidth: 2,
    bottom: -2,
    height: 18,
    justifyContent: 'center',
    position: 'absolute',
    right: -2,
    width: 18,
  },
  completedXp: {
    color: '#11181C',
    fontSize: 12,
    fontWeight: '600',
  },
  failedTitle: {
    color: '#6B7280',
    fontSize: 14,
    fontWeight: '700',
  },
  emptyWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 56,
    gap: 10,
  },
  emptyIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    color: '#9CA3AF',
    fontSize: 14,
  },
  loadMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
  },
  loadMoreText: {
    color: '#11181C',
    fontSize: 13,
    fontWeight: '600',
  },
  locationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    gap: 3,
    marginLeft: 6,
  },
  locationBadgeText: {
    color: '#10B981',
    fontSize: 10,
    fontWeight: '700',
  },
  metaMutedGreen: {
    color: '#10B981',
    fontSize: 12,
    fontWeight: '600',
  },
});
