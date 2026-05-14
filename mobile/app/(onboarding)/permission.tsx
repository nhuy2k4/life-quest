import { Ionicons } from '@expo/vector-icons';
import { type Href, useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { LQButton } from '@/components/lifequest/LQButton';
import { ROUTES } from '@/constants/routes';

export default function OnboardingPermissionScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Enable Permissions</Text>

        <View style={styles.cardList}>
          <View style={styles.card}>
            <View style={styles.iconBubble}>
              <Ionicons name="camera" size={22} color="#fff" />
            </View>
            <Text style={styles.cardTitle}>Camera Access</Text>
            <Text style={styles.cardText}>Take photos to complete quests and earn XP.</Text>
          </View>

          <View style={styles.card}>
            <View style={styles.iconBubble}>
              <Ionicons name="location" size={22} color="#fff" />
            </View>
            <Text style={styles.cardTitle}>Location Access</Text>
            <Text style={styles.cardText}>Discover nearby quests and activities.</Text>
          </View>
        </View>
      </View>

      <LQButton
        title="Allow"
        variant="primary"
        fullWidth
        onPress={() => router.push(ROUTES.onboarding.username as Href)}
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
    flex: 1,
    gap: 24,
    justifyContent: 'center',
  },
  title: {
    color: '#11181C',
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
  },
  cardList: {
    gap: 14,
  },
  card: {
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    gap: 8,
    padding: 18,
  },
  iconBubble: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderRadius: 24,
    height: 48,
    justifyContent: 'center',
    marginBottom: 4,
    width: 48,
  },
  cardTitle: {
    color: '#11181C',
    fontSize: 15,
    fontWeight: '700',
  },
  cardText: {
    color: '#6B7280',
    fontSize: 13,
  },
});
