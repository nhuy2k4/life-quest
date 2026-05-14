import { Redirect } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';

import { ROUTES } from '@/constants/routes';
import { useAuthContext } from '@/contexts/AuthContext';

export default function EntryIndexScreen() {
  const { isHydrating, isAuthenticated, onboardingCompleted } = useAuthContext();

  if (isHydrating) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#fff' }}>
        <ActivityIndicator size="small" color="#11181C" />
      </View>
    );
  }

  if (!isAuthenticated) {
    return <Redirect href={ROUTES.auth.login} />;
  }

  if (!onboardingCompleted) {
    return <Redirect href={ROUTES.onboarding.intro} />;
  }

  return <Redirect href={ROUTES.main.home} />;
}
