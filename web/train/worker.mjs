// 評価用ワーカー: 重みを受け取ってロボットを走らせ、評価値を返す
//   mix: [{stage, seeds}] … 複数の課題で評価して合計する (お手本 + 曲がる + 壁 など)
import { parentPort } from 'node:worker_threads';
import RAPIER from '@dimforge/rapier3d-compat';
import { evaluate } from '../src/arena.js';

await RAPIER.init();
parentPort.on('message', ({ id, stage, params, seeds, mix, imitWeight = null, residual = false }) => {
  const jobs = mix || [{ stage, seeds }];
  let fitness = 0, count = 0;
  const per = {};
  for (const job of jobs) {
    const m = per[job.stage] = { fitness: 0, progress: 0, fell: 0, reached: 0, imitQ: 0, imitContact: 0, speedMatch: 0, n: 0 };
    for (const seed of job.seeds) {
      const r = evaluate(RAPIER, job.stage, params, seed, imitWeight, residual);
      fitness += r.fitness; count++;
      m.fitness += r.fitness; m.progress += r.progress; m.fell += r.fell ? 1 : 0; m.reached += r.reached ? 1 : 0;
      m.imitQ += r.imitQ ?? 0; m.imitContact += r.imitContact ?? 0; m.speedMatch += r.speedMatch ?? 0; m.n++;
    }
    for (const k of Object.keys(m)) if (k !== 'n') m[k] /= m.n;
  }
  const first = per[jobs[0].stage];
  parentPort.postMessage({ id, fitness: fitness / count, progress: first.progress, fell: first.fell, reached: first.reached, per });
});
parentPort.postMessage({ ready: true });
