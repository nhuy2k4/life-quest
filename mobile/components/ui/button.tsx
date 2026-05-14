import { Children, isValidElement } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  type PressableProps,
  type StyleProp,
  type TextStyle,
  type ViewStyle,
} from 'react-native';

import { useColorScheme } from '@/hooks/use-color-scheme';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

type ButtonProps = PressableProps & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
  style?: StyleProp<ViewStyle>;
};

const sizeStyles: Record<ButtonSize, ViewStyle> = {
  sm: { minHeight: 36, paddingHorizontal: 12, paddingVertical: 8 },
  md: { minHeight: 44, paddingHorizontal: 16, paddingVertical: 10 },
  lg: { minHeight: 52, paddingHorizontal: 20, paddingVertical: 14 },
};

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  fullWidth,
  style,
  children,
  ...rest
}: ButtonProps) {
  const isDark = useColorScheme() === 'dark';
  const isDisabled = disabled || loading;
  const textStyle = [
    styles.text,
    variant === 'primary' ? (isDark ? styles.textPrimaryDark : styles.textPrimaryLight) : null,
    variant === 'secondary' ? (isDark ? styles.textSecondaryDark : styles.textSecondaryLight) : null,
    variant === 'outline' ? (isDark ? styles.textOutlineDark : styles.textOutlineLight) : null,
    variant === 'ghost' ? (isDark ? styles.textGhostDark : styles.textGhostLight) : null,
  ] as TextStyle[];

  const baseStyle = [
    styles.base,
    sizeStyles[size],
    fullWidth ? styles.fullWidth : null,
    variant === 'primary' ? (isDark ? styles.primaryDark : styles.primaryLight) : null,
    variant === 'secondary' ? (isDark ? styles.secondaryDark : styles.secondaryLight) : null,
    variant === 'outline' ? (isDark ? styles.outlineDark : styles.outlineLight) : null,
    variant === 'ghost' ? styles.ghost : null,
    isDisabled ? styles.disabled : null,
    style,
  ];

  const normalizedChildren = Children.map(children, (child) => {
    if (typeof child === 'string' || typeof child === 'number') {
      return <Text style={textStyle}>{child}</Text>;
    }
    if (isValidElement(child)) {
      return child;
    }
    return null;
  });

  return (
    <Pressable accessibilityRole="button" disabled={isDisabled} style={baseStyle} {...rest}>
      {loading ? <ActivityIndicator color={isDark ? '#fff' : '#111'} /> : normalizedChildren}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    alignItems: 'center',
    borderRadius: 12,
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    minWidth: 44,
  },
  primaryDark: {
    backgroundColor: '#fff',
  },
  primaryLight: {
    backgroundColor: '#11181C',
  },
  secondaryDark: {
    backgroundColor: '#2A2D2E',
  },
  secondaryLight: {
    backgroundColor: '#ECEDEE',
  },
  outlineDark: {
    borderColor: '#6B7280',
    borderWidth: 1,
    backgroundColor: 'transparent',
  },
  outlineLight: {
    borderColor: '#D1D5DB',
    borderWidth: 1,
    backgroundColor: 'transparent',
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  disabled: {
    opacity: 0.6,
  },
  fullWidth: {
    width: '100%',
  },
  text: {
    fontSize: 15,
    fontWeight: '600',
  },
  textPrimaryDark: {
    color: '#11181C',
  },
  textPrimaryLight: {
    color: '#fff',
  },
  textSecondaryDark: {
    color: '#ECEDEE',
  },
  textSecondaryLight: {
    color: '#11181C',
  },
  textOutlineDark: {
    color: '#ECEDEE',
  },
  textOutlineLight: {
    color: '#11181C',
  },
  textGhostDark: {
    color: '#ECEDEE',
  },
  textGhostLight: {
    color: '#11181C',
  },
});
