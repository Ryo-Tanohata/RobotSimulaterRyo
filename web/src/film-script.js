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
};

// 1 体を横から大きく映す
const close = { kind: 'population', count: 1, camera: [1.5, 0.6, -0.3], lookAhead: 0.1, badge: true, graph: true };
// 何体かを斜め後ろから映す
const group = { kind: 'population', count: 6, spacing: 0.9, camera: [4.2, 2.8, -2.8], lookAhead: 1.0, badge: true, graph: true };

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
           脳 = 小さなニューラルネット (重み 1,708 個)<br>歩き方は<em>一切教えていない</em>`,
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
    kind: 'race', stage: 'walk', seconds: 10, spacing: 1.1, camera: [7.5, 6.0, 0.5], lookAhead: 0, followLead: true,
    gens: ['random', 'walk:5', 'walk:20', 'walk:last', 'posture:225'], labels: true,
    badge: '世代対抗レース', graph: false,
    captions: [[0, '世代対抗レース：同じコースで同時にスタート'], [5, '世代を重ねるごとに、遠くまで進めるようになった']],
  },
  {
    ...group, stage: 'rough', gen: 'last', count: 4, seconds: 8, camera: [3.2, 2.2, -2.6],
    captions: [[0, '次はでこぼこ道'], [4, '段差につまずいても、立て直して進む']],
  },
  {
    ...close, stage: 'obstacles', gen: 0, seconds: 8, camera: [2.8, 3.2, -2.8], lookAhead: 1.5, markers: false,
    captions: [[0, '最後の課題：壁をよけてゴールの旗へ'], [4, '前を見る「距離センサー」はあるが、使い方をまだ知らない']],
  },
  {
    ...close, stage: 'obstacles', gen: 'last', seconds: 14, camera: [2.8, 3.2, -2.8], lookAhead: 1.5, markers: false,
    captions: [[0, '学習後：壁のすき間を見つけて進む'], [7, 'ゴール！']],
  },
  {
    kind: 'card', seconds: 8,
    title: 'まとめ',
    body: `ランダムな脳から、世代をくり返すだけで<br>
           <em>転ぶ → 踏ん張る → はいずる → 歩く → 障害物をよける</em><br><br>
           学習はノート PC 程度の CPU 4 コアで約 1 時間<br>
           (fuRo の研究では 4096 体を GPU で同時に学習)`,
  },
];
