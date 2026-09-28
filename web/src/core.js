// Unity 版 (RobotSimulator/Assets/RobotSim/Scripts/Core) と同じ計算の JavaScript 版。
// Core の座標系: x = 右, y = 上, z = 前。関節角の符号も Unity 版と同じ:
//   外転: 正で足先が右へ / 太もも・すね: 正で足先が後ろへ

export const LEG_COUNT = 4;
export const JOINT_COUNT = 12;
export const LEG_NAMES = ['FL', 'FR', 'RL', 'RR'];

export function createConfig() {
  return {
    trunkLength: 0.267, trunkWidth: 0.194, trunkHeight: 0.114, trunkMass: 6.0,
    hipOffsetForward: 0.183, hipOffsetSide: 0.047, hipLinkLength: 0.08, hipMass: 0.7,
    thighLength: 0.2, thighRadius: 0.025, thighMass: 1.0,
    calfLength: 0.2, calfRadius: 0.013, calfMass: 0.25, footRadius: 0.022,
    kp: 150, kd: 2.0, torqueLimit: 33.5,
    defaultHip: 0, defaultThigh: 0.8, defaultCalf: -1.5,
    hipLimit: 0.8, thighMin: -1.0, thighMax: 3.0, calfMin: -2.7, calfMax: -0.6,
    spawnHeight: 0.36,
  };
}

export const isFront = (leg) => leg < 2;
export const sideSign = (leg) => (leg % 2 === 0 ? -1 : 1); // 左 = -1, 右 = +1

export function totalMass(c) {
  return c.trunkMass + LEG_COUNT * (c.hipMass + c.thighMass + c.calfMass);
}

/** 胴体座標 (Core 座標系) での股関節の位置 */
export function hipPosition(c, leg) {
  return { x: sideSign(leg) * c.hipOffsetSide, y: 0, z: isFront(leg) ? c.hipOffsetForward : -c.hipOffsetForward };
}

export function defaultJointAngles(c) {
  const q = new Float64Array(JOINT_COUNT);
  for (let leg = 0; leg < LEG_COUNT; leg++) {
    q[leg * 3] = c.defaultHip; q[leg * 3 + 1] = c.defaultThigh; q[leg * 3 + 2] = c.defaultCalf;
  }
  return q;
}

export function jointLimits(c, j) {
  switch (j % 3) {
    case 0: return [-c.hipLimit, c.hipLimit];
    case 1: return [c.thighMin, c.thighMax];
    default: return [c.calfMin, c.calfMax];
  }
}

const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
const smoothstep = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
const wrap01 = (v) => { v -= Math.floor(v); return v >= 1 ? 0 : v; };

/** 関節角 → 足先位置 (股関節基準, Core 座標系) */
export function legForward(c, side, hip, thigh, calf) {
  const f = -c.thighLength * Math.sin(thigh) - c.calfLength * Math.sin(thigh + calf);
  const u = -c.thighLength * Math.cos(thigh) - c.calfLength * Math.cos(thigh + calf);
  const lx = side * c.hipLinkLength;
  const ch = Math.cos(hip), sh = Math.sin(hip);
  return { x: lx * ch - u * sh, y: lx * sh + u * ch, z: f };
}

/** 足先位置 → 関節角 (膝は後ろ向きの解) */
export function legInverse(c, side, foot) {
  const lh = c.hipLinkLength, l1 = c.thighLength, l2 = c.calfLength;
  const r2 = foot.x * foot.x + foot.y * foot.y;
  const hPrime = Math.sqrt(Math.max(r2 - lh * lh, 1e-6));
  let hip = Math.atan2(foot.y, foot.x) - Math.atan2(-hPrime, side * lh);
  while (hip > Math.PI) hip -= 2 * Math.PI;
  while (hip < -Math.PI) hip += 2 * Math.PI;

  let f = foot.z, u = -hPrime;
  let d2 = f * f + u * u;
  const maxReach = (l1 + l2) * 0.999, minReach = Math.abs(l1 - l2) + 0.01;
  const d = Math.sqrt(d2);
  if (d > maxReach) { f *= maxReach / d; u *= maxReach / d; d2 = maxReach * maxReach; }
  else if (d < minReach) { const s = minReach / Math.max(d, 1e-6); f *= s; u *= s; d2 = minReach * minReach; }
  const cosK = clamp((d2 - l1 * l1 - l2 * l2) / (2 * l1 * l2), -1, 1);
  const calf = -Math.acos(cosK);
  const k1 = l1 + l2 * Math.cos(calf), k2 = l2 * Math.sin(calf);
  const thigh = Math.atan2(-f, -u) - Math.atan2(k2, k1);
  return [hip, thigh, calf];
}

