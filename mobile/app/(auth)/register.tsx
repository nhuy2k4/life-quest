import { type Href, useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View, Alert } from 'react-native';

import { LQButton } from '@/components/lifequest/LQButton';
import { ROUTES } from '@/constants/routes';
import { Input } from '@/components/ui/input';
import { validateEmail, validatePassword, validateUsername } from '@/utils/validation';
import { register } from '@/services/authService';

export default function RegisterScreen() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [usernameError, setUsernameError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [confirmPasswordError, setConfirmPasswordError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async () => {
    const nextUsernameError = validateUsername(username);
    const nextEmailError = validateEmail(email);
    const nextPasswordError = validatePassword(password);
    const nextConfirmError = confirmPassword !== password ? 'Passwords do not match.' : null;

    setUsernameError(nextUsernameError);
    setEmailError(nextEmailError);
    setPasswordError(nextPasswordError);
    setConfirmPasswordError(nextConfirmError);

    if (nextUsernameError || nextEmailError || nextPasswordError || nextConfirmError) return;

    setIsLoading(true);
    try {
      // Call API to Backend
      await register({
        username,
        email,
        password,
      });

      // Success: route to OTP verification, sending email as param
      router.push({
        pathname: ROUTES.auth.otpVerification,
        params: { email }
      } as any);
    } catch (err: any) {
      const errMsg = err?.message || 'An unexpected error occurred during registration.';
      Alert.alert('Registration Failed', errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.header}>
          <View style={styles.logo} />
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>Join LifeQuest and start your journey</Text>
        </View>

        <View style={styles.form}>
          <Input label="Username" placeholder="username" value={username} onChangeText={setUsername} error={usernameError ?? undefined} />
          <Input
            label="Email"
            placeholder="your@email.com"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            value={email}
            onChangeText={setEmail}
            error={emailError ?? undefined}
          />
          <Input
            label="Password"
            placeholder="••••••••"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
            error={passwordError ?? undefined}
          />
          <Input
            label="Confirm Password"
            placeholder="••••••••"
            secureTextEntry
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            error={confirmPasswordError ?? undefined}
          />

          <LQButton title="Register" variant="primary" fullWidth onPress={handleRegister} loading={isLoading} />
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Already have an account?</Text>
          <Pressable onPress={() => router.push(ROUTES.auth.login as Href)}>
            <Text style={styles.link}>Login</Text>
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
    gap: 24,
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
    textAlign: 'center',
  },
  subtitle: {
    color: '#6B7280',
    fontSize: 14,
    textAlign: 'center',
  },
  form: {
    gap: 12,
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
