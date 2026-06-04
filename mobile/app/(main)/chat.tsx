import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import { useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Avatar } from '@/components/ui/avatar';
import { ROUTES } from '@/constants/routes';
import { HttpError } from '@/services/httpClient';
import { listConversations, type Conversation } from '@/services/chatService';
import { getItem, StorageKeys } from '@/utils/storage';

export default function ChatInboxScreen() {
  const router = useRouter();
  const [items, setItems] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) {
        setItems([]);
        return;
      }
      const response = await listConversations(token);
      setItems(response.items);
    } catch (loadError) {
      setError(loadError instanceof HttpError ? loadError.message : 'Could not load chats.');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void loadConversations();
    }, [loadConversations])
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.iconButton}>
          <Ionicons name="arrow-back" size={20} color="#11181C" />
        </Pressable>
        <Text style={styles.headerTitle}>Messages</Text>
        <View style={styles.iconButton} />
      </View>

      {loading ? (
        <View style={styles.centerPanel}>
          <ActivityIndicator size="small" color="#11181C" />
        </View>
      ) : error ? (
        <View style={styles.centerPanel}>
          <Text style={styles.emptyText}>{error}</Text>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <Pressable
              style={styles.row}
              onPress={() =>
                router.push({
                  pathname: ROUTES.modal.chatDetail as any,
                  params: { conversationId: item.id, username: item.other_user.username },
                })
              }
            >
              <Avatar size={44} uri={item.other_user.avatar_url ?? undefined} label={item.other_user.username.charAt(0)} />
              <View style={styles.rowBody}>
                <View style={styles.nameRow}>
                  <Text style={styles.username}>{item.other_user.username}</Text>
                  {item.is_friend ? <Text style={styles.friendBadge}>Friend</Text> : null}
                </View>
                <Text style={styles.preview} numberOfLines={1}>
                  {item.last_message?.content ?? 'No messages yet'}
                </Text>
              </View>
              {item.unread_count > 0 ? (
                <View style={styles.unreadBadge}>
                  <Text style={styles.unreadText}>{item.unread_count}</Text>
                </View>
              ) : null}
            </Pressable>
          )}
          ListEmptyComponent={
            <View style={styles.centerPanel}>
              <Ionicons name="chatbubbles-outline" size={32} color="#D1D5DB" />
              <Text style={styles.emptyText}>No chats yet.</Text>
            </View>
          }
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
    fontWeight: '700',
  },
  centerPanel: {
    alignItems: 'center',
    flex: 1,
    gap: 8,
    justifyContent: 'center',
    padding: 24,
  },
  row: {
    alignItems: 'center',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  rowBody: {
    flex: 1,
  },
  nameRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  username: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '800',
  },
  friendBadge: {
    backgroundColor: '#F3F4F6',
    borderRadius: 999,
    color: '#6B7280',
    fontSize: 10,
    fontWeight: '700',
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  preview: {
    color: '#9CA3AF',
    fontSize: 13,
    marginTop: 2,
  },
  unreadBadge: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderRadius: 999,
    minWidth: 22,
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  unreadText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '800',
  },
  emptyText: {
    color: '#9CA3AF',
    fontSize: 14,
  },
});
