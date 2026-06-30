import React, { useEffect, useRef, useState } from 'react';
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
import { useXpGain } from '@/contexts/XpGainContext';
import { computeFileHash, submitQuest, startQuest, recommendQuestsFromImage, type QuestListItem } from '@/services/questService';
import { suggestPoi } from '@/services/poiService';
import { getAppLocation } from '@/services/locationService';
import { createPost, deletePost, mapFeedPost } from '@/services/socialService';
import { uploadImage } from '@/services/uploadService';
import type { Post, Quest } from '@/types';
import { StorageKeys, getItem, removeItem, setItem } from '@/utils/storage';

function getDistanceMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371e3; // Earth radius in meters
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const deltaPhi = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLambda = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

export default function CameraResultScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { posts, setPosts } = usePostContext();
  const { showToast } = useToast();
  const { showXpGain } = useXpGain();

  const [caption, setCaption] = useState('');
  const [location, setLocation] = useState('');
  const [visibility, setVisibility] = useState<'public' | 'friends' | 'private'>('public');
  const [posting, setPosting] = useState(false);
  const [attachedQuest, setAttachedQuest] = useState<Pick<Quest, 'title' | 'xpReward'> | null>(null);
  const [attachedQuestId, setAttachedQuestId] = useState<string | null>(null);
  const [coords, setCoords] = useState<{ latitude: number; longitude: number; capturedAt: number } | null>(null);
  const [poiId, setPoiId] = useState<string | null>(null);
  const [questPoiId, setQuestPoiId] = useState<string | null>(null);
  const attachedPoiRef = useRef<string | null>(null);

  const [isQuestFlow, setIsQuestFlow] = useState(false);
  const [isEventQuest, setIsEventQuest] = useState(false);
  const [isCheckingLocation, setIsCheckingLocation] = useState(false);
  const [suggestedPoi, setSuggestedPoi] = useState<{ id: string; name: string } | null>(null);

  const [eventLocationName, setEventLocationName] = useState<string | null>(null);
  const [eventLatitude, setEventLatitude] = useState<number | null>(null);
  const [eventLongitude, setEventLongitude] = useState<number | null>(null);
  const [eventRadiusM, setEventRadiusM] = useState<number | null>(null);

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
      if (!imageUri) return;

      // 1. Phải có ảnh trên Cloudinary thì AI Backend mới phân tích được. Upload nếu chưa cache.
      let activeUpload = uploadedCache;
      if (!activeUpload) {
        const result = await uploadImage(token, imageUri, computeFileHash(imageUri));
        activeUpload = { url: result.url, publicId: result.public_id };
        setUploadedCache(activeUpload); // Cache lại để lát ấn Post ko cần upload lại
      }

      let lat: number | undefined;
      let lng: number | undefined;

      const currentLocation = await getAppLocation({ maxAgeMs: 60 * 1000 });
      lat = currentLocation?.latitude;
      lng = currentLocation?.longitude;

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
    // Không tự động gắn poi_id từ quest — user chưa confirm họ đang ở địa điểm đó.
    // poi_id sẽ chỉ được gắn nếu user bấm chấp nhận gợi ý vị trí (suggestedPoi) từ GPS thực tế.
    setPickerVisible(false);
  };

  const [, setIsLocating] = useState(false);
  const imageUri = typeof params.uri === 'string' ? params.uri : undefined;

  useEffect(() => {
    if (isEventQuest) {
      setVisibility('public');
    }
  }, [isEventQuest]);

  useEffect(() => {
    const init = async () => {
      let isQuest = false;
      let isEvent = false;
      let activeQuestPoiId: string | null = null;
      
      try {
        const cameraMode = await getItem<string>(StorageKeys.cameraMode);
        const raw = await getItem<{
          questId?: string;
          title: string;
          xp: number;
          poi_id?: string | null;
          poi_name?: string | null;
          poi_required?: boolean;
          isEvent?: boolean;
          eventId?: string | null;
          eventLocationName?: string | null;
          eventLatitude?: number | null;
          eventLongitude?: number | null;
          eventRadiusM?: number | null;
        }>(StorageKeys.attachedQuest);

        if (cameraMode === 'quest' && raw) {
          isQuest = true;
          isEvent = !!raw.isEvent;
          setIsQuestFlow(true);
          setIsEventQuest(isEvent);
          setAttachedQuest({
            title: raw.title,
            xpReward: raw.xp,
          });
          setAttachedQuestId(raw.questId ?? null);
          attachedPoiRef.current = raw.poi_id ?? null;
          activeQuestPoiId = raw.poi_id ?? null;
          setQuestPoiId(raw.poi_id ?? null);
          setEventLocationName(raw.eventLocationName ?? null);
          setEventLatitude(raw.eventLatitude ?? null);
          setEventLongitude(raw.eventLongitude ?? null);
          setEventRadiusM(raw.eventRadiusM ?? null);
        }
      } catch (err) {
        console.log('Error hydrating attached quest', err);
      }

      setIsCheckingLocation(true);
      const startTime = Date.now();

      setIsLocating(true);
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          showToast('Không có quyền truy cập vị trí.');
          setIsLocating(false);
          setIsCheckingLocation(false);
          return;
        }

        const currentLocation = await getAppLocation({
          forceRefresh: true,
          maxAgeMs: 30 * 1000,
          accuracy: Location.Accuracy.High,
        });
        if (!currentLocation) {
          setIsCheckingLocation(false);
          setIsLocating(false);
          return;
        }
        let currentPos = {
          coords: {
            latitude: currentLocation.latitude,
            longitude: currentLocation.longitude,
            accuracy: currentLocation.accuracy,
          },
        };
        setCoords({
          latitude: currentPos.coords.latitude,
          longitude: currentPos.coords.longitude,
          capturedAt: currentLocation.capturedAt,
        });

        const { latitude, longitude, accuracy } = currentPos.coords;
        if (isEvent) {
          const storedQuest = await getItem<{
            eventLatitude?: number | null;
            eventLongitude?: number | null;
            eventRadiusM?: number | null;
            eventLocationName?: string | null;
          }>(StorageKeys.attachedQuest);

          if (storedQuest && storedQuest.eventLatitude != null && storedQuest.eventLongitude != null) {
            const radius = storedQuest.eventRadiusM || 100;
            const dist = getDistanceMeters(latitude, longitude, storedQuest.eventLatitude, storedQuest.eventLongitude);
            if (dist <= radius) {
              setPoiId(null);
              setLocation(storedQuest.eventLocationName || 'Khu vực sự kiện');
            } else {
              setPoiId(null);
              setLocation('');
            }
          } else {
            if (latitude >= 15.90 && latitude <= 16.25 && longitude >= 107.80 && longitude <= 108.35) {
              setPoiId(null);
              setLocation('Đà Nẵng');
            } else {
              setPoiId(null);
              setLocation('');
            }
          }
        } else {
          const suggestion = await suggestPoi(latitude, longitude, accuracy);
          
          if (suggestion.poi_id && suggestion.name) {
            if (isQuest && activeQuestPoiId) {
              if (suggestion.poi_id === activeQuestPoiId) {
                setPoiId(activeQuestPoiId);
                setLocation(suggestion.name);
              }
            } else {
              setSuggestedPoi({ id: suggestion.poi_id, name: suggestion.name });
            }
          }
        }
      } catch (err) {
        console.log('POI suggestion failure', err);
      } finally {
        const elapsed = Date.now() - startTime;
        const remaining = 5000 - elapsed;
        if (remaining > 0) {
          await new Promise((resolve) => setTimeout(resolve, remaining));
        }
        setIsCheckingLocation(false);
        setIsLocating(false);
      }
    };

    void init();
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
      let earnedXp = 0;

      // STEP 2: Determine routing logic.
      // Create the social post before quest submission so a post failure can never award XP.
      if (attachedQuestId) {
        // ── FORMAL QUEST SUBMISSION FLOW ──
        // Ensure the quest is started before submitting (covers "Try a Quest" picker flow
        // where startQuest was never called, unlike the quest-detail → camera flow).
        try {
          const startResult = await startQuest(token, attachedQuestId, poiId);
          // If the quest is REJECTED (retry mode), startQuest now returns status=rejected.
          // This is fine — submitQuest will handle the retry path on the backend.
          if (startResult.status === 'submitted' || startResult.status === 'approved') {
            // Quest already finalized; cannot resubmit
            showToast('Quest này đã được nộp hoặc hoàn thành rồi.');
            return;
          }
        } catch (startErr) {
          // Only propagate if it's a hard block (not REJECTED retry allowing resubmit)
          const msg = startErr instanceof Error ? startErr.message : '';
          const isHardBlock = msg.includes('đã được nộp') || msg.includes('hoàn thành') || msg.includes('hết số lần');
          if (isHardBlock) {
            showToast(msg);
            return;
          }
          // Otherwise ignore (quest might already be in STARTED state — safe to continue)
        }

        let submissionLat = coords?.latitude;
        let submissionLng = coords?.longitude;

        const coordsAreOld = !coords?.capturedAt || Date.now() - coords.capturedAt > 30 * 1000;
        if (!submissionLat || !submissionLng || coordsAreOld) {
          const latestLocation = await getAppLocation({ forceRefresh: true, maxAgeMs: 30 * 1000 });
          submissionLat = latestLocation?.latitude ?? submissionLat;
          submissionLng = latestLocation?.longitude ?? submissionLng;
        }

        try {
          serverPost = await createPost(token, {
            imageUrl: upload.url,
            questId: attachedQuestId,
            caption: caption.trim() || undefined,
            locationName: location.trim() || undefined,
            poiId,
            visibility,
            isEvent: isEventQuest,
          });
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
          throw new Error(msg);
        }

        let submission: Awaited<ReturnType<typeof submitQuest>>;
        try {
          submission = await submitQuest(token, attachedQuestId, {
            postId: serverPost.id,
            imageUrl: upload.url,
            cloudinaryPublicId: upload.public_id,
            fileHash: computeFileHash(imageUri),
            poiId,
            lat: submissionLat,
            lng: submissionLng,
            isEvent: isEventQuest,
          });
          if (submission.status === 'approved' || submission.submission_status === 'approved') {
            earnedXp = submission.xp_granted ?? submission.xp_reward ?? attachedQuest?.xpReward ?? 0;
          }
        } catch (err) {
          await deletePost(token, serverPost.id).catch(() => undefined);
          const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
          throw new Error(msg);
        }

        serverPost = {
          ...serverPost,
          id: submission.post_id ?? serverPost.id,
          submission_id: submission.submission_id,
        };
      } else {
        // ── FREE POST FLOW (Optionally attaches a reference quest tag without evaluating for formal completion) ──
        try {
          serverPost = await createPost(token, {
            imageUrl: upload.url,
            questId: attachedQuestId || undefined, // Handled smoothly by decoupled backend link
            caption: caption.trim() || undefined,
            locationName: location.trim() || undefined,
            poiId,
            visibility,
          });
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
          throw new Error(msg);
        }
      }

      // STEP 3: Normalize and finalize client state
      const newPost: Post = {
        ...mapFeedPost(serverPost),
        imageUrl: serverPost.submission_image_url ?? imageUri, // Preserve local URI fallback if server url is slow to load
      };

      const matchingPost = posts.find((post) => {
        if (post.id === newPost.id) return true;
        if (post.submissionId && newPost.submissionId && post.submissionId === newPost.submissionId) return true;
        return false;
      });

      const postForFeed: Post = matchingPost
        ? {
            ...newPost,
            id: matchingPost.id,
            createdAt: matchingPost.createdAt,
            likesCount: matchingPost.likesCount,
            commentsCount: matchingPost.commentsCount,
            isLiked: matchingPost.isLiked,
            followedByMe: matchingPost.followedByMe,
          }
        : newPost;

      setPosts((prev) => {
        const existingIndex = prev.findIndex((post) => {
          if (post.id === postForFeed.id) return true;
          if (post.submissionId && postForFeed.submissionId && post.submissionId === postForFeed.submissionId) return true;
          return false;
        });
        if (existingIndex !== -1) {
          const next = [...prev];
          next[existingIndex] = {
            ...postForFeed,
            id: prev[existingIndex].id,
            createdAt: prev[existingIndex].createdAt,
            likesCount: prev[existingIndex].likesCount,
            commentsCount: prev[existingIndex].commentsCount,
            isLiked: prev[existingIndex].isLiked,
            followedByMe: prev[existingIndex].followedByMe,
          };
          return next;
        }
        return [postForFeed, ...prev];
      });
      void setItem(StorageKeys.newPost, postForFeed);
      void removeItem(StorageKeys.attachedQuest);
      showXpGain(earnedXp);
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

        {isQuestFlow ? (
          <>
            {isCheckingLocation ? (
              <View style={styles.section}>
                <View style={styles.checkingBox}>
                  <ActivityIndicator size="small" color="#4F46E5" style={{ marginRight: 8 }} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.checkingText}>Đang kiểm tra vị trí...</Text>
                  </View>
                </View>
              </View>
            ) : (
              <>
                {isEventQuest && location ? (
                  <View style={styles.section}>
                    <View style={styles.locationInputRow}>
                      <Ionicons name="location" size={18} color="#10B981" />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.locationHint}>Đã check-in vị trí sự kiện</Text>
                        <Text style={styles.locationText}>{location}</Text>
                      </View>
                    </View>
                  </View>
                ) : null}

                {isEventQuest && !location ? (
                  <View style={styles.section}>
                    <View style={styles.warningBox}>
                      <Ionicons name="warning-outline" size={18} color="#DC2626" />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.warningText}>Bạn hiện không ở vị trí này!</Text>
                      </View>
                    </View>
                  </View>
                ) : null}

                {!isEventQuest && location && poiId ? (
                  <View style={styles.section}>
                    <View style={styles.locationInputRow}>
                      <Ionicons name="location" size={18} color="#10B981" />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.locationHint}>Đã gắn vị trí</Text>
                        <Text style={styles.locationText}>{location}</Text>
                      </View>
                      {!attachedPoiRef.current ? (
                        <TouchableOpacity onPress={() => { setPoiId(null); setLocation(''); }}>
                          <Ionicons name="close" size={18} color="#9CA3AF" />
                        </TouchableOpacity>
                      ) : null}
                    </View>
                  </View>
                ) : null}

                {!isEventQuest && questPoiId && !poiId ? (
                  <View style={styles.section}>
                    <View style={styles.warningBox}>
                      <Ionicons name="warning-outline" size={18} color="#DC2626" />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.warningText}>Có vẻ bạn không ở vị trí này!</Text>
                      </View>
                    </View>
                  </View>
                ) : null}
              </>
            )}

            {suggestedPoi && (!poiId || poiId !== suggestedPoi.id) && !isEventQuest ? (
              <View style={styles.section}>
                <TouchableOpacity
                  style={styles.suggestionBox}
                  onPress={() => {
                    setPoiId(suggestedPoi.id);
                    setLocation(suggestedPoi.name);
                    showToast('Đã gắn vị trí gợi ý!');
                  }}
                >
                  <Ionicons name="location-outline" size={18} color="#10B981" />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.suggestionHint}>Bạn đang ở gần đây? Bấm để gắn vị trí</Text>
                    <Text style={styles.suggestionText}>{suggestedPoi.name}</Text>
                  </View>
                  <View style={styles.suggestionAction}>
                    <Text style={styles.suggestionActionText}>Gắn</Text>
                    <Ionicons name="add" size={14} color="#10B981" />
                  </View>
                </TouchableOpacity>
              </View>
            ) : null}
          </>
        ) : (
          <>
            {isCheckingLocation ? (
              <View style={styles.section}>
                <View style={styles.checkingBox}>
                  <ActivityIndicator size="small" color="#4F46E5" style={{ marginRight: 8 }} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.checkingText}>Đang kiểm tra vị trí...</Text>
                  </View>
                </View>
              </View>
            ) : (
              <>
                {location ? (
                  <View style={styles.section}>
                    <View style={styles.locationInputRow}>
                      <Ionicons name="location" size={18} color="#10B981" />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.locationHint}>{poiId ? 'Đã gắn vị trí' : 'Đã lấy vị trí hiện tại'}</Text>
                        <Text style={styles.locationText}>{location}</Text>
                      </View>
                      <TouchableOpacity onPress={() => { setPoiId(null); setLocation(''); }}>
                        <Ionicons name="close" size={18} color="#9CA3AF" />
                      </TouchableOpacity>
                    </View>
                  </View>
                ) : null}

                {suggestedPoi && (!poiId || poiId !== suggestedPoi.id) ? (
                  <View style={styles.section}>
                    <TouchableOpacity
                      style={styles.suggestionBox}
                      onPress={() => {
                        setPoiId(suggestedPoi.id);
                        setLocation(suggestedPoi.name);
                        showToast('Đã gắn vị trí gợi ý!');
                      }}
                    >
                      <Ionicons name="location-outline" size={18} color="#10B981" />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.suggestionHint}>Bạn đang ở gần đây? Bấm để gắn vị trí</Text>
                        <Text style={styles.suggestionText}>{suggestedPoi.name}</Text>
                      </View>
                      <View style={styles.suggestionAction}>
                        <Text style={styles.suggestionActionText}>Gắn</Text>
                        <Ionicons name="add" size={14} color="#10B981" />
                      </View>
                    </TouchableOpacity>
                  </View>
                ) : null}

                {!location && !suggestedPoi ? (
                  <View style={styles.section}>
                    <View style={styles.noLocationBox}>
                      <Ionicons name="location-outline" size={18} color="#6B7280" />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.noLocationText}>Không tìm thấy vị trí phù hợp!</Text>
                      </View>
                    </View>
                  </View>
                ) : null}
              </>
            )}
          </>
        )}

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

        <View style={styles.section}>
          <Text style={styles.visibilityLabel}>Ai có thể xem bài viết này?</Text>
          <View style={styles.visibilityOptions}>
            <TouchableOpacity 
              style={[
                styles.visibilityOption, 
                visibility === 'public' && styles.visibilityOptionActive,
                isEventQuest && { flex: 1 }
              ]}
              onPress={() => setVisibility('public')}
            >
              <Ionicons name="earth" size={16} color={visibility === 'public' ? '#4F46E5' : '#6B7280'} />
              <Text style={[styles.visibilityText, visibility === 'public' && styles.visibilityTextActive]}>Công khai</Text>
            </TouchableOpacity>
            {!isEventQuest && (
              <>
                <TouchableOpacity 
                  style={[styles.visibilityOption, visibility === 'friends' && styles.visibilityOptionActive]}
                  onPress={() => setVisibility('friends')}
                >
                  <Ionicons name="people" size={16} color={visibility === 'friends' ? '#4F46E5' : '#6B7280'} />
                  <Text style={[styles.visibilityText, visibility === 'friends' && styles.visibilityTextActive]}>Bạn bè</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.visibilityOption, visibility === 'private' && styles.visibilityOptionActive]}
                  onPress={() => setVisibility('private')}
                >
                  <Ionicons name="lock-closed" size={16} color={visibility === 'private' ? '#4F46E5' : '#6B7280'} />
                  <Text style={[styles.visibilityText, visibility === 'private' && styles.visibilityTextActive]}>Chỉ mình tôi</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
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
    color: '#11181C',
  },
  locationHint: {
    fontSize: 12,
    color: '#10B981',
    marginBottom: 2,
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
  suggestionBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#ECFDF5',
    borderColor: '#A7F3D0',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  suggestionHint: {
    fontSize: 11,
    color: '#059669',
    fontWeight: '500',
    marginBottom: 2,
  },
  suggestionText: {
    fontSize: 14,
    color: '#047857',
    fontWeight: '600',
  },
  suggestionAction: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 16,
    gap: 2,
  },
  suggestionActionText: {
    fontSize: 12,
    color: '#047857',
    fontWeight: '600',
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#FEF2F2',
    borderColor: '#FCA5A5',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  warningText: {
    fontSize: 14,
    color: '#DC2626',
    fontWeight: '600',
  },
  checkingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#EEF2FF',
    borderColor: '#C7D2FE',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  checkingText: {
    fontSize: 14,
    color: '#4F46E5',
    fontWeight: '600',
  },
  noLocationBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#F3F4F6',
    borderColor: '#E5E7EB',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  noLocationText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  visibilityLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#4B5563',
    marginBottom: 8,
  },
  visibilityOptions: {
    flexDirection: 'row',
    gap: 8,
  },
  visibilityOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  visibilityOptionActive: {
    backgroundColor: '#EEF2FF',
    borderColor: '#C7D2FE',
  },
  visibilityText: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  visibilityTextActive: {
    color: '#4F46E5',
    fontWeight: '600',
  },
});
