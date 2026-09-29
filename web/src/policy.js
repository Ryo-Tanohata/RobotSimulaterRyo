// ロボットの「脳」: 小さなニューラルネット (多層パーセプトロン)。
// 重みはランダムから始め、進化 (進化戦略) で少しずつ良くしていく。
// 入力: 体の傾き・回転、関節の角度と速度、リズム (sin/cos)、目標の方向、前方の距離センサー
// 出力: 12 関節の目標角 (基準姿勢からのずれ)
import { JOINT_COUNT } from './core.js';

export const RAY_ANGLES = [-50, -25, 0, 25, 50].map((d) => (d * Math.PI) / 180); // 前方の距離センサー
export const RAY_LENGTH = 2.0;
// 入力: 傾き 3 + 角速度 3 + 関節角 12 + 関節速度 12 + リズム 2 + 目標の方向 2 + 距離センサー 5 (= 39, 第 1 版)
//       + 目標の速さ 1 (第 2 版で追加: お手本を真似る学習でウォーク/トロットを選ぶため)
export const INPUT_SIZE_V1 = 3 + 3 + JOINT_COUNT + JOINT_COUNT + 2 + 2 + RAY_ANGLES.length; // 39
export const INPUT_SIZE = INPUT_SIZE_V1 + 1; // 40
export const HIDDEN = 32;
// 出力: 12 関節 + お手本の調整 2 (速さの倍率・曲がる量。第 3 版で追加: お手本を土台にして補正する方式のため)
export const OUTPUT_SIZE_V1 = JOINT_COUNT;
export const OUTPUT_SIZE = JOINT_COUNT + 2;
export const PARAM_COUNT_V1 = INPUT_SIZE_V1 * HIDDEN + HIDDEN + HIDDEN * OUTPUT_SIZE_V1 + OUTPUT_SIZE_V1; // 1676
export const PARAM_COUNT_V2 = INPUT_SIZE * HIDDEN + HIDDEN + HIDDEN * OUTPUT_SIZE_V1 + OUTPUT_SIZE_V1;    // 1708
export const PARAM_COUNT = INPUT_SIZE * HIDDEN + HIDDEN + HIDDEN * OUTPUT_SIZE + OUTPUT_SIZE;             // 1774

/**
 * 古い版の重みを最新版に広げる。追加した入力・出力の重みは 0 なので、関節への出力はまったく同じ。
 * これで今までの学習結果から続けて学習できる。
 *   第 1 版 (入力 39, 出力 12) → 第 2 版 (入力 40: 目標の速さ) → 第 3 版 (出力 14: お手本の調整)
 */
export function upgradeParams(p) {
  if (p.length === PARAM_COUNT) return p;
  if (p.length === PARAM_COUNT_V1) {
    const q = new Float32Array(PARAM_COUNT_V2);
    let src = 0, dst = 0;
    for (let h = 0; h < HIDDEN; h++) {
      for (let i = 0; i < INPUT_SIZE_V1; i++) q[dst++] = p[src++];
      q[dst++] = 0; // 目標の速さ
    }
    q.set(p.subarray(src), dst); // 残り (バイアス・出力層) はそのまま
    p = q;
  }
  if (p.length === PARAM_COUNT_V2) {
    const q = new Float32Array(PARAM_COUNT);
    const first = INPUT_SIZE * HIDDEN + HIDDEN;           // 入力層の重み + バイアス
    q.set(p.subarray(0, first), 0);
    q.set(p.subarray(first, first + HIDDEN * OUTPUT_SIZE_V1), first); // 関節の出力の重み (追加分は 0)
    q.set(p.subarray(first + HIDDEN * OUTPUT_SIZE_V1), first + HIDDEN * OUTPUT_SIZE); // 関節の出力のバイアス
    return q;
  }
  throw new Error(`重みの数が合いません: ${p.length}`);
}

/** 関節への出力を factor 倍に弱める (お手本を土台にする方式へ切り替えるとき、最初の補正を小さくするため) */
export function scaleJointOutputs(p, factor) {
  const q = Float32Array.from(upgradeParams(p));
  const first = INPUT_SIZE * HIDDEN + HIDDEN;
  for (let k = 0; k < HIDDEN * JOINT_COUNT; k++) q[first + k] *= factor;
  const bias = first + HIDDEN * OUTPUT_SIZE;
  for (let o = 0; o < JOINT_COUNT; o++) q[bias + o] *= factor;
  return q;
}
export const ACTION_SCALE = 0.6;   // 出力 [-1,1] → ±0.6 rad
export const RESIDUAL_SCALE = 0.25; // お手本を土台にする方式での補正の大きさ (±0.25 rad)
export const RHYTHM_HZ = 2.0;      // 入力として与える「リズム」の周波数

export class Policy {
  constructor(params) {
    this.params = upgradeParams(params instanceof Float32Array ? params : Float32Array.from(params));
    this.hidden = new Float32Array(HIDDEN);
    this.out = new Float32Array(OUTPUT_SIZE);
  }

