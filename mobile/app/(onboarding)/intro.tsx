import { type Href, useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { LQButton } from '@/components/lifequest/LQButton';
import { ROUTES } from '@/constants/routes';

export default function OnboardingIntroScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.illustration}>
          <Text style={styles.illustrationText}>Illustration</Text>
        </View>
        <View style={styles.textBlock}>
          <Text style={styles.title}>Welcome to LifeQuest</Text>
          <Text style={styles.subtitle}>
            Capture moments, complete quests, and level up your lifestyle with AI-powered feedback.
          </Text>
        </View>
      </View>
      <LQButton
        title="Start"
        variant="primary"
        fullWidth
        onPress={() => router.push(ROUTES.onboarding.permission as Href)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flex: 1,
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 42,
  },
  content: {
    alignItems: 'center',
    flex: 1,
    gap: 24,
    justifyContent: 'center',
  },
  illustration: {
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
    height: 240,
    justifyContent: 'center',
    width: 240,
  },
  illustrationText: {
    color: '#9CA3AF',
    fontSize: 13,
  },
  textBlock: {
    gap: 8,
    maxWidth: 320,
  },
  title: {
    color: '#11181C',
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
  },
  subtitle: {
    color: '#6B7280',
    fontSize: 14,
    textAlign: 'center',
  },
});
