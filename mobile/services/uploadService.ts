import { requestJson } from '@/services/httpClient';
import * as ImageManipulator from 'expo-image-manipulator';

export type UploadResponse = {
  url: string;
  public_id: string;
};

type UploadSignatureResponse = {
  cloud_name: string;
  api_key: string;
  timestamp: number;
  signature: string;
  folder: string;
  resource_type: 'image';
  public_id?: string | null;
  overwrite?: string | null;
  unique_filename?: string | null;
};

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

async function prepareUploadUri(uri: string): Promise<string> {
  const result = await ImageManipulator.manipulateAsync(
    uri,
    [{ resize: { width: 1280 } }],
    {
      compress: 0.6,
      format: ImageManipulator.SaveFormat.JPEG,
    }
  );

  return result.uri;
}

export async function uploadImage(token: string, uri: string, idempotencyKey?: string): Promise<UploadResponse> {
  const preparedUri = await prepareUploadUri(uri);

  const uploadToCloudinary = async (signature: UploadSignatureResponse): Promise<UploadResponse> => {
    const uploadStartAt = Date.now();
    const cloudinaryFormData = new FormData();
    cloudinaryFormData.append('file', {
      uri: preparedUri,
      name: 'upload.jpg',
      type: 'image/jpeg',
    } as unknown as Blob);
    cloudinaryFormData.append('api_key', signature.api_key);
    cloudinaryFormData.append('timestamp', String(signature.timestamp));
    cloudinaryFormData.append('signature', signature.signature);
    cloudinaryFormData.append('folder', signature.folder);
    if (signature.public_id) {
      cloudinaryFormData.append('public_id', signature.public_id);
      cloudinaryFormData.append('overwrite', signature.overwrite ?? 'true');
      cloudinaryFormData.append('unique_filename', signature.unique_filename ?? 'false');
    }

    const response = await fetch(`https://api.cloudinary.com/v1_1/${signature.cloud_name}/image/upload`, {
      method: 'POST',
      body: cloudinaryFormData,
    });

    const payload = await readResponsePayload(response);

    if (!response.ok) {
      throw new Error(resolveUploadError(payload, `Upload ảnh thất bại (${response.status}).`));
    }

    if (!payload || typeof payload !== 'object') {
      throw new Error('Upload ảnh thất bại: Cloudinary trả về dữ liệu không hợp lệ.');
    }

    const data = payload as Record<string, unknown>;
    const url = typeof data.secure_url === 'string' ? data.secure_url : typeof data.url === 'string' ? data.url : null;
    const publicId = typeof data.public_id === 'string' ? data.public_id : null;

    if (!url || !publicId) {
      throw new Error('Upload ảnh thất bại: Cloudinary trả về dữ liệu không hợp lệ.');
    }

    if (__DEV__) {
      console.info('[upload] cloudinary_upload_ms=', Date.now() - uploadStartAt);
    }

    return { url, public_id: publicId };
  };

  const uploadRequest = async (): Promise<UploadResponse> => {
    const signStartAt = Date.now();
    const signature = await requestJson<UploadSignatureResponse>('/uploads/image/sign', {
      method: 'POST',
      token,
      body: JSON.stringify({
        idempotency_key: idempotencyKey || undefined,
      }),
    });

    if (__DEV__) {
      console.info('[upload] sign_ms=', Date.now() - signStartAt);
    }

    return await uploadToCloudinary(signature);
  };

  const isNetworkError = (error: unknown) =>
    error instanceof Error && /network request failed/i.test(error.message);

  try {
    const totalStartAt = Date.now();
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

    if (__DEV__) {
      console.info('[upload] total_ms=', Date.now() - totalStartAt);
    }

    throw lastError;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Không xác định';
    throw new Error(`Không upload được ảnh: ${message}`);
  }
}
