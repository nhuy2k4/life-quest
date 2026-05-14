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
};

const RAW_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const BASE_URL = RAW_BASE_URL.replace(/\/+$/, '');

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

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, timeoutMs = 15000, headers, ...rest } = options;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const isFormData = typeof FormData !== 'undefined' && rest.body instanceof FormData;

  try {
    const response = await fetch(buildUrl(path), {
      ...rest,
      headers: {
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
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
  } catch (error) {
    if (error instanceof HttpError) {
      throw error;
    }

    if (error instanceof Error && error.name === 'AbortError') {
      throw new HttpError('Request timeout. Please try again.', 408);
    }

    throw new HttpError('Network error. Please check your connection.', 0);
  } finally {
    clearTimeout(timeoutId);
  }
}
