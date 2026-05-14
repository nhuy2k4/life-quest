import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { CommentSheet } from '@/components/lifequest/CommentSheet';
import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { Avatar } from '@/components/ui/avatar';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { likePost, unlikePost } from '@/services/socialService';
import { getItem, StorageKeys } from '@/utils/storage';

export default function PostDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { posts, setPosts } = usePostContext();
  const postId = typeof params.postId === 'string' ? params.postId : undefined;
  const matched = useMemo(() => posts.find((item) => item.id === postId), [posts, postId]);
  const [liked, setLiked] = useState(Boolean(matched?.isLiked));
  const [saved, setSaved] = useState(false);
  const [commentOpen, setCommentOpen] = useState(false);
  const [likeCount, setLikeCount] = useState(matched?.likesCount ?? 0);

  if (!matched) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.iconButton}>
            <Ionicons name="arrow-back" size={20} color="#11181C" />
          </Pressable>
          <Text style={styles.headerTitle}>Post</Text>
          <View style={styles.iconButton} />
        </View>
        <View style={styles.emptyWrap}>
          <Text style={styles.emptyText}>Post is not available.</Text>
        </View>
      </SafeAreaView>
    );
  }

  const display = {
    id: matched.id,
    username: matched.author.username,
    image: matched.imageUrl,
    caption: matched.caption ?? '',
    location: matched.location,
    likes: matched.likesCount,
    comments: matched.commentsCount,
    timeAgo: matched.createdAt,
    quest: matched.quest,
  };

  const handleLike = async () => {
    const nextLiked = !liked;
    setLiked(nextLiked);
    setLikeCount((prev) => (liked ? Math.max(0, prev - 1) : prev + 1));
    setPosts((prev) =>
      prev.map((item) =>
        item.id === display.id
          ? {
              ...item,
              isLiked: nextLiked,
              likesCount: liked ? Math.max(0, item.likesCount - 1) : item.likesCount + 1,
            }
          : item
      )
    );

    if (!display.id) return;
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) return;

    try {
      if (nextLiked) {
        await likePost(token, display.id);
      } else {
        await unlikePost(token, display.id);
      }
    } catch {
      setLiked((prev) => !prev);
      setLikeCount((prev) => (nextLiked ? Math.max(0, prev - 1) : prev + 1));
      setPosts((prev) =>
        prev.map((item) =>
          item.id === display.id
            ? {
                ...item,
                isLiked: !nextLiked,
                likesCount: nextLiked ? Math.max(0, item.likesCount - 1) : item.likesCount + 1,
              }
            : item
        )
      );
    }
  };



  return (
    <>
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.iconButton}>
            <Ionicons name="arrow-back" size={20} color="#11181C" />
          </Pressable>
          <Text style={styles.headerTitle}>Post</Text>
          <Pressable style={styles.iconButton}>
            <Ionicons name="ellipsis-horizontal" size={20} color="#9CA3AF" />
          </Pressable>
        </View>

        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={styles.userRow}>
            <Pressable
              style={styles.userInfo}
              onPress={() => router.push(`/other-profile/${display.username}`)}>
              <Avatar size={40} label={display.username.charAt(0)} />
              <View>
                <Text style={styles.username}>{display.username}</Text>
                <View style={styles.locationRow}>
                  <Ionicons name="location-outline" size={11} color="#9CA3AF" />
                  <Text style={styles.locationText}>{display.location}</Text>
                </View>
              </View>
            </Pressable>
            <Text style={styles.timeAgo}>{display.timeAgo}</Text>
          </View>

          <View style={styles.imageWrap}>
            <ImageWithFallback uri={display.image} height={420} borderRadius={0} fallbackText="Post image" />
            {display.quest ? (
              <View style={styles.questRibbon}>
                <Ionicons name="flash" size={12} color="#fff" />
                <Text style={styles.questRibbonText}>Quest</Text>
              </View>
            ) : null}
          </View>

          <View style={styles.actionsRow}>
            <View style={styles.actionsLeft}>
              <Pressable onPress={handleLike}>
                <Ionicons name={liked ? 'heart' : 'heart-outline'} size={24} color="#11181C" />
              </Pressable>
              <Pressable onPress={() => setCommentOpen(true)}>
                <Ionicons name="chatbubble-outline" size={24} color="#11181C" />
              </Pressable>
              <Pressable>
                <Ionicons name="paper-plane-outline" size={24} color="#11181C" />
              </Pressable>
            </View>
            <Pressable onPress={() => setSaved((prev) => !prev)}>
              <Ionicons name={saved ? 'bookmark' : 'bookmark-outline'} size={24} color="#11181C" />
            </Pressable>
          </View>

          <Text style={styles.likesText}>{`${likeCount.toLocaleString()} likes`}</Text>
          <Text style={styles.captionText}>
            <Text style={styles.username}>{`${display.username} `}</Text>
            {display.caption}
          </Text>

          {display.quest ? (
            <View style={styles.questCard}>
              <Pressable
                style={styles.questHead}
                onPress={() => router.push({ pathname: ROUTES.modal.questDetail as any, params: { questId: display.quest!.id } })}
              >
                <View style={styles.questIconWrap}>
                  <Ionicons name="flash" size={14} color="#4B5563" />
                </View>
                <View style={styles.questBody}>
                  <Text style={styles.questLabel}>Linked Quest</Text>
                  <Text style={styles.questTitle}>{display.quest.title}</Text>
                  <Text style={styles.questDesc} numberOfLines={1}>
                    {display.quest.description || 'Successfully completed!'}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color="#D1D5DB" />
              </Pressable>

              <View style={styles.progressSection}>
                <View style={styles.progressXp}>
                  <Ionicons name="flash" size={12} color="#6B7280" />
                  <Text style={styles.progressXpText}>{`+${display.quest.xp_reward} XP`}</Text>
                </View>
              </View>
            </View>
          ) : null}

          <Pressable onPress={() => setCommentOpen(true)}>
            <Text style={styles.viewComments}>{`View all ${display.comments} comments`}</Text>
          </Pressable>

          {display.comments === 0 ? (
            <View style={styles.previewWrap}>
              <Text style={styles.previewTime}>No comments yet.</Text>
            </View>
          ) : null}
        </ScrollView>
      </SafeAreaView>

      <CommentSheet
        open={commentOpen}
        onClose={() => setCommentOpen(false)}
        totalComments={display.comments}
        postId={display.id}
      />
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
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
    justifyContent: 'center',
    width: 36,
    height: 36,
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 16,
    fontWeight: '600',
  },
  userRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  userInfo: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  username: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  locationRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 2,
  },
  locationText: {
    color: '#9CA3AF',
    fontSize: 11,
  },
  timeAgo: {
    color: '#9CA3AF',
    fontSize: 11,
  },
  imageWrap: {
    position: 'relative',
  },
  questRibbon: {
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.75)',
    borderRadius: 10,
    flexDirection: 'row',
    gap: 4,
    left: 12,
    paddingHorizontal: 9,
    paddingVertical: 5,
    position: 'absolute',
    top: 12,
  },
  questRibbonText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  actionsRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  actionsLeft: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 16,
  },
  likesText: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
    paddingHorizontal: 16,
  },
  captionText: {
    color: '#11181C',
    fontSize: 14,
    lineHeight: 20,
    paddingHorizontal: 16,
    paddingTop: 6,
  },
  questCard: {
    borderColor: '#E5E7EB',
    borderRadius: 14,
    borderWidth: 1,
    marginHorizontal: 16,
    marginTop: 14,
    overflow: 'hidden',
  },
  questHead: {
    alignItems: 'center',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  questIconWrap: {
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 10,
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  questBody: {
    flex: 1,
    gap: 1,
  },
  questLabel: {
    color: '#9CA3AF',
    fontSize: 11,
  },
  questTitle: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  questDesc: {
    color: '#6B7280',
    fontSize: 12,
  },
  progressSection: {
    gap: 8,
    padding: 12,
  },
  progressMeta: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressLabel: {
    color: '#6B7280',
    fontSize: 12,
  },
  progressValue: {
    color: '#11181C',
    fontSize: 12,
    fontWeight: '600',
  },
  progressTrack: {
    backgroundColor: '#F3F4F6',
    borderRadius: 999,
    height: 6,
    overflow: 'hidden',
  },
  progressFill: {
    backgroundColor: '#11181C',
    height: '100%',
  },
  progressXp: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 4,
    justifyContent: 'flex-end',
  },
  progressXpText: {
    color: '#11181C',
    fontSize: 13,
    fontWeight: '700',
  },
  viewComments: {
    color: '#9CA3AF',
    fontSize: 14,
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  previewWrap: {
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 24,
  },
  previewRow: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: 8,
  },
  previewBody: {
    flex: 1,
    gap: 2,
  },
  previewText: {
    color: '#11181C',
    fontSize: 14,
  },
  previewTime: {
    color: '#D1D5DB',
    fontSize: 11,
  },
  emptyWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  emptyText: {
    color: '#9CA3AF',
    fontSize: 14,
  },
});
