import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';

import { useAuthContext } from '@/contexts/AuthContext';
import { HttpError } from '@/services/httpClient';
import { getCurrentUser } from '@/services/userService';
import type { UserProfile } from '@/types';
import { getItem, StorageKeys } from '@/utils/storage';

type UserContextValue = {
  currentUser: UserProfile | null;
  isLoadingCurrentUser: boolean;
  setCurrentUser: (value: UserProfile | null) => void;
};

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: PropsWithChildren) {
  const { isAuthenticated, isHydrating, setAuthenticated, setOnboardingCompleted } = useAuthContext();
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isLoadingCurrentUser, setIsLoadingCurrentUser] = useState(false);

  useEffect(() => {
    let mounted = true;

    const syncCurrentUser = async () => {
      if (isHydrating) {
        return;
      }

      if (!isAuthenticated) {
        if (mounted) {
          setCurrentUser(null);
          setIsLoadingCurrentUser(false);
        }
        return;
      }

      const accessToken = await getItem<string>(StorageKeys.accessToken);
      if (!accessToken) {
        if (mounted) {
          setAuthenticated(false);
          setCurrentUser(null);
          setIsLoadingCurrentUser(false);
        }
        return;
      }

      if (mounted) {
        setIsLoadingCurrentUser(true);
      }

      try {
        const me = await getCurrentUser(accessToken);
        if (!mounted) return;

        setOnboardingCompleted(me.onboarding_completed);
        setCurrentUser({
          id: me.id,
          username: me.username,
          displayName: me.username,
          level: me.level_id,
          currentXp: me.xp,
          nextLevelXp: Math.max(me.xp + 1000, 1000),
          stats: {
            posts: 0,
            streak: me.streak_days,
            questsCompleted: 0,
            followers: 0,
            following: 0,
          },
          isSelf: true,
        });
      } catch (error) {
        if (!mounted) return;

        if (error instanceof HttpError && error.status === 401) {
          setAuthenticated(false);
          setCurrentUser(null);
        }
      } finally {
        if (mounted) {
          setIsLoadingCurrentUser(false);
        }
      }
    };

    void syncCurrentUser();

    return () => {
      mounted = false;
    };
  }, [isAuthenticated, isHydrating, setAuthenticated, setOnboardingCompleted]);

  const value = useMemo(
    () => ({
      currentUser,
      isLoadingCurrentUser,
      setCurrentUser,
    }),
    [currentUser, isLoadingCurrentUser]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUserContext() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUserContext must be used within a UserProvider');
  }
  return context;
}
