import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { LQButton } from '@/components/lifequest/LQButton';
import { Avatar } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { TextArea } from '@/components/ui/textarea';
import { ROUTES } from '@/constants/routes';
import { updateProfile } from '@/services/userService';
import { getItem, StorageKeys } from '@/utils/storage';

export default function EditProfileScreen() {
  const router = useRouter();
  const [username, setUsername] = useState('username');
  const [displayName, setDisplayName] = useState('LifeQuest Explorer');
  const [bio, setBio] = useState('');
  const [email, setEmail] = useState('user@email.com');

  const handleSave = async () => {
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) return;

    await updateProfile(token, {
      username: username.trim() || undefined,
      email: email.trim() || undefined,
    });
    router.replace(ROUTES.main.profile);
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color="#11181C" />
        </Pressable>
        <Text style={styles.headerTitle}>Edit Profile</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.avatarWrap}>
          <View style={styles.avatarBox}>
            <Avatar size={96} label="U" />
            <Pressable style={styles.cameraFab}>
              <Ionicons name="camera-outline" size={14} color="#fff" />
            </Pressable>
          </View>
          <Pressable>
            <Text style={styles.changeAvatar}>Change Avatar</Text>
          </Pressable>
        </View>

        <Input label="Username" value={username} onChangeText={setUsername} placeholder="username" autoCapitalize="none" />
        <Input label="Display Name" value={displayName} onChangeText={setDisplayName} placeholder="Display Name" />
        <TextArea
          label="Bio"
          value={bio}
          onChangeText={setBio}
          placeholder="Tell us about yourself..."
          maxLength={150}
          helperText={`${bio.length} / 150 characters`}
        />
        <Input
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="user@email.com"
          keyboardType="email-address"
          autoCapitalize="none"
        />

        <View style={styles.actions}>
          <LQButton title="Save Changes" variant="primary" fullWidth onPress={handleSave} />
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
  backButton: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 36,
    height: 36,
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
  avatarWrap: {
    alignItems: 'center',
    gap: 10,
    paddingBottom: 6,
  },
  avatarBox: {
    position: 'relative',
  },
  cameraFab: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderColor: '#fff',
    borderRadius: 14,
    borderWidth: 2,
    bottom: 0,
    height: 28,
    justifyContent: 'center',
    position: 'absolute',
    right: 0,
    width: 28,
  },
  changeAvatar: {
    color: '#11181C',
    fontSize: 13,
    textDecorationLine: 'underline',
  },
  actions: {
    gap: 10,
    paddingTop: 6,
  },
});
