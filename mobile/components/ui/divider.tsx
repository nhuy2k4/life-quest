import { StyleSheet, View, type ViewProps } from 'react-native';

import { useColorScheme } from '@/hooks/use-color-scheme';

export function Divider({ style, ...rest }: ViewProps) {
  const isDark = useColorScheme() === 'dark';
  return <View style={[styles.base, isDark ? styles.dark : styles.light, style]} {...rest} />;
}

const styles = StyleSheet.create({
  base: {
    height: StyleSheet.hairlineWidth,
    width: '100%',
  },
  light: {
    backgroundColor: '#E5E7EB',
  },
  dark: {
    backgroundColor: '#374151',
  },
});
