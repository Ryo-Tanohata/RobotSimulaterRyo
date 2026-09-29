// お手本 (参照モーション) の確認: 関節の範囲・接地パターン・足が滑らないか・物理で実際に進めるか
import RAPIER from '@dimforge/rapier3d-compat';
import { createConfig, jointLimits, hipPosition, sideSign } from '../src/core.js';
import { GAITS, referencePose, ReferencePlayer, contactStats } from '../src/reference.js';
import { QuadrupedRobot, GROUND_GROUPS } from '../src/robot.js';

let failures = 0;
const check = (name, ok, detail) => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}  ${detail}`); if (!ok) failures++; };
const c = createConfig();

// 1. 関節の範囲・周期性・接地パターン
for (const gait of Object.keys(GAITS)) {
  const cmd = { forward: gait === 'walk' ? 0.2 : 0.5, side: 0, yaw: 0 };
  let inLimits = true;
  const contacts = [];
  for (let i = 0; i < 200; i++) {
    const r = referencePose(c, gait, i / 200, cmd);
    r.q.forEach((v, j) => { const [lo, hi] = jointLimits(c, j); if (v < lo - 1e-9 || v > hi + 1e-9 || Number.isNaN(v)) inLimits = false; });
    contacts.push(r.contact);
  }
  const a = referencePose(c, gait, 0, cmd).q, b = referencePose(c, gait, 1, cmd).q;
  const periodic = a.every((v, j) => Math.abs(v - b[j]) < 1e-9);
  const st = contactStats(contacts);
  check(`${gait}: 関節の範囲内・周期的`, inLimits && periodic, `inLimits=${inLimits} periodic=${periodic}`);
  if (gait === 'walk') check('walk: 常に 3 本以上が接地', st.threeOrMore > 0.99, `3本以上=${(st.threeOrMore * 100).toFixed(0)}%`);
  if (gait === 'trot') check('trot: 対角の脚が同じ状態', st.diagonal > 0.99, `対角一致=${(st.diagonal * 100).toFixed(0)}%`);

  // 2. 立脚中の足先は、胴体が cmd.forward で進むとき地面に対して止まっている
  const g = GAITS[gait];
  const dt = 0.001;
  let maxSlip = 0;
  for (let i = 0; i < 1000; i++) {
    const ph = i / 1000;
    const r0 = referencePose(c, gait, ph, cmd), r1 = referencePose(c, gait, ph + dt * g.frequency, cmd);
    for (let leg = 0; leg < 4; leg++) {
      if (!r0.contact[leg] || !r1.contact[leg]) continue;
      const footWorldVel = (r1.feet[leg].z - r0.feet[leg].z) / dt + cmd.forward;
      maxSlip = Math.max(maxSlip, Math.abs(footWorldVel));
    }
  }
  check(`${gait}: 立脚の足が地面に対して止まっている`, maxSlip < 0.01, `最大のすべり速度=${maxSlip.toFixed(4)} m/s`);
}

// 3. 物理エンジンでお手本どおりに脚を動かしたとき、実際に進めるか (学習なし・そのまま再生)
await RAPIER.init();
function play(gait, speed, seconds = 6) {
  const world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
  world.timestep = 1 / 200;
  world.createCollider(RAPIER.ColliderDesc.cuboid(50, 0.5, 50).setTranslation(0, -0.5, 0).setFriction(1).setCollisionGroups(GROUND_GROUPS));
  const robot = new QuadrupedRobot(RAPIER, world, c, { x: 0, y: c.spawnHeight, z: 0 }, 0);
  const player = new ReferencePlayer(c, { gait });
  let minUp = 1;
  const steps = seconds * 200;
  for (let i = 0; i < steps; i++) {
    if (i % 4 === 0) {
      robot.readState();
      const cmd = { forward: i > 200 ? speed : 0, side: 0, yaw: 0 };
      robot.setTargets(player.step(0.02, cmd).q);
      if (i > 200) minUp = Math.min(minUp, robot.upY());
    }
    world.step();
  }
  const p = robot.position;
  world.free();
  return { z: p.z, x: p.x, minUp, expected: speed * (seconds - 1) };
}
// お手本は「形」だけなので、学習なしでそのまま再生しても物理的にはうまく進めない (関節の追従の遅れ・重心の偏り)。
// 物理に合う動きに直すのは学習の役目。ここでは転ばないことだけを合否にし、進んだ距離は参考値として表示する。
for (const [gait, speed] of [['walk', 0.2], ['trot', 0.5]]) {
  const r = play(gait, speed);
  check(`${gait}: 物理で再生しても転ばない (${speed} m/s)`, r.minUp > 0.8,
    `[参考] 進んだ ${r.z.toFixed(2)} m / 指令どおりなら ${r.expected.toFixed(2)} m  横ずれ ${r.x.toFixed(2)} m  傾き最小 ${r.minUp.toFixed(2)}`);
}
console.log(failures ? `\n${failures} 件失敗` : '\nすべて合格');
process.exit(failures ? 1 : 0);
