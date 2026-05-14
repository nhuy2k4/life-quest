import { Ionicons } from '@expo/vector-icons';
import { type Href, usePathname, useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { useColorScheme } from '@/hooks/use-color-scheme';

type BottomNavProps = {
  showNotificationDot?: boolean;
};

type NavItem = {
  label: string;
  path: string;
  icon: keyof typeof Ionicons.glyphMap;
};

const leftItems: NavItem[] = [
  { icon: 'home-outline', label: 'Home', path: ROUTES.main.home },
  { icon: 'compass-outline', label: 'Quest', path: ROUTES.main.questLog },
];

const rightItems: NavItem[] = [
  { icon: 'notifications-outline', label: 'Activity', path: ROUTES.main.notifications },
  { icon: 'person-outline', label: 'Profile', path: ROUTES.main.profile },
];

export function BottomNav({ showNotificationDot = true }: BottomNavProps) {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();
  const isDark = useColorScheme() === 'dark';

  const isActive = (path: string) => pathname === path;

  const handleNavigate = (path: string) => {
    if (isActive(path)) return;
    router.replace(path as Href);
  };

  return (
    <View
      style={[
        styles.wrap,
        isDark ? styles.wrapDark : styles.wrapLight,
        { paddingBottom: Math.max(insets.bottom, Layout.bottomSafeAreaPadding) },
      ]}>
      <View style={styles.row}>
        {leftItems.map((item) => (
          <Pressable key={item.path} onPress={() => handleNavigate(item.path)} style={styles.item}>
            <Ionicons
              name={item.icon}
              size={22}
              color={isActive(item.path) ? (isDark ? '#ECEDEE' : '#11181C') : '#9CA3AF'}
            />
            <Text style={[styles.itemLabel, isActive(item.path) ? styles.labelActive : styles.labelInactive]}>
              {item.label}
            </Text>
          </Pressable>
        ))}

        <Pressable onPress={() => router.push(ROUTES.main.camera as Href)} style={styles.fab}>
          <Ionicons name="camera-outline" size={24} color="#fff" />
        </Pressable>

        {rightItems.map((item) => (
          <Pressable key={item.path} onPress={() => handleNavigate(item.path)} style={styles.item}>
            <View>
              <Ionicons
                name={item.icon}
                size={22}
                color={isActive(item.path) ? (isDark ? '#ECEDEE' : '#11181C') : '#9CA3AF'}
              />
              {showNotificationDot && item.path.includes('notifications') ? <View style={styles.dot} /> : null}
            </View>
            <Text style={[styles.itemLabel, isActive(item.path) ? styles.labelActive : styles.labelInactive]}>
              {item.label}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderTopWidth: 1,
    left: 0,
    paddingHorizontal: 8,
    position: 'absolute',
    right: 0,
    bottom: 0,
  },
  wrapLight: { backgroundColor: '#fff', borderTopColor: '#E5E7EB' },
  wrapDark: { backgroundColor: '#11181C', borderTopColor: '#374151' },
  row: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  item: {
    alignItems: 'center',
    gap: 2,
    minHeight: 52,
    justifyContent: 'center',
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  itemLabel: {
    fontSize: 11,
  },
  labelActive: { color: '#11181C' },
  labelInactive: { color: '#9CA3AF' },
  fab: {
    alignItems: 'center',
    backgroundColor: '#11181C',
    borderRadius: Layout.fabSize / 2,
    height: Layout.fabSize,
    justifyContent: 'center',
    marginTop: -20,
    width: Layout.fabSize,
  },
  dot: {
    backgroundColor: '#11181C',
    borderColor: '#fff',
    borderRadius: 4,
    borderWidth: 1,
    height: 8,
    position: 'absolute',
    right: -2,
    top: -1,
    width: 8,
  },
});
