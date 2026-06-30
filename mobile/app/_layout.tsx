import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack, usePathname } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';
import { useEffect } from 'react';

import { AuthProvider } from '@/contexts/AuthContext';
import { BadgeProvider } from '@/contexts/BadgeContext';
import { PostProvider } from '@/contexts/PostContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { UserProvider } from '@/contexts/UserContext';
import { XpGainProvider } from '@/contexts/XpGainContext';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { logWatchdog, startWatchdog } from '@/utils/watchdog';

export default function RootLayout() {
  const colorScheme = useColorScheme();
  const pathname = usePathname();

  useEffect(() => {
    const stop = startWatchdog();
    return stop;
  }, []);

  useEffect(() => {
    logWatchdog('route_change', { path: pathname });
  }, [pathname]);

  return (
    <ToastProvider>
      <XpGainProvider>
        <AuthProvider>
          <UserProvider>
            <BadgeProvider>
              <PostProvider>
                <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
                  <Stack screenOptions={{ headerShown: false }}>
                    <Stack.Screen name="index" />
                    <Stack.Screen name="(auth)" />
                    <Stack.Screen name="(onboarding)" />
                    <Stack.Screen name="(main)" />
                    <Stack.Screen name="post-detail" />
                    <Stack.Screen name="quest-detail" />
                  </Stack>
                  <StatusBar style="auto" />
                </ThemeProvider>
              </PostProvider>
            </BadgeProvider>
          </UserProvider>
        </AuthProvider>
      </XpGainProvider>
    </ToastProvider>
  );
}
