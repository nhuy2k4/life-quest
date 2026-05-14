import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { LQButton } from '@/components/lifequest/LQButton';
import { Input } from '@/components/ui/input';
import { ROUTES } from '@/constants/routes';

export default function ChangePasswordScreen() {
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const newPasswordError =
    newPassword.length > 0 && newPassword.length < 8
      ? 'Password must be at least 8 characters'
      : undefined;

  const confirmError =
    confirmPassword.length > 0 && confirmPassword !== newPassword
      ? 'Passwords do not match'
      : undefined;

  const canSubmit =
    currentPassword.length > 0 &&
    newPassword.length >= 8 &&
    confirmPassword.length > 0 &&
    confirmPassword === newPassword;

  const handleSubmit = () => {
    if (!canSubmit) return;
    router.replace(ROUTES.main.settings);
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Ionicons name="arrow-back" size={22} color="#11181C" onPress={() => router.back()} />
        <Text style={styles.headerTitle}>Change Password</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Input
          label="Current Password"
          value={currentPassword}
          onChangeText={setCurrentPassword}
          secureTextEntry
          placeholder="••••••••"
          autoCapitalize="none"
        />

        <Input
          label="New Password"
          value={newPassword}
          onChangeText={setNewPassword}
          secureTextEntry
          placeholder="••••••••"
          autoCapitalize="none"
          helperText="Minimum 8 characters with letters and numbers"
          error={newPasswordError}
        />

        <Input
          label="Confirm New Password"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry
          placeholder="••••••••"
          autoCapitalize="none"
          error={confirmError}
        />

        <View style={styles.actions}>
          <LQButton title="Update Password" variant="primary" fullWidth onPress={handleSubmit} disabled={!canSubmit} />
          <LQButton title="Cancel" variant="outline" fullWidth onPress={() => router.back()} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    alignItems: 'center',
    borderBottomColor: '#E5E7EB',
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 22,
    fontWeight: '700',
  },
  content: {
    gap: 14,
    padding: 16,
    paddingBottom: 24,
  },
  actions: {
    gap: 10,
    paddingTop: 6,
  },
});
