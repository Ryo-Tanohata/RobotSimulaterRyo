// 「自然な歩き方」の評価: 学習に使っていないコースで、曲がる・壁 1 枚の成功数と、歩き方 (足運び) を測る
//   node test/natural-eval.mjs natural [世代の間隔]
import RAPIER from '@dimforge/rapier3d-compat';
import fs from 'node:fs';
import { evaluate, buildArenaWorld, Runner } from '../src/arena.js';
import { contactStats, gaitForSpeed } from '../src/reference.js';
import { createConfig } from '../src/core.js';
await RAPIER.init();
const dec = (s) => { const b = Buffer.from(s, 'base64'); return new Float32Array(b.buffer, b.byteOffset, b.byteLength / 4).slice(); };
const [stage = 'natural', every = '50'] = process.argv.slice(2);
const d = JSON.parse(fs.readFileSync(`checkpoints/${stage}.json`));
const residual = !!d.residual;

function walkTest(p, speed) {
  // 平地で指定の速さ。足運び・実際の速さ・胴体の高さ
  const world = buildArenaWorld(RAPIER, []);
  const r = new Runner(RAPIER, world, 'imitate', p, { x: 0, z: 0 }, createConfig(), null, { speed, weight: 1, residual });
  const contacts = []; let hSum = 0, n = 0;
  while (!r.done) { r.control(); if (r.done) break; world.step(); r.afterStep(); if (r.steps % 4 === 0 && r.time > 2) { contacts.push(r.robot.footContact.slice()); hSum += r.robot.position.y; n++; } }
  const res = { speed: r.progress() / r.time, fell: r.fell, height: hSum / n, ...contactStats(contacts) };
  world.free();
  return res;
}

for (const cp of d.checkpoints.filter((c) => c.generation % +every === 0 || c === d.checkpoints[d.checkpoints.length - 1])) {
  const p = dec(cp.params);
  let wall = 0, steer = 0;
  for (let s = 1; s <= 12; s++) {
    wall += evaluate(RAPIER, 'wall1', p, 5000 + s, 1, residual).reached;
    steer += evaluate(RAPIER, 'steer', p, 5000 + s, 1, residual).reached;
  }
  const w = walkTest(p, 0.2), t = walkTest(p, 0.5);
  const fmt = (x, sp) => `${gaitForSpeed(sp)} 指令${sp} 実際${x.speed.toFixed(2)}m/s 対角${(x.diagonal * 100).toFixed(0)}% 3本以上${(x.threeOrMore * 100).toFixed(0)}% 高さ${x.height.toFixed(2)}${x.fell ? ' 転倒' : ''}`;
  console.log(`gen ${String(cp.generation).padStart(3)}: 曲がる ${steer}/12  壁1枚 ${wall}/12 | ${fmt(w, 0.2)} | ${fmt(t, 0.5)}`);
}
