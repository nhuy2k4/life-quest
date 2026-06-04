import { requestJson } from '@/services/httpClient';

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  onboarding_completed: boolean;
};

type LoginRequest = {
  username: string;
  password: string;
};

type GoogleLoginRequest = {
  id_token: string;
};

type RefreshTokenRequest = {
  refresh_token: string;
};

const AUTH_BASE_PATH = '/auth';

export type RegisterRequest = {
  username: string;
  email: string;
  password?: string;
};

export type UserMeResponse = {
  id: string;
  username: string;
  email: string;
  level_id: number;
  xp: number;
  onboarding_completed: boolean;
  role: string;
};

export type VerifyEmailRequest = {
  email: string;
  otp: string;
};

export type ResendOtpRequest = {
  email: string;
};

export type MessageResponse = {
  message: string;
};

export async function login(request: LoginRequest): Promise<TokenResponse> {
  return requestJson<TokenResponse>(`${AUTH_BASE_PATH}/login`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function register(request: RegisterRequest): Promise<UserMeResponse> {
  return requestJson<UserMeResponse>(`${AUTH_BASE_PATH}/register`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function verifyEmail(request: VerifyEmailRequest): Promise<MessageResponse> {
  return requestJson<MessageResponse>(`${AUTH_BASE_PATH}/verify-email`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function resendOtp(request: ResendOtpRequest): Promise<MessageResponse> {
  return requestJson<MessageResponse>(`${AUTH_BASE_PATH}/resend-otp`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function loginWithGoogle(idToken: string): Promise<TokenResponse> {
  const payload: GoogleLoginRequest = { id_token: idToken };
  return requestJson<TokenResponse>(`${AUTH_BASE_PATH}/google/login`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function refreshToken(refreshTokenValue: string): Promise<TokenResponse> {
  const payload: RefreshTokenRequest = { refresh_token: refreshTokenValue };
  return requestJson<TokenResponse>(`${AUTH_BASE_PATH}/refresh`, {
    method: 'POST',
    body: JSON.stringify(payload),
    skipRefresh: true,
  });
}
