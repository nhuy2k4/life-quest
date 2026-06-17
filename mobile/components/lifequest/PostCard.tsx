import { Ionicons } from '@expo/vector-icons';
import { type Href, useRouter } from 'expo-router';
import * as Clipboard from 'expo-clipboard';
import * as Linking from 'expo-linking';
import { useEffect, useMemo, useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';

import { CommentSheet } from '@/components/lifequest/CommentSheet';
import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { Avatar } from '@/components/ui/avatar';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { useToast } from '@/contexts/ToastContext';
import { useUserContext } from '@/contexts/UserContext';
import { startQuest } from '@/services/questService';
import { deletePost, followUser, likePost, unfollowUser, unlikePost } from '@/services/socialService';
import type { Post, Quest } from '@/types';
import { getItem, StorageKeys } from '@/utils/storage';

type PostCardProps = {
  post: Post;
  attachedQuest?: Pick<Quest, 'title' | 'xpReward'> | null;
  showEligibility?: boolean;
};

export function PostCard({ post, attachedQuest = null, showEligibility = false }: PostCardProps) {
  const router = useRouter();
  const { setPosts, hiddenPostIds, hidePost, unhidePost } = usePostContext();
  const { showToast } = useToast();
  const { currentUser, setCurrentUser } = useUserContext();
  const [liked, setLiked] = useState(Boolean(post.isLiked));
  const [saved, setSaved] = useState(Boolean(post.isSaved));
  const [isFollowing, setIsFollowing] = useState(Boolean(post.followedByMe));
  const [commentOpen, setCommentOpen] = useState(false);
  const [likeCount, setLikeCount] = useState(post.likesCount);
  const [commentCount, setCommentCount] = useState(post.commentsCount);
  const [menuOpen, setMenuOpen] = useState(false);

  // Derived Quest data: preferentially use backend quest model, fallback to prop
  const questData = useMemo(() => {
    if (post.quest) {
      return {
        poiId: post.quest.poi_id,
        title: post.quest.title,
        xpReward: post.quest.xp_reward,
        poiName: post.quest.poi_name,
      };
    }
    return attachedQuest;
  }, [post.quest, attachedQuest]);

  const timeAgo = useMemo(() => post.createdAt, [post.createdAt]);
  const questId = post.quest?.id;
  const isQuestCompleted = Boolean(questId && post.submissionId);
  const canFollow = currentUser?.id !== post.author.id;
  const isOwner = currentUser?.id === post.author.id;
  const isHidden = hiddenPostIds.has(post.id);

  useEffect(() => {
    setIsFollowing(Boolean(post.followedByMe));
  }, [post.followedByMe]);

  useEffect(() => {
    setLiked(Boolean(post.isLiked));
    setLikeCount(post.likesCount);
  }, [post.isLiked, post.likesCount]);

  useEffect(() => {
    setCommentCount(post.commentsCount);
  }, [post.commentsCount]);

  const updateCommentCount = (count: number) => {
    setCommentCount(count);
    setPosts((prev) =>
      prev.map((item) =>
        item.id === post.id
          ? {
              ...item,
              commentsCount: count,
            }
          : item
      )
    );
  };

  const onToggleLike = async () => {
    const nextLiked = !liked;
    setLiked(nextLiked);
    setLikeCount((prev) => (liked ? Math.max(0, prev - 1) : prev + 1));
    setPosts((prev) =>
      prev.map((item) =>
        item.id === post.id
          ? {
              ...item,
              isLiked: nextLiked,
              likesCount: liked ? Math.max(0, item.likesCount - 1) : item.likesCount + 1,
            }
          : item
      )
    );

    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) return;

    try {
      if (nextLiked) {
        await likePost(token, post.id);
      } else {
        await unlikePost(token, post.id);
      }
    } catch {
      // Revert on API failure.
      setLiked((prev) => !prev);
      setLikeCount((prev) => (nextLiked ? Math.max(0, prev - 1) : prev + 1));
      setPosts((prev) =>
        prev.map((item) =>
          item.id === post.id
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

  const onToggleFollow = async () => {
    const nextFollowing = !isFollowing;
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      showToast('Báº¡n chÆ°a Ä‘Äƒng nháº­p.');
      return;
    }

    setIsFollowing(nextFollowing);
    setPosts((prev) =>
      prev.map((item) =>
        item.author.id === post.author.id
          ? {
              ...item,
              followedByMe: nextFollowing,
            }
          : item
      )
    );
    setCurrentUser(
      currentUser
        ? {
            ...currentUser,
            stats: {
              ...currentUser.stats,
              following: Math.max(0, currentUser.stats.following + (nextFollowing ? 1 : -1)),
            },
          }
        : currentUser
    );

    try {
      if (nextFollowing) {
        await followUser(token, post.author.id);
      } else {
        await unfollowUser(token, post.author.id);
      }
    } catch {
      setIsFollowing((prev) => !prev);
      setPosts((prev) =>
        prev.map((item) =>
          item.author.id === post.author.id
            ? {
                ...item,
                followedByMe: !nextFollowing,
              }
            : item
        )
      );
      setCurrentUser(
        currentUser
          ? {
              ...currentUser,
              stats: {
                ...currentUser.stats,
                following: Math.max(0, currentUser.stats.following + (nextFollowing ? -1 : 1)),
              },
            }
          : currentUser
      );
      showToast('Follow failed.');
    }
  };

  const onSaveQuest = async () => {
    if (!questId || saved) return;
    setSaved(true);
    setPosts((prev) =>
      prev.map((item) =>
        item.id === post.id
          ? {
              ...item,
              isSaved: true,
            }
          : item
      )
    );

    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      setSaved(false);
      setPosts((prev) =>
        prev.map((item) =>
          item.id === post.id
            ? {
                ...item,
                isSaved: false,
              }
            : item
        )
      );
      showToast('Bạn chưa đăng nhập.');
      return;
    }

    try {
      await startQuest(token, questId);
      showToast('Quest đã vào In Progress.');
    } catch {
      setSaved(false);
      setPosts((prev) =>
        prev.map((item) =>
          item.id === post.id
            ? {
                ...item,
                isSaved: false,
              }
            : item
        )
      );
      showToast('Không thể lưu quest.');
    }
  };

  const onCopyLink = async () => {
    const rawBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';
    const baseUrl = rawBaseUrl.replace(/\/+$/, '');
    const url = `${baseUrl}/social/posts/${post.id}/share`;
    await Clipboard.setStringAsync(url);
    showToast('Copied link.');
    setMenuOpen(false);
  };

  const onHidePost = () => {
    hidePost(post.id);
    showToast('Post hidden.');
    setMenuOpen(false);
  };

  const onReportPost = () => {
    showToast('Report submitted.');
    setMenuOpen(false);
  };

  const onDeletePost = async () => {
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      showToast('Bạn chưa đăng nhập.');
      return;
    }

    try {
      await deletePost(token, post.id);
      setPosts((prev) => prev.filter((item) => item.id !== post.id));
      showToast('Post deleted.');
    } catch {
      showToast('Delete failed.');
    } finally {
      setMenuOpen(false);
    }
  };

  if (isHidden) {
    return (
      <View style={styles.hiddenCard}>
        <Text style={styles.hiddenText}>Post hidden</Text>
        <Pressable style={styles.hiddenUndo} onPress={() => unhidePost(post.id)}>
          <Text style={styles.hiddenUndoText}>Undo</Text>
        </Pressable>
      </View>
    );
  }

  console.log('[PostCard Render]', post.id, 'eventRank:', post.eventRank, 'eventBadgeUrl:', post.eventBadgeUrl);
  return (
    <>
      <View style={styles.card}>
        <View style={styles.userRow}>
          <Pressable style={styles.userInfo} onPress={() => router.push(ROUTES.otherProfile(post.author.id) as Href)}>
            <Avatar size={36} uri={post.author.avatarUrl} label={post.author.username.charAt(0)} />
            <View style={styles.userTextBlock}>
              <View style={styles.usernameRow}>
                <Text style={styles.username}>{post.author.username}</Text>
                {post.eventBadgeUrl ? (
                  <Image
                    source={{ uri: post.eventBadgeUrl }}
                    style={styles.eventBadgeIcon}
                    contentFit="contain"
                  />
                ) : null}
              </View>
              {post.isFriend ? (
                <Text style={styles.friendBadge}>Bạn bè</Text>
              ) : null}
              {post.location ? (
                <View style={styles.locationRow}>
                  <Ionicons name="location-outline" size={11} color="#9CA3AF" />
                  <Text style={styles.location}>{post.location}</Text>
                </View>
              ) : null}
            </View>
          </Pressable>

          <View style={styles.rightActions}>
            {canFollow ? (
              <Pressable
                style={[styles.followChip, isFollowing ? styles.followChipMuted : styles.followChipStrong]}
                onPress={onToggleFollow}
              >
                <Ionicons name={isFollowing ? 'checkmark' : 'person-add-outline'} size={14} color={isFollowing ? '#6B7280' : '#11181C'} />
                <Text style={[styles.followText, isFollowing ? styles.followTextMuted : styles.followTextStrong]}>
                  {isFollowing ? 'Following' : 'Follow'}
                </Text>
              </Pressable>
            ) : null}
            <Pressable onPress={() => setMenuOpen(true)}>
              <Ionicons name="ellipsis-horizontal" size={18} color="#9CA3AF" />
            </Pressable>
          </View>
        </View>

        <Pressable
          onPress={() => router.push({ pathname: ROUTES.modal.postDetail, params: { postId: post.id } })}
          style={styles.imageWrap}
        >
          <ImageWithFallback uri={post.imageUrl} fallbackText="Post image" height={360} borderRadius={0} />
          {questData ? (
            <View style={styles.questRibbon}>
              <Ionicons name="flash" size={12} color="#fff" />
              <Text style={styles.questRibbonText}>Quest</Text>
            </View>
          ) : null}
          {post.event ? (
            <Pressable
              style={styles.eventRibbon}
              onPress={() =>
                router.push({
                  pathname: ROUTES.modal.eventDetail as any,
                  params: { eventId: post.event!.id },
                })
              }
            >
              <Ionicons name="trophy-outline" size={12} color="#fff" />
              <Text style={styles.questRibbonText}>{post.event.title}</Text>
            </Pressable>
          ) : null}
          {post.eventRank != null ? (
            <View
              style={[
                styles.rankOverlay,
                post.eventRank === 1
                  ? styles.rankOverlayGold
                  : post.eventRank === 2
                  ? styles.rankOverlaySilver
                  : post.eventRank === 3
                  ? styles.rankOverlayBronze
                  : styles.rankOverlayDefault,
              ]}
            >
              <Ionicons name="trophy" size={12} color="#fff" />
              <Text style={styles.rankOverlayText}>#{post.eventRank}</Text>
            </View>
          ) : null}
          {showEligibility && post.isEligible === false ? (
            <View style={styles.notEligibleOverlay}>
              <Ionicons name="ban" size={12} color="#fff" />
              <Text style={styles.notEligibleOverlayText}>Not eligible</Text>
            </View>
          ) : null}
        </Pressable>

        <View style={styles.actionRow}>
          <View style={styles.leftActionRow}>
            <Pressable onPress={onToggleLike} style={styles.actionItem}>
              <Ionicons name={liked ? 'heart' : 'heart-outline'} size={20} color="#11181C" />
              <Text style={styles.actionCount}>{likeCount}</Text>
            </Pressable>
            <Pressable onPress={() => setCommentOpen(true)} style={styles.actionItem}>
              <Ionicons name="chatbubble-outline" size={20} color="#11181C" />
              <Text style={styles.actionCount}>{commentCount}</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.textBlock}>
          <Text style={styles.caption}><Text style={styles.username}>{`${post.author.username} `}</Text>{post.caption}</Text>
        </View>

        {questData ? (
          <Pressable 
            style={styles.questChip} 
            onPress={() => {
              const questId = post.quest?.id;
              if (questId) {
                router.push({
                  pathname: ROUTES.modal.questDetail,
                  params: {
                    questId,
                    poiId: post.quest?.poi_id ?? undefined,
                    poiName: post.quest?.poi_name ?? undefined,
                  },
                });
              } else {
                router.push(ROUTES.modal.questDetail);
              }
            }}
          >
            <Ionicons name="flash" size={14} color="#6B7280" />
            <View style={styles.questTextWrap}>
              <Text style={styles.questTitle} numberOfLines={1}>{questData.title}</Text>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <Text style={styles.questMeta}>{`+${questData.xpReward} XP`}</Text>
                {post.quest?.poi_name ? (
                  <View style={styles.questLocBadge}>
                    <Ionicons name="location" size={10} color="#10B981" />
                    <Text style={styles.questLocBadgeText}>
                      {post.quest?.poi_name}
                    </Text>
                  </View>
                ) : null}
              </View>
            </View>
            {questId ? (
              isQuestCompleted ? (
                <View style={styles.saveButton}>
                  <Ionicons name="checkmark-circle" size={16} color="#10B981" />
                </View>
              ) : (
                <Pressable style={styles.saveButton} onPress={onSaveQuest} disabled={saved}>
                  <Ionicons name={saved ? 'bookmark' : 'bookmark-outline'} size={16} color="#11181C" />
                </Pressable>
              )
            ) : null}
            <Ionicons name="chevron-forward" size={14} color="#D1D5DB" />
          </Pressable>
        ) : null}

        {commentCount > 0 ? (
          <Pressable style={styles.commentsButton} onPress={() => setCommentOpen(true)}>
            <Text style={styles.commentsText}>{`View all ${commentCount} comments`}</Text>
          </Pressable>
        ) : null}

        {post.event ? (
          <Pressable
            style={styles.eventChip}
            onPress={() =>
              router.push({
                pathname: ROUTES.modal.eventDetail as any,
                params: { eventId: post.event!.id },
              })
            }
          >
            <Ionicons name="trophy-outline" size={14} color="#6B7280" />
            <Text style={styles.eventChipText} numberOfLines={1}>{post.event.title}</Text>
            <Ionicons name="chevron-forward" size={14} color="#D1D5DB" />
          </Pressable>
        ) : null}

        <Text style={styles.time}>{timeAgo}</Text>
      </View>

      <CommentSheet
        open={commentOpen}
        onClose={() => setCommentOpen(false)}
        totalComments={commentCount}
        postId={post.id}
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
            <Pressable style={styles.menuItem} onPress={onReportPost}>
              <Text style={styles.menuText}>Report</Text>
            </Pressable>
            {isOwner ? (
              <Pressable style={[styles.menuItem, styles.menuDanger]} onPress={onDeletePost}>
                <Text style={[styles.menuText, styles.menuDangerText]}>Delete</Text>
              </Pressable>
            ) : null}
          </View>
        </Pressable>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    paddingBottom: 12,
  },
  userRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  userInfo: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  userTextBlock: {
    gap: 1,
  },
  username: {
    color: '#11181C',
    fontSize: 13,
    fontWeight: '700',
  },
  friendBadge: {
    color: '#6366F1',
    fontSize: 10,
    fontWeight: '600',
  },
  locationRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 2,
  },
  location: {
    color: '#9CA3AF',
    fontSize: 11,
  },
  rightActions: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  followChip: {
    alignItems: 'center',
    borderRadius: 999,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  followChipStrong: {
    borderColor: '#11181C',
  },
  followChipMuted: {
    borderColor: '#D1D5DB',
  },
  followText: {
    fontSize: 11,
    fontWeight: '600',
  },
  followTextStrong: {
    color: '#11181C',
  },
  followTextMuted: {
    color: '#6B7280',
  },
  imageWrap: {
    width: '100%',
  },
  questRibbon: {
    alignItems: 'center',
    backgroundColor: 'rgba(17, 24, 28, 0.85)',
    borderRadius: 10,
    flexDirection: 'row',
    gap: 4,
    left: 10,
    paddingHorizontal: 8,
    paddingVertical: 5,
    position: 'absolute',
    top: 10,
  },
  eventRibbon: {
    alignItems: 'center',
    backgroundColor: 'rgba(17, 24, 28, 0.85)',
    borderRadius: 10,
    flexDirection: 'row',
    gap: 4,
    left: 10,
    maxWidth: '80%',
    paddingHorizontal: 8,
    paddingVertical: 5,
    position: 'absolute',
    top: 42,
  },
  questRibbonText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  actionRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingTop: 10,
  },
  leftActionRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 14,
  },
  actionItem: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  actionCount: {
    color: '#11181C',
    fontSize: 12,
    fontWeight: '600',
  },
  textBlock: {
    gap: 4,
    paddingHorizontal: 12,
    paddingTop: 8,
  },
  caption: {
    color: '#11181C',
    fontSize: 13,
  },
  questChip: {
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 8,
    marginHorizontal: 12,
    marginTop: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  eventChip: {
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 8,
    marginHorizontal: 12,
    marginTop: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  eventChipText: {
    color: '#1F2937',
    flex: 1,
    fontSize: 12,
    fontWeight: '700',
  },
  questTextWrap: {
    flex: 1,
  },
  questTitle: {
    color: '#1F2937',
    fontSize: 12,
    fontWeight: '700',
  },
  questMeta: {
    color: '#9CA3AF',
    fontSize: 11,
  },
  saveButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
    paddingVertical: 4,
  },
  commentsButton: {
    marginTop: 8,
    paddingHorizontal: 12,
  },
  commentsText: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  time: {
    color: '#D1D5DB',
    fontSize: 10,
    letterSpacing: 0.4,
    marginTop: 8,
    paddingHorizontal: 12,
    textTransform: 'uppercase',
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
  hiddenCard: {
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
  },
  hiddenText: {
    color: '#6B7280',
    fontSize: 13,
  },
  hiddenUndo: {
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  hiddenUndoText: {
    color: '#11181C',
    fontSize: 13,
    fontWeight: '600',
  },
  questLocBadge: {
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    borderRadius: 999,
    flexDirection: 'row',
    gap: 3,
    maxWidth: 140,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  questLocBadgeText: {
    color: '#047857',
    flexShrink: 1,
    fontSize: 10,
    fontWeight: '600',
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
  notEligibleOverlay: {
    alignItems: 'center',
    backgroundColor: 'rgba(220, 38, 38, 0.90)',
    borderRadius: 10,
    flexDirection: 'row',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 5,
    position: 'absolute',
    right: 10,
    top: 10,
  },
  notEligibleOverlayText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
});
