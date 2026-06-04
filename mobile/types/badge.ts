export type BadgeRarity = 'common' | 'rare' | 'epic' | 'legendary';

export type BadgeCategory =
  | 'quests'
  | 'social'
  | 'streak'
  | 'progression'
  | 'trust'
  | 'hidden';

export interface BadgeProgress {
  current: number;
  target: number;
}

export interface BadgeCriteria {
  type: string;
  target?: number;
  count?: number;
}

export interface BadgeItem {
  id: string;
  name: string;
  description: string;
  icon_url: string;
  rarity: BadgeRarity;
  category: string;
  criteria: BadgeCriteria;
  is_hidden: boolean;
  is_unlocked: boolean;
  unlocked_at: string | null;
  progress: BadgeProgress;
}

export interface FeaturedBadge {
  id: string;
  name: string;
  icon_url: string;
  rarity: BadgeRarity;
  unlocked_at: string | null;
}

export interface BadgeListResponse {
  data: BadgeItem[];
  total: number;
}

export interface FeaturedBadgeResponse {
  data: FeaturedBadge[];
}
