import { Ionicons } from '@expo/vector-icons';
import { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { Avatar } from '@/components/ui/avatar';
import { BottomSheetShell } from '@/components/ui/bottom-sheet-shell';
import { addComment, listComments, type CommentItem as ApiCommentItem } from '@/services/socialService';
import { getItem, StorageKeys } from '@/utils/storage';

type Reply = {
  id: string;
  username: string;
  text: string;
  likes: number;
  liked: boolean;
  time: string;
};

type CommentItem = {
  id: string;
  username: string;
  text: string;
  likes: number;
  liked: boolean;
  time: string;
  replies: Reply[];
  showReplies: boolean;
};

const initialComments: CommentItem[] = [];

type CommentSheetProps = {
  open: boolean;
  onClose: () => void;
  postId?: string;
  totalComments?: number;
};

function mapApiComment(comment: ApiCommentItem): CommentItem {
  return {
    id: comment.id,
    username: comment.user.username,
    text: comment.is_deleted ? '' : comment.content,
    likes: 0,
    liked: false,
    time: comment.created_at,
    replies: [],
    showReplies: false,
  };
}

export function CommentSheet({ open, onClose, postId, totalComments = 0 }: CommentSheetProps) {
  const [comments, setComments] = useState<CommentItem[]>(initialComments);
  const [inputText, setInputText] = useState('');
  const [replyingTo, setReplyingTo] = useState<{ commentId: string; username: string } | null>(null);

  const total = useMemo(() => totalComments + comments.filter((c) => c.username === 'You').length, [comments, totalComments]);

  const toggleLikeComment = (commentId: string) => {
    setComments((prev) =>
      prev.map((c) =>
        c.id === commentId ? { ...c, liked: !c.liked, likes: c.liked ? c.likes - 1 : c.likes + 1 } : c
      )
    );
  };

  const toggleLikeReply = (commentId: string, replyId: string) => {
    setComments((prev) =>
      prev.map((c) =>
        c.id !== commentId
          ? c
          : {
              ...c,
              replies: c.replies.map((r) =>
                r.id === replyId ? { ...r, liked: !r.liked, likes: r.liked ? r.likes - 1 : r.likes + 1 } : r
              ),
            }
      )
    );
  };

  const toggleShowReplies = (commentId: string) => {
    setComments((prev) => prev.map((c) => (c.id === commentId ? { ...c, showReplies: !c.showReplies } : c)));
  };

  const handleReply = (commentId: string, username: string) => {
    setReplyingTo({ commentId, username });
    setInputText(`@${username} `);
  };

  const handleSubmit = async () => {
    if (!inputText.trim()) return;

    const token = await getItem<string>(StorageKeys.accessToken);
    if (token && postId) {
      try {
        await addComment(token, postId, inputText.trim());
      } catch {
        // Fall back to local insert if API fails.
      }
    }

    if (replyingTo) {
      setComments((prev) =>
        prev.map((c) =>
          c.id !== replyingTo.commentId
            ? c
            : {
                ...c,
                showReplies: true,
                replies: [
                  ...c.replies,
                  {
                    id: `r${Date.now()}`,
                    username: 'You',
                    text: inputText,
                    likes: 0,
                    liked: false,
                    time: 'just now',
                  },
                ],
              }
        )
      );
    } else {
      setComments((prev) => [
        {
          id: `c${Date.now()}`,
          username: 'You',
          text: inputText,
          likes: 0,
          liked: false,
          time: 'just now',
          replies: [],
          showReplies: false,
        },
        ...prev,
      ]);
    }

    setInputText('');
    setReplyingTo(null);
  };

  useEffect(() => {
    const loadComments = async () => {
      if (!open || !postId) return;
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      try {
        const items = await listComments(token, postId);
        setComments(items.map(mapApiComment));
      } catch {
        // Keep local comments if API fails.
      }
    };

    void loadComments();
  }, [open, postId]);

  return (
    <BottomSheetShell open={open} onClose={onClose} height={560}>
      <View style={styles.handle} />

      <View style={styles.header}>
        <Text style={styles.headerTitle}>{`${total} Comments`}</Text>
        <Pressable onPress={onClose}>
          <Ionicons name="close" size={20} color="#6B7280" />
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.listContent} style={styles.list}>
        {comments.map((comment) => (
          <View key={comment.id} style={styles.commentBlock}>
            <View style={styles.row}>
              <Avatar size={32} label={comment.username.charAt(0)} />
              <View style={styles.flex1}>
                <View style={styles.rowTop}>
                  <View style={styles.flex1}>
                    <Text style={styles.meta}>{`${comment.username} · ${comment.time}`}</Text>
                    <Text style={styles.body}>{comment.text}</Text>
                  </View>
                  <Pressable onPress={() => toggleLikeComment(comment.id)} style={styles.likeColumn}>
                    <Ionicons
                      name={comment.liked ? 'heart' : 'heart-outline'}
                      size={16}
                      color={comment.liked ? '#11181C' : '#9CA3AF'}
                    />
                    <Text style={styles.likes}>{comment.likes}</Text>
                  </Pressable>
                </View>

                <View style={styles.actionsRow}>
                  <Pressable onPress={() => handleReply(comment.id, comment.username)}>
                    <Text style={styles.actionText}>Reply</Text>
                  </Pressable>
                  {comment.replies.length > 0 ? (
                    <Pressable onPress={() => toggleShowReplies(comment.id)}>
                      <Text style={styles.actionText}>
                        {comment.showReplies ? 'Hide replies' : `View ${comment.replies.length} replies`}
                      </Text>
                    </Pressable>
                  ) : null}
                </View>

                {comment.showReplies ? (
                  <View style={styles.repliesWrap}>
                    {comment.replies.map((reply) => (
                      <View key={reply.id} style={styles.row}>
                        <Avatar size={24} label={reply.username.charAt(0)} />
                        <View style={styles.flex1}>
                          <View style={styles.rowTop}>
                            <View style={styles.flex1}>
                              <Text style={styles.meta}>{`${reply.username} · ${reply.time}`}</Text>
                              <Text style={styles.body}>{reply.text}</Text>
                            </View>
                            <Pressable onPress={() => toggleLikeReply(comment.id, reply.id)} style={styles.likeColumn}>
                              <Ionicons
                                name={reply.liked ? 'heart' : 'heart-outline'}
                                size={14}
                                color={reply.liked ? '#11181C' : '#9CA3AF'}
                              />
                              <Text style={styles.likes}>{reply.likes}</Text>
                            </Pressable>
                          </View>
                          <Pressable onPress={() => handleReply(comment.id, reply.username)}>
                            <Text style={styles.actionText}>Reply</Text>
                          </Pressable>
                        </View>
                      </View>
                    ))}
                  </View>
                ) : null}
              </View>
            </View>
          </View>
        ))}
      </ScrollView>

      <View style={styles.inputWrap}>
        {replyingTo ? (
          <View style={styles.replyingBanner}>
            <Text style={styles.replyingText}>{`Replying to @${replyingTo.username}`}</Text>
            <Pressable
              onPress={() => {
                setReplyingTo(null);
                setInputText('');
              }}>
              <Ionicons name="close" size={14} color="#6B7280" />
            </Pressable>
          </View>
        ) : null}
        <View style={styles.row}>
          <Avatar size={30} label="Y" />
          <View style={styles.inputBubble}>
            <TextInput
              placeholder="Add a comment..."
              placeholderTextColor="#9CA3AF"
              style={styles.input}
              value={inputText}
              onChangeText={setInputText}
              onSubmitEditing={handleSubmit}
              returnKeyType="send"
            />
            <Pressable disabled={!inputText.trim()} onPress={handleSubmit}>
              <Ionicons name="send" size={16} color={inputText.trim() ? '#11181C' : '#D1D5DB'} />
            </Pressable>
          </View>
        </View>
      </View>
    </BottomSheetShell>
  );
}

