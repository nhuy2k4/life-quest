import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Avatar } from '@/components/ui/avatar';
import { useUserContext } from '@/contexts/UserContext';
import { getFriends, getFollowers, getFollowing } from '@/services/socialService';
import type { FeedUser } from '@/services/socialService';
import { StorageKeys, getItem } from '@/utils/storage';

export default function FriendsScreen() {
  const router = useRouter();
  const { userId, type = 'friends' } = useLocalSearchParams<{ userId?: string; type?: 'friends' | 'followers' | 'following' }>();
  const { currentUser } = useUserContext();
  const [friends, setFriends] = useState<FeedUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const targetUserId = userId || currentUser?.id;

  useEffect(() => {
    async function loadList() {
      if (!targetUserId) return;
      setIsLoading(true);
      try {
        const token = await getItem<string>(StorageKeys.accessToken);
        if (!token) return;
        
        let res;
        if (type === 'followers') {
          res = await getFollowers(token, targetUserId, 1, 100);
        } else if (type === 'following') {
          res = await getFollowing(token, targetUserId, 1, 100);
        } else {
          res = await getFriends(token, targetUserId, 1, 100);
        }
        setFriends(res.items);
      } catch (err) {
        console.error('Failed to load friends/followers/following list', err);
      } finally {
        setIsLoading(false);
      }
    }
    void loadList();
  }, [targetUserId, type]);

  const handleUserPress = (id: string) => {
    if (id === currentUser?.id) {
      router.push('/(main)/profile');
    } else {
      router.push(`/(main)/other-profile/${id}`);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#11181C" />
        </Pressable>
        <Text style={styles.headerTitle}>
          {type === 'followers'
            ? 'Người theo dõi'
            : type === 'following'
            ? 'Đang theo dõi'
            : 'Bạn bè'}
        </Text>
        <View style={styles.backButton} />
      </View>

      {isLoading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      ) : (
        <FlatList
          data={friends}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          renderItem={({ item }) => (
            <Pressable style={styles.userRow} onPress={() => handleUserPress(item.id)}>
              <Avatar uri={item.avatar_url ?? undefined} size={48} label={item.username.charAt(0)} />
              <View style={styles.userInfo}>
                <Text style={styles.userName}>{item.username}</Text>
                <Text style={styles.userHandle}>@{item.username}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
            </Pressable>
          )}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="people-outline" size={48} color="#9CA3AF" />
              <Text style={styles.emptyText}>
                {type === 'followers'
                  ? 'Chưa có người theo dõi nào'
                  : type === 'following'
                  ? 'Chưa theo dõi ai'
                  : 'Chưa có bạn bè nào'}
              </Text>
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
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    flexGrow: 1,
    paddingVertical: 8,
  },
  userRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  userInfo: {
    flex: 1,
    marginLeft: 12,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#11181C',
  },
  userHandle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
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
