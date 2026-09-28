// JavaScript 版の歩容の出力を JSON に書き出す。C# 版 (Unity) と同じ結果になるかを
// tools/verify/CoreTests/ParityTests.cs が確認する。
import fs from 'node:fs';
import { createConfig, TrotGait } from '../src/core.js';

const c = createConfig();
const gait = new TrotGait(c);
const t = new Float64Array(12);
const cmds = [[0.6, 0, 0], [0, 0.2, 0.5], [-0.3, 0, -0.4], [0, 0, 0]];
const gravity = [[0, -1, 0], [0.05, -0.99, -0.08], [-0.1, -0.99, 0.03]];
const steps = [];
for (let i = 0; i < 120; i++) {
  const [f, s, y] = cmds[Math.floor(i / 30)];
  const [gx, gy, gz] = gravity[i % 3];
  gait.step(0.02, { forward: f, side: s, yaw: y }, { x: gx, y: gy, z: gz }, t);
  steps.push({ cmd: [f, s, y], gravity: [gx, gy, gz], targets: Array.from(t) });
}
const out = new URL('../../tools/verify/CoreTests/gait_fixture.json', import.meta.url);
fs.writeFileSync(out, JSON.stringify({ dt: 0.02, steps }, null, 0));
console.log('wrote', out.pathname, steps.length, 'steps');
