// 進化の評価コース。学習 (Node.js, 画面なし) と再生 (ブラウザ) の両方で同じコードを使う。
// 段階 (stage) ごとに地形と「何が良いか (評価関数)」を変える。
import { createConfig, JOINT_COUNT } from './core.js';
import { QuadrupedRobot, GROUND_GROUPS, GROUP_GROUND, GROUP_ROBOT } from './robot.js';
import { Policy, buildInput, readRays, mulberry32, RAY_ANGLES, ACTION_SCALE, RESIDUAL_SCALE } from './policy.js';
import { ReferencePlayer } from './reference.js';

export const DT = 1 / 200;
export const DECIMATION = 4;

// 距離センサーは地面 (障害物を含む) だけを見る
const RAY_GROUPS = (GROUP_ROBOT << 16) | GROUP_GROUND;

export const STAGES = {
  // 平らな地面でまっすぐ前へ。倒れずに遠くへ進むほど良い
  walk: { seconds: 8, goal: null, terrain: 'flat' },
  // 同じ平地で「きれいに」歩く: 胴体を低くしすぎない・傾かない・ガクガク動かさない
  posture: { seconds: 8, goal: null, terrain: 'flat', posture: true },
  // 低い段差がちらばった地面
  rough: { seconds: 10, goal: null, terrain: 'blocks', posture: true },
  // 高い壁をよけて、ゴールまで行く
  obstacles: { seconds: 16, goal: { x: 0, z: 10 }, terrain: 'walls', posture: true },
  // ↓ 課題 4 をやり直すための小分けの課題 (カリキュラム)
  // 4a: 平地で、毎回ちがう方向にある目標へ曲がって向かう
  steer: { seconds: 8, goal: 'random-direction', terrain: 'flat', posture: true },
  // 4b: 壁 1 枚 (すき間の位置は毎回ちがう) の向こうの目標へ
  wall1: { seconds: 12, goal: 'behind-wall', terrain: 'wall1', posture: true },
  // 4c: 壁 3 枚 (課題 4 と同じコース)
  walls3: { seconds: 16, goal: { x: 0, z: 10 }, terrain: 'walls', posture: true, gap: 1.1 },
  // 5: お手本を真似る (平地で、毎回ちがう速さ。ゆっくり = ウォーク、速い = トロット)
  imitate: { seconds: 8, goal: null, terrain: 'flat', imitate: true, speeds: [0.12, 0.2, 0.26, 0.4, 0.5, 0.6] },
};

/** お手本の段階で、seed から目標の速さを決める */
export function stageSpeed(stageName, seed) {
  const sp = STAGES[stageName].speeds;
  if (!sp) return null;
  return sp[Math.floor(mulberry32(seed * 7907 + 11)() * sp.length)];
}

/** 段階と seed から目標地点 (スタート地点からの相対位置) を決める */
export function stageGoal(stageName, seed) {
  const g = STAGES[stageName].goal;
  if (!g || typeof g === 'object') return g;
  const rand = mulberry32(seed * 104729 + 3);
  if (g === 'random-direction') {
    const a = (rand() * 2 - 1) * (75 * Math.PI / 180); // 正面から左右 75° まで
    return { x: 4 * Math.sin(a), z: 4 * Math.cos(a) };
  }
  if (g === 'behind-wall') return { x: (rand() * 2 - 1) * 1.0, z: 5 };
  return null;
}

/** 地形の箱のリスト {x, z, sx, sz, h, kind} を作る (seed が同じなら同じ地形) */
export function makeObstacles(stageName, seed) {
  const rand = mulberry32(seed * 7919 + 17);
  const boxes = [];
  const stage = STAGES[stageName];
  if (stage.terrain === 'blocks') {
    for (let k = 0; k < 70; k++) {
      const x = (rand() * 2 - 1) * 3, z = 0.8 + rand() * 9;
      boxes.push({ x, z, sx: 0.2 + rand() * 0.5, sz: 0.2 + rand() * 0.5, h: 0.02 + rand() * 0.06, kind: 'step' });
    }
  } else if (stage.terrain === 'wall1') {
    const gapCenter = (rand() * 2 - 1) * 1.2, gap = 1.2, width = 5;
    const leftEnd = gapCenter - gap / 2, rightStart = gapCenter + gap / 2;
    const lw = leftEnd + width / 2, rw = width / 2 - rightStart;
    boxes.push({ x: -width / 2 + lw / 2, z: 2.5, sx: lw, sz: 0.25, h: 0.5, kind: 'wall' });
    boxes.push({ x: rightStart + rw / 2, z: 2.5, sx: rw, sz: 0.25, h: 0.5, kind: 'wall' });
  } else if (stage.terrain === 'walls') {
    // ゴールとの間に高い壁を置く (毎回位置が変わるので、覚えるのではなく「見て」よける必要がある)
    const rows = [2.8, 5.2, 7.6];
    rows.forEach((z, i) => {
      const gapCenter = (rand() * 2 - 1) * 1.4;
      const gap = stage.gap ?? 0.9;
      const width = 4.5;
      const leftEnd = gapCenter - gap / 2, rightStart = gapCenter + gap / 2;
      const lw = leftEnd + width / 2;
      const rw = width / 2 - rightStart;
      if (lw > 0.1) boxes.push({ x: -width / 2 + lw / 2, z: z + (rand() - 0.5) * 0.6, sx: lw, sz: 0.25, h: 0.5, kind: 'wall' });
      if (rw > 0.1) boxes.push({ x: rightStart + rw / 2, z: z + (rand() - 0.5) * 0.6, sx: rw, sz: 0.25, h: 0.5, kind: 'wall' });
      if (i < 2) for (let k = 0; k < 6; k++)
        boxes.push({ x: (rand() * 2 - 1) * 2, z: z + 0.6 + rand() * 1.4, sx: 0.3 + rand() * 0.3, sz: 0.3 + rand() * 0.3, h: 0.03 + rand() * 0.04, kind: 'step' });
    });
  }
  return boxes;
}

