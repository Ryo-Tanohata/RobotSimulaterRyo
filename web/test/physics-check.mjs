// ブラウザなしで物理シミュレーションを走らせ、ロボットが立つ・歩く・曲がることを数値で確認する。
import RAPIER from '@dimforge/rapier3d-compat';
import { createConfig, TrotGait, defaultGaitParams } from '../src/core.js';
import { QuadrupedRobot, GROUND_GROUPS } from '../src/robot.js';

await RAPIER.init();
const DT = 1 / 200, DECIM = 4;
let failures = 0;
const check = (name, ok, detail) => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}  ${detail}`); if (!ok) failures++; };

function makeWorld() {
  const world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
  world.timestep = DT;
  world.createCollider(RAPIER.ColliderDesc.cuboid(50, 0.5, 50).setTranslation(0, -0.5, 0).setFriction(1.0).setCollisionGroups(GROUND_GROUPS));
  return world;
}

function run(cmd, seconds, opts = {}) {
  const world = makeWorld();
  const c = createConfig();
  const robot = new QuadrupedRobot(RAPIER, world, c, { x: 0, y: c.spawnHeight, z: 0 }, 0);
  const gait = new TrotGait(c, defaultGaitParams());
  const targets = new Float64Array(12);
  const steps = Math.round(seconds / DT);
  let minUp = 1, heights = [], maxJointErr = 0;
  const t0 = performance.now();
  for (let i = 0; i < steps; i++) {
    if (i % DECIM === 0) {
      robot.readState();
      const t = i * DT;
      const active = t > 1.0 ? cmd : { forward: 0, side: 0, yaw: 0 };
      if (opts.standOnly) robot.setTargets(robot.defaultAngles);
      else { gait.step(DT * DECIM, active, robot.gravityCore(), targets); robot.setTargets(targets); }
      if (opts.kickAt && Math.abs(t - opts.kickAt) < DT * DECIM / 2) robot.push({ x: 1.2, y: 0, z: 0 });
      if (t > 1.0) { minUp = Math.min(minUp, robot.upY()); heights.push(robot.position.y); }
      if (opts.standOnly && t > 1.0) for (let j = 0; j < 12; j++) maxJointErr = Math.max(maxJointErr, Math.abs(robot.jointPos[j] - robot.targets[j]));
    }
    world.step();
  }
  const ms = performance.now() - t0;
  const p = robot.position;
  const r = robot.rotation;
  const yaw = Math.atan2(2 * (r.w * r.y + r.x * r.z), 1 - 2 * (r.y * r.y + r.x * r.x));
  const avgH = heights.reduce((a, b) => a + b, 0) / heights.length;
  return { p, minUp, avgH, yaw, maxJointErr, ms, fallen: robot.isFallen() };
}

let r = run(null, 3, { standOnly: true });
check('stand still', r.minUp > 0.95 && r.avgH > 0.22, `height=${r.avgH.toFixed(3)} up=${r.minUp.toFixed(3)} jointErr=${r.maxJointErr.toFixed(3)}rad (${r.ms.toFixed(0)}ms)`);

r = run({ forward: 0, side: 0, yaw: 0 }, 4);
check('trot in place', r.minUp > 0.9 && Math.hypot(r.p.x, r.p.z) < 0.6, `drift=${Math.hypot(r.p.x, r.p.z).toFixed(2)}m up=${r.minUp.toFixed(2)}`);

r = run({ forward: 0.6, side: 0, yaw: 0 }, 7);
check('walk forward 0.6 m/s (6s)', r.minUp > 0.85 && r.p.z > 2.0 && Math.abs(r.p.x) < 1.0, `z=${r.p.z.toFixed(2)}m x=${r.p.x.toFixed(2)}m up=${r.minUp.toFixed(2)} (${(7 / (r.ms / 1000)).toFixed(1)}x realtime)`);

r = run({ forward: -0.3, side: 0, yaw: 0 }, 6);
check('walk backward 0.3 m/s', r.minUp > 0.85 && r.p.z < -0.4, `z=${r.p.z.toFixed(2)}m`);

r = run({ forward: 0, side: 0.3, yaw: 0 }, 5);
check('side step right (-x in world)', r.minUp > 0.85 && r.p.x < -0.4, `x=${r.p.x.toFixed(2)}m`);

r = run({ forward: 0, side: 0, yaw: 0.8 }, 5);
check('turn right (yaw decreases)', r.minUp > 0.85 && r.yaw < -0.8, `yaw=${r.yaw.toFixed(2)}rad`);

r = run({ forward: 0.4, side: 0, yaw: 0 }, 6, { kickAt: 3 });
check('recover from kick', !r.fallen && r.minUp > 0.5, `up_min=${r.minUp.toFixed(2)} fallen=${r.fallen}`);

console.log(failures ? `\n${failures} check(s) failed` : '\nall physics checks passed');
process.exit(failures ? 1 : 0);
