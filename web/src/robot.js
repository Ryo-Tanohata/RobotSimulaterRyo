// Rapier (Rust 製物理エンジンの WebAssembly 版) で作る四足ロボット。
// 構成は Unity 版と同じ: 胴体 + 脚 4 本 × (股 / 太もも / すね)、12 関節を PD 制御。
//
// ワールド座標 (右手系): y = 上。ロボットの胴体座標は x = 左, y = 上, z = 前。
// (Core 座標系 x = 右 とは x の符号だけ逆: core(x,y,z) = body(-x,y,z))
import {
  LEG_COUNT, JOINT_COUNT, LEG_NAMES, sideSign, hipPosition, defaultJointAngles, jointLimits, totalMass,
} from './core.js';

export const GROUP_GROUND = 0x0001;
export const GROUP_ROBOT = 0x0002;
const ROBOT_GROUPS = (GROUP_ROBOT << 16) | GROUP_GROUND; // ロボットは地面とだけぶつかる
export const GROUND_GROUPS = (GROUP_GROUND << 16) | 0xffff;

// 関節軸 (親リンク座標)。正の回転で: 外転 = 足先が右へ / ピッチ = 足先が後ろへ
const AXIS_HIP = { x: 0, y: 0, z: -1 };
const AXIS_PITCH = { x: 1, y: 0, z: 0 };

// ---------------------------------------------------------------- 小さなクォータニオン演算
export const quat = {
  mul(a, b) {
    return {
      w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
      x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
      y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
      z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
    };
  },
  conj(q) { return { w: q.w, x: -q.x, y: -q.y, z: -q.z }; },
  axisAngle(a, t) { const s = Math.sin(t / 2); return { w: Math.cos(t / 2), x: a.x * s, y: a.y * s, z: a.z * s }; },
  rotate(q, v) {
    const p = quat.mul(quat.mul(q, { w: 0, x: v.x, y: v.y, z: v.z }), quat.conj(q));
    return { x: p.x, y: p.y, z: p.z };
  },
  yaw(t) { return quat.axisAngle({ x: 0, y: 1, z: 0 }, t); },
};
const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
const dot = (a, b) => a.x * b.x + a.y * b.y + a.z * b.z;

export class QuadrupedRobot {
  /**
   * @param RAPIER 初期化済みの Rapier モジュール
   * @param world  RAPIER.World
   * @param config core.createConfig() の値
   */
  constructor(RAPIER, world, config, position, yaw = 0) {
    this.R = RAPIER;
    this.world = world;
    this.c = config;
    this.defaultAngles = defaultJointAngles(config);
    this.targets = Float64Array.from(this.defaultAngles);
    this.links = [];      // { body, name, kind, leg }
    this.joints = [];     // { joint, parent, child, axis }
    this.jointPos = new Float64Array(JOINT_COUNT);
    this.jointVel = new Float64Array(JOINT_COUNT);
    this.footContact = [false, false, false, false];
    this.build(position, yaw);
  }

  // ---------------------------------------------------------------- 生成

  /** 各リンクの姿勢 (順運動学)。q は 12 関節角 */
  linkPoses(position, rotation, q) {
    const c = this.c;
    const poses = [{ p: position, r: rotation }];
    for (let leg = 0; leg < LEG_COUNT; leg++) {
      const hp = hipPosition(c, leg);
      const hipP = add(position, quat.rotate(rotation, { x: -hp.x, y: hp.y, z: hp.z }));
      const hipR = quat.mul(rotation, quat.axisAngle(AXIS_HIP, q[leg * 3]));
      const thighP = add(hipP, quat.rotate(hipR, { x: -sideSign(leg) * c.hipLinkLength, y: 0, z: 0 }));
      const thighR = quat.mul(hipR, quat.axisAngle(AXIS_PITCH, q[leg * 3 + 1]));
      const calfP = add(thighP, quat.rotate(thighR, { x: 0, y: -c.thighLength, z: 0 }));
      const calfR = quat.mul(thighR, quat.axisAngle(AXIS_PITCH, q[leg * 3 + 2]));
      poses.push({ p: hipP, r: hipR }, { p: thighP, r: thighR }, { p: calfP, r: calfR });
    }
    return poses;
  }

