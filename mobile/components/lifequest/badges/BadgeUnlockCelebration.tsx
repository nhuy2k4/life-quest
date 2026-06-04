import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useEffect, useCallback } from 'react';
import {
  Animated,
  Dimensions,
  Easing,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import ReAnimated, {
  useSharedValue,
  useAnimatedStyle,
  withDelay,
  withRepeat,
  withSequence,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

import type { BadgeItem } from '@/types/badge';
import { getRarityConfig } from './badgeUtils';
import { BadgeCard } from './BadgeCard';

const { width: W, height: H } = Dimensions.get('window');
const CONFETTI_COLORS = ['#FCD34D', '#A78BFA', '#60A5FA', '#34D399', '#F87171', '#FB923C'];
const CONFETTI_COUNT = 20;

function randomBetween(a: number, b: number) {
  return a + Math.random() * (b - a);
}

// Single confetti piece — pure Animated API
function ConfettiPiece({ delay, color }: { delay: number; color: string }) {
  const startX = randomBetween(W * 0.05, W * 0.95);
  const targetY = randomBetween(H * 0.3, H * 0.7);
  const drift = randomBetween(-60, 60);
  const size = randomBetween(7, 13);

  const y = new Animated.Value(-20);
  const x = new Animated.Value(startX);
  const rot = new Animated.Value(0);
  const op = new Animated.Value(0);

  useEffect(() => {
    Animated.sequence([
      Animated.delay(delay),
      Animated.parallel([
        Animated.timing(y, { toValue: targetY, duration: 1600, easing: Easing.out(Easing.quad), useNativeDriver: true }),
        Animated.timing(x, { toValue: startX + drift, duration: 1600, useNativeDriver: true }),
        Animated.timing(rot, { toValue: randomBetween(-3, 3), duration: 1600, useNativeDriver: true }),
        Animated.sequence([
          Animated.timing(op, { toValue: 1, duration: 100, useNativeDriver: true }),
          Animated.delay(1100),
          Animated.timing(op, { toValue: 0, duration: 400, useNativeDriver: true }),
        ]),
      ]),
    ]).start();
  }, []);

  const spin = rot.interpolate({ inputRange: [-3, 3], outputRange: ['-540deg', '540deg'] });

  return (
    <Animated.View
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: size,
        height: size * 0.55,
        backgroundColor: color,
        borderRadius: 2,
        opacity: op,
        transform: [{ translateY: y }, { translateX: x }, { rotate: spin }],
      }}
    />
  );
}

// ── Toast for common badges ───────────────────────────────────────────────────
function BadgeToast({ badge, onDismiss }: { badge: BadgeItem; onDismiss: () => void }) {
  const ty = useSharedValue(-120);
  const op = useSharedValue(0);

  useEffect(() => {
    ty.value = withSpring(0, { damping: 16, stiffness: 220 });
    op.value = withTiming(1, { duration: 200 });

    const timer = setTimeout(() => {
      ty.value = withTiming(-120, { duration: 280 });
      op.value = withTiming(0, { duration: 280 });
      setTimeout(onDismiss, 300);
    }, 3200);
    return () => clearTimeout(timer);
  }, []);

  const config = getRarityConfig(badge.rarity);
  const style = useAnimatedStyle(() => ({
    transform: [{ translateY: ty.value }],
    opacity: op.value,
  }));

  return (
    <ReAnimated.View style={[styles.toast, style]}>
      <View style={[styles.toastIconBg, { backgroundColor: config.bgColor, borderColor: config.borderColor }]}>
        <Ionicons
          name={(badge.icon_url as any) || 'ribbon-outline'}
          size={22}
          color={config.dotColor}
        />
      </View>
      <View style={styles.toastText}>
        <Text style={styles.toastEyebrow}>Badge Unlocked!</Text>
        <Text style={styles.toastTitle} numberOfLines={1}>{badge.name}</Text>
      </View>
      <Text style={styles.toastRarityEmoji}>{config.iconEmoji}</Text>
    </ReAnimated.View>
  );
}

// ── Fullscreen celebration ────────────────────────────────────────────────────
type BadgeUnlockCelebrationProps = {
  badge: BadgeItem | null;
  onDismiss: () => void;
};

const FULLSCREEN_RARITIES = new Set(['rare', 'epic', 'legendary']);

