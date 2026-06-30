import { Ionicons } from '@expo/vector-icons';
import { type Href, useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Image } from 'expo-image';

import { CommentSheet } from '@/components/lifequest/CommentSheet';
import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { Avatar } from '@/components/ui/avatar';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { getPost, likePost, unlikePost, deletePost, updatePost } from '@/services/socialService';
import type { Post } from '@/types';
import { getItem, StorageKeys } from '@/utils/storage';
import { useToast } from '@/contexts/ToastContext';
import { useUserContext } from '@/contexts/UserContext';
import * as Clipboard from 'expo-clipboard';
import { Modal } from 'react-native';

export default function PostDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { posts, setPosts, hidePost } = usePostContext();
  const { showToast } = useToast();
  const { currentUser } = useUserContext();
  const postId = typeof params.postId === 'string' ? params.postId : undefined;
  const matched = useMemo(() => posts.find((item) => item.id === postId), [posts, postId]);
  const [fetchedPost, setFetchedPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(false);
  const post = matched || fetchedPost;

  const [liked, setLiked] = useState(Boolean(post?.isLiked));
  const [commentOpen, setCommentOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [likeCount, setLikeCount] = useState(post?.likesCount ?? 0);
  const [commentCount, setCommentCount] = useState(post?.commentsCount ?? 0);
  const [visibilityModalOpen, setVisibilityModalOpen] = useState(false);

  useEffect(() => {
    setLiked(Boolean(post?.isLiked));
    setLikeCount(post?.likesCount ?? 0);
  }, [post?.isLiked, post?.likesCount]);

  useEffect(() => {
    setCommentCount(post?.commentsCount ?? 0);
  }, [post?.commentsCount]);

  useEffect(() => {
    if (!postId) return;
    const fetchPostData = async () => {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;
      setLoading(true);
      try {
        const fetched = await getPost(token, postId);
        setFetchedPost(fetched);
      } catch (error) {
        console.error('Failed to fetch post:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchPostData();
  }, [postId]);

  const isOwner = currentUser?.id === post?.author.id;

  const onCopyLink = async () => {
    if (!post) return;
    const rawBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';
    const baseUrl = rawBaseUrl.replace(/\/+$/, '');
    const url = `${baseUrl}/social/posts/${post.id}/share`;
    await Clipboard.setStringAsync(url);
    showToast('Copied link.');
    setMenuOpen(false);
  };

  const onHidePost = () => {
    if (!post) return;
    hidePost(post.id);
    showToast('Post hidden.');
    setMenuOpen(false);
    router.back();
  };

  const onReportPost = () => {
    showToast('Report submitted.');
    setMenuOpen(false);
  };

  const onDeletePost = async () => {
    if (!post) return;
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      showToast('Bạn chưa đăng nhập.');
      return;
    }

    try {
      await deletePost(token, post.id);
      setPosts((prev) => prev.filter((item) => item.id !== post.id));
      showToast('Post deleted.');
      router.back();
    } catch {
      showToast('Delete failed.');
    } finally {
      setMenuOpen(false);
    }
  };

  const onChangeVisibility = async (newVisibility: 'public' | 'friends' | 'private') => {
    if (!post) return;
    if (post.event) {
      showToast('Không thể đổi chế độ riêng tư của bài viết tham gia sự kiện.');
      return;
    }
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      showToast('Bạn chưa đăng nhập.');
      return;
    }

    try {
      await updatePost(token, post.id, { visibility: newVisibility });
      // Update in local state
      if (fetchedPost) {
        setFetchedPost({
          ...fetchedPost,
          visibility: newVisibility,
        });
      }
      // Update in context
      setPosts((prev) =>
        prev.map((item) =>
          item.id === post.id ? { ...item, visibility: newVisibility } : item
        )
      );
      showToast('Đã cập nhật chế độ hiển thị.');
    } catch {
      showToast('Cập nhật thất bại.');
    } finally {
      setVisibilityModalOpen(false);
    }
  };

  if (loading && !post) {
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
          <Text style={styles.emptyText}>Loading post...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!post) {
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
    id: post.id,
    authorId: post.author.id,
    username: post.author.username,
    image: post.imageUrl,
    caption: post.caption ?? '',
    location: post.location,
    likes: likeCount,
    comments: commentCount,
    timeAgo: post.createdAt,
    quest: post.quest,
    event: post.event,
    eventRank: post.eventRank,
    eventBadgeUrl: post.eventBadgeUrl,
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

  const updateCommentCount = (count: number) => {
    setCommentCount(count);
    setPosts((prev) =>
      prev.map((item) =>
        item.id === display.id
          ? {
              ...item,
              commentsCount: count,
            }
          : item
      )
    );
  };

  return (
    <>
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.iconButton}>
            <Ionicons name="arrow-back" size={20} color="#11181C" />
          </Pressable>
          <Text style={styles.headerTitle}>Post</Text>
          <Pressable style={styles.iconButton} onPress={() => setMenuOpen(true)}>
            <Ionicons name="ellipsis-horizontal" size={20} color="#9CA3AF" />
          </Pressable>
        </View>

        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={styles.userRow}>
            <Pressable
              style={styles.userInfo}
              onPress={() => router.push(ROUTES.otherProfile(display.authorId) as Href)}>
              <Avatar size={40} uri={post.author.avatarUrl} label={display.username.charAt(0)} />
              <View>
                <View style={styles.usernameRow}>
                  <Text style={styles.username}>{display.username}</Text>
                  {display.eventBadgeUrl ? (
                    <Image
                      source={{ uri: display.eventBadgeUrl }}
                      style={styles.eventBadgeIcon}
                      contentFit="contain"
                    />
                  ) : null}
                </View>
                {post.isFriend ? (
                  <Text style={styles.friendBadge}>Bạn bè</Text>
                ) : null}
                {display.location ? (
                  <View style={styles.locationRow}>
                    <Ionicons name="location-outline" size={11} color="#9CA3AF" />
                    <Text style={styles.locationText}>{display.location}</Text>
                  </View>
                ) : null}
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
            {display.event ? (
              <Pressable
                style={styles.eventRibbon}
                onPress={() =>
                  router.push({
                    pathname: ROUTES.modal.eventDetail as any,
                    params: { eventId: display.event!.id },
                  })
                }
              >
                <Ionicons name="trophy-outline" size={12} color="#fff" />
                <Text style={styles.questRibbonText}>{display.event.title}</Text>
              </Pressable>
            ) : null}
            {display.eventRank != null ? (
              <View
                style={[
                  styles.rankOverlay,
                  display.eventRank === 1
                    ? styles.rankOverlayGold
                    : display.eventRank === 2
                    ? styles.rankOverlaySilver
                    : display.eventRank === 3
                    ? styles.rankOverlayBronze
                    : styles.rankOverlayDefault,
                ]}
              >
                <Ionicons name="trophy" size={12} color="#fff" />
                <Text style={styles.rankOverlayText}>#{display.eventRank}</Text>
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
            </View>
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
                onPress={() =>
                  router.push({
                    pathname: ROUTES.modal.questDetail as any,
                    params: {
                      questId: display.quest!.id,
                      poiId: display.quest?.poi_id ?? undefined,
                      poiName: display.quest?.poi_name ?? undefined,
                    },
                  })
                }
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

          {display.event ? (
            <Pressable
              style={styles.eventCard}
              onPress={() =>
                router.push({
                  pathname: ROUTES.modal.eventDetail as any,
                  params: { eventId: display.event!.id },
                })
              }
            >
              <Ionicons name="trophy-outline" size={14} color="#6B7280" />
              <View style={styles.eventBody}>
                <Text style={styles.questLabel}>Event</Text>
                <Text style={styles.questTitle}>{display.event.title}</Text>
              </View>
              <Ionicons name="chevron-forward" size={16} color="#D1D5DB" />
            </Pressable>
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
        onCommentCountChange={updateCommentCount}
      />

      <Modal transparent visible={menuOpen} animationType="fade" onRequestClose={() => setMenuOpen(false)}>
        <Pressable style={styles.menuOverlay} onPress={() => setMenuOpen(false)}>
          <View style={styles.menuSheet}>
            <Pressable style={styles.menuItem} onPress={onHidePost}>
              <Text style={styles.menuText}>Hide post</Text>
            </Pressable>
            <Pressable style={styles.menuItem} onPress={onCopyLink}>
              <Text style={styles.menuText}>Copy link</Text>
            </Pressable>
            {isOwner ? (
              <>
                <Pressable
                  style={styles.menuItem}
                  onPress={() => {
                    if (post.event) {
                      showToast('Bài viết tham gia Event luôn ở chế độ công khai.');
                      return;
                    }
                    setMenuOpen(false);
                    setVisibilityModalOpen(true);
                  }}
                >
                  <Text style={styles.menuText}>Chế độ hiển thị</Text>
                </Pressable>
                <Pressable style={[styles.menuItem, styles.menuDanger]} onPress={onDeletePost}>
                  <Text style={[styles.menuText, styles.menuDangerText]}>Delete</Text>
                </Pressable>
              </>
            ) : null}
          </View>
        </Pressable>
      </Modal>

      <Modal transparent visible={visibilityModalOpen} animationType="fade" onRequestClose={() => setVisibilityModalOpen(false)}>
        <Pressable style={styles.menuOverlay} onPress={() => setVisibilityModalOpen(false)}>
          <View style={styles.menuSheet}>
            <Text style={styles.visibilityModalTitle}>Chọn chế độ hiển thị</Text>
            <Pressable style={[styles.menuItem, { flexDirection: 'row', alignItems: 'center' }]} onPress={() => onChangeVisibility('public')}>
              <Ionicons name="earth" size={16} color={post?.visibility === 'public' ? '#4F46E5' : '#6B7280'} style={{ marginRight: 8 }} />
              <Text style={[styles.menuText, post?.visibility === 'public' && { color: '#4F46E5', fontWeight: '600' }]}>Công khai</Text>
            </Pressable>
            <Pressable style={[styles.menuItem, { flexDirection: 'row', alignItems: 'center' }]} onPress={() => onChangeVisibility('friends')}>
              <Ionicons name="people" size={16} color={post?.visibility === 'friends' ? '#4F46E5' : '#6B7280'} style={{ marginRight: 8 }} />
              <Text style={[styles.menuText, post?.visibility === 'friends' && { color: '#4F46E5', fontWeight: '600' }]}>Bạn bè</Text>
            </Pressable>
            <Pressable style={[styles.menuItem, { flexDirection: 'row', alignItems: 'center' }]} onPress={() => onChangeVisibility('private')}>
              <Ionicons name="lock-closed" size={16} color={post?.visibility === 'private' ? '#4F46E5' : '#6B7280'} style={{ marginRight: 8 }} />
              <Text style={[styles.menuText, post?.visibility === 'private' && { color: '#4F46E5', fontWeight: '600' }]}>Chỉ mình tôi</Text>
            </Pressable>
          </View>
        </Pressable>
      </Modal>
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
  friendBadge: {
    color: '#6366F1',
    fontSize: 10,
    fontWeight: '600',
    marginTop: 1,
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
  eventRibbon: {
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.75)',
    borderRadius: 10,
    flexDirection: 'row',
    gap: 4,
    left: 12,
    maxWidth: '80%',
    paddingHorizontal: 9,
    paddingVertical: 5,
    position: 'absolute',
    top: 44,
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
  eventCard: {
    alignItems: 'center',
    borderColor: '#E5E7EB',
    borderRadius: 14,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    marginHorizontal: 16,
    marginTop: 14,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  eventBody: {
    flex: 1,
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
  usernameRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 5,
  },
  eventBadgeIcon: {
    borderRadius: 10,
    height: 20,
    width: 20,
  },
  rankOverlay: {
    alignItems: 'center',
    borderRadius: 10,
    flexDirection: 'row',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 5,
    position: 'absolute',
    right: 10,
    top: 10,
  },
  rankOverlayGold: {
    backgroundColor: 'rgba(180, 120, 0, 0.88)',
  },
  rankOverlaySilver: {
    backgroundColor: 'rgba(100, 110, 125, 0.88)',
  },
  rankOverlayBronze: {
    backgroundColor: 'rgba(140, 80, 30, 0.88)',
  },
  rankOverlayDefault: {
    backgroundColor: 'rgba(17, 24, 28, 0.80)',
  },
  rankOverlayText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
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
  menuOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.35)',
    justifyContent: 'flex-end',
  },
  menuSheet: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 18,
    gap: 4,
  },
  menuItem: {
    paddingVertical: 12,
  },
  menuText: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '600',
  },
  menuDanger: {
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  menuDangerText: {
    color: '#B91C1C',
  },
  visibilityModalTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#374151',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    textAlign: 'center',
    marginBottom: 8,
  },
});
