import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { LQButton } from '@/components/lifequest/LQButton';
import { Avatar } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { TextArea } from '@/components/ui/textarea';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { useToast } from '@/contexts/ToastContext';
import { useUserContext } from '@/contexts/UserContext';
import { HttpError } from '@/services/httpClient';
import { getCurrentUser, getUserProfile, updateProfile } from '@/services/userService';
import { getLevelProgress } from '@/utils/levels';
import { getItem, StorageKeys } from '@/utils/storage';

export default function EditProfileScreen() {
  const router = useRouter();
  const { currentUser, setCurrentUser } = useUserContext();
  const { setPosts } = usePostContext();
  const { showToast } = useToast();
  const [username, setUsername] = useState(currentUser?.username ?? '');
  const [displayName, setDisplayName] = useState(currentUser?.displayName ?? '');
  const [bio, setBio] = useState('');
  const [email, setEmail] = useState('');
  const [originalEmail, setOriginalEmail] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let mounted = true;

    const loadProfile = async () => {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const me = await getCurrentUser(token);
        if (!mounted) return;
        setUsername(me.username);
        setDisplayName(me.display_name || me.username);
        setBio(me.bio || '');
        setEmail(me.email);
        setOriginalEmail(me.email);
      } catch (error) {
        if (mounted) {
          const message = error instanceof Error ? error.message : 'Could not load profile.';
          showToast(message);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    void loadProfile();

    return () => {
      mounted = false;
    };
  }, [showToast]);

  const handleSave = async () => {
    if (isSaving) return;
    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) {
      showToast('Bạn chưa đăng nhập.');
      return;
    }

    const nextUsername = username.trim();
    const nextEmail = email.trim().toLowerCase();
    const isEmailChanged = nextEmail !== originalEmail;
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!nextUsername) {
      showToast('Username không được để trống.');
      return;
    }

    if (isEmailChanged && !nextEmail) {
      showToast('Email không được để trống.');
      return;
    }

    if (isEmailChanged && nextEmail && !emailPattern.test(nextEmail)) {
      showToast('Email không hợp lệ.');
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        username: nextUsername,
        display_name: displayName.trim() || null,
        bio: bio.trim() || null,
      } as const;

      const updated = await updateProfile(token, {
        ...payload,
        ...(isEmailChanged && nextEmail ? { email: nextEmail } : {}),
      });
      const profile = await getUserProfile(token, updated.id);
      const progress = getLevelProgress(updated.level_id, updated.xp);
      const nextUser = {
        id: updated.id,
        username: updated.username,
        displayName: updated.display_name || updated.username,
        bio: updated.bio || undefined,
        level: progress.levelId,
        currentXp: progress.currentXp,
        nextLevelXp: progress.nextLevelXp,
        stats: {
          posts: profile.stats.posts,
          streak: profile.stats.streak,
          questsCompleted: profile.stats.quests_completed,
          followers: profile.stats.followers,
          following: profile.stats.following,
        },
        isSelf: true,
      };
      setCurrentUser(nextUser);
      setPosts((prev) =>
        prev.map((post) =>
          post.author.id === updated.id
            ? {
                ...post,
                author: {
                  ...post.author,
                  username: updated.username,
                },
              }
            : post
        )
      );
      showToast('Profile updated.');
      router.replace(ROUTES.main.profile);
    } catch (error) {
      const message =
        error instanceof HttpError || error instanceof Error
          ? error.message
          : 'Could not update profile.';
      showToast(message);
    } finally {
      setIsSaving(false);
    }
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
            <Avatar size={96} label={(username || 'U').charAt(0)} />
          </View>
        </View>

        <Input label="Username" value={username} onChangeText={setUsername} placeholder="username" autoCapitalize="none" editable={!isLoading && !isSaving} />
        <Input label="Display Name" value={displayName} onChangeText={setDisplayName} placeholder="Display Name" editable={!isLoading && !isSaving} />
        <TextArea
          label="Bio"
          value={bio}
          onChangeText={setBio}
          placeholder="Tell us about yourself..."
          maxLength={150}
          helperText={`${bio.length} / 150 characters`}
          editable={!isLoading && !isSaving}
        />
        <Input
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="user@email.com"
          keyboardType="email-address"
          autoCapitalize="none"
          editable={!isLoading && !isSaving}
        />

        <View style={styles.actions}>
          <LQButton title="Save Changes" variant="primary" fullWidth onPress={handleSave} loading={isSaving || isLoading} disabled={isSaving || isLoading} />
          <LQButton title="Cancel" variant="outline" fullWidth onPress={() => router.back()} disabled={isSaving} />
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
  actions: {
    gap: 10,
    paddingTop: 6,
  },
});
