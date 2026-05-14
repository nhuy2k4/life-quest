import React, { useEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  Modal,
  FlatList,
  ActivityIndicator,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { Button } from '@/components/ui/button';
import { ROUTES } from '@/constants/routes';
import { usePostContext } from '@/contexts/PostContext';
import { useToast } from '@/contexts/ToastContext';
import { computeFileHash, submitQuest, recommendQuestsFromImage, type QuestListItem } from '@/services/questService';
import { createPost } from '@/services/socialService';
import { uploadImage } from '@/services/uploadService';
import type { Post, Quest } from '@/types';
import { StorageKeys, getItem, removeItem, setItem } from '@/utils/storage';

export default function CameraResultScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { posts, setPosts } = usePostContext();
  const { showToast } = useToast();

  const [caption, setCaption] = useState('');
  const [location, setLocation] = useState('');
  const [showLocation, setShowLocation] = useState(false);
  const [posting, setPosting] = useState(false);
  const [attachedQuest, setAttachedQuest] = useState<Pick<Quest, 'title' | 'xpReward'> | null>(null);
  const [attachedQuestId, setAttachedQuestId] = useState<string | null>(null);

  // Caching uploaded image details to prevent redundant network calls
  const [uploadedCache, setUploadedCache] = useState<{ url: string; publicId: string } | null>(null);

  // Trạng thái quản lý Picker Quest động
  const [isPickerVisible, setPickerVisible] = useState(false);
  const [availableQuests, setAvailableQuests] = useState<QuestListItem[]>([]);
  const [loadingQuests, setLoadingQuests] = useState(false);

  const handleOpenPicker = async () => {
    setPickerVisible(true);
    setLoadingQuests(true);
    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      // 1. Phải có ảnh trên Cloudinary thì AI Backend mới phân tích được. Upload nếu chưa cache.
      let activeUpload = uploadedCache;
      if (!activeUpload) {
        const result = await uploadImage(token, imageUri, computeFileHash(imageUri));
        activeUpload = { url: result.url, publicId: result.public_id };
        setUploadedCache(activeUpload); // Cache lại để lát ấn Post ko cần upload lại
      }

      let lat: number | undefined;
      let lng: number | undefined;

      // Attempt fast GPS fetch to enable cross-referencing AI vision with physical location proximity
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status === 'granted') {
          const currentPos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
          lat = currentPos.coords.latitude;
          lng = currentPos.coords.longitude;
        }
      } catch {
        console.log('Location acquisition skipped/failed for recommendations.');
      }

      // 2. Gọi AI Backend để lọc danh sách Quest khớp cả ảnh VÀ địa lý
      const matchedQuests = await recommendQuestsFromImage(token, activeUpload.url, lat, lng);
      
      // Chỉ hiển thị những gì AI tìm thấy, nếu ko thấy thì để trống (ko fallback bừa bãi)
      setAvailableQuests(matchedQuests || []);

    } catch {
      showToast('AI phân tích ảnh thất bại. Hãy thử lại.');
      setPickerVisible(false);
    } finally {
      setLoadingQuests(false);
    }
  };

  const handleSelectQuest = (quest: QuestListItem) => {
    setAttachedQuest({
      title: quest.rendered_text,
      xpReward: quest.xp_reward,
    });
    setAttachedQuestId(quest.id);
    setPickerVisible(false);
  };

  const [isLocating, setIsLocating] = useState(false);

  const handleLocateSelf = async () => {
    setShowLocation(true);
    setIsLocating(true);
    setLocation('Đang lấy vị trí...');

    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocation('');
        showToast('Không có quyền truy cập vị trí.');
        setIsLocating(false);
        return;
      }

      // OPTIMIZATION: Fetch last known cached location for INSTANT execution
      let currentPos = await Location.getLastKnownPositionAsync({});
      
      if (!currentPos) {
        // Fallback to CELL TOWER lookup which takes ~0.5s instead of waiting 10s for satellite lock
        currentPos = await Location.getCurrentPositionAsync({ 
          accuracy: Location.Accuracy.Low 
        });
      }

      const addresses = await Location.reverseGeocodeAsync({
        latitude: currentPos.coords.latitude,
        longitude: currentPos.coords.longitude,
      });

      if (addresses && addresses.length > 0) {
        const a = addresses[0];
        // Build clean descriptive location string from component parts
        const parts = [a.name, a.street, a.district, a.city || a.region].filter(Boolean);
        // Select best readable subset (usually top 2 items provide nice context e.g. "Quận 1, HCM")
        const readable = parts.slice(0, 2).join(', '); 
        setLocation(readable || 'Vị trí hiện tại');
      } else {
        setLocation('Vị trí hiện tại');
      }
    } catch (err) {
      console.log('Geocoding failure', err);
      setLocation('');
    } finally {
      setIsLocating(false);
    }
  };


  const imageUri = typeof params.uri === 'string' ? params.uri : undefined;

  useEffect(() => {
    const hydrateAttachedQuest = async () => {
      const raw = await getItem<{
        questId?: string;
        title: string;
        xp: number;
      }>(StorageKeys.attachedQuest);

      if (!raw) return;

      setAttachedQuest({
        title: raw.title,
        xpReward: raw.xp,
      });
      setAttachedQuestId(raw.questId ?? null);
    };

    void hydrateAttachedQuest();
  }, []);

  const handlePost = async () => {
    const token = await getItem<string>(StorageKeys.accessToken);

    if (!token) {
      showToast('Bạn chưa đăng nhập.');
      return;
    }

    if (!imageUri) {
      showToast('Không tìm thấy ảnh để đăng.');
      return;
    }

    setPosting(true);

    try {
      const cameraMode = await getItem<string>(StorageKeys.cameraMode);

      // STEP 1: Universal image upload (reuses cache if preset)
      let upload: { url: string; public_id: string };
      try {
        if (uploadedCache) {
          upload = { url: uploadedCache.url, public_id: uploadedCache.publicId };
        } else {
          const res = await uploadImage(token, imageUri, computeFileHash(imageUri));
          upload = { url: res.url, public_id: res.public_id };
          setUploadedCache({ url: upload.url, publicId: upload.public_id });
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
        throw new Error(`Upload ảnh thất bại: ${msg}`);
      }

      let serverPost: Awaited<ReturnType<typeof createPost>>;

      // STEP 2: Determine routing logic. 
      // Explicitly separate formal "Do task" flow from casual "Free post with tag" flow.
      if (attachedQuestId && cameraMode === 'quest') {
        // ── FORMAL QUEST SUBMISSION FLOW ──
        let submission: { submission_id: string };
        try {
          submission = await submitQuest(token, attachedQuestId, {
            imageUrl: upload.url,
            cloudinaryPublicId: upload.public_id,
            fileHash: computeFileHash(imageUri),
          });
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
          throw new Error(`Submit quest thất bại: ${msg}`);
        }

        try {
          serverPost = await createPost(token, {
            submissionId: submission.submission_id,
            caption: caption.trim() || undefined
          });
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
          throw new Error(`Tạo post thất bại: ${msg}`);
        }
      } else {
        // ── FREE POST FLOW (Optionally attaches a reference quest tag without evaluating for formal completion) ──
        try {
          serverPost = await createPost(token, {
            imageUrl: upload.url,
            questId: attachedQuestId || undefined, // Handled smoothly by decoupled backend link
            caption: caption.trim() || undefined
          });
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
          throw new Error(`Tạo post thất bại: ${msg}`);
        }
      }

      // STEP 3: Normalize and finalize client state
      const newPost: Post = {
        id: serverPost.id,
        author: {
          id: serverPost.user.id,
          username: serverPost.user.username,
        },
        submissionId: serverPost.submission_id ?? undefined,
        imageUrl: serverPost.submission_image_url ?? imageUri,
        caption: caption.trim() || '',
        quest: serverPost.quest
          ? {
              id: serverPost.quest.id,
              title: serverPost.quest.title,
              description: serverPost.quest.description ?? undefined,
              xp_reward: serverPost.quest.xp_reward,
            }
          : undefined,
        location: location.trim() || undefined,
        createdAt: serverPost.created_at,
        likesCount: 0,
        commentsCount: 0,
        isLiked: false,
        isSaved: false,
      };

      setPosts([newPost, ...posts]);
      void setItem(StorageKeys.newPost, newPost);
      void removeItem(StorageKeys.attachedQuest);
      showToast('Đăng bài thành công! 🎉');


      router.replace(ROUTES.main.home);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Đã xảy ra lỗi.';
      showToast(message);
    } finally {
      setPosting(false);
    }
  };


  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.iconBtn}>
            <Ionicons name="arrow-back" size={24} color="#11181C" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>New Post</Text>
        </View>

        <View style={styles.row}>
          <TouchableOpacity onPress={() => router.back()}>
            <ImageWithFallback uri={imageUri} width={96} height={96} borderRadius={16} />
          </TouchableOpacity>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <TextInput
              value={caption}
              onChangeText={setCaption}
              placeholder="Write a caption…"
              maxLength={300}
              multiline
              style={styles.captionInput}
            />
            <Text style={styles.captionCount}>{`${caption.length}/300`}</Text>
          </View>
        </View>

        <View style={styles.section}>
          {!showLocation ? (
            <TouchableOpacity 
              style={styles.locationBtn} 
              onPress={handleLocateSelf}
              disabled={isLocating}
            >
              {isLocating ? (
                <ActivityIndicator size="small" color="#6B7280" style={{ marginRight: 6 }} />
              ) : (
                <Ionicons name="location-outline" size={18} color="#6B7280" />
              )}
              <Text style={styles.locationText}>
                {isLocating ? 'Finding location...' : 'Add location'}
              </Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.locationInputRow}>
              <Ionicons name="location-outline" size={18} color="#6B7280" />
              <TextInput
                value={location}
                onChangeText={setLocation}
                placeholder="Where was this taken?"
                style={styles.locationInput}
                autoFocus
                editable={!isLocating}
              />
              <TouchableOpacity
                onPress={() => {
                  setShowLocation(false);
                  setLocation('');
                }}
                disabled={isLocating}
              >
                <Ionicons name="close" size={18} color="#9CA3AF" />
              </TouchableOpacity>
            </View>
          )}
        </View>


        <View style={styles.section}>
          {attachedQuest ? (
            <View style={styles.questRow}>
              <View style={styles.questIcon}>
                <Ionicons name="flash" size={18} color="#F59E0B" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.questLabel}>Quest attached</Text>
                <Text style={styles.questTitle}>{attachedQuest.title}</Text>
                <Text style={styles.questMeta}>{`+${attachedQuest.xpReward} XP`}</Text>
              </View>
              <TouchableOpacity onPress={() => { setAttachedQuest(null); setAttachedQuestId(null); }}>
                <Ionicons name="close" size={18} color="#9CA3AF" />
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity
              style={styles.questCta}
              onPress={handleOpenPicker}>
              <Ionicons name="sparkles" size={18} color="#6366F1" />
              <View style={{ flex: 1 }}>
                <Text style={styles.questCtaTitle}>Try a Quest</Text>
                <Text style={styles.questCtaDesc}>Browse quests to attach to this post</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.questHint}>Quest will be automatically evaluated and rewarded after you post.</Text>

        <View style={styles.bottomRow}>
          <Button variant="outline" style={{ flex: 1, marginRight: 8 }} onPress={() => router.back()}>
            Retake
          </Button>
          <Button variant="primary" style={{ flex: 1 }} onPress={handlePost} loading={posting} disabled={posting}>
            Post
          </Button>
        </View>
      </KeyboardAvoidingView>

      <Modal visible={isPickerVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select a Quest</Text>
              <TouchableOpacity onPress={() => setPickerVisible(false)}>
                <Ionicons name="close" size={24} color="#11181C" />
              </TouchableOpacity>
            </View>

            {loadingQuests ? (
              <View style={{ padding: 32 }}>
                <ActivityIndicator color="#6366F1" size="large" />
              </View>
            ) : (
              <FlatList
                data={availableQuests}
                keyExtractor={(item) => item.id}
                contentContainerStyle={{ padding: 16 }}
                ItemSeparatorComponent={() => <View style={{ height: 1, backgroundColor: '#F3F4F6', marginVertical: 8 }} />}
                ListEmptyComponent={
                  <Text style={{ textAlign: 'center', color: '#6B7280', marginTop: 20 }}>
                    Không tìm thấy nhiệm vụ phù hợp chưa hoàn thành.
                  </Text>
                }

                renderItem={({ item }) => (
                  <Pressable style={styles.pickerItem} onPress={() => handleSelectQuest(item)}>
                    <View style={styles.questIconMini}>
                      <Ionicons name="flash" size={16} color="#F59E0B" />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={{ fontWeight: '600', fontSize: 15, color: '#11181C' }}>
                        {item.rendered_text}
                      </Text>
                      <Text style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>
                        {`+${item.xp_reward} XP`}
                      </Text>
                    </View>
                    <Ionicons name="chevron-forward" size={16} color="#9CA3AF" />
                  </Pressable>
                )}
              />
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 24,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderColor: '#F3F4F6',
    backgroundColor: '#fff',
  },
  iconBtn: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#11181C',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    borderBottomWidth: 1,
    borderColor: '#F3F4F6',
    backgroundColor: '#fff',
  },
  captionInput: {
    fontSize: 15,
    minHeight: 44,
    maxHeight: 100,
    color: '#11181C',
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
    marginBottom: 4,
  },
  captionCount: {
    fontSize: 12,
    color: '#9CA3AF',
    alignSelf: 'flex-end',
  },
  section: {
    borderBottomWidth: 1,
    borderColor: '#F3F4F6',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  locationBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 6,
  },
  locationText: {
    fontSize: 15,
    color: '#6B7280',
    marginLeft: 8,
  },
  locationInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  locationInput: {
    flex: 1,
    fontSize: 15,
    color: '#11181C',
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  questRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 6,
  },
  questIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  questLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    marginBottom: 2,
  },
  questTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#11181C',
  },
  questMeta: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  questCta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 6,
  },
  questCtaTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: '#11181C',
  },
  questCtaDesc: {
    fontSize: 12,
    color: '#6B7280',
  },
  questHint: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 4,
  },
  bottomRow: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderColor: '#F3F4F6',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '80%',
    minHeight: '40%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderColor: '#F3F4F6',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#11181C',
  },
  pickerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  questIconMini: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
});
