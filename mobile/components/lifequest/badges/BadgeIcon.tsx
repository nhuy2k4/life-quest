import { Ionicons } from '@expo/vector-icons';
import { useEffect } from 'react';
import { StyleSheet, Text, View, Image } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withSequence,
  withDelay,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';

import type { BadgeItem } from '@/types/badge';
import { getRarityConfig } from './badgeUtils';

type BadgeIconProps = {
  badge: BadgeItem;
  size?: number;
  isNew?: boolean;
  showLabel?: boolean;
};

const ICON_SIZE_RATIO = 0.52;

export function BadgeIcon({ badge, size = 72, isNew = false, showLabel = true }: BadgeIconProps) {
  const { is_unlocked, is_hidden, rarity, icon_url, name } = badge;
  const config = getRarityConfig(rarity);

  const scale = useSharedValue(0.85);
  const glowOpacity = useSharedValue(is_unlocked ? 1 : 0);

  useEffect(() => {
    // Entrance animation
    scale.value = withSpring(1, { damping: 12, stiffness: 150 });

    // Glow pulse for rare+ unlocked badges
    if (is_unlocked && (rarity === 'rare' || rarity === 'epic' || rarity === 'legendary')) {
      glowOpacity.value = withDelay(
        300,
        withRepeat(
          withSequence(
            withTiming(0.6, { duration: 1200, easing: Easing.inOut(Easing.sine) }),
            withTiming(1, { duration: 1200, easing: Easing.inOut(Easing.sine) })
          ),
          -1,
          true
        )
      );
    }
  }, [is_unlocked, rarity, scale, glowOpacity]);

  const animatedContainerStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const animatedGlowStyle = useAnimatedStyle(() => ({
    opacity: glowOpacity.value,
  }));

  const iconSize = Math.round(size * ICON_SIZE_RATIO);
  const isImage = typeof icon_url === 'string' && (icon_url.startsWith('http://') || icon_url.startsWith('https://'));
  const iconName = isImage ? 'ribbon-outline' : ((icon_url as any) || 'ribbon-outline');

  // Hidden and locked rendering
  if (is_hidden && !is_unlocked) {
    return (
      <View style={[styles.wrapper, { width: size, height: size + (showLabel ? 22 : 0) }]}>
        <Animated.View style={animatedContainerStyle}>
          <View
            style={[
              styles.iconContainer,
              {
                width: size,
                height: size,
                borderRadius: size * 0.28,
                backgroundColor: '#1F2937',
                borderColor: '#374151',
                borderWidth: 2,
              },
            ]}
          >
            <Text style={[styles.hiddenQuestion, { fontSize: size * 0.32 }]}>?</Text>
          </View>
        </Animated.View>
        {showLabel ? (
          <Text style={styles.hiddenLabel} numberOfLines={1}>
            ???
          </Text>
        ) : null}
      </View>
    );
  }

  const isLocked = !is_unlocked;
  const borderColor = isLocked ? '#4B5563' : config.borderColor;
  const bgColor = isLocked ? '#1F2937' : '#111827';

  return (
    <View style={[styles.wrapper, { width: size, height: size + (showLabel ? 22 : 0) }]}>
      <Animated.View style={animatedContainerStyle}>
        {/* Glow halo */}
        {!isLocked && config.glowColor !== 'transparent' ? (
          <Animated.View
            style={[
              styles.glowHalo,
              {
                width: size + 12,
                height: size + 12,
                borderRadius: (size + 12) * 0.3,
                backgroundColor: config.glowColor,
                top: -6,
                left: -6,
              },
              animatedGlowStyle,
            ]}
          />
        ) : null}

        <View
          style={[
            styles.iconContainer,
            {
              width: size,
              height: size,
              borderRadius: size * 0.28,
              backgroundColor: bgColor,
              borderColor,
              borderWidth: 2,
              opacity: isLocked ? 0.45 : 1,
            },
          ]}
        >
          {isImage ? (
            <Image
              source={{ uri: icon_url }}
              style={{
                width: size * 0.65,
                height: size * 0.65,
                opacity: isLocked ? 0.3 : 1,
                tintColor: isLocked ? '#6B7280' : undefined,
              }}
              resizeMode="contain"
            />
          ) : (
            <Ionicons
              name={iconName}
              size={iconSize}
              color={isLocked ? '#6B7280' : config.borderColor}
            />
          )}
          {/* "NEW" badge for newly unlocked */}
          {isNew && !isLocked ? (
            <View style={styles.newBadge}>
              <Text style={styles.newBadgeText}>NEW</Text>
            </View>
          ) : null}
        </View>
      </Animated.View>
      {showLabel ? (
        <Text
          style={[
            styles.label,
            { color: isLocked ? '#6B7280' : '#E5E7EB', fontSize: size < 56 ? 10 : 11 },
          ]}
          numberOfLines={1}
        >
          {name}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
    position: 'relative',
  },
  glowHalo: {
    position: 'absolute',
    zIndex: 0,
  },
  iconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    zIndex: 1,
  },
  hiddenQuestion: {
    color: '#6B7280',
    fontWeight: '900',
  },
  hiddenLabel: {
    color: '#6B7280',
    fontSize: 11,
    marginTop: 4,
  },
  label: {
    fontWeight: '600',
    marginTop: 5,
    textAlign: 'center',
    maxWidth: 72,
  },
  newBadge: {
    backgroundColor: '#10B981',
    borderRadius: 4,
    bottom: 4,
    paddingHorizontal: 4,
    paddingVertical: 1,
    position: 'absolute',
    right: 4,
  },
  newBadgeText: {
    color: '#fff',
    fontSize: 8,
    fontWeight: '800',
  },
});
