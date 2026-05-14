import { StyleSheet, Text, View } from 'react-native';

import { LQButton } from '@/components/lifequest/LQButton';
import type { Reward } from '@/types';

type RewardItemProps = {
  reward: Reward;
  onClaim?: (rewardId: string) => void;
};

export function RewardItem({ reward, onClaim }: RewardItemProps) {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>{reward.title}</Text>
        {reward.description ? <Text style={styles.description}>{reward.description}</Text> : null}
      </View>
      <LQButton
        title={reward.claimed ? 'Claimed' : 'Claim'}
        variant={reward.claimed ? 'secondary' : 'primary'}
        size="sm"
        disabled={reward.claimed}
        onPress={() => onClaim?.(reward.id)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 12,
    justifyContent: 'space-between',
    padding: 12,
  },
  content: {
    flex: 1,
    gap: 4,
  },
  title: {
    color: '#11181C',
    fontSize: 14,
    fontWeight: '700',
  },
  description: {
    color: '#6B7280',
    fontSize: 12,
  },
});
