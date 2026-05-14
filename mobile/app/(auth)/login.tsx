import { type Href, useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { LQButton } from '@/components/lifequest/LQButton';
import { ROUTES } from '@/constants/routes';
import { Input } from '@/components/ui/input';
import { useLogin } from '@/hooks/useLogin';

export default function LoginScreen() {
  const router = useRouter();
  const {
    username,
    password,
    errors,
    apiError,
    isLoading,
    isGoogleLoading,
    googleDebug,
    setUsername,
    setPassword,
    handleLogin,
    handleGoogleLogin,
  } = useLogin();

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.header}>
          <View style={styles.logo} />
          <Text style={styles.title}>LifeQuest</Text>
          <Text style={styles.subtitle}>Level up your lifestyle</Text>
        </View>

        <View style={styles.form}>
          <Input
            label="Username"
            placeholder="your_username"
            autoCorrect={false}
            value={username}
            onChangeText={setUsername}
            error={errors.username ?? undefined}
          />
          <Input
            label="Password"
            placeholder="••••••••"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
            error={errors.password ?? undefined}
          />

          {apiError ? <Text style={styles.apiError}>{apiError}</Text> : null}

          <LQButton title="Login" variant="primary" fullWidth loading={isLoading} onPress={handleLogin} />
          <LQButton
            title="Continue with Google"
            variant="outline"
            fullWidth
            loading={isGoogleLoading}
            onPress={handleGoogleLogin}
          />
          <Text style={styles.debugText}>{`Google debug: ${googleDebug}`}</Text>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Don&apos;t have an account?</Text>
          <Pressable onPress={() => router.push(ROUTES.auth.register as Href)}>
            <Text style={styles.link}>Register</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  card: {
    alignSelf: 'center',
    gap: 28,
    maxWidth: 420,
    width: '100%',
  },
  header: {
    alignItems: 'center',
    gap: 8,
  },
  logo: {
    backgroundColor: '#11181C',
    borderRadius: 16,
    height: 80,
    marginBottom: 8,
    width: 80,
  },
  title: {
    color: '#11181C',
    fontSize: 30,
    fontWeight: '700',
  },
  subtitle: {
    color: '#6B7280',
    fontSize: 14,
  },
  form: {
    gap: 14,
  },
  apiError: {
    color: '#B91C1C',
    fontSize: 13,
    marginTop: -4,
  },
  debugText: {
    color: '#6B7280',
    fontSize: 12,
  },
  footer: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
    justifyContent: 'center',
  },
  footerText: {
    color: '#6B7280',
    fontSize: 13,
  },
  link: {
    color: '#11181C',
    fontSize: 13,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
});
