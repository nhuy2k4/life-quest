import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

// ── Status filter ─────────────────────────────────────────────────────────────
export type StatusFilter = 'all' | 'completed' | 'in_progress' | 'locked';

const STATUS_FILTERS: { key: StatusFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'completed', label: 'Completed' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'locked', label: 'Locked' },
];

// ── Rarity filter ─────────────────────────────────────────────────────────────
export type RarityFilter = 'all' | 'common' | 'rare' | 'epic' | 'legendary';

const RARITY_FILTERS: { key: RarityFilter; emoji: string; label: string; activeColor: string }[] = [
  { key: 'common', emoji: '⚪', label: 'Common', activeColor: '#9CA3AF' },
  { key: 'rare', emoji: '💎', label: 'Rare', activeColor: '#3B82F6' },
  { key: 'epic', emoji: '🔮', label: 'Epic', activeColor: '#A855F7' },
  { key: 'legendary', emoji: '👑', label: 'Legendary', activeColor: '#F59E0B' },
];

type AchievementFilterBarProps = {
  statusFilter: StatusFilter;
  rarityFilter: RarityFilter;
  onStatusChange: (filter: StatusFilter) => void;
  onRarityChange: (filter: RarityFilter) => void;
  totalCount: number;
  unlockedCount: number;
};

export function AchievementFilterBar({
  statusFilter,
  rarityFilter,
  onStatusChange,
  onRarityChange,
  totalCount,
  unlockedCount,
}: AchievementFilterBarProps) {
  return (
    <View style={styles.wrapper}>
      {/* Top row: progress summary */}
      <View style={styles.summaryRow}>
        <Text style={styles.summaryText}>
          <Text style={styles.summaryCount}>{unlockedCount}</Text>
          <Text style={styles.summaryOf}> / {totalCount} unlocked</Text>
        </Text>
        {/* Rarity icon filters */}
        <View style={styles.rarityRow}>
          {RARITY_FILTERS.map((r) => {
            const isActive = rarityFilter === r.key;
            return (
              <Pressable
                key={r.key}
                onPress={() => onRarityChange(isActive ? 'all' : r.key)}
                style={({ pressed }) => [
                  styles.rarityBtn,
                  isActive && { backgroundColor: r.activeColor + '20', borderColor: r.activeColor },
                  { opacity: pressed ? 0.7 : 1 },
                ]}
                accessibilityLabel={r.label}
              >
                <Text style={[styles.rarityEmoji, { opacity: isActive ? 1 : 0.45 }]}>
                  {r.emoji}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Status filter pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.pillRow}
      >
        {STATUS_FILTERS.map((f) => {
          const isActive = statusFilter === f.key;
          return (
            <Pressable
              key={f.key}
              onPress={() => onStatusChange(f.key)}
              style={({ pressed }) => [
                styles.pill,
                isActive ? styles.pillActive : styles.pillInactive,
                { opacity: pressed ? 0.75 : 1 },
              ]}
            >
              <Text style={[styles.pillText, isActive ? styles.pillTextActive : styles.pillTextInactive]}>
                {f.label}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: '#fff',
    paddingBottom: 4,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  summaryRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 10,
  },
  summaryText: {},
  summaryCount: {
    color: '#111827',
    fontSize: 18,
    fontWeight: '800',
  },
  summaryOf: {
    color: '#9CA3AF',
    fontSize: 14,
    fontWeight: '500',
  },
  rarityRow: {
    flexDirection: 'row',
    gap: 6,
  },
  rarityBtn: {
    alignItems: 'center',
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: 'transparent',
    height: 34,
    justifyContent: 'center',
    width: 34,
  },
  rarityEmoji: {
    fontSize: 16,
    lineHeight: 20,
  },
  pillRow: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingBottom: 10,
  },
  pill: {
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 7,
    borderWidth: 1.5,
  },
  pillActive: {
    backgroundColor: '#111827',
    borderColor: '#111827',
  },
  pillInactive: {
    backgroundColor: '#fff',
    borderColor: '#E5E7EB',
  },
  pillText: {
    fontSize: 13,
    fontWeight: '700',
  },
  pillTextActive: {
    color: '#fff',
  },
  pillTextInactive: {
    color: '#6B7280',
  },
});
