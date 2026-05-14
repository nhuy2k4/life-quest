import { StyleSheet, Text, View } from 'react-native';

type LevelProgressBarProps = {
  level: number;
  currentXp: number;
  nextLevelXp: number;
};

export function LevelProgressBar({ level, currentXp, nextLevelXp }: LevelProgressBarProps) {
  const safeNext = Math.max(nextLevelXp, 1);
  const progress = Math.min(1, Math.max(0, currentXp / safeNext));

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.level}>{`Level ${level}`}</Text>
        <Text style={styles.xp}>{`${currentXp}/${nextLevelXp} XP`}</Text>
      </View>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${progress * 100}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 8,
    width: '100%',
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  level: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  xp: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '600',
  },
  track: {
    backgroundColor: '#E5E7EB',
    borderRadius: 999,
    height: 8,
    overflow: 'hidden',
  },
  fill: {
    backgroundColor: '#0a7ea4',
    height: '100%',
  },
});
