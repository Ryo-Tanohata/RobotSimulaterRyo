// 動画の台本 (仮)
export const STAGE_LABELS = {
  walk: '段階 1　平らな地面を前へ',
  rough: '段階 2　でこぼこ道',
  obstacles: '段階 3　壁をよけてゴールへ',
};
const close = { count: 1, camera: [1.4, 0.55, -0.2], lookAhead: 0.1, markers: true, markerLength: 12 };
export const SCENES = [
  { kind: 'population', stage: 'walk', gen: 0, randomBrains: true, seconds: 6, badge: '第 1 <small>世代</small>', graph: true, spacing: 0.9 },
  { kind: 'population', stage: 'walk', gen: 0, seconds: 5, badge: '第 1 (代表)', ...close },
  { kind: 'population', stage: 'walk', gen: 5, seconds: 5, badge: '第 5', ...close },
  { kind: 'population', stage: 'walk', gen: 10, seconds: 5, badge: '第 10', ...close },
  { kind: 'population', stage: 'walk', gen: 20, seconds: 5, badge: '第 20', ...close },
  { kind: 'population', stage: 'walk', gen: 60, seconds: 5, badge: '第 60', ...close },
  { kind: 'population', stage: 'walk', gen: 150, seconds: 5, badge: '第 150', ...close },
  { kind: 'population', stage: 'walk', gen: 'last', seconds: 5, badge: '最終', ...close },
  { kind: 'race', stage: 'walk', gens: ['random', 5, 20, 60, 'last'], labels: ['第1世代', '第5世代', '第20世代', '第60世代', '最終世代'], seconds: 9, spacing: 1.1, camera: [6.5, 4.0, -2.0], followLead: true, badge: '世代対抗レース', graph: true },
];
