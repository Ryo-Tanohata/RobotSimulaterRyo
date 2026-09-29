// 動画の台本。場面 (scene) を上から順に再生する。字幕の文章や秒数はここを書き換えれば変わる。
//   kind: 'card'       … 文字だけの画面 (title, body)
//         'population' … ある世代の個体たちを走らせる (stage, gen, count)
//         'race'       … 違う世代を横に並べて同時にスタート (stage, gens, labels)
//   badge: true で「第 N 世代」を自動表示 (段階をまたいだ通し番号)
//   captions: [[秒, '字幕'], ...]   camera: 注視点から見たカメラの位置 [x, y, z]
export const STAGE_LABELS = {
  walk: '課題 1　平らな地面を前へ',
  posture: '課題 2　きれいな姿勢で歩く',
  rough: '課題 3　でこぼこ道',
  obstacles: '課題 4　壁をよけてゴールへ',
  steer: '課題 4a　曲がって目標へ',
  wall1: '課題 4b　壁 1 枚の向こうへ',
  walls3: '課題 4c　壁 3 枚をぬけてゴールへ',
  imitate: '課題 5　お手本を真似る (1 回目)',
  natural: '課題 5　お手本を土台に自然な歩き方へ',
};

// 1 体を横から大きく映す
const close = { kind: 'population', count: 1, camera: [1.5, 0.6, -0.3], lookAhead: 0.1, badge: true, graph: true };
// 何体かを斜め後ろから映す
const group = { kind: 'population', count: 6, spacing: 0.9, camera: [4.2, 2.8, -2.8], lookAhead: 1.0, badge: true, graph: true };

export const EXTRA_SCRIPTS = {};
// 壁や目標のあるコースを映す
const course = { kind: 'population', badge: true, graph: true, markers: false };

