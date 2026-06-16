import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { ROUTES } from '@/constants/routes';
import { getEvents } from '@/services/socialService';
import type { EventListItem } from '@/services/socialService';
import { StorageKeys, getItem } from '@/utils/storage';

type TabId = 'active' | 'ended';

function formatTimeLeft(endAt: string): string {
  const diffMs = new Date(endAt).getTime() - Date.now();
  if (diffMs <= 0) return 'Ended';
  const hours = Math.floor(diffMs / (60 * 60 * 1000));
  const minutes = Math.ceil((diffMs % (60 * 60 * 1000)) / (60 * 1000));
  if (hours >= 24) return `${Math.ceil(hours / 24)}d left`;
  if (hours > 0) return `${hours}h ${minutes}m left`;
  return `${minutes}m left`;
}

export default function EventsScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabId>('active');
  const [events, setEvents] = useState<EventListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadEvents() {
      setIsLoading(true);
      try {
        const token = await getItem<string>(StorageKeys.accessToken);
        if (!token) return;
        const res = await getEvents(token, activeTab);
        setEvents(res);
      } catch (err) {
        console.error('Failed to load events', err);
      } finally {
        setIsLoading(false);
      }
    }
    void loadEvents();
  }, [activeTab]);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#11181C" />
        </Pressable>
        <Text style={styles.headerTitle}>Sự kiện</Text>
        <View style={styles.backButton} />
      </View>

      <View style={styles.tabBar}>
        <Pressable
          style={[styles.tabButton, activeTab === 'active' && styles.tabButtonActive]}
          onPress={() => setActiveTab('active')}
        >
          <Text style={[styles.tabText, activeTab === 'active' && styles.tabTextActive]}>Đang diễn ra</Text>
        </Pressable>
        <Pressable
          style={[styles.tabButton, activeTab === 'ended' && styles.tabButtonActive]}
          onPress={() => setActiveTab('ended')}
        >
          <Text style={[styles.tabText, activeTab === 'ended' && styles.tabTextActive]}>Đã kết thúc</Text>
        </Pressable>
      </View>

      {isLoading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      ) : (
        <FlatList
          data={events}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          renderItem={({ item }) => (
            <Pressable
              style={styles.eventCard}
              onPress={() =>
                router.push({
                  pathname: ROUTES.modal.eventDetail as any,
                  params: { eventId: item.id },
                })
              }
            >
              <ImageWithFallback uri={item.banner_url || undefined} width="100%" height={140} borderRadius={12} fallbackText="Event Banner" />
              <View style={styles.eventInfo}>
                <View style={styles.eventHeaderRow}>
                  <Text style={styles.eventTitle}>{item.title}</Text>
                  {item.status === 'active' ? (
                    <View style={styles.activeBadge}>
                      <Text style={styles.activeBadgeText}>{formatTimeLeft(item.end_at)}</Text>
                    </View>
                  ) : null}
                </View>
                {item.description ? (
                  <Text style={styles.eventDesc} numberOfLines={2}>{item.description}</Text>
                ) : null}
              </View>
            </Pressable>
          )}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="trophy-outline" size={48} color="#9CA3AF" />
              <Text style={styles.emptyText}>Chưa có sự kiện nào</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#11181C',
  },
  tabBar: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabButtonActive: {
    borderBottomColor: '#11181C',
  },
  tabText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#6B7280',
  },
  tabTextActive: {
    color: '#11181C',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    flexGrow: 1,
    padding: 16,
    gap: 16,
  },
  eventCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    overflow: 'hidden',
  },
  eventInfo: {
    padding: 12,
  },
  eventHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  eventTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '700',
    color: '#11181C',
  },
  activeBadge: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  activeBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4F46E5',
  },
  eventDesc: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 6,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 80,
  },
  emptyText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 12,
  },
});
