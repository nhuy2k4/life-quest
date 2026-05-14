import { type PropsWithChildren, useEffect, useMemo, useRef } from 'react';
import {
  Animated,
  Modal,
  Pressable,
  StyleSheet,
  View,
  type ViewStyle,
} from 'react-native';

type BottomSheetShellProps = PropsWithChildren<{
  open: boolean;
  onClose: () => void;
  height?: number;
  style?: ViewStyle;
}>;

export function BottomSheetShell({ open, onClose, height = 420, style, children }: BottomSheetShellProps) {
  const translateY = useRef(new Animated.Value(height)).current;

  useEffect(() => {
    Animated.timing(translateY, {
      toValue: open ? 0 : height,
      duration: 220,
      useNativeDriver: true,
    }).start();
  }, [height, open, translateY]);

  const sheetStyle = useMemo(
    () => [styles.sheet, { height, transform: [{ translateY }] }, style],
    [height, style, translateY]
  );

  return (
    <Modal animationType="none" transparent visible={open} onRequestClose={onClose}>
      <View style={styles.overlay}>
        <Pressable style={styles.backdrop} onPress={onClose} />
        <Animated.View style={sheetStyle}>{children}</Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  sheet: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 16,
  },
});