export const SCENES = [
  {
    kind: 'card', seconds: 5,
    title: 'AI が歩き方を覚えるまで',
    body: '四足ロボット × 物理シミュレーション × 進化',
  },
  {
    kind: 'card', seconds: 10,
    title: 'しくみ',
    body: `<span class="step">ランダムな脳で 48 体を歩かせる</span><span class="arrow">→</span>
           <span class="step">遠くまで進めた脳の特徴を残す</span><br>
           <span class="arrow">→</span><span class="step">少しずつ変えて次の世代へ</span><span class="arrow">→</span>
           <span class="step">何百世代もくり返す</span><br><br>
           脳 = 小さなニューラルネット (重み 約 1,700 個)<br>歩き方は<em>一切教えていない</em>`,
  },
  {
    ...group, stage: 'walk', gen: 0, randomBrains: true, seconds: 7,
    captions: [[0, '第1世代：脳の中身はまったくのランダム'], [3.2, '体の動かし方を何も知らないので、ほとんどが転んでしまう']],
  },
  {
    ...close, stage: 'walk', gen: 0, seconds: 5,
    captions: [[0, '脚をでたらめに動かして…'], [2.2, 'ひっくり返った']],
  },
  {
    ...close, stage: 'walk', gen: 5, seconds: 6,
    captions: [[0, '転ばずに踏ん張れるようになった'], [3, '脚を広げて体を支えている']],
  },
  {
    ...close, stage: 'walk', gen: 10, seconds: 6,
    captions: [[0, '脚をばたつかせて、少しずつ前へ']],
  },
  {
    ...close, stage: 'walk', gen: 20, seconds: 6,
    captions: [[0, '前に進むコツをつかんだ'], [3, 'でも胴体を低くした「はいずり」のような姿勢']],
  },
  {
    ...close, stage: 'walk', gen: 'last', seconds: 7,
    captions: [[0, 'どんどん速くなった！'], [3.5, '「遠くへ進め」としか言っていないので、姿勢はおかまいなし']],
  },
  {
    kind: 'card', seconds: 7,
    title: '新しい課題を追加',
    body: `<span class="step">胴体を低くしすぎない</span><span class="step">傾かない</span><span class="step">脚をガクガク動かさない</span><br><br>
           これを守れた脳ほど高い評価にして、進化を続ける`,
  },
  {
    ...close, stage: 'posture', gen: 50, seconds: 6,
    captions: [[0, '姿勢を気にしはじめた']],
  },
  {
    ...close, stage: 'posture', gen: 225, seconds: 7,
    captions: [[0, '胴体を持ち上げて歩けるようになった']],
  },
  {
    kind: 'race', stage: 'walk', seconds: 10, spacing: 1.1, camera: [0.6, 4.2, -4.6], lookAhead: 2.2, followLead: true,
    gens: ['random', 'walk:5', 'walk:20', 'walk:last', 'posture:225'], labels: true,
    badge: '世代対抗レース', graph: false,
    captions: [[0, '世代対抗レース：同じコースで同時にスタート'], [5, '世代を重ねるごとに、遠くまで進めるようになった']],
  },
  {
    ...group, stage: 'rough', gen: 0, count: 4, seconds: 7, camera: [3.2, 2.2, -2.6],
    captions: [[0, '課題 3：でこぼこ道'], [3, '平らな道の歩き方のままでは、段差につまずいて転んでしまう']],
  },
  {
    ...group, stage: 'rough', gen: 90, count: 4, seconds: 8, camera: [3.2, 2.2, -2.6],
    captions: [[0, '90 世代後：ほとんど転ばなくなった'], [4, 'ただし慎重になって、歩みはゆっくり']],
  },
  {
    ...close, stage: 'obstacles', gen: 100, seconds: 10, camera: [2.8, 3.2, -2.8], lookAhead: 1.5, markers: false,
    captions: [[0, '課題 4：壁をよけて、ゴールの旗へ'], [4, '200 世代学習しても、壁の手前で止まってしまった…']],
  },
  {
    kind: 'card', seconds: 9,
    title: '課題 4 をやり直し',
    body: `いきなり「壁 3 枚」は難しすぎた<br>
           → 課題 2 の脳 (第 526 世代) から分かれて、小分けにして練習<br><br>
           <span class="step">曲がって目標へ</span><span class="arrow">→</span><span class="step">壁 1 枚</span><span class="arrow">→</span><span class="step">壁 3 枚</span>`,
  },
  {
    ...course, stage: 'steer', gen: 0, count: 3, varySeed: true, spacing: 6, seconds: 8, camera: [0, 8.5, -5.5], lookAhead: 2.2,
    graphTitle: '目標に近づいた距離 (世代ごと)',
    captions: [[0, '3 体それぞれ、違う方向に目標の旗'], [3.5, '「まっすぐ前へ」しか練習していないので、旗を無視して直進']],
  },
  {
    ...course, stage: 'steer', gen: 70, count: 3, varySeed: true, spacing: 6, seconds: 8, camera: [0, 8.5, -5.5], lookAhead: 2.2,
    graphTitle: '目標に近づいた距離 (世代ごと)',
    captions: [[0, '70 世代後：旗の方向へ曲がって向かえるようになった']],
  },
  {
    ...course, stage: 'wall1', gen: 0, count: 1, terrainSeed: 3, seconds: 9, camera: [2.2, 4.2, -3.6], lookAhead: 2.2,
    graphTitle: 'ゴールに近づいた距離 (世代ごと)',
    captions: [[0, '次は壁 1 枚。すき間の位置は毎回変わる'], [4, 'このコースでは、壁にぶつかって止まってしまった']],
  },
  {
    ...course, stage: 'wall1', gen: 100, count: 1, terrainSeed: 3, seconds: 12, camera: [2.2, 4.2, -3.6], lookAhead: 2.2,
    graphTitle: 'ゴールに近づいた距離 (世代ごと)',
    captions: [[0, '100 世代後：前の距離センサーで壁を見て…'], [4.5, 'すき間を通ってゴールへ！'],
               [8, '初めてのコース 12 個でのゴール：学習前 3 個 → 100 世代後 9 個']],
  },
  {
    ...course, stage: 'walls3', gen: 30, count: 1, terrainSeed: 12, seconds: 16, camera: [2.8, 4.6, -4.2], lookAhead: 2.2,
    graphTitle: 'ゴールに近づいた距離 (世代ごと)',
    captions: [[0, '最後にもう一度、壁 3 枚に挑戦'], [5, '1 枚目は抜けたが、2 枚目の前で止まってしまう'], [10, '150 世代学習しても、ゴールできたコースはなかった']],
  },
  {
    kind: 'card', seconds: 9,
    title: 'ここまでの結果',
    body: `<span class="step">曲がって目標へ ○</span><span class="step">壁 1 枚 ○</span><span class="step">壁 3 枚 △ (1 枚目まで)</span><br><br>
           次の挑戦：もっと多くのロボットで・もっと長く学習する<br>
           (大規模な研究では、数千体のロボットを GPU で同時に学習させている)`,
  },
  {
    kind: 'card', seconds: 9,
    title: 'まとめ',
    body: `ランダムな脳から、世代をくり返すだけで<br>
           <em>転ぶ → 踏ん張る → はいずる → 走る → 姿勢よく歩く → 曲がる → 壁をよける</em><br><br>
           学習した世代：のべ 1,235 世代 (1 世代 48 体)<br>
           学習時間：CPU 4 コアだけで約 2 時間 (GPU なし)`,
  },
];

