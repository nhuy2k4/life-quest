/**
 * OAuth Callback Screen — lifequestmobile://auth/callback
 *
 * This is the deep-link landing page after Google OAuth.
 * Expo Router renders this when the custom scheme redirect fires.
 * WebBrowser.maybeCompleteAuthSession() (called in useLogin.ts) detects
 * the OAuth result params in the URL and resolves the promptAsync() promise.
 */
import { useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import * as WebBrowser from 'expo-web-browser';

export default function AuthCallbackScreen() {
  useEffect(() => {
    WebBrowser.maybeCompleteAuthSession();
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#6366F1" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    backgroundColor: '#fff',
    flex: 1,
    justifyContent: 'center',
  },
});
