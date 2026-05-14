import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack, usePathname } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';
import { useEffect } from 'react';

import { AuthProvider } from '@/contexts/AuthContext';
import { PostProvider } from '@/contexts/PostContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { UserProvider } from '@/contexts/UserContext';
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
      <AuthProvider>
        <UserProvider>
          <PostProvider>
            <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
              <Stack screenOptions={{ headerShown: false }}>
                <Stack.Screen name="index" />
                <Stack.Screen name="(auth)" />
                <Stack.Screen name="(onboarding)" />
                <Stack.Screen name="(main)" />
                <Stack.Screen name="auth/callback" options={{ presentation: 'transparentModal', headerShown: false }} />
                <Stack.Screen name="post-detail" />
                <Stack.Screen name="quest-detail" />
              </Stack>
              <StatusBar style="auto" />
            </ThemeProvider>
          </PostProvider>
        </UserProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
