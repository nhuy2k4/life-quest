import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getItem, removeItem, setItem, StorageKeys } from '@/utils/storage';
import { warmLocationCache } from '@/services/locationService';

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<'back' | 'front'>('back');
  const [torchEnabled, setTorchEnabled] = useState(false);
  const [zoom, setZoom] = useState(0);
  const cameraRef = useRef<CameraView | null>(null);
  const router = useRouter();

  useEffect(() => {
    const resetQuestContext = async () => {
      const mode = await getItem<string>(StorageKeys.cameraMode);
      if (mode === 'quest') {
        void warmLocationCache();
        return;
      }
      await setItem(StorageKeys.cameraMode, 'free');
      await removeItem(StorageKeys.attachedQuest);
    };
    void resetQuestContext();
  }, []);

  const handleCapture = async () => {
    if (!cameraRef.current) {
      return;
    }

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.5,
        skipProcessing: false,
      });
      if (photo?.uri) {
        router.push({ pathname: '/(main)/camera-result', params: { uri: photo.uri } });
      }
    } catch {
      // Capture errors are intentionally ignored to keep UX non-blocking.
    }
  };

  if (!permission) {
    return (
      <SafeAreaView style={styles.center}>
        <Text style={styles.statusText}>Checking camera permission...</Text>
      </SafeAreaView>
    );
  }

  if (!permission.granted) {
    if (permission.canAskAgain) {
      return (
        <SafeAreaView style={styles.center}>
          <Text style={styles.statusText}>Camera permission is required to continue.</Text>
          <TouchableOpacity onPress={requestPermission} style={styles.permissionButton}>
            <Text style={styles.permissionButtonText}>Grant permission</Text>
          </TouchableOpacity>
        </SafeAreaView>
      );
    }

    return (
      <SafeAreaView style={styles.center}>
        <Text style={styles.statusText}>Camera access is denied. Enable it in your device settings.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <View style={styles.previewContainer}>
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing={facing}
          enableTorch={torchEnabled}
          zoom={zoom}
        />

        <View pointerEvents="box-none" style={styles.overlayLayer}>
          <View style={styles.topBar}>
            <TouchableOpacity onPress={() => router.back()} style={styles.iconBtn}>
              <Ionicons name="arrow-back" size={24} color="#fff" />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setTorchEnabled((prev) => !prev)} style={styles.iconBtn}>
              <Ionicons name={torchEnabled ? 'flash' : 'flash-off'} size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          {/* Zoom controls */}
          <View style={styles.zoomContainer}>
            {[0, 0.25, 0.5].map((z, idx) => {
              const label = idx === 0 ? '1x' : idx === 1 ? '2x' : '3x';
              const active = zoom === z;
              return (
                <TouchableOpacity
                  key={z}
                  onPress={() => setZoom(z)}
                  style={[styles.zoomBtn, active && styles.zoomBtnActive]}
                >
                  <Text style={[styles.zoomBtnText, active && styles.zoomBtnTextActive]}>
                    {label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <View style={styles.bottomBar}>
            <TouchableOpacity onPress={handleCapture} style={styles.shutterBtn}>
              <View style={styles.shutterOuter}>
                <View style={styles.shutterInner} />
              </View>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setFacing((prev) => (prev === 'back' ? 'front' : 'back'))}
              style={styles.iconBtn}
            >
              <Ionicons name="camera-reverse" size={28} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  previewContainer: { flex: 1 },
  camera: { flex: 1 },
  overlayLayer: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'space-between',
  },
  topBar: {
    position: 'absolute',
    top: 40,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    zIndex: 10,
  },
  zoomContainer: {
    position: 'absolute',
    bottom: 140,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    zIndex: 10,
  },
  zoomBtn: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  zoomBtnActive: {
    backgroundColor: '#fff',
    borderColor: '#fff',
  },
  zoomBtnText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  zoomBtnTextActive: {
    color: '#000',
  },
  bottomBar: {
    position: 'absolute',
    bottom: 40,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 60,
    zIndex: 10,
  },
  iconBtn: {
    backgroundColor: 'rgba(0,0,0,0.4)',
    borderRadius: 24,
    padding: 8,
  },
  shutterBtn: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  shutterOuter: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 4,
    borderColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shutterInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#fff',
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#000',
    paddingHorizontal: 24,
    gap: 16,
  },
  statusText: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
  },
  permissionButton: {
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  permissionButtonText: {
    color: '#11181C',
    fontSize: 15,
    fontWeight: '600',
  },
});
