import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';

import { refreshToken } from '@/services/authService';
import { registerPushToken } from '@/services/notificationService';
import { clearItems, getItem, saveItem, StorageKeys } from '@/utils/storage';

type AuthContextValue = {
  isHydrating: boolean;
  isAuthenticated: boolean;
  onboardingCompleted: boolean;
  setAuthenticated: (value: boolean) => void;
  setOnboardingCompleted: (value: boolean) => void;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Decode JWT payload và kiểm tra exp claim.
 * Không cần verify signature — chỉ dùng để tránh dùng token hết hạn.
 * Backend vẫn sẽ reject nếu token giả mạo.
 */
function isTokenValid(token: string): boolean {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return false;

    // Base64url → Base64 → JSON
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const decoded = JSON.parse(atob(payload)) as Record<string, unknown>;

    const exp = typeof decoded.exp === 'number' ? decoded.exp : null;
    if (!exp) return false;

    // exp là Unix timestamp (seconds) — thêm 10s buffer
    return Date.now() / 1000 < exp - 10;
  } catch {
    return false;
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [isHydrating, setHydrating] = useState(true);
  const [isAuthenticated, setAuthenticatedState] = useState(false);
  const [onboardingCompleted, setOnboardingCompletedState] = useState(false);

  useEffect(() => {
    let mounted = true;

    const hydrateSession = async () => {
      const accessToken = await getItem<string>(StorageKeys.accessToken);
      const refreshTokenValue = await getItem<string>(StorageKeys.refreshToken);
      const persistedOnboarding = await getItem<boolean>(StorageKeys.onboardingCompleted);

      if (!mounted) return;

      // Nếu có token nhưng đã hết hạn → thử refresh bằng refresh_token
      if (accessToken && !isTokenValid(accessToken)) {
        if (refreshTokenValue) {
          try {
            const tokenResponse = await refreshToken(refreshTokenValue);
            await Promise.all([
              saveItem(StorageKeys.accessToken, tokenResponse.access_token),
              saveItem(StorageKeys.refreshToken, tokenResponse.refresh_token),
              saveItem(StorageKeys.onboardingCompleted, tokenResponse.onboarding_completed),
            ]);
            setAuthenticatedState(true);
            setOnboardingCompletedState(Boolean(tokenResponse.onboarding_completed));
            setHydrating(false);
            return;
          } catch {
            // Fall through to clear session
          }
        }

        await clearItems([StorageKeys.accessToken, StorageKeys.refreshToken, StorageKeys.pushToken, StorageKeys.onboardingCompleted]);
        setAuthenticatedState(false);
        setOnboardingCompletedState(false);
        setHydrating(false);
        return;
      }

      setAuthenticatedState(Boolean(accessToken));
      setOnboardingCompletedState(Boolean(persistedOnboarding));
      setHydrating(false);
    };

    void hydrateSession();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const syncPushToken = async () => {
      if (!isAuthenticated) return;

      const accessToken = await getItem<string>(StorageKeys.accessToken);
      if (!accessToken) return;

      try {
        await registerPushToken(accessToken);
      } catch {
        // Push registration should never block app entry.
      }
    };

    void syncPushToken();
  }, [isAuthenticated]);

  const setAuthenticated = useCallback((value: boolean) => {
    setAuthenticatedState(value);

    if (!value) {
      setOnboardingCompletedState(false);
      void clearItems([StorageKeys.accessToken, StorageKeys.refreshToken, StorageKeys.pushToken, StorageKeys.onboardingCompleted]);
    }
  }, []);

  const setOnboardingCompleted = useCallback((value: boolean) => {
    setOnboardingCompletedState(value);
    void saveItem(StorageKeys.onboardingCompleted, value);
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    // Xóa storage trước, set state sau — tránh race condition
    await clearItems([
      StorageKeys.accessToken,
      StorageKeys.refreshToken,
      StorageKeys.pushToken,
      StorageKeys.onboardingCompleted,
      StorageKeys.feedCache,
      StorageKeys.attachedQuest,
      StorageKeys.newPost,
      StorageKeys.cameraMode,
      StorageKeys.searchHistory,
    ]);
    setAuthenticatedState(false);
    setOnboardingCompletedState(false);
  }, []);

  const value = useMemo(
    () => ({
      isHydrating,
      isAuthenticated,
      onboardingCompleted,
      setAuthenticated,
      setOnboardingCompleted,
      logout,
    }),
    [isHydrating, isAuthenticated, onboardingCompleted, setAuthenticated, setOnboardingCompleted, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
