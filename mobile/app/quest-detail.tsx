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
import { startQuest, getQuestDetail } from '@/services/questService';
import { getItem, StorageKeys, setItem } from '@/utils/storage';




export default function QuestDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const questId = typeof params.questId === 'string' ? params.questId : undefined;
  const [questTitle, setQuestTitle] = useState('');
  const [questDescription, setQuestDescription] = useState('');
  const [questXp, setQuestXp] = useState(0);
  const [userStatus, setUserStatus] = useState<string>('not_started');
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);


  const handleStartQuest = async () => {
    if (!questId) return;
    setIsStarting(true);

    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      if (userStatus !== 'started') {
        try {
          await startQuest(token, questId);
        } catch {
          // Ignore conflict
        }
      }

      await setItem(StorageKeys.cameraMode, 'quest');
      await setItem(StorageKeys.attachedQuest, {
        questId,
        title: questTitle,
        xp: questXp,
      });
      router.push(ROUTES.main.camera as Href);
    } finally {
      setIsStarting(false);
    }
  };

  useEffect(() => {
    const loadQuest = async () => {
      if (!questId) return;
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      setIsLoading(true);
      try {
        const detail = await getQuestDetail(token, questId);
        setQuestTitle(detail.rendered_text);
        if (detail.labels && detail.labels.length > 0) {
          setQuestDescription(`Category: ${detail.labels.join(', ')}`);
        } else {
          setQuestDescription('');
        }
        setQuestXp(detail.xp_reward);
        setUserStatus(detail.user_status);

      } finally {
        setIsLoading(false);
      }
    };

    void loadQuest();
  }, [questId]);

  const { statusLabel, buttonTitle, isButtonDisabled, buttonVariant } = useMemo(() => {
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
          statusLabel: 'Failed (Retry)',
          buttonTitle: 'Retry Quest',
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
  }, [userStatus]);

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
        <ImageWithFallback fallbackText="Quest" height={220} borderRadius={14} />

        <View style={styles.infoWrap}>
          <View style={styles.titleRow}>
            <View style={styles.titleBlock}>
              <Text style={styles.title}>{questTitle}</Text>
              <Text style={styles.description}>{questDescription}</Text>
            </View>
            <XPBadge xp={questXp} />
          </View>

          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Status</Text>
              <Text style={[styles.statValue, { color: userStatus === 'approved' ? '#10B981' : '#11181C' }]}>{statusLabel}</Text>
            </View>
          </View>

          <View style={styles.actionsWrap}>
            <LQButton 
              title={buttonTitle} 
              variant={buttonVariant} 
              disabled={isButtonDisabled}
              fullWidth 
              onPress={handleStartQuest} 
              loading={isStarting} 
            />

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
});
