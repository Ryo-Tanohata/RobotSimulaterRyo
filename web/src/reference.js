// 「お手本」の歩き方 (参照モーション)。動物の歩き方の研究で知られている脚の出し方
// (どの脚をどの順番・タイミングで出すか = 位相差、1 周期のうち地面に着いている割合 = 接地率) から、
// 足先の軌道を計算し、逆運動学でロボットの関節角に変換する。
//
//   ウォーク: 左後 → 左前 → 右後 → 右前 の順に 1 本ずつ (常に 3 本以上が接地、接地率 0.75)
//   トロット: 対角の脚 (左前 + 右後, 右前 + 左後) を同時に (接地率 0.5 強)
//
// 脚の番号は core.js と同じ: 0 = 左前 (FL), 1 = 右前 (FR), 2 = 左後 (RL), 3 = 右後 (RR)
import { LEG_COUNT, JOINT_COUNT, legInverse, sideSign, hipPosition, jointLimits } from './core.js';

export const GAITS = {
  walk: {
    label: 'ウォーク',
    // 左後 0 → 左前 0.25 → 右後 0.5 → 右前 0.75
    offsets: [0.25, 0.75, 0.0, 0.5],
    duty: 0.75,
    frequency: 1.4,   // 1 秒あたりの周期数
    stepHeight: 0.05,
  },
  trot: {
    label: 'トロット',
    offsets: [0.0, 0.5, 0.5, 0.0],
    duty: 0.55,
    frequency: 2.2,
    stepHeight: 0.07,
  },
};

/** 速さでウォークとトロットを切り替える (動物もゆっくりはウォーク、速くなるとトロット) */
export const WALK_TROT_SPEED = 0.3; // m/s
export function gaitForSpeed(speed) {
  return Math.abs(speed) < WALK_TROT_SPEED ? 'walk' : 'trot';
}

const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
const smoothstep = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
const wrap01 = (v) => v - Math.floor(v);

/**
 * お手本の 1 瞬間の姿勢。
 * @param config  ロボットの寸法 (core.createConfig())
 * @param gaitName 'walk' | 'trot'
 * @param phase   歩行の位相 0..1
 * @param cmd     {forward, side, yaw} 速度の指令 (Core 座標系)
 * @param opts    {standHeight, footSpread, footOffset}
 * @returns {q: Float64Array(12) 関節角, feet: 足先の位置 (股関節基準) ×4, contact: 接地 ×4, swing: 遊脚の進み具合 ×4}
 */
export function referencePose(config, gaitName, phase, cmd, opts = {}) {
  const g = GAITS[gaitName];
  const standHeight = opts.standHeight ?? 0.28;
  const footSpread = opts.footSpread ?? 0.02;
  const footOffset = opts.footOffset ?? -0.03;
  const q = new Float64Array(JOINT_COUNT);
  const feet = [], contact = [], swing = [];
  const stanceTime = g.duty / g.frequency;

  for (let leg = 0; leg < LEG_COUNT; leg++) {
    const side = sideSign(leg);
    const hip = hipPosition(config, leg);
    // 股関節の速度 = 胴体の速度 + 旋回による速度 (core.TrotGait と同じ)
    const hipVelX = cmd.side + cmd.yaw * hip.z;
    const hipVelZ = cmd.forward - cmd.yaw * hip.x;
    // 立脚のあいだに足先が後ろへ動く量 = 速さ × 立脚時間 (これで足が地面に対して止まって見える)
    const strideZ = clamp(hipVelZ * stanceTime, -0.2, 0.2);
    const strideX = clamp(hipVelX * stanceTime, -0.12, 0.12);

    const p = wrap01(phase + g.offsets[leg]);
    let s, lift, inContact, sw;
    if (p < g.duty) {
      // 立脚: 前 (+0.5) から後ろ (-0.5) へ等速
      s = 0.5 - p / g.duty;
      lift = 0; inContact = true; sw = 0;
    } else {
      // 遊脚: 先に持ち上げてから前へ振り、前で止めてから下ろす
      const t = (p - g.duty) / (1 - g.duty);
      s = -0.5 + smoothstep((t - 0.15) / 0.7);
      lift = g.stepHeight * Math.sin(Math.PI * t);
      inContact = false; sw = t;
    }
    const foot = {
      x: side * (config.hipLinkLength + footSpread) + strideX * s,
      y: -(standHeight - lift),
      z: strideZ * s + footOffset,
    };
    const [qh, qt, qc] = legInverse(config, side, foot);
    const angles = [qh, qt, qc];
    for (let k = 0; k < 3; k++) {
      const [lo, hi] = jointLimits(config, leg * 3 + k);
      q[leg * 3 + k] = clamp(angles[k], lo, hi);
    }
    feet.push(foot); contact.push(inContact); swing.push(sw);
  }
  return { q, feet, contact, swing };
}

/**
 * 時間とともに位相を進める「お手本の再生器」。速さの指令に応じてウォーク/トロットを選ぶ。
 * 切り替えのときは位相を保ったまま次の歩き方に移る。
 */
export class ReferencePlayer {
  constructor(config, opts = {}) {
    this.config = config;
    this.opts = opts;
    this.phase = 0;
    this.gait = 'walk';
    this.forcedGait = opts.gait || null; // 指定すると速さに関係なくその歩き方
  }
  reset() { this.phase = 0; }
  step(dt, cmd) {
    const speed = Math.hypot(cmd.forward, cmd.side);
    this.gait = this.forcedGait || gaitForSpeed(speed);
    this.phase = wrap01(this.phase + dt * GAITS[this.gait].frequency);
    return referencePose(this.config, this.gait, this.phase, cmd, this.opts);
  }
}

/** 接地パターンから計算する指標 (お手本・学習結果の両方に使う) */
export function contactStats(contactSeries) {
  // contactSeries: 各時刻の [FL, FR, RL, RR] の接地 (true/false)
  let diagSync = 0, lateralSync = 0, three = 0, n = contactSeries.length;
  for (const c of contactSeries) {
    if (c[0] === c[3] && c[1] === c[2]) diagSync++;      // 対角が同じ状態 (トロットらしさ)
    if (c[0] === c[2] && c[1] === c[3]) lateralSync++;   // 同じ側が同じ状態 (ペースらしさ)
    if (c.filter(Boolean).length >= 3) three++;          // 3 本以上が接地 (ウォークらしさ)
  }
  return { diagonal: diagSync / n, lateral: lateralSync / n, threeOrMore: three / n };
}
