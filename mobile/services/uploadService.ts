export type UploadResponse = {
  url: string;
  public_id: string;
};

const RAW_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const BASE_URL = RAW_BASE_URL.replace(/\/+$/, '');

async function readResponsePayload(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function resolveUploadError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback;
  const data = payload as Record<string, unknown>;
  if (typeof data.detail === 'string' && data.detail.trim()) return data.detail;
  if (typeof data.message === 'string' && data.message.trim()) return data.message;
  return fallback;
}

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout>;
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(new Error('Upload ảnh quá lâu. Vui lòng thử lại.'));
    }, timeoutMs);
  });

  return Promise.race([promise, timeout]).finally(() => clearTimeout(timeoutId));
}

export async function uploadImage(token: string, uri: string, idempotencyKey?: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', {
    uri,
    name: 'upload.jpg',
    type: 'image/jpeg',
  } as unknown as Blob);
  if (idempotencyKey) {
    formData.append('idempotency_key', idempotencyKey);
  }

  const uploadRequest = async (): Promise<UploadResponse> => {
    const response = await fetch(`${BASE_URL}/uploads/image`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    const payload = await readResponsePayload(response);

    if (!response.ok) {
      throw new Error(resolveUploadError(payload, `Upload ảnh thất bại (${response.status}).`));
    }

    return payload as UploadResponse;
  };

  const isNetworkError = (error: unknown) =>
    error instanceof Error && /network request failed/i.test(error.message);

  try {
    const attempts = 2;
    let lastError: unknown = null;

    for (let attempt = 1; attempt <= attempts; attempt += 1) {
      try {
        return await withTimeout(uploadRequest(), 120000);
      } catch (error) {
        lastError = error;
        if (!isNetworkError(error) || attempt === attempts) {
          break;
        }
      }
    }

    throw lastError;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Không xác định';
    throw new Error(`Không upload được ảnh: ${message}`);
  }
}
