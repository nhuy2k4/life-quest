import { Ionicons } from '@expo/vector-icons';
import { type Href, useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';

import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BottomNav } from '@/components/lifequest/BottomNav';
import { ImageWithFallback } from '@/components/lifequest/ImageWithFallback';
import { LQButton } from '@/components/lifequest/LQButton';
import { XPBadge } from '@/components/lifequest/XPBadge';
import { Layout } from '@/constants/layout';
import { ROUTES } from '@/constants/routes';
import { logRecommendationEvent, type RecommendationSectionKey, type RecommendationScoreBreakdown } from '@/services/recommendationService';
import { startQuest, getQuestDetail } from '@/services/questService';
import { warmLocationCache } from '@/services/locationService';
import { getItem, StorageKeys, setItem } from '@/utils/storage';




export default function QuestDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const questId = typeof params.questId === 'string' ? params.questId : undefined;
  const poiId = typeof params.poiId === 'string' ? params.poiId : undefined;
  const isEvent = params.isEvent === 'true';
  const routePoiName = typeof params.poiName === 'string' ? params.poiName : undefined;
  const recommendationRequestId = typeof params.recommendationRequestId === 'string' ? params.recommendationRequestId : undefined;
  const recommendationSection = typeof params.recommendationSection === 'string' ? params.recommendationSection as RecommendationSectionKey : undefined;
  const recommendationRank = typeof params.recommendationRank === 'string' ? Number(params.recommendationRank) : undefined;
  const recommendationScore = typeof params.recommendationScore === 'string' ? Number(params.recommendationScore) : undefined;
  const recommendationReasons = typeof params.recommendationReasons === 'string' ? params.recommendationReasons : undefined;
  const recommendationBreakdown = typeof params.recommendationBreakdown === 'string' ? params.recommendationBreakdown : undefined;
  const [questTitle, setQuestTitle] = useState('');
  const [questDescription, setQuestDescription] = useState('');
  const [questXp, setQuestXp] = useState(0);
  const [baseXp, setBaseXp] = useState(0);
