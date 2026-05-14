import { type Href, useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { makeRedirectUri } from 'expo-auth-session';
import Constants from 'expo-constants';

import { ROUTES } from '@/constants/routes';
import { useAuthContext } from '@/contexts/AuthContext';
import { login, loginWithGoogle } from '@/services/authService';
import { HttpError } from '@/services/httpClient';
import { saveItem, StorageKeys } from '@/utils/storage';
import { validatePassword, validateUsername } from '@/utils/validation';

// Closes the auth browser when the app is restored via deep link.
// Must be called at module level in the screen that handles the OAuth redirect.
WebBrowser.maybeCompleteAuthSession();

type LoginErrors = {
  username: string | null;
  password: string | null;
};

export function useLogin() {
  const router = useRouter();
  const { setAuthenticated, setOnboardingCompleted } = useAuthContext();

  const webClientId = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID;

  // scheme được lấy từ app.json ("scheme": "lifequestmobile") qua expo-constants
  // Không hardcode ở đây để tránh mismatch khi đổi scheme
  const appScheme = Constants.expoConfig?.scheme ?? 'lifequestmobile';
  const scheme = Array.isArray(appScheme) ? appScheme[0] : appScheme;

  // Nếu có EXPO_PUBLIC_REDIRECT_URI trong .env → dùng (hữu ích khi chạy Expo Go,
  // URI exp://IP:PORT/--/auth/callback thay đổi theo IP nên cần set thủ công).
  // Dev build / production → để trống, makeRedirectUri() tự sinh lifequestmobile://auth/callback
  const envRedirectUri = process.env.EXPO_PUBLIC_REDIRECT_URI;
  const redirectUri = envRedirectUri ?? makeRedirectUri({ scheme, path: 'auth/callback' });

  const [request, response, promptAsync] = Google.useAuthRequest({
    clientId: webClientId,
    redirectUri,
    scopes: ['openid', 'profile', 'email'],
    responseType: 'id_token',
    usePKCE: false,
    extraParams: {
      prompt: 'select_account',
    },
  });




  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<LoginErrors>({ username: null, password: null });
  const [apiError, setApiError] = useState<string | null>(null);
  const [googleDebug, setGoogleDebug] = useState<string>('idle');
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const isProcessingGoogleRef = useRef(false);

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

  const handleGoogleLogin = async () => {
    setApiError(null);
    setGoogleDebug('pressed');

    if (!webClientId) {
      setGoogleDebug('missing_web_client_id');
      setApiError('Missing Google OAuth env. Set EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID for Expo Go.');
      return;
    }

    if (!request) {
      setGoogleDebug('request_not_ready');
      setApiError('Google Sign-In is initializing. Please try again in a moment.');
      return;
    }

    setIsGoogleLoading(true);
    setGoogleDebug('prompt_opened');

    try {
      const authResult = await promptAsync();

      console.log('[GoogleAuth] authResult.type:', authResult.type);
      setGoogleDebug(`auth_result_${authResult.type}`);

      if (authResult.type === 'error') {
        const authParams = (authResult as { params?: { error?: string; error_description?: string } }).params;
        const rawError = authParams?.error_description ?? authParams?.error;
        throw new HttpError(rawError ?? 'Google Sign-In failed.', 400);
      }

      if (authResult.type === 'dismiss') {
        setGoogleDebug('dismiss_waiting_response');
      }
    } catch (error) {
      if (error instanceof HttpError) {
        setApiError(error.message);
      } else {
        setApiError('Google login failed. Please try again.');
      }
      setGoogleDebug('google_login_error');
      setIsGoogleLoading(false);
    }
  };

  useEffect(() => {
    const completeGoogleLogin = async () => {
      if (response?.type !== 'success') {
        return;
      }

      if (isProcessingGoogleRef.current) {
        return;
      }

      isProcessingGoogleRef.current = true;
      setIsGoogleLoading(true);

      try {
        const idToken = (response as { params?: { id_token?: string } }).params?.id_token;

        console.log('[GoogleAuth] hasIdToken from response:', Boolean(idToken));
        setGoogleDebug(idToken ? 'id_token_ready' : 'id_token_missing');

        if (!idToken) {
          throw new HttpError(
            `Google did not return id_token. Verify redirect URI ${redirectUri} in Google Cloud.`,
            400
          );
        }

        console.log('[GoogleAuth] calling backend /auth/google/login');
        setGoogleDebug('calling_backend_google_login');
        const tokenResponse = await loginWithGoogle(idToken);
        console.log('[GoogleAuth] backend login success');
        setGoogleDebug('backend_google_login_success');

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
          setApiError('Google login failed. Please try again.');
        }
        setGoogleDebug('google_login_error');
      } finally {
        isProcessingGoogleRef.current = false;
        setIsGoogleLoading(false);
      }
    };

    void completeGoogleLogin();
  }, [response, redirectUri, router, setAuthenticated, setOnboardingCompleted]);

  return {
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
  };
}
