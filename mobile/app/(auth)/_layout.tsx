import { Redirect, Stack } from 'expo-router';

import { useAuthContext } from '@/contexts/AuthContext';

export default function AuthLayout() {
  const { isAuthenticated, isHydrating } = useAuthContext();

  // Nếu đã đăng nhập → không cho vào auth screens nữa, redirect về home
  if (!isHydrating && isAuthenticated) {
    return <Redirect href="/(main)/home" />;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}