const SCENES_V1 = [
  {
    kind: 'card', seconds: 5,
    title: 'AI が歩き方を覚えるまで',
    body: '四足ロボット × 物理シミュレーション × 進化',
  },
  {
    kind: 'card', seconds: 10,
    title: 'しくみ',
    body: `<span class="step">ランダムな脳で 48 体を歩かせる</span><span class="arrow">→</span>
           <span class="step">遠くまで進めた脳の特徴を残す</span><br>
           <span class="arrow">→</span><span class="step">少しずつ変えて次の世代へ</span><span class="arrow">→</span>
           <span class="step">何百世代もくり返す</span><br><br>
           脳 = 小さなニューラルネット (重み 約 1,700 個)<br>歩き方は<em>一切教えていない</em>`,
  },
  {
    ...group, stage: 'walk', gen: 0, randomBrains: true, seconds: 7,
    captions: [[0, '第1世代：脳の中身はまったくのランダム'], [3.2, '体の動かし方を何も知らないので、ほとんどが転んでしまう']],
  },
  {
    ...close, stage: 'walk', gen: 0, seconds: 5,
    captions: [[0, '脚をでたらめに動かして…'], [2.2, 'ひっくり返った']],
  },
  {
    ...close, stage: 'walk', gen: 5, seconds: 6,
    captions: [[0, '転ばずに踏ん張れるようになった'], [3, '脚を広げて体を支えている']],
  },
  {
    ...close, stage: 'walk', gen: 10, seconds: 6,
    captions: [[0, '脚をばたつかせて、少しずつ前へ']],
  },
  {
    ...close, stage: 'walk', gen: 20, seconds: 6,
    captions: [[0, '前に進むコツをつかんだ'], [3, 'でも胴体を低くした「はいずり」のような姿勢']],
  },
  {
    ...close, stage: 'walk', gen: 'last', seconds: 7,
    captions: [[0, 'どんどん速くなった！'], [3.5, '「遠くへ進め」としか言っていないので、姿勢はおかまいなし']],
  },
  {
    kind: 'card', seconds: 7,
    title: '新しい課題を追加',
    body: `<span class="step">胴体を低くしすぎない</span><span class="step">傾かない</span><span class="step">脚をガクガク動かさない</span><br><br>
           これを守れた脳ほど高い評価にして、進化を続ける`,
  },
  {
    ...close, stage: 'posture', gen: 50, seconds: 6,
    captions: [[0, '姿勢を気にしはじめた']],
  },
  {
    ...close, stage: 'posture', gen: 225, seconds: 7,
    captions: [[0, '胴体を持ち上げて歩けるようになった']],
  },
  {
    kind: 'race', stage: 'walk', seconds: 10, spacing: 1.1, camera: [0.6, 4.2, -4.6], lookAhead: 2.2, followLead: true,
    gens: ['random', 'walk:5', 'walk:20', 'walk:last', 'posture:225'], labels: true,
    badge: '世代対抗レース', graph: false,
    captions: [[0, '世代対抗レース：同じコースで同時にスタート'], [5, '世代を重ねるごとに、遠くまで進めるようになった']],
  },
  {
    ...group, stage: 'rough', gen: 0, count: 4, seconds: 7, camera: [3.2, 2.2, -2.6],
    captions: [[0, '課題 3：でこぼこ道'], [3, '平らな道の歩き方のままでは、段差につまずいて転んでしまう']],
  },
  {
    ...group, stage: 'rough', gen: 90, count: 4, seconds: 8, camera: [3.2, 2.2, -2.6],
    captions: [[0, '90 世代後：ほとんど転ばなくなった'], [4, 'ただし慎重になって、歩みはゆっくり']],
  },
  {
    ...close, stage: 'obstacles', gen: 100, seconds: 10, camera: [2.8, 3.2, -2.8], lookAhead: 1.5, markers: false,
    captions: [[0, '課題 4：壁をよけて、ゴールの旗へ'], [4, '200 世代学習しても、壁の手前で止まってしまった…']],
  },
  {
    kind: 'card', seconds: 10,
    title: 'できなかったこと',
    body: `これまで「まっすぐ前へ」しか練習していないので、<br>
           <em>曲がり方</em>も、前を見る<em>距離センサーの使い方</em>も知らなかった<br><br>
           次の挑戦：課題を小分けにする<br>
           <span class="step">曲がって目標へ</span><span class="arrow">→</span><span class="step">壁 1 枚</span><span class="arrow">→</span><span class="step">壁 3 枚</span>`,
  },
  {
    kind: 'card', seconds: 9,
    title: 'まとめ',
    body: `ランダムな脳から、世代をくり返すだけで<br>
           <em>転ぶ → 踏ん張る → はいずる → 速く走る → 姿勢よく歩く → でこぼこ道</em><br><br>
           全 845 世代・1 世代 48 体<br>
           学習は CPU 4 コアだけで約 70 分 (GPU なし)`,
  },
];
EXTRA_SCRIPTS.v1 = SCENES_V1;

