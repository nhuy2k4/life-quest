import { type Href, useRouter } from 'expo-router';
import { useState } from 'react';

import { ROUTES } from '@/constants/routes';
import { useAuthContext } from '@/contexts/AuthContext';
import { login } from '@/services/authService';
import { HttpError } from '@/services/httpClient';
import { saveItem, StorageKeys } from '@/utils/storage';
import { validatePassword, validateUsername } from '@/utils/validation';

type LoginErrors = {
  username: string | null;
  password: string | null;
};

export function useLogin() {
  const router = useRouter();
  const { setAuthenticated, setOnboardingCompleted } = useAuthContext();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<LoginErrors>({ username: null, password: null });
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const routeAfterLogin = (onboardingCompleted: boolean): Href => {
    if (!onboardingCompleted) return ROUTES.onboarding.intro as Href;
    return ROUTES.main.home as Href;
  };

  const persistSession = async (
    accessToken: string,
    refreshToken: string,
    onboardingCompleted: boolean
  ) => {
    await Promise.all([
      saveItem(StorageKeys.accessToken, accessToken),
      saveItem(StorageKeys.refreshToken, refreshToken),
      saveItem(StorageKeys.onboardingCompleted, onboardingCompleted),
    ]);
  };

  const handleLogin = async () => {
    const usernameError = validateUsername(username);
    const passwordError = validatePassword(password);

    setErrors({ username: usernameError, password: passwordError });
    setApiError(null);

    if (usernameError || passwordError) return;

    setIsLoading(true);
    try {
      const tokenResponse = await login({ username: username.trim(), password });

      await persistSession(
        tokenResponse.access_token,
        tokenResponse.refresh_token,
        tokenResponse.onboarding_completed
      );

      setAuthenticated(true);
      setOnboardingCompleted(tokenResponse.onboarding_completed);
      router.replace(routeAfterLogin(tokenResponse.onboarding_completed));
    } catch (error) {
      if (error instanceof HttpError) {
        setApiError(error.message);
      } else {
        setApiError('Unable to login right now. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return {
    username,
    password,
    errors,
    apiError,
    isLoading,
    setUsername,
    setPassword,
    handleLogin,
  };
}
