import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';

export type BadgeFilter = 'all' | 'quests' | 'social' | 'streak' | 'progression' | 'trust' | 'hidden';

const FILTERS: { key: BadgeFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'quests', label: '🗺 Quests' },
  { key: 'social', label: '💬 Social' },
  { key: 'streak', label: '🔥 Streak' },
  { key: 'progression', label: '⚡ Progression' },
  { key: 'trust', label: '🛡 Trust' },
  { key: 'hidden', label: '👁 Hidden' },
];

type BadgeCategoryFilterProps = {
  active: BadgeFilter;
  onChange: (filter: BadgeFilter) => void;
};

export function BadgeCategoryFilter({ active, onChange }: BadgeCategoryFilterProps) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      {FILTERS.map((f) => {
        const isActive = f.key === active;
        return (
          <Pressable
            key={f.key}
            onPress={() => onChange(f.key)}
            style={[styles.pill, isActive ? styles.pillActive : styles.pillInactive]}
          >
            <Text style={[styles.pillText, isActive ? styles.pillTextActive : styles.pillTextInactive]}>
              {f.label}
            </Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    gap: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  pill: {
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderWidth: 1,
  },
  pillActive: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  pillInactive: {
    backgroundColor: '#1F2937',
    borderColor: '#374151',
  },
  pillText: {
    fontSize: 13,
    fontWeight: '600',
  },
  pillTextActive: {
    color: '#fff',
  },
  pillTextInactive: {
    color: '#9CA3AF',
  },
});
