import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';

import { useAuthContext } from '@/contexts/AuthContext';
import { HttpError } from '@/services/httpClient';
import { getCurrentUser, getUserProfile } from '@/services/userService';
import type { UserProfile } from '@/types';
import { getLevelProgress } from '@/utils/levels';
import { getItem, StorageKeys } from '@/utils/storage';

type UserContextValue = {
  currentUser: UserProfile | null;
  isLoadingCurrentUser: boolean;
  setCurrentUser: (value: UserProfile | null) => void;
  refreshCurrentUser: () => Promise<void>;
};

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: PropsWithChildren) {
  const { isAuthenticated, isHydrating, setAuthenticated, setOnboardingCompleted } = useAuthContext();
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isLoadingCurrentUser, setIsLoadingCurrentUser] = useState(false);

  useEffect(() => {
    let mounted = true;

    const syncCurrentUser = async (force: boolean = false) => {
      if (!force && isHydrating) {
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

      if (mounted && !force) {
        setIsLoadingCurrentUser(true);
      }

      try {
        const me = await getCurrentUser(accessToken);
        const latestToken = (await getItem<string>(StorageKeys.accessToken)) ?? accessToken;
        const profile = await getUserProfile(latestToken, me.id);
        if (!mounted) return;

        const progress = getLevelProgress(me.level_id, me.xp);

        setOnboardingCompleted(me.onboarding_completed);
        setCurrentUser({
          id: me.id,
          username: me.username,
          displayName: me.display_name || me.username,
          bio: me.bio || undefined,
          level: progress.levelId,
          currentXp: progress.currentXp,
          nextLevelXp: progress.nextLevelXp,
          stats: {
            posts: profile.stats.posts,
            streak: profile.stats.streak,
            questsCompleted: profile.stats.quests_completed,
            followers: profile.stats.followers,
            following: profile.stats.following,
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

    // Attach to window/global for manual refresh if needed
    (global as any)._refreshCurrentUser = () => syncCurrentUser(true);

    return () => {
      mounted = false;
      delete (global as any)._refreshCurrentUser;
    };
  }, [isAuthenticated, isHydrating, setAuthenticated, setOnboardingCompleted]);

  const refreshCurrentUser = useCallback(async () => {
    if ((global as any)._refreshCurrentUser) {
      await (global as any)._refreshCurrentUser();
    }
  }, []);

  const value = useMemo(
    () => ({
      currentUser,
      isLoadingCurrentUser,
      setCurrentUser,
      refreshCurrentUser,
    }),
    [currentUser, isLoadingCurrentUser, refreshCurrentUser]
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
