import { type Href, useRouter } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { InterestTag } from '@/components/lifequest/InterestTag';
import { LQButton } from '@/components/lifequest/LQButton';
import { ROUTES } from '@/constants/routes';
import { useAuthContext } from '@/contexts/AuthContext';
import { HttpError } from '@/services/httpClient';
import { saveMyPreferences } from '@/services/preferenceService';
import { getItem, StorageKeys } from '@/utils/storage';

const interests = [
  'Food',
  'Fitness',
  'Travel',
  'Lifestyle',
  'Community',
  'Photography',
  'Nature',
  'Art',
  'Music',
  'Reading',
  'Cooking',
  'Gaming',
];

export default function OnboardingInterestsScreen() {
  const router = useRouter();
  const { setOnboardingCompleted } = useAuthContext();
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleInterest = (interest: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interest) ? prev.filter((item) => item !== interest) : [...prev, interest]
    );
  };

  const completeOnboarding = async () => {
    if (isSubmitting) return;

    setError(null);
    setIsSubmitting(true);

    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) {
        throw new Error('Missing access token');
      }

      const selectedIds = interests
        .map((interest, index) => ({ interest, id: index + 1 }))
        .filter((entry) => selectedInterests.includes(entry.interest))
        .map((entry) => entry.id);

      await saveMyPreferences(token, {
        interests: selectedIds,
        activity_level: 'medium',
        location_enabled: true,
      });

      setOnboardingCompleted(true);
      router.replace(ROUTES.main.home as Href);
    } catch (err) {
      if (err instanceof HttpError) {
        setError(err.message);
      } else {
        setError('Unable to save preferences right now. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>Choose Your Interests</Text>
          <Text style={styles.subtitle}>Personalize your quests and feed based on what you love.</Text>
        </View>

        <View style={styles.tagsWrap}>
          {interests.map((interest) => (
            <InterestTag
              key={interest}
              label={interest}
              selected={selectedInterests.includes(interest)}
              onPress={() => toggleInterest(interest)}
            />
          ))}
        </View>
      </View>

      <View style={styles.actions}>
        <LQButton
          title={`Next (${selectedInterests.length} selected)`}
          variant="primary"
          fullWidth
          loading={isSubmitting}
          disabled={selectedInterests.length === 0}
          onPress={() => void completeOnboarding()}
        />
        <LQButton
          title="Skip for now"
          variant="ghost"
          fullWidth
          loading={isSubmitting}
          onPress={() => void completeOnboarding()}
        />
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flex: 1,
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 36,
  },
  content: {
    flex: 1,
    gap: 20,
  },
  header: {
    gap: 8,
    marginTop: 8,
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
  tagsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    justifyContent: 'center',
    paddingTop: 8,
  },
  actions: {
    gap: 10,
  },
  errorText: {
    color: '#B91C1C',
    fontSize: 12,
    textAlign: 'center',
  },
});