export function buildArenaWorld(RAPIER, boxes) {
  const world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
  world.timestep = DT;
  world.createCollider(RAPIER.ColliderDesc.cuboid(30, 0.5, 30).setTranslation(0, -0.5, 5)
    .setFriction(1.0).setCollisionGroups(GROUND_GROUPS));
  for (const b of boxes) {
    world.createCollider(RAPIER.ColliderDesc.cuboid(b.sx / 2, b.h / 2, b.sz / 2).setTranslation(b.x, b.h / 2, b.z)
      .setFriction(1.0).setCollisionGroups(GROUND_GROUPS));
  }
  return world;
}

/**
 * 1 体のロボットの 1 回の評価。step() を呼ぶと物理が 1 ステップ進む。
 * 同じ world に複数の Runner を置けば同時に何体も走らせられる (ロボット同士はぶつからない)。
 */
export class Runner {
  /**
   * @param imitation null か {speed, weight}: お手本を使う (リズムをお手本の位相にし、お手本との近さを評価に入れる)
   */
  constructor(RAPIER, world, stageName, params, start = { x: 0, z: 0 }, config = createConfig(), goal = undefined, imitation = null) {
    this.R = RAPIER;
    this.world = world;
    this.stage = STAGES[stageName];
    this.stageName = stageName;
    this.policy = new Policy(params);
    this.robot = new QuadrupedRobot(RAPIER, world, config, { x: start.x, y: config.spawnHeight, z: start.z }, 0);
    this.start = { ...start };
    const g = goal !== undefined ? goal : (typeof this.stage.goal === 'object' ? this.stage.goal : null);
    this.goal = g ? { x: start.x + g.x, z: start.z + g.z } : null;
    this.rays = new Float32Array(RAY_ANGLES.length).fill(1);
    this.targets = new Float64Array(JOINT_COUNT);
    this.time = 0;
    this.steps = 0;
    this.done = false;
    this.fell = false;
    this.aliveTime = 0;
    this.reached = false;
    this.bestProgress = 0;
    this.lowSum = 0;   // 胴体が低すぎた量の合計
    this.tiltSum = 0;  // 傾きの合計
    this.jerkSum = 0;  // 出力の急な変化の合計
    this.ctrlN = 0;
    this.prevOut = new Float32Array(JOINT_COUNT);
    // お手本
    this.imitation = imitation;
    if (imitation) {
      this.player = new ReferencePlayer(config);
      this.refCmd = { forward: imitation.speed, side: 0, yaw: 0 };
      this.imit = { q: 0, contact: 0, height: 0, speed: 0 }; // 各項目の合計
      this.pose = null;
    }
  }

  /** 物理を 1 ステップ進める前に呼ぶ (DECIMATION ステップごとに脳が判断する) */
  control() {
    if (this.done) return;
    if (this.steps % DECIMATION !== 0) return;
    const r = this.robot;
    r.readState();
    readRays(this.R, this.world, r, RAY_GROUPS, this.rays);
    let inputOpts = {};
    const residual = this.imitation && this.imitation.residual;
    if (this.imitation && !residual) {
      this.pose = this.player.step(DT * DECIMATION, this.refCmd);
    }
    if (this.imitation) inputOpts = { phase: this.player.phase, speed: this.imitation.speed };
    const input = buildInput(r, this.time, this.goal, this.rays, undefined, inputOpts);
    const out = this.policy.forward(input);
    if (residual) {
      // お手本を土台にする方式: 脳はお手本の速さ・曲がる量を調整し、関節角に小さな補正を足す
      this.refCmd.forward = this.imitation.speed * (1 + 0.5 * out[JOINT_COUNT]);
      this.refCmd.yaw = 1.0 * out[JOINT_COUNT + 1];
      this.pose = this.player.step(DT * DECIMATION, this.refCmd);
    }
    let jerk = 0;
    for (let j = 0; j < JOINT_COUNT; j++) {
      this.targets[j] = residual ? this.pose.q[j] + out[j] * RESIDUAL_SCALE : r.defaultAngles[j] + out[j] * ACTION_SCALE;
      jerk += Math.abs(out[j] - this.prevOut[j]);
      this.prevOut[j] = out[j];
    }
    r.setTargets(this.targets);
    this.lowSum += Math.max(0, 0.27 - r.position.y);
    this.tiltSum += 1 - r.upY();
    if (this.imitation && this.pose) {
      // お手本との近さ (1 に近いほどそっくり)
      let qErr = 0;
      for (let j = 0; j < JOINT_COUNT; j++) qErr += (r.jointPos[j] - this.pose.q[j]) ** 2;
      let match = 0;
      for (let leg = 0; leg < 4; leg++) if (r.footContact[leg] === this.pose.contact[leg]) match++;
      this.imit.q += Math.exp(-0.5 * qErr);
      this.imit.contact += match / 4;
      this.imit.height += Math.exp(-(((r.position.y - 0.30) / 0.04) ** 2));
      if (!this.goal) this.imit.speed += Math.exp(-((r.velocityCore().z - this.imitation.speed) ** 2) / 0.04);
    }
    if (this.ctrlN > 0) this.jerkSum += jerk / JOINT_COUNT;
    this.ctrlN++;

    if (r.isFallen()) { this.fell = true; this.done = true; }
    if (this.goal) {
      const p = r.position;
      const d = Math.hypot(this.goal.x - p.x, this.goal.z - p.z);
      if (d < 0.6) { this.reached = true; this.done = true; }
    }
  }

