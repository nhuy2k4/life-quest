import { Ionicons } from '@expo/vector-icons';
import { useEffect } from 'react';
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  Animated,
  Easing,
} from 'react-native';
import ReAnimated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

import type { BadgeItem } from '@/types/badge';
import { formatUnlockDate, getProgressPercent, getRarityConfig } from './badgeUtils';

type BadgeDetailModalProps = {
  badge: BadgeItem | null;
  onClose: () => void;
};

export function BadgeDetailModal({ badge, onClose }: BadgeDetailModalProps) {
  const translateY = useSharedValue(700);
  const opacity = useSharedValue(0);

  useEffect(() => {
    if (badge) {
      opacity.value = withTiming(1, { duration: 180 });
      translateY.value = withSpring(0, { damping: 20, stiffness: 240 });
    } else {
      opacity.value = withTiming(0, { duration: 150 });
      translateY.value = withTiming(700, { duration: 200 });
    }
  }, [badge, translateY, opacity]);

  const backdropStyle = useAnimatedStyle(() => ({ opacity: opacity.value * 0.45 }));
  const sheetStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: translateY.value }],
  }));

  if (!badge) return null;

  const config = getRarityConfig(badge.rarity);
  const percent = getProgressPercent(badge.progress?.current || 0, badge.progress?.target || 1);
  const isHiddenLocked = badge.is_hidden && !badge.is_unlocked;
  const isLocked = !badge.is_unlocked;

  return (
    <Modal transparent animationType="none" visible={!!badge} onRequestClose={onClose}>
      {/* Backdrop */}
      <ReAnimated.View
        style={[StyleSheet.absoluteFill, { backgroundColor: '#000' }, backdropStyle]}
        pointerEvents="box-none"
      >
        <Pressable style={StyleSheet.absoluteFill} onPress={onClose} />
      </ReAnimated.View>

      {/* Sheet */}
      <ReAnimated.View style={[styles.sheet, sheetStyle]}>
        {/* Handle bar */}
        <View style={styles.handle} />

        <ScrollView
          showsVerticalScrollIndicator={false}
          bounces={false}
          contentContainerStyle={styles.scrollContent}
        >
          {/* ── Header ─────────────────────────────────────────────────── */}
          <View style={[styles.header, { backgroundColor: isLocked ? '#F9FAFB' : config.bgColor }]}>
            {/* Large icon */}
            <View
              style={[
                styles.iconCircle,
                {
                  borderColor: isLocked ? '#E5E7EB' : config.borderColor,
                  backgroundColor: '#fff',
                },
              ]}
            >
              {isHiddenLocked ? (
                <Text style={styles.lockEmoji}>🔒</Text>
              ) : (
                <Ionicons
                  name={(badge.icon_url as any) || 'ribbon-outline'}
                  size={44}
                  color={isLocked ? '#D1D5DB' : config.dotColor}
                />
              )}
            </View>

            {/* Rarity chip */}
            <View style={[styles.rarityChip, { borderColor: config.borderColor }]}>
              <Text style={styles.rarityEmoji}>{config.iconEmoji}</Text>
              <Text style={[styles.rarityLabel, { color: config.labelColor }]}>
                {config.label}
              </Text>
            </View>

            {/* Badge name */}
            <Text style={styles.badgeName}>
              {isHiddenLocked ? 'Hidden Achievement' : badge.name}
            </Text>

            {/* Description */}
            <Text style={styles.badgeDesc}>
              {isHiddenLocked
                ? 'Keep exploring to reveal this secret badge.'
                : badge.description}
            </Text>
          </View>

          {/* ── Progress ───────────────────────────────────────────────── */}
          {!badge.is_unlocked && !isHiddenLocked ? (
            <View style={styles.section}>
              <View style={styles.sectionRow}>
                <Text style={styles.sectionLabel}>Progress</Text>
                <Text style={[styles.progressFraction, { color: config.dotColor }]}>
                  {badge.progress?.current || 0} / {badge.progress?.target || 1}
                </Text>
              </View>
              <View style={styles.progressBg}>
                <Animated.View
                  style={[
                    styles.progressBar,
                    { width: `${percent}%` as any, backgroundColor: config.dotColor },
                  ]}
                />
              </View>
            </View>
          ) : null}

          {/* ── Unlock date ────────────────────────────────────────────── */}
          {badge.is_unlocked && badge.unlocked_at ? (
            <View style={styles.section}>
              <View style={styles.infoRow}>
                <Ionicons name="checkmark-circle" size={18} color="#10B981" />
                <Text style={styles.infoText}>
                  Unlocked {formatUnlockDate(badge.unlocked_at)}
                </Text>
              </View>
            </View>
          ) : null}

          {/* ── How to earn ────────────────────────────────────────────── */}
          {!isHiddenLocked ? (
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>How to earn</Text>
              <View style={styles.criteriaCard}>
                <Ionicons name="flag-outline" size={15} color={config.dotColor} />
                <Text style={styles.criteriaText}>{badge.description}</Text>
              </View>
            </View>
          ) : null}

          <View style={{ height: 16 }} />
        </ScrollView>

        {/* Close button */}
        <View style={styles.footer}>
          <Pressable
            style={({ pressed }) => [styles.closeBtn, { opacity: pressed ? 0.8 : 1 }]}
            onPress={onClose}
          >
            <Text style={styles.closeBtnText}>Close</Text>
          </Pressable>
        </View>
      </ReAnimated.View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  sheet: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    bottom: 0,
    left: 0,
    position: 'absolute',
    right: 0,
    maxHeight: '85%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 20,
  },
  handle: {
    alignSelf: 'center',
    backgroundColor: '#E5E7EB',
    borderRadius: 3,
    height: 4,
    marginTop: 12,
    marginBottom: 4,
    width: 40,
  },
  scrollContent: {
    paddingBottom: 8,
  },
  // Header section
  header: {
    alignItems: 'center',
    borderRadius: 20,
    gap: 10,
    margin: 16,
    paddingVertical: 28,
    paddingHorizontal: 20,
  },
  iconCircle: {
    alignItems: 'center',
    borderRadius: 40,
    borderWidth: 2,
    height: 80,
    justifyContent: 'center',
    width: 80,
  },
  lockEmoji: {
    fontSize: 36,
  },
  rarityChip: {
    alignItems: 'center',
    borderRadius: 14,
    borderWidth: 1.5,
    flexDirection: 'row',
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  rarityEmoji: {
    fontSize: 13,
  },
  rarityLabel: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  badgeName: {
    color: '#111827',
    fontSize: 22,
    fontWeight: '800',
    textAlign: 'center',
  },
  badgeDesc: {
    color: '#6B7280',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 21,
    paddingHorizontal: 8,
  },
  // Sections
  section: {
    marginTop: 4,
    paddingHorizontal: 20,
    paddingVertical: 10,
    gap: 8,
  },
  sectionRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  sectionLabel: {
    color: '#9CA3AF',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  progressBg: {
    backgroundColor: '#F3F4F6',
    borderRadius: 6,
    height: 8,
    overflow: 'hidden',
  },
  progressBar: {
    borderRadius: 6,
    height: 8,
  },
  progressFraction: {
    fontSize: 13,
    fontWeight: '700',
  },
  infoRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  infoText: {
    color: '#10B981',
    fontSize: 14,
    fontWeight: '600',
  },
  criteriaCard: {
    alignItems: 'flex-start',
    backgroundColor: '#F9FAFB',
    borderColor: '#F3F4F6',
    borderRadius: 14,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    padding: 14,
  },
  criteriaText: {
    color: '#374151',
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },
  rewardCard: {
    alignItems: 'center',
    borderRadius: 14,
    borderWidth: 1.5,
    flexDirection: 'row',
    gap: 10,
    padding: 14,
  },
  rewardEmoji: {
    fontSize: 20,
  },
  rewardText: {
    fontSize: 16,
    fontWeight: '700',
  },
  // Footer
  footer: {
    borderTopColor: '#F3F4F6',
    borderTopWidth: 1,
    padding: 16,
  },
  closeBtn: {
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 16,
    paddingVertical: 14,
  },
  closeBtnText: {
    color: '#374151',
    fontSize: 16,
    fontWeight: '700',
  },
});