// 途中経過の動画 (?script=progress)
EXTRA_SCRIPTS.progress = [
  {
    kind: 'card', seconds: 6,
    title: '課題 4 をやり直し',
    body: `いきなり「壁 3 枚」は難しすぎたので、小分けにして練習<br><br>
           <span class="step">曲がって目標へ</span><span class="arrow">→</span><span class="step">壁 1 枚</span><span class="arrow">→</span><span class="step">壁 3 枚</span>`,
  },
  {
    ...course, stage: 'steer', gen: 0, count: 3, varySeed: true, spacing: 6, seconds: 8, camera: [0, 8.5, -5.5], lookAhead: 2.2,
    graphTitle: '目標に近づいた距離 (世代ごと)',
    captions: [[0, '3 体それぞれ、違う方向に目標の旗'], [3.5, 'これまで「まっすぐ前へ」しか練習していないので、旗を無視して直進']],
  },
  {
    ...course, stage: 'steer', gen: 70, count: 3, varySeed: true, spacing: 6, seconds: 8, camera: [0, 8.5, -5.5], lookAhead: 2.2,
    graphTitle: '目標に近づいた距離 (世代ごと)',
    captions: [[0, '70 世代後：旗の方向へ曲がって向かえるようになった']],
  },
  {
    ...course, stage: 'wall1', gen: 0, count: 1, terrainSeed: 3, seconds: 10, camera: [2.2, 4.2, -3.6], lookAhead: 2.2,
    graphTitle: 'ゴールに近づいた距離 (世代ごと)',
    captions: [[0, '次は壁 1 枚。すき間の位置は毎回変わる'], [4, '最初は壁にぶつかって止まってしまう']],
  },
  {
    ...course, stage: 'wall1', gen: 100, count: 1, terrainSeed: 3, seconds: 12, camera: [2.2, 4.2, -3.6], lookAhead: 2.2,
    graphTitle: 'ゴールに近づいた距離 (世代ごと)',
    captions: [[0, '100 世代後：前の距離センサーで壁を見て…'], [5, 'すき間を通ってゴールへ']],
  },
];

