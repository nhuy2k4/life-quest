const rawApiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL;

if (!rawApiBaseUrl) {
  throw new Error('Missing EXPO_PUBLIC_API_BASE_URL. Set it in .env for local dev and EAS Environment Variables for builds.');
}

export const API_BASE_URL = rawApiBaseUrl.replace(/\/+$/, '');

export function buildApiUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export function buildApiWebSocketUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL.replace(/^http/, 'ws')}${normalizedPath}`;
}