const [poiBonusXp, setPoiBonusXp] = useState(0);
const [totalXpWithPoi, setTotalXpWithPoi] = useState(0);
  const [questImageUrl, setQuestImageUrl] = useState<string | null>(null);
  const [userStatus, setUserStatus] = useState<string>('not_started');
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [poiRequired, setPoiRequired] = useState(false);
  const [poiName, setPoiName] = useState<string | null>(null);
  const [effectivePoiId, setEffectivePoiId] = useState<string | null>(poiId ?? null);
  const [isEventQuestFromServer, setIsEventQuestFromServer] = useState(false);


  const handleStartQuest = async () => {
    if (!questId) return;

    if (isEventQuestFromServer && !isEvent && userStatus === 'not_started') {
      router.back();
      return;
    }

    setIsStarting(true);

    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      if (userStatus !== 'started') {
        try {
          await startQuest(token, questId, effectivePoiId);
          if (recommendationRequestId) {
            let reasons: string[] = [];
            let scoreBreakdown: RecommendationScoreBreakdown | undefined;
            try {
              reasons = recommendationReasons ? JSON.parse(recommendationReasons) : [];
              scoreBreakdown = recommendationBreakdown ? JSON.parse(recommendationBreakdown) : undefined;
            } catch {
              reasons = [];
            }
            await logRecommendationEvent(token, {
              request_id: recommendationRequestId,
              quest_id: questId,
              event: 'started',
              section: recommendationSection,
              rank: Number.isFinite(recommendationRank) ? recommendationRank : undefined,
              final_score: Number.isFinite(recommendationScore) ? recommendationScore : undefined,
              reasons,
              score_breakdown: scoreBreakdown,
            });
          }
        } catch {
          // Ignore conflict
        }
      }

      await setItem(StorageKeys.cameraMode, 'quest');
      await setItem(StorageKeys.attachedQuest, {
        questId,
        title: questTitle,
        xp: questXp,
        poi_id: effectivePoiId,
        poi_name: poiName,
        isEvent,
      });
      router.push(ROUTES.main.camera as Href);
    } finally {
      setIsStarting(false);
    }
  };

  useEffect(() => {
    void warmLocationCache();

    const loadQuest = async () => {
      if (!questId) return;
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      setIsLoading(true);
      try {
        const detail = await getQuestDetail(token, questId, poiId);
        const nextPoiId = detail.poi_id ?? poiId ?? null;
        const nextPoiName = detail.poi_name ?? routePoiName ?? null;
        const hasLocationContext = Boolean(nextPoiId || nextPoiName || detail.poi_required);

        setQuestTitle(detail.rendered_text);
        if (detail.labels && detail.labels.length > 0) {
          setQuestDescription(`Category: ${detail.labels.join(', ')}`);
        } else {
          setQuestDescription('');
        }
setQuestXp(hasLocationContext ? detail.total_xp_with_poi : detail.base_xp);
setBaseXp(detail.base_xp);
setPoiBonusXp(detail.poi_bonus_xp);
setTotalXpWithPoi(detail.total_xp_with_poi);
  setQuestImageUrl(detail.image_url ?? null);
        setUserStatus(detail.user_status);
        setPoiRequired(hasLocationContext);
        setPoiName(nextPoiName);
        setEffectivePoiId(nextPoiId);
        setIsEventQuestFromServer(!!detail.is_event);

      } finally {
        setIsLoading(false);
      }
    };

    void loadQuest();
  }, [questId, poiId, routePoiName]);

  const { statusLabel, buttonTitle, isButtonDisabled, buttonVariant } = useMemo(() => {
    console.log('[QuestDetail] isEventQuestFromServer:', isEventQuestFromServer, 'isEvent:', isEvent, 'userStatus:', userStatus);

    if (isEventQuestFromServer && !isEvent && userStatus === 'not_started') {
      return {
        statusLabel: 'Event Quest',
        buttonTitle: 'Back to feed',
        isButtonDisabled: false,
        buttonVariant: 'primary' as const,
      };
    }

    switch (userStatus) {
      case 'approved':
        return {
          statusLabel: 'Completed',
          buttonTitle: 'Quest Completed 🎉',
          isButtonDisabled: true,
          buttonVariant: 'primary' as const,
        };
      case 'submitted':
        return {
          statusLabel: 'Reviewing',
          buttonTitle: 'Already Submitted ⏳',
          isButtonDisabled: true,
          buttonVariant: 'primary' as const,
        };
      case 'started':
        return {
          statusLabel: 'Progressing',
          buttonTitle: 'Continue Quest',
          isButtonDisabled: false,
          buttonVariant: 'primary' as const,
        };
      case 'rejected':
        return {
          statusLabel: 'Almost there!',
          buttonTitle: 'Try Again',
          isButtonDisabled: false,
          buttonVariant: 'primary' as const,
        };
      default:
        return {
          statusLabel: 'Available',
          buttonTitle: 'Start Quest',
          isButtonDisabled: false,
          buttonVariant: 'primary' as const,
        };
    }
  }, [userStatus, isEventQuestFromServer, isEvent]);

  return (

    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color="#11181C" />
        </Pressable>
        <Text style={styles.headerTitle}>Quest Details</Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}>
        <ImageWithFallback uri={questImageUrl ?? undefined} fallbackText="Quest" height={220} borderRadius={14} />

        <View style={styles.infoWrap}>
          <View style={styles.titleRow}>
            <View style={styles.titleBlock}>
              <Text style={styles.title}>{questTitle}</Text>
              <Text style={styles.description}>{questDescription}</Text>
            </View>
            <XPBadge xp={baseXp} />
          </View>

          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Trạng thái</Text>
              <Text style={[styles.statValue, { color: userStatus === 'approved' ? '#10B981' : '#11181C' }]}>{statusLabel}</Text>
            </View>

            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Thưởng cơ bản</Text>
              <Text style={styles.statValue}>{`+${baseXp} XP`}</Text>
            </View>

            {poiRequired ? (
              <View style={styles.statItem}>
                <Text style={styles.statLabelGreen}>Thưởng Vị trí</Text>
                <Text style={styles.statValueGreen}>{`+${poiBonusXp} XP`}</Text>
              </View>
            ) : null}
          </View>

          {isEventQuestFromServer ? (
            <View style={styles.locationReqCardEvent}>
              <View style={styles.locationReqHeader}>
                <Ionicons name="calendar" size={16} color="#7C3AED" />
                <Text style={styles.locationReqTitleEvent}>Nhiệm vụ Event</Text>
              </View>
              <Text style={styles.locationReqDescEvent}>
                Đây là nhiệm vụ dành riêng cho sự kiện. Bạn cần tham gia sự kiện và chụp ảnh tại khu vực Đà Nẵng để hoàn thành nhiệm vụ này và nhận {baseXp} XP.
              </Text>
            </View>
          ) : poiRequired ? (
            <View style={styles.locationReqCard}>
              <View style={styles.locationReqHeader}>
                <Ionicons name="location" size={16} color="#10B981" />
                <Text style={styles.locationReqTitle}>Nhiệm vụ có Vị trí (+50% XP)</Text>
              </View>
              <Text style={styles.locationReqDesc}>
                Bạn có thể hoàn thành nhiệm vụ này theo cách cơ bản để nhận {baseXp} XP, hoặc chụp ảnh kèm định vị GPS ngay tại địa điểm {poiName ? `"${poiName}"` : 'quy định'} để nhận thêm {poiBonusXp} XP, tổng cộng {totalXpWithPoi} XP.
              </Text>
            </View>
          ) : (
            <View style={styles.locationReqCardBase}>
              <View style={styles.locationReqHeader}>
                <Ionicons name="sparkles" size={16} color="#F59E0B" />
                <Text style={styles.locationReqTitleBase}>Nhiệm vụ Cơ bản</Text>
              </View>
              <Text style={styles.locationReqDescBase}>
                Đây là nhiệm vụ chụp ảnh cơ bản, bạn có thể thực hiện ở bất kỳ đâu để nhận {baseXp} XP.
              </Text>
            </View>
          )}

          <View style={styles.actionsWrap}>
            {!(isEventQuestFromServer && !isEvent && userStatus === 'not_started') && (
              <LQButton 
                title={buttonTitle} 
                variant={buttonVariant} 
                disabled={isButtonDisabled}
                fullWidth 
                onPress={handleStartQuest} 
                loading={isStarting} 
              />
            )}

            <LQButton
              title="Back to Feed"
              variant="outline"
              fullWidth
              onPress={() => router.push(ROUTES.main.home as Href)}
            />
          </View>
        </View>
      </ScrollView>

      <BottomNav />
      {isLoading ? (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="small" color="#11181C" />
        </View>
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 20,
    fontWeight: '700',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: Layout.bottomNavHeight + 36,
    gap: 18,
  },
  infoWrap: {
    gap: 16,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  titleBlock: {
    flex: 1,
    gap: 8,
  },
  title: {
    color: '#11181C',
    fontSize: 28,
    fontWeight: '800',
    lineHeight: 34,
  },
  description: {
    color: '#4B5563',
    fontSize: 14,
    lineHeight: 21,
  },
  statsRow: {
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#E5E7EB',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 14,
    gap: 8,
  },
  statItem: {
    flex: 1,
    gap: 2,
  },
  statLabel: {
    color: '#6B7280',
    fontSize: 12,
  },
  statValue: {
    color: '#11181C',
    fontSize: 15,
    fontWeight: '600',
  },


  actionsWrap: {
    gap: 10,
    paddingTop: 6,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 12,
    right: 16,
  },
  locationReqCard: {
    backgroundColor: '#ECFDF5',
    borderColor: '#A7F3D0',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    gap: 6,
  },
  locationReqHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  locationReqTitle: {
    color: '#065F46',
    fontSize: 14,
    fontWeight: '700',
  },
  locationReqDesc: {
    color: '#047857',
    fontSize: 13,
    lineHeight: 18,
  },
  locationReqCardBase: {
    backgroundColor: '#FEF3C7',
    borderColor: '#FDE68A',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    gap: 6,
  },
  locationReqTitleBase: {
    color: '#92400E',
    fontSize: 14,
    fontWeight: '700',
  },
  locationReqDescBase: {
    color: '#B45309',
    fontSize: 13,
    lineHeight: 18,
  },
  locationReqCardEvent: {
    backgroundColor: '#F5F3FF',
    borderColor: '#C4B5FD',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    gap: 6,
  },
  locationReqTitleEvent: {
    color: '#5B21B6',
    fontSize: 14,
    fontWeight: '700',
  },
  locationReqDescEvent: {
    color: '#6D28D9',
    fontSize: 13,
    lineHeight: 18,
  },
  statLabelGreen: {
    color: '#10B981',
    fontSize: 12,
    fontWeight: '700',
  },
  statValueGreen: {
    color: '#10B981',
    fontSize: 15,
    fontWeight: '700',
  },
});
