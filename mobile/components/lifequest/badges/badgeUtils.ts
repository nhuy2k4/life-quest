import type { BadgeRarity } from '@/types/badge';

// ── Light-mode rarity config ──────────────────────────────────────────────────
export const RARITY_CONFIG: Record<
  BadgeRarity,
  {
    borderColor: string;
    glowColor: string;
    labelColor: string;
    bgColor: string;       // card accent background (tinted)
    label: string;
    dotColor: string;      // small indicator dot
    iconEmoji: string;     // rarity badge emoji
  }
> = {
  common: {
    borderColor: '#D1D5DB',
    glowColor: 'transparent',
    labelColor: '#6B7280',
    bgColor: '#F9FAFB',
    label: 'Common',
    dotColor: '#9CA3AF',
    iconEmoji: '⚪',
  },
  rare: {
    borderColor: '#93C5FD',
    glowColor: 'rgba(59,130,246,0.12)',
    labelColor: '#2563EB',
    bgColor: '#EFF6FF',
    label: 'Rare',
    dotColor: '#3B82F6',
    iconEmoji: '💎',
  },
  epic: {
    borderColor: '#C4B5FD',
    glowColor: 'rgba(139,92,246,0.12)',
    labelColor: '#7C3AED',
    bgColor: '#F5F3FF',
    label: 'Epic',
    dotColor: '#A855F7',
    iconEmoji: '🔮',
  },
  legendary: {
    borderColor: '#FCD34D',
    glowColor: 'rgba(245,158,11,0.14)',
    labelColor: '#D97706',
    bgColor: '#FFFBEB',
    label: 'Legendary',
    dotColor: '#F59E0B',
    iconEmoji: '👑',
  },
};

export function getRarityConfig(rarity: string) {
  return RARITY_CONFIG[rarity as BadgeRarity] ?? RARITY_CONFIG.common;
}

export function formatUnlockDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function getProgressPercent(current: number, target: number): number {
  if (target === 0) return 100;
  return Math.min(100, Math.round((current / target) * 100));
}
