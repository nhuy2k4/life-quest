import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  Easing,
} from 'react-native-reanimated';

type BadgeProgressRingProps = {
  size?: number;
  strokeWidth?: number;
  percent: number; // 0–100
  color: string;
  backgroundColor?: string;
};

/**
 * Arc-style progress indicator built purely with Reanimated View transforms.
 * No SVG dependency required.
 * Renders a half-arc using two rotated semi-circle Views.
 */
export function BadgeProgressRing({
  size = 80,
  strokeWidth = 6,
  percent,
  color,
  backgroundColor = '#1F2937',
}: BadgeProgressRingProps) {
  const progress = useSharedValue(0);

  useEffect(() => {
    progress.value = withTiming(percent / 100, {
      duration: 900,
      easing: Easing.out(Easing.cubic),
    });
  }, [percent, progress]);

  // Left half fill: 0–50%
  const leftStyle = useAnimatedStyle(() => {
    const angle = Math.min(progress.value * 2, 1) * 180;
    return {
      transform: [{ rotate: `${angle}deg` }],
    };
  });

  // Right half fill: 50–100%
  const rightStyle = useAnimatedStyle(() => {
    if (progress.value <= 0.5) {
      return { transform: [{ rotate: '0deg' }] };
    }
    const angle = (progress.value - 0.5) * 2 * 180;
    return {
      transform: [{ rotate: `${angle}deg` }],
    };
  });

  const rightVisible = useAnimatedStyle(() => ({
    opacity: progress.value > 0.5 ? 1 : 0,
  }));

  const half = size / 2;
  const innerSize = size - strokeWidth * 2;

  return (
    <View style={{ width: size, height: size }}>
      {/* Background circle */}
      <View
        style={[
          styles.circle,
          {
            width: size,
            height: size,
            borderRadius: half,
            borderWidth: strokeWidth,
            borderColor: backgroundColor,
          },
        ]}
      />

      {/* Left semi-circle clip */}
      <View
        style={[
          styles.clipContainer,
          { width: half, height: size, left: 0, top: 0 },
        ]}
      >
        <Animated.View
          style={[
            styles.halfCircle,
            {
              width: size,
              height: size,
              borderRadius: half,
              borderWidth: strokeWidth,
              borderColor: color,
              transformOrigin: `${half}px ${half}px`,
            },
            leftStyle,
          ]}
        />
      </View>

      {/* Right semi-circle clip */}
      <Animated.View
        style={[
          styles.clipContainer,
          { width: half, height: size, right: 0, top: 0 },
          rightVisible,
        ]}
      >
        <Animated.View
          style={[
            styles.halfCircleRight,
            {
              width: size,
              height: size,
              borderRadius: half,
              borderWidth: strokeWidth,
              borderColor: color,
              right: 0,
              transformOrigin: `${half}px ${half}px`,
            },
            rightStyle,
          ]}
        />
      </Animated.View>

      {/* Inner mask to create ring effect */}
      <View
        style={[
          styles.innerMask,
          {
            width: innerSize,
            height: innerSize,
            borderRadius: innerSize / 2,
            top: strokeWidth,
            left: strokeWidth,
          },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  circle: {
    position: 'absolute',
  },
  clipContainer: {
    overflow: 'hidden',
    position: 'absolute',
  },
  halfCircle: {
    position: 'absolute',
    left: 0,
    top: 0,
  },
  halfCircleRight: {
    position: 'absolute',
    top: 0,
  },
  innerMask: {
    backgroundColor: '#0F172A', // matches sheet background
    position: 'absolute',
  },
});
