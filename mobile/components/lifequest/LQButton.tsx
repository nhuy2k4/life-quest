import { StyleSheet, Text, type PressableProps } from 'react-native';

import { Button } from '@/components/ui/button';
import { useColorScheme } from '@/hooks/use-color-scheme';

type LQButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type LQButtonSize = 'sm' | 'md' | 'lg';

type LQButtonProps = PressableProps & {
  title: string;
  variant?: LQButtonVariant;
  size?: LQButtonSize;
  fullWidth?: boolean;
  loading?: boolean;
};

export function LQButton({
  title,
  variant = 'primary',
  size = 'md',
  fullWidth,
  loading,
  ...rest
}: LQButtonProps) {
  const isDark = useColorScheme() === 'dark';

  const textStyle = [
    styles.text,
    variant === 'primary' ? (isDark ? styles.textPrimaryDark : styles.textPrimaryLight) : null,
    variant === 'secondary' ? (isDark ? styles.textSecondaryDark : styles.textSecondaryLight) : null,
    variant === 'outline' ? (isDark ? styles.textOutlineDark : styles.textOutlineLight) : null,
    variant === 'ghost' ? (isDark ? styles.textGhostDark : styles.textGhostLight) : null,
  ];

  return (
    <Button variant={variant} size={size} fullWidth={fullWidth} loading={loading} {...rest}>
      <Text style={textStyle}>{title}</Text>
    </Button>
  );
}

const styles = StyleSheet.create({
  text: {
    fontSize: 15,
    fontWeight: '600',
  },
  textPrimaryDark: { color: '#11181C' },
  textPrimaryLight: { color: '#fff' },
  textSecondaryDark: { color: '#ECEDEE' },
  textSecondaryLight: { color: '#11181C' },
  textOutlineDark: { color: '#ECEDEE' },
  textOutlineLight: { color: '#11181C' },
  textGhostDark: { color: '#ECEDEE' },
  textGhostLight: { color: '#11181C' },
});
