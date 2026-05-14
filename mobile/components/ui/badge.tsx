import { StyleSheet, Text, View, type ViewProps } from 'react-native';

import { useColorScheme } from '@/hooks/use-color-scheme';

type BadgeProps = ViewProps & {
  label: string;
};

export function Badge({ label, style, ...rest }: BadgeProps) {
  const isDark = useColorScheme() === 'dark';

  return (
    <View style={[styles.base, isDark ? styles.dark : styles.light, style]} {...rest}>
      <Text style={[styles.label, isDark ? styles.labelDark : styles.labelLight]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    alignSelf: 'flex-start',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  light: {
    backgroundColor: '#11181C',
  },
  dark: {
    backgroundColor: '#ECEDEE',
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
  },
  labelLight: {
    color: '#fff',
  },
  labelDark: {
    color: '#11181C',
  },
});
