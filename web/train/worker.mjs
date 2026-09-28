// 評価用ワーカー: 重みを受け取ってロボットを走らせ、評価値を返す
import { parentPort } from 'node:worker_threads';
import RAPIER from '@dimforge/rapier3d-compat';
import { evaluate } from '../src/arena.js';

await RAPIER.init();
parentPort.on('message', ({ id, stage, params, seeds }) => {
  let fitness = 0, progress = 0, fell = 0, reached = 0;
  for (const seed of seeds) {
    const r = evaluate(RAPIER, stage, params, seed);
    fitness += r.fitness; progress += r.progress; fell += r.fell ? 1 : 0; reached += r.reached ? 1 : 0;
  }
  const n = seeds.length;
  parentPort.postMessage({ id, fitness: fitness / n, progress: progress / n, fell: fell / n, reached: reached / n });
});
parentPort.postMessage({ ready: true });
