import { Ionicons } from '@expo/vector-icons';
import { type Href, usePathname, useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { removeItem, setItem, StorageKeys } from '@/utils/storage';

type BottomNavProps = {
  showNotificationDot?: boolean;
};

type NavItem = {
  label: string;
  path: string;
  icon: keyof typeof Ionicons.glyphMap;
  activeIcon: keyof typeof Ionicons.glyphMap;
  activeMatchers: string[];
};

const leftItems: NavItem[] = [
  { activeIcon: 'home', activeMatchers: ['/home'], icon: 'home-outline', label: 'Home', path: ROUTES.main.home },
  { activeIcon: 'compass', activeMatchers: ['/quest-log', '/quest-detail'], icon: 'compass-outline', label: 'Quest', path: ROUTES.main.questLog },
];

const rightItems: NavItem[] = [
  { activeIcon: 'notifications', activeMatchers: ['/notifications'], icon: 'notifications-outline', label: 'Activity', path: ROUTES.main.notifications },
  { activeIcon: 'person', activeMatchers: ['/profile', '/settings', '/other-profile'], icon: 'person-outline', label: 'Profile', path: ROUTES.main.profile },
];

function normalizePath(path: string): string {
  return path.replace(/\/\([^)]*\)/g, '').replace(/\/+$/, '') || '/';
}

export function BottomNav({ showNotificationDot = true }: BottomNavProps) {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();
  const isDark = useColorScheme() === 'dark';

  const currentPath = normalizePath(pathname);
  const isActive = (item: NavItem) => item.activeMatchers.some((matcher) => currentPath.startsWith(matcher));

  const handleNavigate = (path: string) => {
    if (normalizePath(path) === currentPath) return;
    router.replace(path as Href);
  };

  const handleOpenFreeCamera = async () => {
    await setItem(StorageKeys.cameraMode, 'free');
    await removeItem(StorageKeys.attachedQuest);
    router.push(ROUTES.main.camera as Href);
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
          <Pressable
            key={item.path}
            onPress={() => handleNavigate(item.path)}
            style={[styles.item, isActive(item) ? (isDark ? styles.itemActiveDark : styles.itemActiveLight) : null]}
          >
            <Ionicons
              name={isActive(item) ? item.activeIcon : item.icon}
              size={22}
              color={isActive(item) ? (isDark ? '#ECEDEE' : '#11181C') : '#9CA3AF'}
            />
            <Text style={[styles.itemLabel, isActive(item) ? (isDark ? styles.labelActiveDark : styles.labelActive) : styles.labelInactive]}>
              {item.label}
            </Text>
          </Pressable>
        ))}

        <Pressable onPress={handleOpenFreeCamera} style={styles.fab}>
          <Ionicons name="camera-outline" size={24} color="#fff" />
        </Pressable>

        {rightItems.map((item) => (
          <Pressable
            key={item.path}
            onPress={() => handleNavigate(item.path)}
            style={[styles.item, isActive(item) ? (isDark ? styles.itemActiveDark : styles.itemActiveLight) : null]}
          >
            <View>
              <Ionicons
                name={isActive(item) ? item.activeIcon : item.icon}
                size={22}
                color={isActive(item) ? (isDark ? '#ECEDEE' : '#11181C') : '#9CA3AF'}
              />
              {showNotificationDot && item.path.includes('notifications') ? <View style={styles.dot} /> : null}
            </View>
            <Text style={[styles.itemLabel, isActive(item) ? (isDark ? styles.labelActiveDark : styles.labelActive) : styles.labelInactive]}>
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
    borderRadius: 14,
    gap: 2,
    minHeight: 52,
    justifyContent: 'center',
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  itemActiveLight: {
    backgroundColor: '#F3F4F6',
  },
  itemActiveDark: {
    backgroundColor: '#1F2937',
  },
  itemLabel: {
    fontSize: 11,
  },
  labelActive: { color: '#11181C', fontWeight: '800' },
  labelActiveDark: { color: '#ECEDEE', fontWeight: '800' },
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
