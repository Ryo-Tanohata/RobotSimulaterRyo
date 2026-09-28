// ロボットの「脳」: 小さなニューラルネット (多層パーセプトロン)。
// 重みはランダムから始め、進化 (進化戦略) で少しずつ良くしていく。
// 入力: 体の傾き・回転、関節の角度と速度、リズム (sin/cos)、目標の方向、前方の距離センサー
// 出力: 12 関節の目標角 (基準姿勢からのずれ)
import { JOINT_COUNT } from './core.js';

export const RAY_ANGLES = [-50, -25, 0, 25, 50].map((d) => (d * Math.PI) / 180); // 前方の距離センサー
export const RAY_LENGTH = 2.0;
export const INPUT_SIZE = 3 + 3 + JOINT_COUNT + JOINT_COUNT + 2 + 2 + RAY_ANGLES.length; // 39
export const HIDDEN = 32;
export const OUTPUT_SIZE = JOINT_COUNT;
export const PARAM_COUNT = INPUT_SIZE * HIDDEN + HIDDEN + HIDDEN * OUTPUT_SIZE + OUTPUT_SIZE;
export const ACTION_SCALE = 0.6;   // 出力 [-1,1] → ±0.6 rad
export const RHYTHM_HZ = 2.0;      // 入力として与える「リズム」の周波数

export class Policy {
  constructor(params) {
    this.params = params instanceof Float32Array ? params : Float32Array.from(params);
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
  const p = new Float32Array(PARAM_COUNT);
  let k = 0;
  const layer = (nIn, nOut) => {
    const s = scale / Math.sqrt(nIn);
    for (let i = 0; i < nIn * nOut; i++) p[k++] = gaussianFrom(rand) * s;
    for (let i = 0; i < nOut; i++) p[k++] = 0;
  };
  layer(INPUT_SIZE, HIDDEN);
  layer(HIDDEN, OUTPUT_SIZE);
  return p;
}

/**
 * センサーの値を読んで入力ベクトルを作る。
 * @param robot   QuadrupedRobot (readState() 済み)
 * @param time    経過時間 [s] (リズムの位相)
 * @param goal    目標地点 {x, z} (ワールド座標) または null (まっすぐ前へ)
 * @param rays    距離センサーの値 (0 = 目の前に壁, 1 = 何もない)
 */
export function buildInput(robot, time, goal, rays, input = new Float32Array(INPUT_SIZE)) {
  const g = robot.gravityCore();
  const w = robot.angularVelocityCore();
  let i = 0;
  input[i++] = g.x; input[i++] = g.y; input[i++] = g.z;
  input[i++] = w.x * 0.25; input[i++] = w.y * 0.25; input[i++] = w.z * 0.25;
  for (let j = 0; j < JOINT_COUNT; j++) input[i++] = robot.jointPos[j] - robot.defaultAngles[j];
  for (let j = 0; j < JOINT_COUNT; j++) input[i++] = Math.max(-3, Math.min(3, robot.jointVel[j] * 0.05));
  const ph = 2 * Math.PI * RHYTHM_HZ * time;
  input[i++] = Math.sin(ph); input[i++] = Math.cos(ph);
  const [gs, gc] = goalDirection(robot, goal);
  input[i++] = gs; input[i++] = gc;
  for (let r = 0; r < rays.length; r++) input[i++] = rays[r];
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
