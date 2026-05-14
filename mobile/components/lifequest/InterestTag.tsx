import { Pressable, StyleSheet, Text } from 'react-native';

type InterestTagProps = {
  label: string;
  selected?: boolean;
  onPress?: () => void;
};

export function InterestTag({ label, selected = false, onPress }: InterestTagProps) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={[styles.base, selected ? styles.selected : styles.unselected]}>
      <Text style={[styles.text, selected ? styles.selectedText : styles.unselectedText]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: 999,
    borderWidth: 1,
    minHeight: 36,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  selected: {
    backgroundColor: '#11181C',
    borderColor: '#11181C',
  },
  unselected: {
    backgroundColor: '#fff',
    borderColor: '#D1D5DB',
  },
  text: {
    fontSize: 13,
    fontWeight: '600',
  },
  selectedText: {
    color: '#fff',
  },
  unselectedText: {
    color: '#11181C',
  },
});
