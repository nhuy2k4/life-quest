export const ROUTES = {
  auth: {
    login: '/(auth)/login',
    register: '/(auth)/register',
    otpVerification: '/(auth)/otp-verification',
  },
  onboarding: {
    intro: '/(onboarding)/intro',
    permission: '/(onboarding)/permission',
    username: '/(onboarding)/username',
    interests: '/(onboarding)/interests',
  },
  main: {
    home: '/(main)/home',
    camera: '/(main)/camera',
    cameraResult: '/(main)/camera-result',
    questLog: '/(main)/quest-log',
    notifications: '/(main)/notifications',
    profile: '/(main)/profile',
    settings: '/(main)/settings',
    editProfile: '/(main)/settings/edit-profile',
    changePassword: '/(main)/settings/change-password',
    xpHistory: '/(main)/settings/xp-history',
  },
  modal: {
    postDetail: '/post-detail',
    questDetail: '/quest-detail',
  },
  otherProfile: (id: string) => `/(main)/other-profile/${id}`,
} as const;
