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
    title: string;
    description?: string;
    xp_reward: number;
  };
  createdAt: string;
  likesCount: number;
  commentsCount: number;
  isLiked?: boolean;
  isSaved?: boolean;
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
