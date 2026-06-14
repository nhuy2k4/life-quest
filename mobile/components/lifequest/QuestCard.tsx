import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { XPBadge } from '@/components/lifequest/XPBadge';
import type { Quest } from '@/types';

type QuestCardProps = {
  quest: Quest;
  onPress?: (questId: string) => void;
};

export function QuestCard({ quest, onPress }: QuestCardProps) {
  return (
    <Pressable onPress={() => onPress?.(quest.id)} style={styles.card}>
      <ImageWithFallback uri={quest.imageUrl} fallbackText={quest.title} height={180} borderRadius={12} />

      <View style={styles.content}>
        <Text style={styles.title}>{quest.title}</Text>
        <Text style={styles.description} numberOfLines={2}>{quest.description}</Text>

        <View style={styles.metaRow}>
          <XPBadge xp={quest.xpReward} />
          {typeof quest.durationMinutes === 'number' ? (
            <View style={styles.pill}>
              <Ionicons name="time-outline" size={12} color="#6B7280" />
              <Text style={styles.pillText}>{`${quest.durationMinutes} min`}</Text>
            </View>
          ) : null}
          {quest.difficulty ? (
            <View style={styles.pill}>
              <Ionicons name="bar-chart-outline" size={12} color="#6B7280" />
              <Text style={styles.pillText}>{quest.difficulty}</Text>
            </View>
          ) : null}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    gap: 12,
    padding: 12,
  },
  content: {
    gap: 8,
  },
  title: {
    color: '#11181C',
    fontSize: 16,
    fontWeight: '700',
  },
  description: {
    color: '#6B7280',
    fontSize: 13,
  },
  metaRow: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pill: {
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 999,
    flexDirection: 'row',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  pillText: {
    color: '#6B7280',
    fontSize: 11,
    fontWeight: '600',
  },
});
