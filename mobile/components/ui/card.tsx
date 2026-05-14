import { StyleSheet, View, type ViewProps } from 'react-native';

import { useColorScheme } from '@/hooks/use-color-scheme';

export function Card({ style, ...rest }: ViewProps) {
  const isDark = useColorScheme() === 'dark';

  return <View style={[styles.base, isDark ? styles.dark : styles.light, style]} {...rest} />;
}

const styles = StyleSheet.create({
  base: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
  },
  light: {
    backgroundColor: '#fff',
    borderColor: '#E5E7EB',
  },
  dark: {
    backgroundColor: '#1F2937',
    borderColor: '#374151',
  },
});