  /** world.step() の後に呼ぶ */
  afterStep() {
    if (this.done) return;
    this.steps++;
    this.time += DT;
    this.aliveTime = this.time;
    const pr = this.progress();
    if (pr > this.bestProgress) this.bestProgress = pr;
    if (this.time >= this.stage.seconds) this.done = true;
  }

  /** 前進量 (ゴールがあればゴールへの近づき量) */
  progress() {
    const p = this.robot.position;
    if (!this.goal) return p.z - this.start.z;
    const d0 = Math.hypot(this.goal.x - this.start.x, this.goal.z - this.start.z);
    return d0 - Math.hypot(this.goal.x - p.x, this.goal.z - p.z);
  }

  /** 評価値 (大きいほど良い) */
  fitness() {
    const p = this.robot.position;
    const lateral = this.goal ? 0 : Math.abs(p.x - this.start.x);
    const early = this.fell ? 1.0 : 0; // 転んだら減点
    let f = this.progress() - 0.3 * lateral + 0.15 * this.aliveTime - early
      + (this.reached ? 3 + (this.stage.seconds - this.time) * 0.2 : 0);
    if (this.imitation && this.ctrlN > 0) {
      const n = this.ctrlN, alive = this.aliveTime / this.stage.seconds;
      const imitScore = 0.5 * this.imit.q / n + 0.3 * this.imit.contact / n + 0.2 * this.imit.height / n;
      if (!this.goal) {
        // お手本の課題: 指定の速さで進む + お手本に近い。長く転ばずに続けるほど高い
        return alive * 10 * (this.imit.speed / n + this.imitation.weight * imitScore) - (this.fell ? 2 : 0);
      }
      // 曲がる・壁の課題: 今までの評価 + お手本らしさ (ゴールへ向かうあいだも自然な歩き方で)
      f += alive * 5 * this.imitation.weight * imitScore;
    }
    if (this.stage.posture && this.ctrlN > 0) {
      const n = this.ctrlN;
      f -= 15 * (this.lowSum / n) + 3 * (this.tiltSum / n) + 1.5 * (this.jerkSum / n);
    }
    return f;
  }
}

/** 画面なしで 1 回評価する (学習用) */
/** imitWeight: お手本の重み (0 ならお手本なし)。お手本の課題以外でも weight > 0 ならお手本らしさを評価に加える */
export function imitationFor(stageName, seed, imitWeight, residual = false) {
  if (imitWeight === null || imitWeight === undefined) return null; // お手本を使わない学習
  if (STAGES[stageName].imitate) return { speed: stageSpeed(stageName, seed), weight: imitWeight, residual };
  return { speed: 0.45, weight: imitWeight, residual }; // 曲がる・壁の課題はトロットの速さで (リズムは最初からお手本に合わせる)
}

export function evaluate(RAPIER, stageName, params, seed, imitWeight = null, residual = false) {
  const boxes = makeObstacles(stageName, seed);
  const world = buildArenaWorld(RAPIER, boxes);
  const runner = new Runner(RAPIER, world, stageName, params, { x: 0, z: 0 }, createConfig(), stageGoal(stageName, seed),
    imitationFor(stageName, seed, imitWeight, residual));
  while (!runner.done) {
    runner.control();
    if (runner.done) break;
    world.step();
    runner.afterStep();
  }
  const n = Math.max(1, runner.ctrlN);
  const result = { fitness: runner.fitness(), progress: runner.progress(), fell: runner.fell, reached: runner.reached, time: runner.time,
    imitQ: runner.imit ? runner.imit.q / n : null, imitContact: runner.imit ? runner.imit.contact / n : null,
    speedMatch: runner.imit && !runner.goal ? runner.imit.speed / n : null };
  world.free();
  return result;
}
