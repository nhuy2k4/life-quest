import { StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';

import { useColorScheme } from '@/hooks/use-color-scheme';

type InputProps = TextInputProps & {
  label?: string;
  error?: string;
  helperText?: string;
};

export function Input({ label, error, helperText, style, ...rest }: InputProps) {
  const isDark = useColorScheme() === 'dark';

  return (
    <View style={styles.container}>
      {label ? <Text style={[styles.label, isDark ? styles.labelDark : styles.labelLight]}>{label}</Text> : null}
      <TextInput
        style={[
          styles.input,
          isDark ? styles.inputDark : styles.inputLight,
          error ? styles.inputError : null,
          style,
        ]}
        placeholderTextColor={isDark ? '#9CA3AF' : '#6B7280'}
        {...rest}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {!error && helperText ? (
        <Text style={[styles.helper, isDark ? styles.helperDark : styles.helperLight]}>{helperText}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 6,
    width: '100%',
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
  },
  labelLight: { color: '#11181C' },
  labelDark: { color: '#ECEDEE' },
  input: {
    borderRadius: 10,
    borderWidth: 1,
    fontSize: 15,
    minHeight: 44,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  inputLight: {
    backgroundColor: '#fff',
    borderColor: '#D1D5DB',
    color: '#11181C',
  },
  inputDark: {
    backgroundColor: '#1F2937',
    borderColor: '#4B5563',
    color: '#ECEDEE',
  },
  inputError: {
    borderColor: '#DC2626',
  },
  error: {
    color: '#DC2626',
    fontSize: 12,
  },
  helper: {
    fontSize: 12,
  },
  helperLight: { color: '#6B7280' },
  helperDark: { color: '#9CA3AF' },
});
