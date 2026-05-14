import { Ionicons } from '@expo/vector-icons';
import { type Href, useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { LQButton } from '@/components/lifequest/LQButton';
import { ROUTES } from '@/constants/routes';
import { Avatar } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { validateUsername } from '@/utils/validation';

export default function OnboardingUsernameScreen() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [usernameError, setUsernameError] = useState<string | null>(null);

  const handleConfirm = () => {
    const nextError = validateUsername(username);
    setUsernameError(nextError);
    if (nextError) return;
    router.push(ROUTES.onboarding.interests as Href);
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Set Up Your Profile</Text>

        <View style={styles.avatarBlock}>
          <View style={styles.avatarWrap}>
            <Avatar size={96} label="U" />
            <Pressable style={styles.cameraFab}>
              <Ionicons name="camera" size={14} color="#fff" />
            </Pressable>
          </View>
          <Text style={styles.hint}>Optional: Add a profile photo</Text>
        </View>

        <Input
          label="Username"
          placeholder="Enter your username"
          value={username}
          onChangeText={setUsername}
          error={usernameError ?? undefined}
        />
      </View>

      <LQButton title="Confirm" variant="primary" fullWidth onPress={handleConfirm} />
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
    gap: 22,
    justifyContent: 'center',
    marginTop: 30,
  },
  title: {
    color: '#11181C',
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
  },
  avatarBlock: {
    alignItems: 'center',
    gap: 10,
  },
  avatarWrap: {
    position: 'relative',
  },
  cameraFab: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderRadius: 16,
    bottom: 0,
    height: 30,
    justifyContent: 'center',
    position: 'absolute',
    right: 0,
    width: 30,
  },
  hint: {
    color: '#6B7280',
    fontSize: 13,
  },
});
