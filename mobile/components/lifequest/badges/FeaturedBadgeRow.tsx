import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { FeaturedBadge } from '@/types/badge';
import { getRarityConfig } from './badgeUtils';

type FeaturedBadgeRowProps = {
  featuredBadges: FeaturedBadge[];
  onPressBadge?: (badgeId: string) => void;
};

export function FeaturedBadgeRow({ featuredBadges, onPressBadge }: FeaturedBadgeRowProps) {
  if (featuredBadges.length === 0) return null;

  return (
    <View style={styles.container}>
      <View style={styles.row}>
        {featuredBadges.map((badge) => {
          const config = getRarityConfig(badge.rarity);
          return (
            <Pressable
              key={badge.id}
              onPress={() => onPressBadge?.(badge.id)}
              style={({ pressed }) => [
                styles.pill,
                { borderColor: config.borderColor, opacity: pressed ? 0.8 : 1 },
              ]}
            >
              <Ionicons
                name={(badge.icon_url as any) || 'ribbon-outline'}
                size={14}
                color={config.borderColor}
              />
              <Text style={[styles.pillText, { color: config.labelColor }]} numberOfLines={1}>
                {badge.name}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 2,
    alignItems: 'center',
  },
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 4,
    paddingVertical: 2,
  },
  pill: {
    alignItems: 'center',
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: 'rgba(0,0,0,0.05)',
  },
  pillText: {
    fontSize: 12,
    fontWeight: '700',
    maxWidth: 100,
  },
});