  build(position, yaw) {
    const R = this.R, c = this.c, world = this.world;
    const poses = this.linkPoses(position, quat.yaw(yaw), this.defaultAngles);

    const makeBody = (pose, name, kind, leg) => {
      const desc = R.RigidBodyDesc.dynamic()
        .setTranslation(pose.p.x, pose.p.y, pose.p.z)
        .setRotation(pose.r)
        .setCanSleep(false);
      const body = world.createRigidBody(desc);
      this.links.push({ body, name, kind, leg });
      return body;
    };
    const collider = (desc, body, mass, friction = 0.6) => {
      desc.setMass(mass).setFriction(friction).setCollisionGroups(ROBOT_GROUPS);
      return world.createCollider(desc, body);
    };

    // 胴体
    const trunk = makeBody(poses[0], 'trunk', 'trunk', -1);
    this.trunkCollider = collider(R.ColliderDesc.cuboid(c.trunkWidth / 2, c.trunkHeight / 2, c.trunkLength / 2), trunk, c.trunkMass);
    this.trunk = trunk;

    for (let leg = 0; leg < LEG_COUNT; leg++) {
      const side = sideSign(leg);
      const hp = hipPosition(c, leg);
      const hip = makeBody(poses[1 + leg * 3], LEG_NAMES[leg] + '_hip', 'hip', leg);
      collider(R.ColliderDesc.ball(0.04), hip, c.hipMass);
      const thigh = makeBody(poses[2 + leg * 3], LEG_NAMES[leg] + '_thigh', 'thigh', leg);
      collider(R.ColliderDesc.capsule(c.thighLength / 2, c.thighRadius).setTranslation(0, -c.thighLength / 2, 0), thigh, c.thighMass);
      const calf = makeBody(poses[3 + leg * 3], LEG_NAMES[leg] + '_calf', 'calf', leg);
      collider(R.ColliderDesc.capsule(c.calfLength / 2 - c.calfRadius, c.calfRadius).setTranslation(0, -c.calfLength / 2, 0), calf, c.calfMass * 0.8);
      collider(R.ColliderDesc.ball(c.footRadius).setTranslation(0, -c.calfLength, 0), calf, c.calfMass * 0.2, 1.0);

      this.addJoint(trunk, hip, { x: -hp.x, y: hp.y, z: hp.z }, AXIS_HIP, leg * 3);
      this.addJoint(hip, thigh, { x: -side * c.hipLinkLength, y: 0, z: 0 }, AXIS_PITCH, leg * 3 + 1);
      this.addJoint(thigh, calf, { x: 0, y: -c.thighLength, z: 0 }, AXIS_PITCH, leg * 3 + 2);
    }
  }

  addJoint(parent, child, anchorInParent, axis, j) {
    const R = this.R, c = this.c;
    const data = R.JointData.revolute(anchorInParent, { x: 0, y: 0, z: 0 }, axis);
    const joint = this.world.createImpulseJoint(data, parent, child, true);
    joint.setContactsEnabled(false);
    joint.configureMotorModel(R.MotorModel.ForceBased);
    joint.setMotorMaxForce(c.torqueLimit);
    const [lo, hi] = jointLimits(c, j);
    joint.setLimits(lo, hi);
    joint.configureMotorPosition(this.defaultAngles[j], c.kp, c.kd);
    this.joints[j] = { joint, parent, child, axis };
  }

  // ---------------------------------------------------------------- 制御

  setTarget(j, angle) {
    const [lo, hi] = jointLimits(this.c, j);
    const a = Math.min(hi, Math.max(lo, angle));
    this.targets[j] = a;
    this.joints[j].joint.configureMotorPosition(a, this.c.kp, this.c.kd);
  }

