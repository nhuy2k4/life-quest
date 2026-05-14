import { Ionicons } from '@expo/vector-icons';
import { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { Layout } from '@/constants/layout';
import { useToast } from '@/contexts/ToastContext';
import { getXpHistory, type XpHistoryItem } from '@/services/xpHistoryService';
import { getItem, StorageKeys } from '@/utils/storage';

function formatSource(source: string): string {
  return source.replace(/_/g, ' ').toLowerCase();
}

export default function XpHistoryScreen() {
  const { showToast } = useToast();
  const [items, setItems] = useState<XpHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(true);

  useEffect(() => {
    void loadPage(1, 'initial');
  }, []);

  const loadPage = async (nextPage: number, mode: 'initial' | 'refresh' | 'more') => {
    if (mode === 'initial') {
      setIsLoading(true);
    } else if (mode === 'refresh') {
      setIsRefreshing(true);
    } else {
      setIsLoadingMore(true);
    }

    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      const response = await getXpHistory(token, nextPage, 30);
      setHasNext(response.has_next);
      setPage(response.page);

      setItems((prev) => {
        if (nextPage === 1) return response.items;
        const seen = new Set(prev.map((item) => item.id));
        const merged = [...prev];
        response.items.forEach((item) => {
          if (!seen.has(item.id)) {
            merged.push(item);
          }
        });
        return merged;
      });
    } catch {
      showToast('Could not load XP history.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
      setIsLoadingMore(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>XP History</Text>
      </View>

      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <View style={styles.iconWrap}>
              <Ionicons name={item.amount >= 0 ? 'flash' : 'remove'} size={16} color="#11181C" />
            </View>
            <View style={styles.body}>
              <Text style={styles.title}>{formatSource(item.source)}</Text>
              <Text style={styles.meta}>{new Date(item.created_at).toLocaleString()}</Text>
            </View>
            <Text style={[styles.amount, item.amount < 0 ? styles.amountNegative : null]}>{item.amount}</Text>
          </View>
        )}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshing={isRefreshing}
        onRefresh={() => loadPage(1, 'refresh')}
        onEndReached={() => {
          if (!isLoadingMore && hasNext) {
            void loadPage(page + 1, 'more');
          }
        }}
        onEndReachedThreshold={0.3}
        ListHeaderComponent={
          isLoading ? (
            <View style={styles.loadingWrap}>
              <ActivityIndicator size="small" color="#11181C" />
            </View>
          ) : null
        }
        ListEmptyComponent={
          !isLoading ? (
            <View style={styles.emptyWrap}>
              <Text style={styles.emptyText}>No XP activity yet.</Text>
            </View>
          ) : null
        }
        ListFooterComponent={
          isLoadingMore ? (
            <View style={styles.loadingWrap}>
              <ActivityIndicator size="small" color="#11181C" />
            </View>
          ) : null
        }
      />

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
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#fff',
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 22,
    fontWeight: '700',
  },
  content: {
    padding: 16,
    paddingBottom: Layout.bottomNavHeight + 24,
    gap: 10,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#fff',
    borderColor: '#E5E7EB',
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  iconWrap: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  body: {
    flex: 1,
  },
  title: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '600',
  },
  meta: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  amount: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  amountNegative: {
    color: '#B91C1C',
  },
  loadingWrap: {
    paddingVertical: 12,
  },
  emptyWrap: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  emptyText: {
    color: '#9CA3AF',
    fontSize: 13,
  },
});
