// 地形生成 (Unity 版 TerrainGenerator と同じ考え方)。
// 列 (x 方向) = 地形の種類、行 (z 方向) = 難易度。ロボットはタイル中央の平らな台からスタートして外へ歩く。
// 階段や段差は「箱」の組み合わせ (垂直な壁を正確に表現)、坂やでこぼこは三角形メッシュで作る。
import { GROUND_GROUPS } from './robot.js';

export const TERRAIN_TYPES = [
  { key: 'rough', label: 'でこぼこ', color: 0x8fbf8a, blocky: false },
  { key: 'slopeUp', label: '上り坂', color: 0xc9a46f, blocky: false },
  { key: 'stairsUp', label: '上り階段', color: 0x9b8fd6, blocky: true },
  { key: 'stairsDown', label: '下り階段', color: 0x7fa3d9, blocky: true },
  { key: 'obstacles', label: '段差ブロック', color: 0xd48f8f, blocky: true },
];

function mulberry32(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class TerrainGenerator {
  constructor({ levels = 4, tileSize = 8, cellSize = 0.1, platformSize = 2, seed = 1 } = {}) {
    Object.assign(this, { levels, tileSize, cellSize, platformSize, seed });
    this.cells = Math.round(tileSize / cellSize);
    this.columns = TERRAIN_TYPES.length;
  }

  generate() {
    const rng = mulberry32(this.seed);
    this.tiles = [];
    for (let col = 0; col < this.columns; col++) {
      this.tiles[col] = [];
      for (let level = 0; level < this.levels; level++) {
        const difficulty = this.levels > 1 ? level / (this.levels - 1) : 0;
        this.tiles[col][level] = this.generateTile(TERRAIN_TYPES[col], level, difficulty, rng);
      }
    }
    return this.tiles;
  }

  generateTile(type, level, difficulty, rng) {
    const n = this.cells, cs = this.cellSize, half = this.tileSize / 2, ph = this.platformSize / 2;
    const h = new Float32Array(n * n); // h[ix * n + iz]
    const center = (i) => (i + 0.5) * cs - half;
    const each = (f) => { for (let ix = 0; ix < n; ix++) for (let iz = 0; iz < n; iz++) h[ix * n + iz] = f(center(ix), center(iz)); };
    const dist = (x, z) => half - Math.max(Math.max(Math.abs(x), Math.abs(z)), ph); // 端で 0

    switch (type.key) {
      case 'rough': addNoise(h, n, rng, 0.01 + 0.05 * difficulty); break;
      case 'slopeUp': {
        const slope = 0.05 + 0.35 * difficulty;
        each((x, z) => -slope * dist(x, z)); // 中央が低い → 外へ向かって登る
        if (difficulty > 0.3) addNoise(h, n, rng, 0.015);
        break;
      }
      case 'stairsUp':
      case 'stairsDown': {
        const stepH = 0.05 + 0.15 * difficulty, stepW = 0.3;
        const sign = type.key === 'stairsDown' ? 1 : -1;
        each((x, z) => sign * stepH * Math.floor(dist(x, z) / stepW + 1e-4));
        break;
      }
      case 'obstacles': {
        const maxH = 0.05 + 0.15 * difficulty;
        for (let k = 0; k < 40; k++) {
          const w = 3 + Math.floor(rng() * 8), d = 3 + Math.floor(rng() * 8);
          const x0 = Math.floor(rng() * (n - w)), z0 = Math.floor(rng() * (n - d));
          const v = (rng() * 2 - 1) * maxH;
          for (let ix = x0; ix < x0 + w; ix++) for (let iz = z0; iz < z0 + d; iz++) h[ix * n + iz] = v;
        }
        break;
      }
    }
    // 中央のスタート台を平らに
    const edgeIdx = Math.floor((ph - cs * 0.5 + half) / cs);
    const platformH = h[edgeIdx * n + Math.floor(n / 2)];
    for (let ix = 0; ix < n; ix++) for (let iz = 0; iz < n; iz++)
      if (Math.abs(center(ix)) < ph && Math.abs(center(iz)) < ph) h[ix * n + iz] = platformH;

    return { type, level, difficulty, heights: h, cells: n, cellSize: cs, size: this.tileSize, platformHeight: platformH };
  }

  tileCenter(col, level) {
    return { x: (col + 0.5) * this.tileSize, z: (level + 0.5) * this.tileSize };
  }

  /** ワールド座標の地面の高さ (セル単位) */
  heightAt(x, z) {
    const col = Math.floor(x / this.tileSize), level = Math.floor(z / this.tileSize);
    if (col < 0 || level < 0 || col >= this.columns || level >= this.levels) return 0;
    const t = this.tiles[col][level];
    const c = this.tileCenter(col, level);
    const ix = Math.min(t.cells - 1, Math.max(0, Math.floor((x - c.x + t.size / 2) / t.cellSize)));
    const iz = Math.min(t.cells - 1, Math.max(0, Math.floor((z - c.z + t.size / 2) / t.cellSize)));
    return t.heights[ix * t.cells + iz];
  }

  get width() { return this.columns * this.tileSize; }
  get depth() { return this.levels * this.tileSize; }
}

function addNoise(h, n, rng, amp) {
  const m = Math.floor(n / 2) + 2;
  const coarse = new Float32Array(m * m).map(() => (rng() * 2 - 1) * amp);
  for (let ix = 0; ix < n; ix++) for (let iz = 0; iz < n; iz++) {
    const fx = ix * 0.5, fz = iz * 0.5, x0 = Math.floor(fx), z0 = Math.floor(fz), tx = fx - x0, tz = fz - z0;
    const a = coarse[x0 * m + z0] * (1 - tx) + coarse[(x0 + 1) * m + z0] * tx;
    const b = coarse[x0 * m + z0 + 1] * (1 - tx) + coarse[(x0 + 1) * m + z0 + 1] * tx;
    h[ix * n + iz] += a * (1 - tz) + b * tz;
  }
}

/** 同じ高さのセルを長方形にまとめる (箱の数を減らす) */
export function greedyRects(tile) {
  const n = tile.cells, h = tile.heights, used = new Uint8Array(n * n), rects = [];
  for (let ix = 0; ix < n; ix++) for (let iz = 0; iz < n; iz++) {
    if (used[ix * n + iz]) continue;
    const v = h[ix * n + iz];
    let w = 1; // z 方向に伸ばす
    while (iz + w < n && !used[ix * n + iz + w] && h[ix * n + iz + w] === v) w++;
    let d = 1; // x 方向に伸ばす
    outer: while (ix + d < n) {
      for (let k = 0; k < w; k++) if (used[(ix + d) * n + iz + k] || h[(ix + d) * n + iz + k] !== v) break outer;
      d++;
    }
    for (let a = 0; a < d; a++) for (let k = 0; k < w; k++) used[(ix + a) * n + iz + k] = 1;
    rects.push({ ix, iz, nx: d, nz: w, h: v });
  }
  return rects;
}

const BOTTOM = -3;

/** Rapier の当たり判定を作る */
export function buildTerrainColliders(RAPIER, world, gen) {
  for (let col = 0; col < gen.columns; col++) for (let level = 0; level < gen.levels; level++) {
    const t = gen.tiles[col][level], c = gen.tileCenter(col, level), cs = t.cellSize, half = t.size / 2;
    if (t.type.blocky) {
      for (const r of greedyRects(t)) {
        const hx = r.nx * cs / 2, hz = r.nz * cs / 2, hy = (r.h - BOTTOM) / 2;
        const desc = RAPIER.ColliderDesc.cuboid(hx, hy, hz)
          .setTranslation(c.x - half + r.ix * cs + hx, BOTTOM + hy, c.z - half + r.iz * cs + hz)
          .setFriction(1.0).setCollisionGroups(GROUND_GROUPS);
        world.createCollider(desc);
      }
    } else {
      const { vertices, indices } = smoothMesh(t, c);
      world.createCollider(RAPIER.ColliderDesc.trimesh(vertices, indices).setFriction(1.0).setCollisionGroups(GROUND_GROUPS));
    }
  }
}

/** なめらかなタイルの頂点 (ワールド座標) と三角形 */
export function smoothMesh(t, c) {
  const n = t.cells, cs = t.cellSize, half = t.size / 2, v = n + 1;
  const vertices = new Float32Array(v * v * 3), indices = new Uint32Array(n * n * 6);
  for (let ix = 0; ix <= n; ix++) for (let iz = 0; iz <= n; iz++) {
    let sum = 0, cnt = 0;
    for (let dx = -1; dx <= 0; dx++) for (let dz = -1; dz <= 0; dz++) {
      const x = ix + dx, z = iz + dz;
      if (x < 0 || z < 0 || x >= n || z >= n) continue;
      sum += t.heights[x * n + z]; cnt++;
    }
    const k = (ix * v + iz) * 3;
    vertices[k] = c.x - half + ix * cs; vertices[k + 1] = sum / cnt; vertices[k + 2] = c.z - half + iz * cs;
  }
  let q = 0;
  for (let ix = 0; ix < n; ix++) for (let iz = 0; iz < n; iz++) {
    const a = ix * v + iz, b = a + 1, cc = a + v + 1, d = a + v;
    // 右手系で上向きの面 (反時計回り)
    indices[q++] = a; indices[q++] = b; indices[q++] = cc;
    indices[q++] = a; indices[q++] = cc; indices[q++] = d;
  }
  return { vertices, indices };
}
