export class HttpError extends Error {
  status: number;
  payload?: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.payload = payload;
  }
}

type RequestOptions = RequestInit & {
  token?: string;
  timeoutMs?: number;
  skipRefresh?: boolean;
};

const RAW_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const BASE_URL = RAW_BASE_URL.replace(/\/+$/, '');

let refreshInFlight: Promise<string | null> | null = null;

function buildUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${BASE_URL}${normalizedPath}`;
}

async function safeReadJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function resolveErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback;

  const payloadObject = payload as Record<string, unknown>;
  const detail = payloadObject.detail;
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail;
  }

  const message = payloadObject.message;
  if (typeof message === 'string' && message.trim().length > 0) {
    return message;
  }

  return fallback;
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshInFlight) {
    return refreshInFlight;
  }

  refreshInFlight = (async () => {
    const { getItem, setItem, StorageKeys } = await import('@/utils/storage');
    const refreshToken = await getItem<string>(StorageKeys.refreshToken);

    if (!refreshToken) {
      return null;
    }

    try {
      const response = await fetch(buildUrl('/auth/refresh'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      const payload = await safeReadJson(response);

      if (!response.ok || !payload || typeof payload !== 'object') {
        return null;
      }

      const tokenPayload = payload as Record<string, unknown>;
      const accessToken = typeof tokenPayload.access_token === 'string' ? tokenPayload.access_token : null;
      const newRefreshToken = typeof tokenPayload.refresh_token === 'string' ? tokenPayload.refresh_token : null;

      if (!accessToken || !newRefreshToken) {
        return null;
      }

      await Promise.all([
        setItem(StorageKeys.accessToken, accessToken),
        setItem(StorageKeys.refreshToken, newRefreshToken),
      ]);

      return accessToken;
    } catch {
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();

  const refreshedToken = await refreshInFlight;
  if (!refreshedToken) {
    const { clearItems, StorageKeys } = await import('@/utils/storage');
    await clearItems([
      StorageKeys.accessToken,
      StorageKeys.refreshToken,
      StorageKeys.pushToken,
      StorageKeys.onboardingCompleted,
    ]);
  }

  return refreshedToken;
}

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, timeoutMs = 15000, headers, skipRefresh = false, ...rest } = options;

  const isFormData = typeof FormData !== 'undefined' && rest.body instanceof FormData;

  const executeRequest = async (overrideToken?: string): Promise<T> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(buildUrl(path), {
        ...rest,
        headers: {
          ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
          ...(overrideToken ? { Authorization: `Bearer ${overrideToken}` } : {}),
          ...(headers ?? {}),
        },
        signal: controller.signal,
      });

      const payload = await safeReadJson(response);

      if (!response.ok) {
        const fallback = `Request failed with status ${response.status}`;
        throw new HttpError(resolveErrorMessage(payload, fallback), response.status, payload);
      }

      return payload as T;
    } finally {
      clearTimeout(timeoutId);
    }
  };

  try {
    return await executeRequest(token);
  } catch (error) {
    if (error instanceof HttpError && error.status === 401 && token && !skipRefresh) {
      const isRefreshEndpoint = /\/auth\/refresh$/.test(buildUrl(path));
      if (!isRefreshEndpoint) {
        const refreshedToken = await refreshAccessToken();
        if (refreshedToken) {
          return await executeRequest(refreshedToken);
        }
      }
    }

    if (error instanceof HttpError) {
      throw error;
    }

    if (error instanceof Error && error.name === 'AbortError') {
      throw new HttpError('Request timeout. Please try again.', 408);
    }

    throw new HttpError('Network error. Please check your connection.', 0);
  }
}
