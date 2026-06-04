type LevelThreshold = {
  id: number;
  requiredXp: number;
};

const LEVEL_THRESHOLDS: LevelThreshold[] = [
  { id: 1, requiredXp: 0 },
  { id: 2, requiredXp: 100 },
  { id: 3, requiredXp: 300 },
  { id: 4, requiredXp: 600 },
  { id: 5, requiredXp: 1000 },
  { id: 6, requiredXp: 1500 },
  { id: 7, requiredXp: 2200 },
  { id: 8, requiredXp: 3000 },
  { id: 9, requiredXp: 4000 },
  { id: 10, requiredXp: 5500 },
];

export type LevelProgress = {
  levelId: number;
  currentXp: number;
  nextLevelXp: number;
};

export function getLevelProgress(levelId: number, totalXp: number): LevelProgress {
  const byLevelId = LEVEL_THRESHOLDS.findIndex((level) => level.id === levelId);
  let fallbackIndex = 0;
  for (let i = LEVEL_THRESHOLDS.length - 1; i >= 0; i -= 1) {
    if (totalXp >= LEVEL_THRESHOLDS[i].requiredXp) {
      fallbackIndex = i;
      break;
    }
  }
  const index = byLevelId >= 0 ? byLevelId : fallbackIndex;

  const current = LEVEL_THRESHOLDS[index];
  const next = LEVEL_THRESHOLDS[index + 1] ?? current;
  const rawCurrentXp = Math.max(0, totalXp - current.requiredXp);
  const isMaxLevel = index === LEVEL_THRESHOLDS.length - 1;
  const nextLevelXp = isMaxLevel
    ? Math.max(rawCurrentXp, 1)
    : Math.max(1, next.requiredXp - current.requiredXp);
  const currentXp = isMaxLevel ? rawCurrentXp : Math.min(rawCurrentXp, nextLevelXp);

  return {
    levelId: current.id,
    currentXp,
    nextLevelXp,
  };
}
