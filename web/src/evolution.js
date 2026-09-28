// 遺伝的アルゴリズム (進化戦略) で歩容パラメータを改良する。
// 1 世代 = 全ロボットが同じ条件で歩いて「進んだ距離」を測る → 上位を親として残し、
// 親をランダムに少し変えた (突然変異) 子で残りを埋める。これを繰り返す。
import { GAIT_PARAMS, defaultGaitParams } from './core.js';

const clampParams = (p) => {
  for (const [k, , lo, hi] of GAIT_PARAMS) p[k] = Math.min(hi, Math.max(lo, p[k]));
  return p;
};

function gaussian() {
  const u = 1 - Math.random(), v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export class Evolution {
  constructor(size, { eliteFraction = 0.25, sigma = 0.12, sigmaDecay = 0.96, minSigma = 0.02 } = {}) {
    this.size = size;
    this.eliteCount = Math.max(1, Math.round(size * eliteFraction));
    this.sigma = sigma;
    this.sigmaDecay = sigmaDecay;
    this.minSigma = minSigma;
    this.generation = 0;
    this.history = [];
    this.best = null;
    // 最初の世代: 既定の歩き方 + それを大きめに変えたもの
    this.population = Array.from({ length: size }, (_, i) => (i === 0 ? defaultGaitParams() : this.mutate(defaultGaitParams(), 0.25)));
  }

  mutate(parent, sigma = this.sigma) {
    const child = { ...parent };
    for (const [k, , lo, hi] of GAIT_PARAMS) child[k] += gaussian() * sigma * (hi - lo);
    return clampParams(child);
  }

  crossover(a, b) {
    const child = {};
    for (const [k] of GAIT_PARAMS) child[k] = Math.random() < 0.5 ? a[k] : b[k];
    return child;
  }

  /** fitness[i] は population[i] の評価値。次の世代を作る */
  next(fitness) {
    const ranked = this.population.map((p, i) => ({ params: { ...p }, fitness: fitness[i] }))
      .sort((a, b) => b.fitness - a.fitness);
    const mean = fitness.reduce((s, f) => s + f, 0) / fitness.length;
    this.history.push({ best: ranked[0].fitness, mean });
    if (!this.best || ranked[0].fitness > this.best.fitness) this.best = ranked[0];

    const elites = ranked.slice(0, this.eliteCount).map((r) => r.params);
    const next = elites.map((e) => ({ ...e }));
    while (next.length < this.size) {
      const a = elites[Math.floor(Math.random() * elites.length)];
      const b = elites[Math.floor(Math.random() * elites.length)];
      next.push(this.mutate(Math.random() < 0.3 ? this.crossover(a, b) : a));
    }
    this.population = next;
    this.sigma = Math.max(this.minSigma, this.sigma * this.sigmaDecay);
    this.generation++;
    return ranked;
  }
}
