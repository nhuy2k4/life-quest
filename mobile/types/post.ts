export interface PostAuthor {
  id: string;
  username: string;
  avatarUrl?: string;
}

export interface Post {
  id: string;
  author: PostAuthor;
  submissionId?: string;
  imageUrl?: string;
  caption: string;
  location?: string;
  questId?: string;
  quest?: {
    id: string;
    poi_id?: string | null;
    title: string;
    description?: string;
    xp_reward: number;
    poi_name?: string | null;
  };
  event?: {
    id: string;
    title: string;
  };
  createdAt: string;
  visibility?: 'public' | 'friends' | 'private';
  likesCount: number;
  commentsCount: number;
  isLiked?: boolean;
  isSaved?: boolean;
  followedByMe?: boolean;
  isFriend?: boolean;
  recommendationReasons?: string[];
  recommendationScore?: number;
  eventRank?: number;
  eventBadgeUrl?: string;
  isEligible?: boolean;
}

export interface Comment {
  id: string;
  postId: string;
  author: PostAuthor;
  content: string;
  createdAt: string;
  replies?: Reply[];
}

export interface Reply {
  id: string;
  commentId: string;
  author: PostAuthor;
  content: string;
  createdAt: string;
}
