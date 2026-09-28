// 進化戦略 (OpenAI-ES) でニューラルネットの重みを学習する。画面なし・マルチスレッド。
//   node train/train.mjs walk 300            # 段階 walk を 300 世代
//   node train/train.mjs rough 200 walk      # walk の最終結果から続けて rough を学習
// 世代ごとの記録と重みを checkpoints/<stage>.json に保存する (動画で再生するため)。
import { Worker } from 'node:worker_threads';
import os from 'node:os';
import fs from 'node:fs';
import { PARAM_COUNT, randomParams, mulberry32, gaussianFrom } from '../src/policy.js';

const [stage = 'walk', gensArg = '200', fromStage] = process.argv.slice(2);
const GENERATIONS = +gensArg;
const PAIRS = +(process.env.PAIRS || 24);          // 1 世代 = 2 × PAIRS 体
const SIGMA = +(process.env.SIGMA || 0.04);        // 突然変異の大きさ
const LR = +(process.env.LR || 0.03);              // 学習率 (Adam)
const SEEDS = +(process.env.SEEDS || (stage === 'walk' ? 1 : 3)); // 何種類の地形で評価するか
const SAVE_EVERY = +(process.env.SAVE_EVERY || 5);
const outPath = new URL(`../checkpoints/${stage}.json`, import.meta.url);

const toB64 = (f32) => Buffer.from(f32.buffer, f32.byteOffset, f32.byteLength).toString('base64');
const fromB64 = (s) => { const b = Buffer.from(s, 'base64'); return new Float32Array(b.buffer, b.byteOffset, b.byteLength / 4).slice(); };

// ---- 初期の重み
let theta;
if (fromStage) {
  const prev = JSON.parse(fs.readFileSync(new URL(`../checkpoints/${fromStage}.json`, import.meta.url)));
  theta = fromB64(prev.checkpoints[prev.checkpoints.length - 1].params);
  console.log(`start from ${fromStage} generation ${prev.checkpoints[prev.checkpoints.length - 1].generation}`);
} else {
  theta = randomParams(1);
}

// ---- ワーカー
const nWorkers = Math.max(1, os.cpus().length);
const workers = await Promise.all(Array.from({ length: nWorkers }, () => new Promise((res) => {
  const w = new Worker(new URL('./worker.mjs', import.meta.url));
  w.once('message', () => res(w));
})));
let nextId = 0;
const pending = new Map();
workers.forEach((w) => w.on('message', (m) => { pending.get(m.id)(m); pending.delete(m.id); }));
let rr = 0;
function evalParams(params, seeds) {
  return new Promise((res) => {
    const id = nextId++;
    pending.set(id, res);
    workers[rr++ % workers.length].postMessage({ id, stage, params, seeds });
  });
}

// ---- Adam
const m = new Float32Array(PARAM_COUNT), v = new Float32Array(PARAM_COUNT);
const b1 = 0.9, b2 = 0.999;
let t = 0;

const log = { stage, from: fromStage || null, paramCount: PARAM_COUNT, pairs: PAIRS, sigma: SIGMA, history: [], checkpoints: [] };
const rand = mulberry32(12345);
const t0 = Date.now();

for (let gen = 0; gen <= GENERATIONS; gen++) {
  const seeds = Array.from({ length: SEEDS }, (_, i) => gen * 100 + i + 1);
  const thetaGen = Float32Array.from(theta); // この世代の「代表」の重み (更新前)
  // 突然変異のペア (±ε) を作って評価
  const eps = Array.from({ length: PAIRS }, () => { const e = new Float32Array(PARAM_COUNT); for (let i = 0; i < PARAM_COUNT; i++) e[i] = gaussianFrom(rand); return e; });
  const cands = [];
  for (const e of eps) for (const sgn of [1, -1]) {
    const p = new Float32Array(PARAM_COUNT);
    for (let i = 0; i < PARAM_COUNT; i++) p[i] = theta[i] + sgn * SIGMA * e[i];
    cands.push(p);
  }
  const [center, ...results] = await Promise.all([evalParams(theta, seeds), ...cands.map((p) => evalParams(p, seeds))]);

  // 順位で重み付け (外れ値に強い)
  const fit = results.map((r) => r.fitness);
  const order = fit.map((f, i) => [f, i]).sort((a, b) => a[0] - b[0]);
  const ranks = new Float32Array(fit.length);
  order.forEach(([, i], r) => { ranks[i] = r / (fit.length - 1) - 0.5; });
  const grad = new Float32Array(PARAM_COUNT);
  for (let k = 0; k < PAIRS; k++) {
    const w = ranks[2 * k] - ranks[2 * k + 1];
    const e = eps[k];
    for (let i = 0; i < PARAM_COUNT; i++) grad[i] += w * e[i];
  }
  t++;
  for (let i = 0; i < PARAM_COUNT; i++) {
    const g = grad[i] / (PAIRS * SIGMA) - 0.005 * theta[i]; // 重み減衰
    m[i] = b1 * m[i] + (1 - b1) * g;
    v[i] = b2 * v[i] + (1 - b2) * g * g;
    const mh = m[i] / (1 - b1 ** t), vh = v[i] / (1 - b2 ** t);
    if (gen < GENERATIONS) theta[i] += LR * mh / (Math.sqrt(vh) + 1e-8);
  }

  const mean = fit.reduce((a, b) => a + b, 0) / fit.length;
  const best = Math.max(...fit);
  const fallRate = results.reduce((a, r) => a + r.fell, 0) / results.length;
  const rec = { generation: gen, center: +center.fitness.toFixed(3), progress: +center.progress.toFixed(3), mean: +mean.toFixed(3), best: +best.toFixed(3), fallRate: +fallRate.toFixed(3), reached: center.reached };
  log.history.push(rec);
  if (gen % SAVE_EVERY === 0 || gen === GENERATIONS || gen < 5) {
    log.checkpoints.push({ generation: gen, fitness: rec.center, params: toB64(thetaGen) });
  }
  const sec = (Date.now() - t0) / 1000;
  console.log(`${stage} gen ${String(gen).padStart(3)}  center ${rec.center.toFixed(2)}  progress ${rec.progress.toFixed(2)}m  mean ${rec.mean.toFixed(2)}  best ${rec.best.toFixed(2)}  fall ${(fallRate * 100).toFixed(0)}%  ${sec.toFixed(0)}s`);
  if (gen % 10 === 0 || gen === GENERATIONS) fs.writeFileSync(outPath, JSON.stringify(log));
}
fs.writeFileSync(outPath, JSON.stringify(log));
workers.forEach((w) => w.terminate());
