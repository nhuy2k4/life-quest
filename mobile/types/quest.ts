export type QuestDifficulty = 'easy' | 'medium' | 'hard';

export interface QuestStep {
  id: string;
  title: string;
  completed: boolean;
}

export interface Quest {
  id: string;
  title: string;
  description: string;
  imageUrl?: string;
  xpReward: number;
  durationMinutes?: number;
  difficulty?: QuestDifficulty;
  participants?: number;
  steps?: QuestStep[];
}

export interface Reward {
  id: string;
  title: string;
  description?: string;
  type: 'badge' | 'xp_boost' | 'rare_item';
  claimed: boolean;
}
