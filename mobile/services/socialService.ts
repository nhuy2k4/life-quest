import { requestJson } from '@/services/httpClient';
import type { Post } from '@/types';

export type FeedUser = {
  id: string;
  username: string;
};

export type FeedPost = {
  id: string;
  submission_id: string | null;
  submission_image_url: string | null;
  caption?: string | null;
  quest?: { id: string; title: string; description?: string; xp_reward: number } | null;
  user: FeedUser;
  like_count: number;
  comment_count: number;
  liked_by_me: boolean;
  created_at: string;
};

export type FeedResponse = {
  items: FeedPost[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export function mapFeedPost(post: FeedPost): Post {
  return {
    id: post.id,
    author: {
      id: post.user.id,
      username: post.user.username,
    },
    submissionId: post.submission_id ?? undefined,
    imageUrl: post.submission_image_url ?? undefined,
    caption: post.caption ?? '',
    quest: post.quest
      ? {
          id: post.quest.id,
          title: post.quest.title,
          description: post.quest.description ?? undefined,
          xp_reward: post.quest.xp_reward,
        }
      : undefined,
    createdAt: post.created_at,
    likesCount: post.like_count,
    commentsCount: post.comment_count,
    isLiked: post.liked_by_me,
  };
}

export type FeedPage = {
  items: Post[];
  page: number;
  hasNext: boolean;
};

export async function getFeed(token: string, page = 1, pageSize = 20): Promise<FeedPage> {
  const response = await requestJson<FeedResponse>(`/social/feed?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });

  return {
    items: response.items.map(mapFeedPost),
    page: response.page,
    hasNext: response.has_next,
  };
}

export type PostResponse = {
  id: string;
  submission_id: string | null;
  submission_image_url: string | null;
  caption?: string | null;
  quest?: { id: string; title: string; description?: string; xp_reward: number } | null;
  user: FeedUser;
  like_count: number;
  comment_count: number;
  liked_by_me: boolean;
  created_at: string;
};

/**
 * Tạo social post.
 * Có thể truyền submissionId (làm Quest) hoặc imageUrl (Post tự do)
 */
export async function createPost(
  token: string,
  payload: { 
    submissionId?: string | null; 
    imageUrl?: string | null; 
    caption?: string | null; 
    questId?: string | null;
  }
): Promise<PostResponse> {
  return requestJson<PostResponse>('/social/posts', {
    method: 'POST',
    token,
    body: JSON.stringify({
      submission_id: payload.submissionId || undefined,
      image_url: payload.imageUrl || undefined,
      caption: payload.caption || undefined,
      quest_id: payload.questId || undefined,
    }),
  });
}


export async function likePost(token: string, postId: string): Promise<void> {
  await requestJson('/social/posts/' + postId + '/like', {
    method: 'POST',
    token,
  });
}

export async function unlikePost(token: string, postId: string): Promise<void> {
  await requestJson('/social/posts/' + postId + '/like', {
    method: 'DELETE',
    token,
  });
}

export type CommentUser = {
  id: string;
  username: string;
};

export type CommentItem = {
  id: string;
  post_id: string;
  parent_id: string | null;
  user: CommentUser;
  content: string;
  is_deleted: boolean;
  created_at: string;
};

export type CommentListResponse = {
  items: CommentItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export async function listComments(
  token: string,
  postId: string,
  page = 1,
  pageSize = 20
): Promise<CommentItem[]> {
  const response = await requestJson<CommentListResponse>(
    `/social/posts/${postId}/comments?page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      token,
    }
  );
  return response.items;
}

export async function addComment(token: string, postId: string, content: string): Promise<void> {
  await requestJson(`/social/posts/${postId}/comments`, {
    method: 'POST',
    token,
    body: JSON.stringify({ content }),
  });
}

export async function followUser(token: string, userId: string): Promise<void> {
  await requestJson(`/social/users/${userId}/follow`, {
    method: 'POST',
    token,
  });
}

export async function unfollowUser(token: string, userId: string): Promise<void> {
  await requestJson(`/social/users/${userId}/follow`, {
    method: 'DELETE',
    token,
  });
}

export async function deletePost(token: string, postId: string): Promise<void> {
  await requestJson(`/social/posts/${postId}`, {
    method: 'DELETE',
    token,
  });
}