// お手本 (参照モーション) の確認用 (?script=reference)
const refView = { kind: 'reference', stage: 'walk', footfall: true, footfallLanes: [0, 1], markers: true, markerLength: 8, spacing: 1.3,
  camera: [3.4, 1.3, -1.0], lookAhead: 0.4 };
EXTRA_SCRIPTS.reference = [
  {
    kind: 'card', seconds: 7,
    title: 'お手本の歩き方',
    body: `動物の歩き方の研究で知られている「脚を出す順番とタイミング」から計算で作る<br><br>
           <span class="step">ウォーク：1 本ずつ (いつも 3 本が地面に)</span><br>
           <span class="step">トロット：対角の脚を同時に</span>`,
  },
  {
    ...refView, seconds: 9,
    lanes: [{ gait: 'walk', speed: 0.2, physics: false, label: 'ウォーク (0.2 m/s)' },
            { gait: 'trot', speed: 0.5, physics: false, label: 'トロット (0.5 m/s)' }],
    labels: ['ウォーク', 'トロット'],
    captions: [[0, 'お手本 (物理なしで姿勢だけを再生)'], [4, '右上の図：色の帯 = 足が地面に着いている時間']],
  },
  {
    ...refView, seconds: 9,
    lanes: [{ gait: 'walk', speed: 0.2, physics: true, label: 'ウォーク (0.2 m/s)' },
            { gait: 'trot', speed: 0.5, physics: true, label: 'トロット (0.5 m/s)' }],
    labels: ['ウォーク', 'トロット'],
    captions: [[0, '同じ動きを、物理エンジンの中でそのまま再生すると…'], [4.5, '滑ったり遅れたりして、思うように進まない → ここを学習で補う']],
  },
];

// 自然な歩き方の確認用 (?script=natural)
EXTRA_SCRIPTS.natural = [
  {
    kind: 'population', stage: 'walk', brainStage: 'wall1', gen: 100, count: 1, seconds: 7, badge: true, graph: false,
    footfall: true, footfallLanes: [0], camera: [1.5, 0.6, -0.3], lookAhead: 0.1,
    captions: [[0, 'これまでの脳 (壁 1 枚 第 746 世代)：胴体を低くした はいずり歩き']],
  },
  {
    kind: 'population', stage: 'walk', brainStage: 'natural', gen: 150, count: 2, speeds: [0.2, 0.5], spacing: 1.3, seconds: 10,
    badge: true, graph: false, footfall: true, footfallLanes: [0, 1], labels: ['ゆっくり (0.2 m/s)', '速め (0.5 m/s)'],
    lanes: [{ label: 'ゆっくり 0.2 m/s' }, { label: '速め 0.5 m/s' }],
    camera: [3.4, 1.3, -1.0], lookAhead: 0.4, markerLength: 8,
    captions: [[0, 'お手本を土台に学習した脳：ゆっくりはウォーク、速いとトロット'], [5, '右上の図：色の帯 = 足が地面に着いている時間']],
  },
  {
    kind: 'population', stage: 'wall1', brainStage: 'natural', gen: 150, count: 1, terrainSeed: 9, seconds: 11, badge: true, graph: false,
    markers: false, camera: [2.2, 4.2, -3.6], lookAhead: 2.2,
    captions: [[0, '自然な歩き方のまま、壁 1 枚をぬけてゴールへ'],
               [5, '初めてのコース 48 個でのゴール：はいずり歩きの脳 17 個 → 36 個']],
  },
];

