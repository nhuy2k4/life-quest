import { createContext, useCallback, useContext, useMemo, useState, type PropsWithChildren } from 'react';
import { StyleSheet, Text, View } from 'react-native';

type ToastContextValue = {
  showToast: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: PropsWithChildren) {
  const [message, setMessage] = useState<string | null>(null);

  const showToast = useCallback((nextMessage: string) => {
    setMessage(nextMessage);
    setTimeout(() => setMessage(null), 2400);
  }, []);

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {message ? (
        <View style={styles.toast} pointerEvents="none">
          <Text style={styles.toastText}>{message}</Text>
        </View>
      ) : null}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

const styles = StyleSheet.create({
  toast: {
    position: 'absolute',
    bottom: 42,
    left: 20,
    right: 20,
    backgroundColor: '#11181C',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 14,
    alignItems: 'center',
  },
  toastText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
});