  setTargets(q) { for (let j = 0; j < JOINT_COUNT; j++) this.setTarget(j, q[j]); }

  /** 全リンクを基準姿勢で指定位置に置き直す */
  reset(position, yaw = 0) {
    const poses = this.linkPoses(position, quat.yaw(yaw), this.defaultAngles);
    const zero = { x: 0, y: 0, z: 0 };
    this.links.forEach((l, i) => {
      l.body.setTranslation(poses[i].p, true);
      l.body.setRotation(poses[i].r, true);
      l.body.setLinvel(zero, true);
      l.body.setAngvel(zero, true);
    });
    this.setTargets(this.defaultAngles);
  }

  /** 胴体に速度変化 Δv を与える (蹴り) */
  push(dv) {
    const m = totalMass(this.c);
    this.trunk.applyImpulse({ x: dv.x * m, y: dv.y * m, z: dv.z * m }, true);
  }

  // ---------------------------------------------------------------- センサ

  get position() { return this.trunk.translation(); }
  get rotation() { return this.trunk.rotation(); }

  /** 胴体座標での重力方向 (Core 座標系: x = 右) */
  gravityCore() {
    const g = quat.rotate(quat.conj(this.rotation), { x: 0, y: -1, z: 0 });
    return { x: -g.x, y: g.y, z: g.z };
  }

  /** 胴体座標での速度 (Core 座標系) */
  velocityCore() {
    const v = quat.rotate(quat.conj(this.rotation), this.trunk.linvel());
    return { x: -v.x, y: v.y, z: v.z };
  }

  /** 胴体座標での角速度 (Core 座標系: y = ヨー, 正 = 右旋回) */
  angularVelocityCore() {
    const w = quat.rotate(quat.conj(this.rotation), this.trunk.angvel());
    // x の符号反転 (鏡映) で回転の向きも反転するため、軸ベクトルは (x, -y, -z) になる
    return { x: w.x, y: -w.y, z: -w.z };
  }

  upY() { return quat.rotate(this.rotation, { x: 0, y: 1, z: 0 }).y; }

  footPosition(leg) {
    const calf = this.links[3 + leg * 3].body;
    return add(calf.translation(), quat.rotate(calf.rotation(), { x: 0, y: -this.c.calfLength, z: 0 }));
  }

  /** 関節角・角速度・足の接地を読み込む */
  readState() {
    for (let j = 0; j < JOINT_COUNT; j++) {
      const { parent, child, axis } = this.joints[j];
      const pr = parent.rotation();
      const rel = quat.mul(quat.conj(pr), child.rotation());
      let a = 2 * Math.atan2(rel.x * axis.x + rel.y * axis.y + rel.z * axis.z, rel.w);
      if (a > Math.PI) a -= 2 * Math.PI;
      if (a < -Math.PI) a += 2 * Math.PI;
      this.jointPos[j] = a;
      const wp = parent.angvel(), wc = child.angvel();
      const axisWorld = quat.rotate(pr, axis);
      this.jointVel[j] = dot({ x: wc.x - wp.x, y: wc.y - wp.y, z: wc.z - wp.z }, axisWorld);
    }
    const R = this.R;
    const ball = new R.Ball(this.c.footRadius + 0.012);
    const ident = { w: 1, x: 0, y: 0, z: 0 };
    for (let leg = 0; leg < LEG_COUNT; leg++) {
      this.footContact[leg] = this.world.intersectionWithShape(
        this.footPosition(leg), ident, ball, undefined, ROBOT_GROUPS) !== null;
    }
    const box = new R.Cuboid(this.c.trunkWidth / 2 + 0.01, this.c.trunkHeight / 2 + 0.01, this.c.trunkLength / 2 + 0.01);
    this.baseContact = this.world.intersectionWithShape(this.position, this.rotation, box, undefined, ROBOT_GROUPS) !== null;
  }

  isFallen() { return this.upY() < 0.3 || this.baseContact; }

  remove() {
    for (const l of this.links) this.world.removeRigidBody(l.body);
    this.links = [];
  }
}
