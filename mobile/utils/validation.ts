const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email: string): string | null {
  const value = email.trim();
  if (!value) return 'Email is required.';
  if (!EMAIL_REGEX.test(value)) return 'Invalid email format.';
  return null;
}

export function validatePassword(password: string): string | null {
  if (!password) return 'Password is required.';
  if (password.length < 8) return 'Password must be at least 8 characters.';
  return null;
}

export function validateUsername(username: string): string | null {
  const value = username.trim();
  if (!value) return 'Username is required.';
  if (value.length < 3) return 'Username must be at least 3 characters.';
  if (value.length > 24) return 'Username must be at most 24 characters.';
  return null;
}

export function validateCaption(caption: string, limit = 300): string | null {
  if (caption.length > limit) return `Caption cannot exceed ${limit} characters.`;
  return null;
}