/** 遺伝的アルゴリズムで調整する歩容パラメータの既定値と範囲 */
// 既定値は test/evolve.mjs (遺伝的アルゴリズム) で平地の前進・後退・足踏みに最適化した値
export const GAIT_PARAMS = [
  // name,         default, min,   max
  ['frequency',    2.4,     1.0,   4.0],   // 歩行周波数 [Hz]
  ['stepHeight',   0.085,   0.02,  0.14],  // 足を上げる高さ [m]
  ['standHeight',  0.27,    0.20,  0.33],  // 股関節から足先までの高さ [m]
  ['strideGain',   1.13,    0.3,   2.0],   // 歩幅の倍率
  ['balanceGain',  0.28,    0.0,   0.8],   // 傾き補正の強さ
  ['footSpread',   0.028,  -0.03,  0.06],  // 足を外に広げる量 [m]
  ['bodyPitch',   -0.03,   -0.06,  0.06],  // 前脚と後脚の高さの差 [m]
  ['footOffset',  -0.055,  -0.08,  0.04],  // 足の前後の基準位置 [m] (脚の重さで重心が後ろにあるため)
  ['phaseLead',    0.07,    0.0,   0.2],   // 関節の追従遅れを見越して目標を先の位相で出す
];

export function defaultGaitParams() {
  const p = {};
  for (const [name, def] of GAIT_PARAMS) p[name] = def;
  return p;
}

/** トロット歩容 (Unity 版 TrotGait と同じ)。params は GAIT_PARAMS の値 */
export class TrotGait {
  constructor(config, params = defaultGaitParams()) {
    this.c = config;
    this.p = params;
    this.maxStride = 0.16;
    this.phase = 0;
  }
  reset() { this.phase = 0; }

  /**
   * cmd = {forward, side, yaw}, gravityBody = Core 座標系での重力方向。targets (12) に書き込む
   */
  step(dt, cmd, gravityBody, targets) {
    const c = this.c, p = this.p;
    const moving = Math.abs(cmd.forward) > 0.05 || Math.abs(cmd.side) > 0.05 || Math.abs(cmd.yaw) > 0.05;
    this.phase = wrap01(this.phase + dt * p.frequency);
    const stanceTime = 0.5 / p.frequency;
    const offsets = [0, 0.5, 0.5, 0];
    for (let leg = 0; leg < LEG_COUNT; leg++) {
      const side = sideSign(leg), front = isFront(leg) ? 1 : -1;
      const hip = hipPosition(c, leg);
      const hipVelX = cmd.side + cmd.yaw * hip.z;
      const hipVelZ = cmd.forward - cmd.yaw * hip.x;
      const strideZ = clamp(hipVelZ * stanceTime * p.strideGain, -this.maxStride, this.maxStride);
      const strideX = clamp(hipVelX * stanceTime * p.strideGain, -this.maxStride * 0.6, this.maxStride * 0.6);

      const ph = wrap01(this.phase + offsets[leg] + p.phaseLead);
      let s, lift;
      if (ph < 0.5) { s = 0.5 - ph / 0.5; lift = 0; }
      else {
        const t = (ph - 0.5) / 0.5;
        // 先に足を持ち上げてから前へ振り、前で止めてから下ろす (引きずり防止)
        s = -0.5 + smoothstep((t - 0.2) / 0.6);
        lift = (moving ? p.stepHeight : p.stepHeight * 0.6) * Math.sin(Math.PI * t);
      }
      const balance = p.balanceGain * (gravityBody.z * front + gravityBody.x * side);
      const height = clamp(p.standHeight + balance - lift + p.bodyPitch * front, 0.12, 0.36);
      const foot = {
        x: side * (c.hipLinkLength + p.footSpread) + strideX * s,
        y: -height,
        z: strideZ * s + p.footOffset,
      };
      const q = legInverse(c, side, foot);
      for (let k = 0; k < 3; k++) {
        const [lo, hi] = jointLimits(c, leg * 3 + k);
        targets[leg * 3 + k] = clamp(q[k], lo, hi);
      }
    }
  }
}
