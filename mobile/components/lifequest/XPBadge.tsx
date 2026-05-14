import { StyleSheet, Text, View } from 'react-native';

type XPBadgeProps = {
  xp: number;
};

export function XPBadge({ xp }: XPBadgeProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.sparkle}>✦</Text>
      <Text style={styles.label}>{`+${xp} XP`}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#11181C',
    borderRadius: 999,
    flexDirection: 'row',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  sparkle: {
    color: '#F59E0B',
    fontSize: 12,
  },
  label: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
});
