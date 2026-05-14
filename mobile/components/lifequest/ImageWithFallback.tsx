import { Image } from 'expo-image';
import { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

type ImageWithFallbackProps = {
  uri?: string;
  fallbackText?: string;
  width?: number | '100%';
  height?: number;
  borderRadius?: number;
};

export function ImageWithFallback({
  uri,
  fallbackText = 'No image',
  width = '100%',
  height = 180,
  borderRadius = 12,
}: ImageWithFallbackProps) {
  const [failed, setFailed] = useState(false);

  const style = useMemo(() => ({ width, height, borderRadius }), [borderRadius, height, width]);

  if (!uri || failed) {
    return (
      <View style={[styles.fallback, style]}>
        <Text style={styles.fallbackText}>{fallbackText}</Text>
      </View>
    );
  }

  return <Image source={{ uri }} style={style} contentFit="cover" onError={() => setFailed(true)} />;
}

const styles = StyleSheet.create({
  fallback: {
    alignItems: 'center',
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
  },
  fallbackText: {
    color: '#6B7280',
    fontSize: 13,
    fontWeight: '600',
  },
});
