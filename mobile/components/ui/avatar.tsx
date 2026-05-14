import { Image } from 'expo-image';
import { StyleSheet, Text, View } from 'react-native';

type AvatarProps = {
  uri?: string;
  size?: number;
  label?: string;
};

export function Avatar({ uri, size = 40, label = '?' }: AvatarProps) {
  const borderRadius = size / 2;

  if (!uri) {
    return (
      <View style={[styles.fallback, { width: size, height: size, borderRadius }]}> 
        <Text style={styles.fallbackText}>{label.slice(0, 1).toUpperCase()}</Text>
      </View>
    );
  }

  return <Image source={{ uri }} style={{ width: size, height: size, borderRadius }} contentFit="cover" />;
}

const styles = StyleSheet.create({
  fallback: {
    alignItems: 'center',
    backgroundColor: '#6B7280',
    justifyContent: 'center',
  },
  fallbackText: {
    color: '#fff',
    fontWeight: '700',
  },
});
