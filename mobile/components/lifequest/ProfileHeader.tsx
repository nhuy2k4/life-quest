import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Avatar } from '@/components/ui/avatar';
import { useColorScheme } from '@/hooks/use-color-scheme';
import type { UserProfile } from '@/types';

type ProfileHeaderProps = {
  user: UserProfile;
  isSelf: boolean;
  isFollowing?: boolean;
  onBack?: () => void;
  onSettings?: () => void;
  onEdit?: () => void;
  onToggleFollow?: () => void;
};

export function ProfileHeader({
  user,
  isSelf,
  isFollowing = false,
  onBack,
  onSettings,
  onEdit,
  onToggleFollow,
}: ProfileHeaderProps) {
  const isDark = useColorScheme() === 'dark';
  const followers = user.stats.followers + (isSelf || !isFollowing ? 0 : 1);

  return (
    <View style={[styles.container, isDark ? styles.containerDark : styles.containerLight]}>
      <View style={styles.topRow}>
        {isSelf ? (
          <>
            <Text style={[styles.title, isDark ? styles.textDark : styles.textLight]}>Profile</Text>
            <Pressable onPress={onSettings} style={styles.iconButton}>
              <Ionicons name="settings-outline" size={20} color={isDark ? '#ECEDEE' : '#11181C'} />
            </Pressable>
          </>
        ) : (
          <>
            <Pressable onPress={onBack} style={styles.iconButton}>
              <Ionicons name="arrow-back" size={20} color={isDark ? '#ECEDEE' : '#11181C'} />
            </Pressable>
            <Text style={[styles.subtitle, isDark ? styles.textDark : styles.textLight]}>{`@${user.username}`}</Text>
            <View style={styles.iconButton} />
          </>
        )}
      </View>

      <View style={styles.mainSection}>
        <View style={styles.avatarWrap}>
          <Avatar uri={user.avatarUrl} size={96} label={user.username.charAt(0)} />
          {isSelf ? (
            <Pressable onPress={onEdit} style={styles.editFab}>
              <Ionicons name="pencil" size={14} color="#fff" />
            </Pressable>
          ) : null}
        </View>

        <View style={styles.textCenter}>
          <Text style={[styles.username, isDark ? styles.textDark : styles.textLight]}>{`@${user.username}`}</Text>
          {user.bio ? (
            <Text style={[styles.bio, isDark ? styles.bioDark : styles.bioLight]}>{user.bio}</Text>
          ) : null}
        </View>

        <View style={styles.followRow}>
          <View style={styles.statCenter}>
            <Text style={[styles.statValue, isDark ? styles.textDark : styles.textLight]}>{followers}</Text>
            <Text style={[styles.statLabel, isDark ? styles.bioDark : styles.bioLight]}>Followers</Text>
          </View>
          <View style={[styles.separator, isDark ? styles.separatorDark : styles.separatorLight]} />
          <View style={styles.statCenter}>
            <Text style={[styles.statValue, isDark ? styles.textDark : styles.textLight]}>{user.stats.following}</Text>
            <Text style={[styles.statLabel, isDark ? styles.bioDark : styles.bioLight]}>Following</Text>
          </View>
        </View>

        {!isSelf ? (
          <Pressable
            onPress={onToggleFollow}
            style={[styles.followButton, isFollowing ? styles.following : styles.followPrimary]}>
            <Ionicons
              name={isFollowing ? 'checkmark' : 'person-add'}
              size={14}
              color={isFollowing ? '#374151' : '#fff'}
            />
            <Text style={[styles.followText, isFollowing ? styles.followTextMuted : styles.followTextPrimary]}>
              {isFollowing ? 'Following' : 'Follow'}
            </Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderBottomWidth: 1,
    gap: 16,
    paddingBottom: 16,
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  containerLight: { borderBottomColor: '#E5E7EB' },
  containerDark: { borderBottomColor: '#374151' },
  topRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    minHeight: 40,
  },
  title: { fontSize: 22, fontWeight: '700' },
  subtitle: { fontSize: 16, fontWeight: '600' },
  iconButton: {
    alignItems: 'center',
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  mainSection: {
    alignItems: 'center',
    gap: 12,
  },
  avatarWrap: {
    position: 'relative',
  },
  editFab: {
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
  textCenter: {
    alignItems: 'center',
    gap: 4,
  },
  username: { fontSize: 18, fontWeight: '700' },
  bio: { fontSize: 13, textAlign: 'center' },
  bioLight: { color: '#6B7280' },
  bioDark: { color: '#9CA3AF' },
  followRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 20,
  },
  statCenter: {
    alignItems: 'center',
  },
  statValue: { fontSize: 16, fontWeight: '700' },
  statLabel: { fontSize: 12 },
  separator: { height: 26, width: 1 },
  separatorLight: { backgroundColor: '#E5E7EB' },
  separatorDark: { backgroundColor: '#4B5563' },
  followButton: {
    alignItems: 'center',
    borderRadius: 12,
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 22,
    paddingVertical: 10,
  },
  followPrimary: { backgroundColor: '#11181C' },
  following: {
    backgroundColor: '#fff',
    borderColor: '#D1D5DB',
    borderWidth: 1,
  },
  followText: {
    fontSize: 14,
    fontWeight: '600',
  },
  followTextPrimary: { color: '#fff' },
  followTextMuted: { color: '#374151' },
  textLight: { color: '#11181C' },
  textDark: { color: '#ECEDEE' },
});
