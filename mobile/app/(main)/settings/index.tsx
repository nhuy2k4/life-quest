import { Ionicons } from '@expo/vector-icons';
import { type Href, useRouter } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { LQButton } from '@/components/lifequest/LQButton';
import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { useAuthContext } from '@/contexts/AuthContext';

type SettingsItem = {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  path?: string;
};

const accountItems: SettingsItem[] = [
  { icon: 'person-outline', label: 'Edit Profile', path: ROUTES.main.editProfile },
  { icon: 'lock-closed-outline', label: 'Change Password', path: ROUTES.main.changePassword },
];

const preferenceItems: SettingsItem[] = [
  { icon: 'notifications-outline', label: 'Notifications' },
  { icon: 'shield-checkmark-outline', label: 'Privacy' },
];

const activityItems: SettingsItem[] = [
  { icon: 'flash-outline', label: 'XP History', path: ROUTES.main.xpHistory },
];

function SettingsSection({ title, items }: { title: string; items: SettingsItem[] }) {
  const router = useRouter();

  return (
    <View style={styles.sectionWrap}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionCard}>
        {items.map((item, index) => (
          <Pressable
            key={item.label}
            onPress={() => {
              if (item.path) {
                router.push(item.path as Href);
              }
            }}
            style={[styles.itemRow, index !== items.length - 1 ? styles.itemDivider : null]}>
            <View style={styles.itemLeft}>
              <Ionicons name={item.icon} size={18} color="#4B5563" />
              <Text style={styles.itemLabel}>{item.label}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
          </Pressable>
        ))}
      </View>
    </View>
  );
}

export default function SettingsScreen() {
  const router = useRouter();
  const { logout } = useAuthContext();

  const handleLogout = async () => {
    await logout();
    router.replace(ROUTES.auth.login as Href);
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color="#11181C" />
        </Pressable>
        <Text style={styles.headerTitle}>Settings</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SettingsSection title="Account" items={accountItems} />
        <SettingsSection title="Preferences" items={preferenceItems} />
        <SettingsSection title="Activity" items={activityItems} />

        <View style={styles.sectionWrap}>
          <Text style={styles.sectionTitle}>About</Text>
          <View style={styles.aboutCard}>
            <Text style={styles.aboutText}>Version 1.0.0</Text>
          </View>
        </View>

        <View style={styles.logoutWrap}>
          <LQButton title="Logout" variant="outline" fullWidth onPress={handleLogout} />
        </View>
      </ScrollView>

      <BottomNav />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
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
    gap: 18,
    padding: 16,
    paddingBottom: Layout.bottomNavHeight + 26,
  },
  sectionWrap: {
    gap: 8,
  },
  sectionTitle: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.4,
    paddingHorizontal: 2,
    textTransform: 'uppercase',
  },
  sectionCard: {
    backgroundColor: '#fff',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    overflow: 'hidden',
  },
  itemRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  itemDivider: {
    borderBottomColor: '#E5E7EB',
    borderBottomWidth: 1,
  },
  itemLeft: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  itemLabel: {
    color: '#11181C',
    fontSize: 15,
    fontWeight: '500',
  },
  aboutCard: {
    backgroundColor: '#fff',
    borderColor: '#E5E7EB',
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  aboutText: {
    color: '#6B7280',
    fontSize: 14,
  },
  logoutWrap: {
    paddingTop: 4,
  },
});
