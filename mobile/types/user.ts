export interface UserStats {
  posts: number;
  streak: number;
  questsCompleted: number;
  followers: number;
  following: number;
}

export interface UserProfile {
  id: string;
  username: string;
  displayName: string;
  avatarUrl?: string;
  bio?: string;
  level: number;
  currentXp: number;
  nextLevelXp: number;
  isFollowing?: boolean;
  isSelf?: boolean;
  stats: UserStats;
}
