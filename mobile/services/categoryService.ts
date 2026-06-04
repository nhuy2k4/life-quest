import { requestJson } from '@/services/httpClient';

export type CategoryItem = {
  id: number;
  slug: string;
  name: string;
  icon?: string | null;
};

type CategoryListResponse = {
  items: CategoryItem[];
};

export async function listCategories(token: string): Promise<CategoryItem[]> {
  const response = await requestJson<CategoryListResponse>('/categories', {
    method: 'GET',
    token,
  });

  return response.items;
}
