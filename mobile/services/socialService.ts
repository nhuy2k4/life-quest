import { requestJson } from '@/services/httpClient';
import type { Post } from '@/types';

export type FeedUser = {
  id: string;
  username: string;
  avatar_url?: string | null;
};

export type FeedPost = {
  id: string;
  submission_id: string | null;
  submission_image_url: string | null;
  caption?: string | null;
  location_name?: string | null;
  quest?: { id: string; poi_id?: string | null; title: string; description?: string; xp_reward: number; poi_name?: string | null; } | null;
  event?: { id: string; title: string } | null;
  user: FeedUser;
  like_count: number;
  comment_count: number;
  liked_by_me: boolean;
  followed_by_me: boolean;
  is_friend?: boolean;
  created_at: string;
  visibility?: 'public' | 'friends' | 'private';
  final_score?: number;
  reasons?: string[];
  event_rank?: number | null;
  event_badge_url?: string | null;
  is_eligible?: boolean;
};

export type FeedResponse = {
  items: FeedPost[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export function mapFeedPost(post: FeedPost): Post {
  if (post.event_rank != null || post.event_badge_url != null) {
    console.log('[Feed] event post:', post.id, 'rank:', post.event_rank, 'badge:', post.event_badge_url);
  }
  return {
    id: post.id,
    author: {
      id: post.user.id,
      username: post.user.username,
      avatarUrl: post.user.avatar_url ?? undefined,
    },
    submissionId: post.submission_id ?? undefined,
    imageUrl: post.submission_image_url ?? undefined,
    caption: post.caption ?? '',
    location: post.location_name ?? undefined,
    quest: post.quest
      ? {
          id: post.quest.id,
          poi_id: post.quest.poi_id ?? null,
          title: post.quest.title,
          description: post.quest.description ?? undefined,
          xp_reward: post.quest.xp_reward,
          poi_name: post.quest.poi_name ?? null,
        }
      : undefined,
    event: post.event
      ? {
          id: post.event.id,
          title: post.event.title,
        }
      : undefined,
    visibility: post.visibility || 'public',
    createdAt: post.created_at,
    likesCount: post.like_count,
    commentsCount: post.comment_count,
    isLiked: post.liked_by_me,
    followedByMe: post.followed_by_me,
    isFriend: post.is_friend,
    recommendationReasons: post.reasons,
    recommendationScore: post.final_score,
    eventRank: post.event_rank ?? undefined,
    eventBadgeUrl: post.event_badge_url ?? undefined,
    isEligible: post.is_eligible,
  };
}

export type FeedPage = {
  items: Post[];
  page: number;
  hasNext: boolean;
};

export async function getFeed(
  token: string,
  page = 1,
  pageSize = 20,
  scope: 'all' | 'following' = 'all'
): Promise<FeedPage> {
  const response = await requestJson<FeedResponse>(`/social/feed?page=${page}&page_size=${pageSize}&scope=${scope}`, {
    method: 'GET',
    token,
  });

  return {
    items: response.items.map(mapFeedPost),
    page: response.page,
    hasNext: response.has_next,
  };
}

export async function searchPosts(token: string, query: string, page = 1, pageSize = 20): Promise<FeedPage> {
  const response = await requestJson<FeedResponse>(
    `/social/search?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      token,
    }
  );

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
  location_name?: string | null;
  quest?: { id: string; poi_id?: string | null; title: string; description?: string; xp_reward: number; poi_name?: string | null; } | null;
  event?: { id: string; title: string } | null;
  user: FeedUser;
  like_count: number;
  comment_count: number;
  liked_by_me: boolean;
  followed_by_me: boolean;
  is_friend?: boolean;
  event_rank?: number | null;
  event_badge_url?: string | null;
  visibility?: 'public' | 'friends' | 'private';
  created_at: string;
};

export type EventListItem = {
  id: string;
  title: string;
  description?: string | null;
  banner_url?: string | null;
  start_at: string;
  end_at: string;
  status: 'draft' | 'active' | 'ended';
};

export type EventDetail = EventListItem & {
  reward_config: { rank_from: number; rank_to: number; bonus_xp: number; badge_id?: string | null }[];
  quests: { id: string; title: string; description?: string | null; xp_reward: number }[];
  is_joined?: boolean;
};

export type EventLeaderboardItem = {
  rank: number;
  user: FeedUser;
  post: {
    id: string | null;
    image_url?: string | null;
    like_count: number;
    is_deleted: boolean;
  };
};

export type EventLeaderboardResponse = {
  items: EventLeaderboardItem[];
  total: number;
};

export async function getEvents(token: string, status?: 'draft' | 'active' | 'ended'): Promise<EventListItem[]> {
  const url = status ? `/events?status=${status}` : '/events';
  return requestJson<EventListItem[]>(url, {
    method: 'GET',
    token,
  });
}

export async function getEventDetail(token: string, eventId: string): Promise<EventDetail> {
  return requestJson<EventDetail>(`/events/${eventId}`, {
    method: 'GET',
    token,
  });
}

export async function getEventLeaderboard(token: string, eventId: string, limit = 5): Promise<EventLeaderboardResponse> {
  return requestJson<EventLeaderboardResponse>(`/events/${eventId}/leaderboard?limit=${limit}`, {
    method: 'GET',
    token,
  });
}

export async function getEventPosts(token: string, eventId: string, page = 1, pageSize = 20): Promise<FeedPage> {
  const response = await requestJson<FeedResponse>(`/events/${eventId}/posts?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });

  return {
    items: response.items.map(mapFeedPost),
    page: response.page,
    hasNext: response.has_next,
  };
}

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
    locationName?: string | null;
    questId?: string | null;
    poiId?: string | null;
    visibility?: 'public' | 'friends' | 'private';
    isEvent?: boolean;
  }
): Promise<PostResponse> {
  return requestJson<PostResponse>('/social/posts', {
    method: 'POST',
    token,
    body: JSON.stringify({
      submission_id: payload.submissionId || undefined,
      image_url: payload.imageUrl || undefined,
      caption: payload.caption || undefined,
      location_name: payload.locationName || undefined,
      quest_id: payload.questId || undefined,
      poi_id: payload.poiId || undefined,
      visibility: payload.visibility || 'public',
      is_event: payload.isEvent || undefined,
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

export async function addComment(token: string, postId: string, content: string): Promise<Post> {
  const response = await requestJson<PostResponse>(`/social/posts/${postId}/comments`, {
    method: 'POST',
    token,
    body: JSON.stringify({ content }),
  });
  return mapFeedPost(response as FeedPost);
}

export async function getPost(token: string, postId: string): Promise<Post> {
  const response = await requestJson<PostResponse>(`/social/posts/${postId}`, {
    method: 'GET',
    token,
  });
  return mapFeedPost(response as FeedPost);
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

export async function getFriends(token: string, userId: string, page = 1, pageSize = 20): Promise<{ items: FeedUser[]; total: number; page: number; page_size: number }> {
  return requestJson(`/social/users/${userId}/friends?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });
}

export async function getFollowers(token: string, userId: string, page = 1, pageSize = 20): Promise<{ items: FeedUser[]; total: number; page: number; page_size: number }> {
  return requestJson(`/social/users/${userId}/followers?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });
}

export async function getFollowing(token: string, userId: string, page = 1, pageSize = 20): Promise<{ items: FeedUser[]; total: number; page: number; page_size: number }> {
  return requestJson(`/social/users/${userId}/following?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });
}

export async function deletePost(token: string, postId: string): Promise<void> {
  await requestJson(`/social/posts/${postId}`, {
    method: 'DELETE',
    token,
  });
}

export async function updatePost(
  token: string,
  postId: string,
  payload: {
    caption?: string | null;
    visibility?: 'public' | 'friends' | 'private';
  }
): Promise<PostResponse> {
  return requestJson<PostResponse>(`/social/posts/${postId}`, {
    method: 'PATCH',
    token,
    body: JSON.stringify(payload),
  });
}

export async function getUserAwards(token: string, userId: string, page = 1, pageSize = 20): Promise<FeedPage> {
  const response = await requestJson<FeedResponse>(`/social/users/${userId}/awards?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    token,
  });

  return {
    items: response.items.map(mapFeedPost),
    page: response.page,
    hasNext: response.has_next,
  };
}