const styles = StyleSheet.create({
  handle: {
    alignSelf: 'center',
    backgroundColor: '#D1D5DB',
    borderRadius: 999,
    height: 4,
    marginBottom: 10,
    width: 38,
  },
  header: {
    alignItems: 'center',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingBottom: 10,
    paddingHorizontal: 4,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  list: {
    flex: 1,
  },
  listContent: {
    gap: 14,
    paddingTop: 12,
    paddingBottom: 16,
  },
  commentBlock: {
    gap: 8,
  },
  row: {
    flexDirection: 'row',
    gap: 10,
  },
  rowTop: {
    flexDirection: 'row',
    gap: 8,
  },
  flex1: {
    flex: 1,
  },
  meta: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 2,
  },
  body: {
    color: '#11181C',
    fontSize: 14,
  },
  likeColumn: {
    alignItems: 'center',
    gap: 2,
  },
  likes: {
    color: '#9CA3AF',
    fontSize: 11,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 4,
  },
  actionText: {
    color: '#6B7280',
    fontSize: 12,
  },
  repliesWrap: {
    borderLeftColor: '#F3F4F6',
    borderLeftWidth: 2,
    gap: 12,
    marginTop: 8,
    paddingLeft: 8,
  },
  inputWrap: {
    borderTopColor: '#F3F4F6',
    borderTopWidth: 1,
    gap: 8,
    paddingTop: 10,
  },
  replyingBanner: {
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  replyingText: {
    color: '#6B7280',
    fontSize: 12,
  },
  inputBubble: {
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 999,
    flex: 1,
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  input: {
    flex: 1,
    fontSize: 14,
    paddingVertical: 0,
  },
});