// ============================================================================
// v3: v2 + 課題 5 (お手本を土台に自然な歩き方へ)。ずんだもんのナレーション付き (?script=v3)
//   narration: 読み上げる文 (字幕にも同じ文を出す)。場面の長さは読み上げに合わせて自動で延びる
// ============================================================================
const V2 = SCENES;
const v2 = (i, narration, extra = {}) => ({ ...V2[i], ...extra, captions: undefined, narration });
const table = `<table class="roles"><tr><th></th><th>人が作った</th><th>AI が学んだ</th></tr>
  <tr><td>脚を出す順番とリズム (ウォーク・トロット)</td><td>✅</td><td></td></tr>
  <tr><td>速さでウォークとトロットを切り替える</td><td>✅</td><td></td></tr>
  <tr><td>物理の世界で実際に進むための関節の補正</td><td></td><td>✅</td></tr>
  <tr><td>速さの調整・曲がる量</td><td></td><td>✅</td></tr>
  <tr><td>距離センサーで壁を見て、すき間へ向かう</td><td></td><td>✅</td></tr></table>`;

EXTRA_SCRIPTS.v3 = [
  v2(0, ['ずんだもんなのだ。ロボットが歩き方を覚えるまでを、いっしょに見ていくのだ。']),
  v2(1, ['ロボットの脳は、小さなニューラルネットなのだ。最初は中身がでたらめなのだ。',
         '遠くまで進めた脳を少しずつ変えて、次の世代に残す。これを何百世代もくり返すのだ。',
         '歩き方は、いっさい教えていないのだ。']),
  v2(2, ['第1世代。体の動かし方を何も知らないから、ほとんどが転んでしまうのだ。']),
  v2(3, ['脚をでたらめに動かして、ひっくり返ったのだ。']),
  v2(4, ['第6世代。脚を広げて、転ばずに踏ん張れるようになったのだ。']),
  v2(5, ['第11世代。脚をばたつかせて、少しずつ前へ進むのだ。']),
  v2(6, ['第21世代。前に進むコツをつかんだのだ。', 'でも、胴体を低くした、はいずりみたいな姿勢なのだ。']),
  v2(7, ['第301世代。どんどん速くなったのだ。', 'でも、遠くへ進め、としか言っていないから、姿勢はおかまいなしなのだ。']),
  v2(8, ['そこで新しい課題なのだ。胴体を低くしすぎない、傾かない、脚をガクガク動かさない。', 'これを守れた脳ほど、高く評価するのだ。']),
  v2(9, ['姿勢を気にし始めたのだ。']),
  v2(10, ['胴体を持ち上げて、歩けるようになったのだ。']),
  v2(11, ['世代対抗レースなのだ。同じコースで、同時にスタートするのだ。', '世代を重ねるほど、遠くまで進めるようになっているのだ。']),
  v2(12, ['課題3は、でこぼこ道なのだ。', '平らな道の歩き方のままだと、段差につまずいて転んでしまうのだ。']),
  v2(13, ['90世代後。ほとんど転ばなくなったのだ。', 'そのかわり、慎重になって、歩みはゆっくりなのだ。']),
  v2(14, ['課題4は、壁をよけて、ゴールの旗へ向かうのだ。', 'でも、200世代学習しても、壁の手前で止まってしまったのだ。']),
  v2(15, ['いきなり壁3枚は、難しすぎたのだ。課題を小分けにして、やり直すのだ。']),
  v2(16, ['まずは、違う方向にある旗へ向かう練習なのだ。', 'まっすぐ前しか練習していないから、旗を無視して直進してしまうのだ。']),
  v2(17, ['70世代後。旗の方向へ、曲がれるようになったのだ。', '初めてのコース48個で数えると、旗に届いたのは12個から43個に増えたのだ。']),
  v2(18, ['次は壁1枚。すき間の位置は、毎回変わるのだ。', 'このコースでは、壁にぶつかって止まってしまったのだ。']),
  v2(19, ['100世代後。前の距離センサーで壁を見て、すき間を通ってゴールしたのだ。',
          'ただ、初めてのコース48個で数えると、ゴールは13個から17個。あまり伸びていなかったのだ。']),
  v2(20, ['最後に、もう一度壁3枚に挑戦なのだ。', '1枚目は抜けたけど、2枚目の前で止まってしまうのだ。', '150世代学習しても、ゴールできたコースはなかったのだ。']),

  // ---------------- 課題 5: 歩き方を見直す
  {
    kind: 'card', seconds: 6,
    title: '課題 5　歩き方を見直す',
    body: 'ここまでの脳の歩き方を、もう一度よく見てみると…',
    narration: ['課題5なのだ。ここまでの脳の歩き方を、もう一度よく見てみるのだ。'],
  },
  {
    kind: 'population', stage: 'walk', brainStage: 'wall1', gen: 100, count: 1, seconds: 7, badge: true, graph: false,
    footfall: true, footfallLanes: [0], camera: [1.5, 0.6, -0.3], lookAhead: 0.1,
    narration: ['胴体を低くした、はいずり歩きなのだ。', 'AIは、進めればいいと思っているから、見た目は気にしないのだ。'],
  },
  {
    kind: 'card', seconds: 7,
    title: 'お手本の歩き方',
    body: `動物の歩き方の研究で知られている「脚を出す順番とタイミング」から計算で作る<br><br>
           <span class="step">ウォーク：1 本ずつ (いつも 3 本が地面に)</span><br>
           <span class="step">トロット：対角の脚を同時に</span>`,
    narration: ['そこで、お手本を用意したのだ。', '動物の歩き方の研究で知られている、脚を出す順番とタイミングから、計算で作ったのだ。'],
  },
  {
    kind: 'reference', stage: 'walk', footfall: true, footfallLanes: [0, 1], markers: true, markerLength: 8, spacing: 1.3,
    camera: [3.4, 1.3, -1.0], lookAhead: 0.4, seconds: 8,
    lanes: [{ gait: 'walk', speed: 0.2, physics: false, label: 'ウォーク (0.2 m/s)' },
            { gait: 'trot', speed: 0.5, physics: false, label: 'トロット (0.5 m/s)' }],
    labels: ['ウォーク', 'トロット'],
    narration: ['ゆっくりのときはウォーク、速いときはトロットなのだ。', '右上の図の色の帯は、足が地面に着いている時間なのだ。',
                'ウォークは1本ずつ、トロットは対角の脚が同時に着地するのだ。'],
  },
  {
    kind: 'population', stage: 'walk', brainStage: 'imitate', gen: 200, count: 2, speeds: [0.2, 0.5], spacing: 1.3, seconds: 8,
    badge: '1 回目の挑戦', badgeStage: 'imitate', graph: false, footfall: true, footfallLanes: [0, 1],
    labels: ['ゆっくり (0.2 m/s)', '速め (0.5 m/s)'], lanes: [{ label: 'ゆっくり 0.2 m/s' }, { label: '速め 0.5 m/s' }],
    camera: [3.4, 1.3, -1.0], lookAhead: 0.4, markerLength: 8,
    narration: ['1回目の挑戦。お手本に近いほど高く評価して、200世代学習したのだ。',
                'でも、お手本とはほとんど似なかったのだ。', '12個の関節の正しい動かし方を、手探りで見つけるのは、難しすぎたと考えられるのだ。'],
  },
  {
    kind: 'card', seconds: 10,
    title: '作戦を変える',
    body: table,
    narration: ['そこで作戦を変えたのだ。歩き方の型は、人が与えるのだ。',
                'AIは、その型を物理の世界で使いこなす方法を学ぶのだ。', '進むための補正、速さと曲がる量の調整、壁を見てよけること。ここがAIの担当なのだ。'],
  },
  {
    kind: 'population', stage: 'wall1', brainStage: 'natural', gen: 0, count: 1, terrainSeed: 9, seconds: 8, badge: true, graph: false,
    markers: false, camera: [2.2, 4.2, -3.6], lookAhead: 2.2,
    narration: ['型を与えたばかりの状態なのだ。歩き方は自然だけど、まだうまく進めず、曲がることもできないのだ。'],
  },
  {
    kind: 'population', stage: 'walk', brainStage: 'natural', gen: 150, count: 2, speeds: [0.2, 0.5], spacing: 1.3, seconds: 9,
    badge: true, graph: false, footfall: true, footfallLanes: [0, 1], labels: ['ゆっくり (0.2 m/s)', '速め (0.5 m/s)'],
    lanes: [{ label: 'ゆっくり 0.2 m/s' }, { label: '速め 0.5 m/s' }],
    camera: [3.4, 1.3, -1.0], lookAhead: 0.4, markerLength: 8,
    narration: ['150世代後。ゆっくりのときはウォーク、速いときはトロットで、胴体を持ち上げて歩いているのだ。'],
  },
  {
    kind: 'population', stage: 'wall1', brainStage: 'natural', gen: 150, count: 1, terrainSeed: 9, seconds: 10, badge: true, graph: false,
    markers: false, camera: [2.2, 4.2, -3.6], lookAhead: 2.2,
    narration: ['自然な歩き方のまま、壁をよけてゴールしたのだ。', '初めてのコース48個で、ゴールは17個から36個に増えたのだ。'],
  },
  {
    kind: 'card', seconds: 9,
    title: 'ここまでの結果',
    body: `<span class="step">曲がって目標へ ○</span><span class="step">壁 1 枚 ○ (48 コース中 36)</span><span class="step">壁 3 枚 × (まだ)</span><br><br>
           歩き方の型は人が与えたもの。AI がすべてを自分で覚えたわけではない<br>
           (大規模な研究では、数千体のロボットを GPU で同時に学習させている)`,
    narration: ['歩き方の型は人が与えたもので、AIがすべてを自分で覚えたわけではないのだ。', '壁3枚は、まだ次の課題なのだ。'],
  },
  {
    kind: 'card', seconds: 9,
    title: 'まとめ',
    body: `ランダムな脳から、世代をくり返して<br>
           <em>転ぶ → 踏ん張る → はいずる → 走る → 姿勢よく歩く → 曲がる → 壁をよける</em><br>
           お手本の型を使いこなして、自然な歩き方で壁をよけられるように<br><br>
           学習した世代：のべ 1,635 世代 (1 世代 48 体)<br>
           学習時間：CPU 4 コアだけで約 3 時間 20 分 (GPU なし)`,
    narration: ['でたらめな脳から、転ぶ、踏ん張る、はいずる、走る、曲がる、壁をよける。', 'そして、お手本の型を使いこなして、自然な歩き方になったのだ。',
                '学習はのべ1635世代。CPUだけで、約3時間20分だったのだ。'],
  },
  {
    kind: 'card', seconds: 7,
    title: 'クレジット',
    body: `ナレーション：VOICEVOX:ずんだもん<br>
           物理エンジン：Rapier (Apache License 2.0)　描画：three.js (MIT License)<br>
           効果音・BGM：プログラムで自作<br><br>
           このシミュレータと動画は個人の学習・研究目的で作成したもので、特定の研究機関とは関係ありません`,
    narration: ['見てくれて、ありがとうなのだ。'],
  },
];
