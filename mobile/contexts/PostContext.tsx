import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type Dispatch,
  type PropsWithChildren,
  type SetStateAction,
} from 'react';

import type { Post } from '@/types';
import { getItem, saveItem, StorageKeys } from '@/utils/storage';

type PostContextValue = {
  posts: Post[];
  setPosts: Dispatch<SetStateAction<Post[]>>;
  hiddenPostIds: Set<string>;
  hidePost: (postId: string) => void;
  unhidePost: (postId: string) => void;
};

const PostContext = createContext<PostContextValue | undefined>(undefined);

function dedupePosts(posts: Post[]): Post[] {
  const result: Post[] = [];

  posts.forEach((post) => {
    const existingIndex = result.findIndex((item) => {
      if (item.id === post.id) return true;
      if (item.submissionId && post.submissionId && item.submissionId === post.submissionId) return true;
      return false;
    });

    if (existingIndex === -1) {
      result.push(post);
      return;
    }

    result[existingIndex] = {
      ...result[existingIndex],
      ...post,
      id: result[existingIndex].id,
      createdAt: result[existingIndex].createdAt,
    };
  });

  return result;
}

export function PostProvider({ children }: PropsWithChildren) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [hiddenPostIds, setHiddenPostIds] = useState<Set<string>>(new Set());
  const [hasHydrated, setHasHydrated] = useState(false);

  useEffect(() => {
    let mounted = true;

    const hydrate = async () => {
      const cached = await getItem<Post[]>(StorageKeys.feedCache);
      if (!mounted) return;
      if (cached && cached.length > 0) {
        setPosts(dedupePosts(cached));
      }
      setHasHydrated(true);
    };

    void hydrate();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!hasHydrated) return;
    void saveItem(StorageKeys.feedCache, dedupePosts(posts));
  }, [hasHydrated, posts]);

  const hidePost = (postId: string) => {
    setHiddenPostIds((prev) => {
      const next = new Set(prev);
      next.add(postId);
      return next;
    });
  };

  const unhidePost = (postId: string) => {
    setHiddenPostIds((prev) => {
      const next = new Set(prev);
      next.delete(postId);
      return next;
    });
  };

  const value = useMemo(
    () => ({
      posts,
      setPosts,
      hiddenPostIds,
      hidePost,
      unhidePost,
    }),
    [posts, hiddenPostIds]
  );

  return <PostContext.Provider value={value}>{children}</PostContext.Provider>;
}

export function usePostContext() {
  const context = useContext(PostContext);
  if (!context) {
    throw new Error('usePostContext must be used within a PostProvider');
  }
  return context;
}
