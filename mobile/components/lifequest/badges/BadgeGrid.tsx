import { Pressable, StyleSheet, View, Dimensions, FlatList } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

import type { BadgeItem } from '@/types/badge';
import { BadgeCard } from './BadgeCard';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const COLUMNS = 3;
const H_PADDING = 16;
const GAP = 10;
const CARD_SIZE = Math.floor((SCREEN_WIDTH - H_PADDING * 2 - GAP * (COLUMNS - 1)) / COLUMNS);

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

type PressableCardProps = {
  badge: BadgeItem;
  isNew: boolean;
  onPress: (badge: BadgeItem) => void;
};

function PressableCard({ badge, isNew, onPress }: PressableCardProps) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <AnimatedPressable
      style={animatedStyle}
      onPressIn={() => {
        scale.value = withSpring(0.93, { damping: 12, stiffness: 300 });
      }}
      onPressOut={() => {
        scale.value = withSpring(1, { damping: 12, stiffness: 300 });
      }}
      onPress={() => onPress(badge)}
    >
      <BadgeCard badge={badge} size={CARD_SIZE} isNew={isNew} />
    </AnimatedPressable>
  );
}

type BadgeGridProps = {
  badges: BadgeItem[];
  newlyUnlockedIds?: Set<string>;
  onPressBadge: (badge: BadgeItem) => void;
};

export function BadgeGrid({ badges, newlyUnlockedIds, onPressBadge }: BadgeGridProps) {
  return (
    <FlatList
      data={badges}
      numColumns={COLUMNS}
      keyExtractor={(item) => item.id}
      scrollEnabled={false}
      contentContainerStyle={styles.container}
      columnWrapperStyle={styles.row}
      renderItem={({ item }) => (
        <PressableCard
          badge={item}
          isNew={newlyUnlockedIds?.has(item.id) ?? false}
          onPress={onPressBadge}
        />
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: H_PADDING,
    paddingTop: 14,
    paddingBottom: 24,
    gap: GAP,
  },
  row: {
    gap: GAP,
    justifyContent: 'flex-start',
  },
});