export function BadgeUnlockCelebration({ badge, onDismiss }: BadgeUnlockCelebrationProps) {
  const scale = useSharedValue(0.3);
  const opacity = useSharedValue(0);
  const cardScale = useSharedValue(0.5);

  const triggerHaptics = useCallback(async () => {
    if (Platform.OS !== 'web') {
      try {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        if (badge?.rarity === 'legendary' || badge?.rarity === 'epic') {
          setTimeout(() => void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy), 350);
        }
      } catch {}
    }
  }, [badge?.rarity]);

  useEffect(() => {
    if (!badge || !FULLSCREEN_RARITIES.has(badge.rarity)) return;
    void triggerHaptics();
    opacity.value = withTiming(1, { duration: 220 });
    scale.value = withSpring(1, { damping: 18, stiffness: 180 });
    cardScale.value = withDelay(120, withSpring(1, { damping: 12, stiffness: 160 }));
  }, [badge]);

  const overlayStyle = useAnimatedStyle(() => ({ opacity: opacity.value }));
  const cardStyle = useAnimatedStyle(() => ({
    transform: [{ scale: cardScale.value }],
  }));

  if (!badge) return null;

  if (!FULLSCREEN_RARITIES.has(badge.rarity)) {
    return <BadgeToast badge={badge} onDismiss={onDismiss} />;
  }

  const config = getRarityConfig(badge.rarity);

  return (
    <Modal transparent statusBarTranslucent visible animationType="none">
      <ReAnimated.View style={[styles.overlay, overlayStyle]}>
        {/* Confetti */}
        {Array.from({ length: CONFETTI_COUNT }).map((_, i) => (
          <ConfettiPiece
            key={i}
            delay={i * 55}
            color={CONFETTI_COLORS[i % CONFETTI_COLORS.length]}
          />
        ))}

        {/* Tinted soft bg glow */}
        <View
          style={[
            styles.glowCircle,
            { backgroundColor: config.glowColor, borderColor: config.borderColor },
          ]}
        />

        {/* Content */}
        <View style={styles.center}>
          <Text style={styles.eyebrow}>🎉 Badge Unlocked!</Text>

          <ReAnimated.View style={cardStyle}>
            <BadgeCard badge={badge} size={140} showProgressOnLocked={false} />
          </ReAnimated.View>

          <View style={[styles.nameChip, { borderColor: config.borderColor, backgroundColor: config.bgColor }]}>
            <Text style={styles.rarityEmoji}>{config.iconEmoji}</Text>
            <Text style={[styles.badgeName, { color: config.labelColor }]}>{badge.name}</Text>
          </View>

          <Text style={styles.badgeDesc}>{badge.description}</Text>

        </View>

        <Pressable
          onPress={onDismiss}
          style={({ pressed }) => [styles.tapBtn, { opacity: pressed ? 0.7 : 1 }]}
        >
          <Text style={styles.tapText}>Tap to continue</Text>
        </Pressable>
      </ReAnimated.View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  // Fullscreen
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255,255,255,0.97)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  glowCircle: {
    borderRadius: 200,
    borderWidth: 1,
    height: 340,
    opacity: 0.7,
    position: 'absolute',
    width: 340,
  },
  center: {
    alignItems: 'center',
    gap: 14,
    paddingHorizontal: 32,
  },
  eyebrow: {
    color: '#6B7280',
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  nameChip: {
    alignItems: 'center',
    borderRadius: 16,
    borderWidth: 1.5,
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 18,
    paddingVertical: 8,
  },
  rarityEmoji: {
    fontSize: 18,
  },
  badgeName: {
    fontSize: 20,
    fontWeight: '800',
  },
  badgeDesc: {
    color: '#6B7280',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  rewardRow: {
    alignItems: 'center',
    borderRadius: 14,
    borderWidth: 1.5,
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  rewardEmoji: { fontSize: 18 },
  rewardText: {
    fontSize: 15,
    fontWeight: '700',
  },
  tapBtn: {
    bottom: 52,
    position: 'absolute',
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
  },
  tapText: {
    color: '#9CA3AF',
    fontSize: 14,
    fontWeight: '600',
  },
  // Toast
  toast: {
    alignItems: 'center',
    backgroundColor: '#fff',
    borderColor: '#F3F4F6',
    borderRadius: 20,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 12,
    left: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    position: 'absolute',
    right: 16,
    top: 60,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 10,
    zIndex: 999,
  },
  toastIconBg: {
    alignItems: 'center',
    borderRadius: 12,
    borderWidth: 1.5,
    height: 42,
    justifyContent: 'center',
    width: 42,
  },
  toastText: { flex: 1 },
  toastEyebrow: {
    color: '#9CA3AF',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  toastTitle: {
    color: '#111827',
    fontSize: 15,
    fontWeight: '800',
  },
  toastRarityEmoji: {
    fontSize: 20,
  },
});
