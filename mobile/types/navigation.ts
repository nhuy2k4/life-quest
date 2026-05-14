export type AuthRoutes = '/(auth)/login' | '/(auth)/register' | '/(auth)/otp-verification';

export type OnboardingRoutes =
  | '/(onboarding)/intro'
  | '/(onboarding)/permission'
  | '/(onboarding)/username'
  | '/(onboarding)/interests';

export type MainRoutes =
  | '/(main)/home'
  | '/(main)/camera'
  | '/(main)/camera-result'
  | '/(main)/quest-log'
  | '/(main)/notifications'
  | '/(main)/profile'
  | '/(main)/settings'
  | '/(main)/settings/edit-profile'
  | '/(main)/settings/change-password';

export type ModalRoutes = '/post-detail' | '/quest-detail';

export interface OtherProfileParams {
  id: string;
}