  /** input (INPUT_SIZE) → out (OUTPUT_SIZE, -1..1) */
  forward(input) {
    const p = this.params;
    let k = 0;
    for (let h = 0; h < HIDDEN; h++) {
      let s = 0;
      for (let i = 0; i < INPUT_SIZE; i++) s += p[k++] * input[i];
      this.hidden[h] = s;
    }
    for (let h = 0; h < HIDDEN; h++) this.hidden[h] = Math.tanh(this.hidden[h] + p[k++]);
    for (let o = 0; o < OUTPUT_SIZE; o++) {
      let s = 0;
      for (let h = 0; h < HIDDEN; h++) s += p[k++] * this.hidden[h];
      this.out[o] = s;
    }
    for (let o = 0; o < OUTPUT_SIZE; o++) this.out[o] = Math.tanh(this.out[o] + p[k++]);
    return this.out;
  }
}

/** 標準正規乱数 (seed 付きの乱数関数から) */
export function gaussianFrom(rand) {
  const u = 1 - rand(), v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export function mulberry32(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** ランダムな初期の重み (第 1 世代: まだ何も知らない脳) */
export function randomParams(seed, scale = 1.5) {
  const rand = mulberry32(seed);
  const p = new Float32Array(PARAM_COUNT_V1);
  let k = 0;
  const layer = (nIn, nOut) => {
    const s = scale / Math.sqrt(nIn);
    for (let i = 0; i < nIn * nOut; i++) p[k++] = gaussianFrom(rand) * s;
    for (let i = 0; i < nOut; i++) p[k++] = 0;
  };
  layer(INPUT_SIZE_V1, HIDDEN);
  layer(HIDDEN, OUTPUT_SIZE_V1);
  return upgradeParams(p);
}

/**
 * センサーの値を読んで入力ベクトルを作る。
 * @param robot   QuadrupedRobot (readState() 済み)
 * @param time    経過時間 [s] (リズムの位相)
 * @param goal    目標地点 {x, z} (ワールド座標) または null (まっすぐ前へ)
 * @param rays    距離センサーの値 (0 = 目の前に壁, 1 = 何もない)
 */
export function buildInput(robot, time, goal, rays, input = new Float32Array(INPUT_SIZE), opts = {}) {
  const g = robot.gravityCore();
  const w = robot.angularVelocityCore();
  let i = 0;
  input[i++] = g.x; input[i++] = g.y; input[i++] = g.z;
  input[i++] = w.x * 0.25; input[i++] = w.y * 0.25; input[i++] = w.z * 0.25;
  for (let j = 0; j < JOINT_COUNT; j++) input[i++] = robot.jointPos[j] - robot.defaultAngles[j];
  for (let j = 0; j < JOINT_COUNT; j++) input[i++] = Math.max(-3, Math.min(3, robot.jointVel[j] * 0.05));
  // リズム: お手本を使うときはお手本の歩き方の位相、そうでなければ 2 Hz の一定のリズム
  const ph = opts.phase !== undefined ? 2 * Math.PI * opts.phase : 2 * Math.PI * RHYTHM_HZ * time;
  input[i++] = Math.sin(ph); input[i++] = Math.cos(ph);
  const [gs, gc] = goalDirection(robot, goal);
  input[i++] = gs; input[i++] = gc;
  for (let r = 0; r < rays.length; r++) input[i++] = rays[r];
  input[i++] = (opts.speed ?? 0) * 2; // 目標の速さ (m/s × 2)
  return input;
}

/** 胴体から見た目標の方向 (sin, cos)。正の sin = 右 */
export function goalDirection(robot, goal) {
  if (!goal) return [0, 1];
  const p = robot.position;
  const heading = robotHeading(robot);
  const target = Math.atan2(goal.x - p.x, goal.z - p.z); // +z から +x へ向かう角 (右手系で左 = +x)
  const d = heading - target; // 右手系: x = 左なので、目標が右にあるとき正
  return [Math.sin(d), Math.cos(d)];
}

/** 胴体の前方向 (+z) の水平面での向き (atan2(x, z)) */
export function robotHeading(robot) {
  const q = robot.rotation;
  const fx = 2 * (q.x * q.z + q.w * q.y);
  const fz = 1 - 2 * (q.x * q.x + q.y * q.y);
  return Math.atan2(fx, fz);
}

/** 前方の距離センサー (胴体の高さから水平に少し下向きに光線を飛ばす) */
export function readRays(RAPIER, world, robot, groups, out = new Float32Array(RAY_ANGLES.length)) {
  const p = robot.position;
  const heading = robotHeading(robot);
  for (let r = 0; r < RAY_ANGLES.length; r++) {
    const a = heading - RAY_ANGLES[r]; // 正の角度 = 右 (= -x 方向へ回す)
    const dir = { x: Math.sin(a) * 0.995, y: -0.1, z: Math.cos(a) * 0.995 }; // 平らな地面には届かない角度
    const ray = new RAPIER.Ray({ x: p.x, y: p.y + 0.05, z: p.z }, dir);
    const hit = world.castRay(ray, RAY_LENGTH, true, undefined, groups);
    out[r] = hit ? hit.timeOfImpact / RAY_LENGTH : 1;
  }
  return out;
}
