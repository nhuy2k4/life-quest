import { Stack } from 'expo-router';

export default function MainLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: 'fade',
        animationDuration: 150,
        contentStyle: { backgroundColor: '#fff' },
      }}
    />
  );
}
