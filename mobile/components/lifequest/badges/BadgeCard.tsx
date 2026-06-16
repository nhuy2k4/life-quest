import { Ionicons } from '@expo/vector-icons';
import { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text, View, Easing, Image } from 'react-native';

import type { BadgeItem } from '@/types/badge';
import { getRarityConfig, getProgressPercent } from './badgeUtils';

type BadgeCardProps = {
  badge: BadgeItem;
  isNew?: boolean;
  size?: number;
};

const CARD_RADIUS = 20;

/**
 * Minimalist game-style achievement card.
 * Light background, soft shadow, rounded square, rarity indicator top-right.
 */
export function BadgeCard({ badge, isNew = false, size = 104 }: BadgeCardProps) {
  const { is_unlocked, is_hidden, rarity, icon_url, name, progress } = badge;
  const config = getRarityConfig(rarity);

  // ── Entrance animation (scale + fade) ──────────────────────────────────────
  const scaleAnim = useRef(new Animated.Value(0.88)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        damping: 14,
        stiffness: 160,
        useNativeDriver: true,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 220,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }),
    ]).start();
  }, [scaleAnim, opacityAnim]);

  // ── Progress bar animation ─────────────────────────────────────────────────
  const percent = getProgressPercent(progress?.current || 0, progress?.target || 1);
  const progressAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(progressAnim, {
      toValue: percent / 100,
      duration: 700,
      delay: 200,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false, // width cannot use native driver
    }).start();
  }, [percent, progressAnim]);

  const iconSize = Math.round(size * 0.38);
  const isImage = typeof icon_url === 'string' && (icon_url.startsWith('http://') || icon_url.startsWith('https://'));
  const iconName = isImage ? 'ribbon-outline' : ((icon_url as any) || 'ribbon-outline');

  // ── Hidden locked ─────────────────────────────────────────────────────────
  if (is_hidden && !is_unlocked) {
    return (
      <Animated.View
        style={[
          styles.card,
          {
            width: size,
            height: size,
            borderRadius: CARD_RADIUS,
            opacity: opacityAnim,
            transform: [{ scale: scaleAnim }],
            backgroundColor: '#F3F4F6',
            borderColor: '#E5E7EB',
          },
        ]}
      >
        <Text style={[styles.hiddenIcon, { fontSize: iconSize * 0.8 }]}>🔒</Text>
        <Text style={styles.hiddenLabel}>???</Text>
        {/* Rarity dot top-right */}
        <View style={[styles.rarityDot, { backgroundColor: config.dotColor }]} />
      </Animated.View>
    );
  }

  const isLocked = !is_unlocked;
  const cardBg = isLocked ? '#FAFAFA' : config.bgColor;
  const cardBorder = isLocked ? '#E5E7EB' : config.borderColor;
  const iconColor = isLocked ? '#D1D5DB' : config.dotColor;

  return (
    <Animated.View
      style={[
        styles.card,
        {
          width: size,
          height: size,
          borderRadius: CARD_RADIUS,
          opacity: opacityAnim,
          transform: [{ scale: scaleAnim }],
          backgroundColor: cardBg,
          borderColor: cardBorder,
          // Subtle shadow for unlocked only
          ...(is_unlocked && {
            shadowColor: config.dotColor,
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.18,
            shadowRadius: 8,
            elevation: 3,
          }),
        },
        isLocked && styles.lockedCard,
      ]}
    >
      {/* Rarity badge top-right */}
      <View style={styles.rarityBadge}>
        <Text style={styles.rarityEmoji}>{config.iconEmoji}</Text>
      </View>

      {/* Icon */}
      <View style={styles.iconWrap}>
        {isImage ? (
          <Image
            source={{ uri: icon_url }}
            style={{
              width: iconSize * 1.5,
              height: iconSize * 1.5,
              opacity: isLocked ? 0.3 : 1,
              tintColor: isLocked ? '#C4C9D4' : undefined,
            }}
            resizeMode="contain"
          />
        ) : (
          <Ionicons name={iconName} size={iconSize} color={iconColor} />
        )}
      </View>

      {/* Title */}
      <Text
        style={[
          styles.cardTitle,
          { color: isLocked ? '#C4C9D4' : '#1F2937', fontSize: size > 100 ? 11 : 10 },
        ]}
        numberOfLines={2}
        ellipsizeMode="tail"
      >
        {name}
      </Text>

      {/* Progress bar — only for locked non-hidden badges */}
      {isLocked && !is_hidden ? (
        <View style={styles.progressWrap}>
          <View style={styles.progressBg}>
            <Animated.View
              style={[
                styles.progressFill,
                {
                  width: progressAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: ['0%', '100%'],
                  }),
                  backgroundColor: config.dotColor,
                },
              ]}
            />
          </View>
          <Text style={[styles.progressLabel, { color: config.dotColor }]}>
            {progress?.current || 0}/{progress?.target || 1}
          </Text>
        </View>
      ) : null}

      {/* "NEW" sticker for newly unlocked */}
      {isNew && is_unlocked ? (
        <View style={[styles.newSticker, { backgroundColor: config.dotColor }]}>
          <Text style={styles.newStickerText}>NEW</Text>
        </View>
      ) : null}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    alignItems: 'center',
    borderWidth: 1.5,
    justifyContent: 'center',
    padding: 8,
    position: 'relative',
    gap: 4,
  },
  lockedCard: {
    opacity: 0.55,
  },
  iconWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },
  cardTitle: {
    fontWeight: '600',
    textAlign: 'center',
    lineHeight: 14,
    paddingHorizontal: 4,
  },
  hiddenIcon: {
    textAlign: 'center',
  },
  hiddenLabel: {
    color: '#9CA3AF',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
  },
  rarityBadge: {
    position: 'absolute',
    top: 6,
    right: 6,
    zIndex: 2,
  },
  rarityEmoji: {
    fontSize: 13,
    lineHeight: 16,
  },
  rarityDot: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  progressWrap: {
    width: '100%',
    paddingHorizontal: 8,
    gap: 2,
    alignItems: 'center',
  },
  progressBg: {
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    height: 4,
    overflow: 'hidden',
    width: '100%',
  },
  progressFill: {
    borderRadius: 4,
    height: 4,
  },
  progressLabel: {
    fontSize: 9,
    fontWeight: '700',
  },
  newSticker: {
    borderRadius: 6,
    paddingHorizontal: 5,
    paddingVertical: 2,
    position: 'absolute',
    bottom: 6,
    right: 6,
  },
  newStickerText: {
    color: '#fff',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
});
