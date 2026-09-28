// Web 版のエントリポイント: Three.js で描画、Rapier で物理計算、UI とモード (デモ / 進化で学習) を管理する。
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import RAPIER from '@dimforge/rapier3d-compat';
import { createConfig, TrotGait, defaultGaitParams, GAIT_PARAMS, JOINT_COUNT } from './core.js';
import { QuadrupedRobot } from './robot.js';
import { TerrainGenerator, TERRAIN_TYPES, buildTerrainColliders, greedyRects, smoothMesh } from './terrain.js';
import { Evolution } from './evolution.js';
import { createRobotMeshFactory, syncRobotMeshes } from './robot-mesh.js';

const DT = 1 / 200;          // 物理 200 Hz
const DECIMATION = 4;        // 制御 50 Hz
const EVAL_SECONDS = 8;      // 進化: 1 世代の評価時間
const EVAL_COMMAND = { forward: 0.5, side: 0, yaw: 0 };

const $ = (id) => document.getElementById(id);

// ------------------------------------------------------------------ 描画の準備
const canvas = $('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xbfd4e6);
scene.fog = new THREE.Fog(0xbfd4e6, 30, 90);
const camera = new THREE.PerspectiveCamera(50, 1, 0.05, 300);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.49;

scene.add(new THREE.HemisphereLight(0xffffff, 0x556070, 1.1));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: 0.5, far: 40 });
scene.add(sun, sun.target);

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);

// ------------------------------------------------------------------ 状態
const state = {
  mode: 'demo',
  count: 16,
  terrain: 'all',
  level: 0,
  speed: 1,
  paused: false,
  pushes: true,
  selected: 0,
  overview: false,
  demoParams: defaultGaitParams(),
};
const keys = new Set();

let world, gen, robots = [], terrainGroup = null, evolution = null, simTime = 0, genTime = 0;
const prevTarget = new THREE.Vector3();
const config = createConfig();

// ------------------------------------------------------------------ 地形
function buildTerrainMeshes() {
  if (terrainGroup) scene.remove(terrainGroup);
  terrainGroup = new THREE.Group();
  const boxGeo = new THREE.BoxGeometry(1, 1, 1);
  for (let col = 0; col < gen.columns; col++) for (let level = 0; level < gen.levels; level++) {
    const t = gen.tiles[col][level], c = gen.tileCenter(col, level);
    const base = new THREE.Color(t.type.color);
    if (t.type.blocky) {
      const rects = greedyRects(t);
      const mat = new THREE.MeshStandardMaterial({ roughness: 0.9 });
      const mesh = new THREE.InstancedMesh(boxGeo, mat, rects.length);
      const m = new THREE.Matrix4(), col3 = new THREE.Color();
      rects.forEach((r, i) => {
        const sx = r.nx * t.cellSize, sz = r.nz * t.cellSize, sy = r.h + 3;
        m.makeScale(sx, sy, sz).setPosition(c.x - t.size / 2 + r.ix * t.cellSize + sx / 2, -3 + sy / 2, c.z - t.size / 2 + r.iz * t.cellSize + sz / 2);
        mesh.setMatrixAt(i, m);
        // 段ごとに明るさを変えて段差を見やすく
        const shade = 0.82 + 0.18 * (((Math.round(r.h / 0.01) % 7) + 7) % 7) / 6;
        mesh.setColorAt(i, col3.copy(base).multiplyScalar(shade));
      });
      mesh.receiveShadow = true;
      mesh.castShadow = true;
      terrainGroup.add(mesh);
    } else {
      const { vertices, indices } = smoothMesh(t, c);
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
      geo.setIndex(new THREE.BufferAttribute(indices, 1));
      // 1m ごとの市松模様を頂点色で
      const colors = new Float32Array(vertices.length);
      for (let i = 0; i < vertices.length; i += 3) {
        const k = (Math.floor(vertices[i]) + Math.floor(vertices[i + 2])) & 1 ? 0.9 : 1.0;
        colors[i] = base.r * k; colors[i + 1] = base.g * k; colors[i + 2] = base.b * k;
      }
      geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      geo.computeVertexNormals();
      const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95 }));
      mesh.receiveShadow = true;
      terrainGroup.add(mesh);
    }
  }
  // タイルの境界線
  const lines = [];
  for (let i = 0; i <= gen.columns; i++) lines.push(i * gen.tileSize, 0.02, 0, i * gen.tileSize, 0.02, gen.depth);
  for (let j = 0; j <= gen.levels; j++) lines.push(0, 0.02, j * gen.tileSize, gen.width, 0.02, j * gen.tileSize);
  const lg = new THREE.BufferGeometry();
  lg.setAttribute('position', new THREE.Float32BufferAttribute(lines, 3));
  terrainGroup.add(new THREE.LineSegments(lg, new THREE.LineBasicMaterial({ color: 0x445566, transparent: true, opacity: 0.5 })));
  scene.add(terrainGroup);
}

// ------------------------------------------------------------------ ロボットの見た目
const robotMeshes = createRobotMeshFactory(config);
const createRobotMeshes = (robot, color) => robotMeshes.create(scene, robot, color);
const syncMeshes = (r) => syncRobotMeshes(r.robot, r.meshes);

// ------------------------------------------------------------------ ロボットの配置と制御
function tileFor(i) {
  if (state.mode === 'demo' && state.terrain === 'all') return { col: i % gen.columns, level: state.level };
  const col = Math.max(0, TERRAIN_TYPES.findIndex((t) => t.key === state.terrain));
  return { col, level: state.level };
}

function spawnPoint(i) {
  const { col, level } = tileFor(i);
  const c = gen.tileCenter(col, level);
  const t = gen.tiles[col][level];
  // 同じタイルのロボットは少しずつずらす (ロボット同士はぶつからない設定)
  const ring = Math.floor(i / gen.columns);
  const x = c.x + ((i * 0.37) % 1 - 0.5) * 1.2;
  const z = c.z + ((ring * 0.61) % 1 - 0.5) * 1.2;
  return { x, y: t.platformHeight + config.spawnHeight, z };
}

function randomCommand() {
  const r = Math.random();
  if (r < 0.1) return { forward: 0, side: 0, yaw: 0 };
  return {
    forward: -0.2 + Math.random() * 0.8,
    side: (Math.random() * 2 - 1) * 0.2,
    yaw: (Math.random() * 2 - 1) * 0.6,
  };
}

function resetRobot(r, i) {
  const p = spawnPoint(i);
  r.robot.reset(p, 0);
  r.gait.reset();
  r.start = { x: p.x, z: p.z };
  r.cmd = state.mode === 'evolve' ? { ...EVAL_COMMAND } : randomCommand();
  r.cmdTimer = 4 + Math.random() * 4;
  r.pushTimer = 3 + Math.random() * 6;
  r.fallenTime = 0;
  r.fell = false;
}

function rebuild() {
  if (world) {
    robots.forEach((r) => r.meshes.forEach((m) => scene.remove(m)));
    world.free();
  }
  world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
  world.timestep = DT;
  buildTerrainColliders(RAPIER, world, gen);

  if (state.mode === 'evolve' && (!evolution || evolution.size !== state.count)) evolution = new Evolution(state.count);
  robots = [];
  for (let i = 0; i < state.count; i++) {
    const p = spawnPoint(i);
    const robot = new QuadrupedRobot(RAPIER, world, config, p, 0);
    const params = state.mode === 'evolve' ? evolution.population[i] : { ...state.demoParams };
    const color = new THREE.Color().setHSL((i * 0.618) % 1, 0.6, 0.55);
    const r = { robot, params, gait: new TrotGait(config, params), meshes: createRobotMeshes(robot, color), targets: new Float64Array(JOINT_COUNT) };
    resetRobot(r, i);
    robots.push(r);
  }
  state.selected = Math.min(state.selected, robots.length - 1);
  simTime = 0; genTime = 0;
  const target = robots[state.selected].robot.position;
  controls.target.set(target.x, target.y, target.z);
  prevTarget.copy(controls.target);
  camera.position.set(target.x + 1.6, target.y + 1.0, target.z - 2.0);
}

function keyboardCommand() {
  let f = 0, s = 0, y = 0;
  if (keys.has('w') || keys.has('arrowup')) f += 0.6;
  if (keys.has('s') || keys.has('arrowdown')) f -= 0.3;
  if (keys.has('d')) s += 0.3;
  if (keys.has('a')) s -= 0.3;
  if (keys.has('e') || keys.has('arrowright')) y += 0.8;
  if (keys.has('q') || keys.has('arrowleft')) y -= 0.8;
  return { forward: f, side: s, yaw: y };
}
let manual = false;

function controlStep() {
  const ctrlDt = DT * DECIMATION;
  robots.forEach((r, i) => {
    const robot = r.robot;
    robot.readState();
    if (state.mode === 'demo') {
      if (i === state.selected && manual) r.cmd = keyboardCommand();
      else if ((r.cmdTimer -= ctrlDt) <= 0) { r.cmd = randomCommand(); r.cmdTimer = 4 + Math.random() * 4; }
      if (state.pushes && (r.pushTimer -= ctrlDt) <= 0) {
        const a = Math.random() * Math.PI * 2;
        robot.push({ x: Math.cos(a) * 0.6, y: 0, z: Math.sin(a) * 0.6 });
        r.pushTimer = 5 + Math.random() * 6;
      }
    }
    r.gait.step(ctrlDt, r.cmd, robot.gravityCore(), r.targets);
    robot.setTargets(r.targets);

    const fallen = robot.isFallen();
    if (fallen) r.fell = true;
    r.fallenTime = fallen ? r.fallenTime + ctrlDt : 0;
    const p = robot.position;
    const outside = p.x < 0 || p.z < 0 || p.x > gen.width || p.z > gen.depth || p.y < -4;
    if (state.mode === 'demo' && (r.fallenTime > 2 || outside)) resetRobot(r, i);
  });
}

function physicsStep() {
  if (Math.round(simTime / DT) % DECIMATION === 0) controlStep();
  world.step();
  simTime += DT;
  if (state.mode === 'evolve') {
    genTime += DT;
    if (genTime >= EVAL_SECONDS) finishGeneration();
  }
}

// ------------------------------------------------------------------ 進化
function finishGeneration() {
  const fitness = robots.map((r) => {
    const p = r.robot.position;
    return (p.z - r.start.z) - 0.5 * Math.abs(p.x - r.start.x) - (r.fell ? 1.5 : 0);
  });
  evolution.next(fitness);
  robots.forEach((r, i) => {
    Object.assign(r.params, evolution.population[i]);
    resetRobot(r, i);
  });
  genTime = 0;
  drawChart();
}

function drawChart() {
  const cv = $('chart'), ctx = cv.getContext('2d');
  const w = cv.width, h = cv.height, hist = evolution ? evolution.history : [];
  ctx.clearRect(0, 0, w, h);
  $('genInfo').textContent = `第 ${evolution ? evolution.generation : 0} 世代` +
    (hist.length ? `  最高 ${hist[hist.length - 1].best.toFixed(2)} m  平均 ${hist[hist.length - 1].mean.toFixed(2)} m` : '');
  if (hist.length === 0) { ctx.fillStyle = '#667'; ctx.font = '12px sans-serif'; ctx.fillText(`${EVAL_SECONDS} 秒ごとに世代交代します`, 10, h / 2); return; }
  const all = hist.flatMap((x) => [x.best, x.mean]);
  const lo = Math.min(0, ...all), hi = Math.max(1, ...all);
  const X = (i) => 8 + (i / Math.max(1, hist.length - 1)) * (w - 16);
  const Y = (v) => h - 10 - ((v - lo) / (hi - lo)) * (h - 20);
  ctx.strokeStyle = '#2a3140'; ctx.beginPath(); ctx.moveTo(0, Y(0)); ctx.lineTo(w, Y(0)); ctx.stroke();
  const line = (key, color) => {
    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath();
    hist.forEach((x, i) => (i ? ctx.lineTo(X(i), Y(x[key])) : ctx.moveTo(X(i), Y(x[key]))));
    ctx.stroke();
  };
  line('mean', '#6b7a99');
  line('best', '#ffb84f');
  ctx.fillStyle = '#ffb84f'; ctx.font = '11px sans-serif'; ctx.fillText('最高', w - 34, 14);
  ctx.fillStyle = '#6b7a99'; ctx.fillText('平均', w - 34, 28);
  const best = evolution.best;
  if (best) $('bestParams').textContent = GAIT_PARAMS.map(([k]) => `${k.padEnd(13)} ${best.params[k].toFixed(3)}`).join('\n');
}

// ------------------------------------------------------------------ UI
function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll('.tab').forEach((b) => b.classList.toggle('active', b.dataset.mode === mode));
  $('evolvePanel').hidden = mode !== 'evolve';
  $('modeHint').textContent = mode === 'demo'
    ? 'プログラムされたトロット歩容で歩きます。ランダムな速度指令で動き、選択中のロボットはキーボードで操作できます。'
    : `全員が同じ地形で ${EVAL_SECONDS} 秒間「前へ 0.5 m/s」を目指して歩き、進んだ距離が長い歩き方ほど次の世代に残ります (遺伝的アルゴリズム)。世代を重ねるほど上手に歩けるようになります。`;
  if (mode === 'evolve' && state.terrain === 'all') { state.terrain = 'rough'; $('terrain').value = 'rough'; }
  evolution = null;
  rebuild();
  drawChart();
}

function setupUi() {
  const sel = $('terrain');
  sel.innerHTML = '<option value="all">すべて (ロボットごとに違う地形)</option>' +
    TERRAIN_TYPES.map((t) => `<option value="${t.key}">${t.label}</option>`).join('');
  document.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => setMode(b.dataset.mode)));
  $('count').addEventListener('input', (e) => { $('countLabel').textContent = e.target.value; });
  $('count').addEventListener('change', (e) => { state.count = +e.target.value; evolution = null; rebuild(); drawChart(); });
  sel.addEventListener('change', (e) => { state.terrain = e.target.value; rebuild(); });
  $('level').addEventListener('input', (e) => { state.level = +e.target.value; $('levelLabel').textContent = e.target.value; });
  $('level').addEventListener('change', () => rebuild());
  $('speed').addEventListener('change', (e) => { state.speed = +e.target.value; });
  $('restart').addEventListener('click', () => { if (state.mode === 'evolve') evolution = null; rebuild(); drawChart(); });
  $('pause').addEventListener('click', (e) => { state.paused = !state.paused; e.target.textContent = state.paused ? '再開' : '一時停止'; });
  $('kick').addEventListener('click', kick);
  $('pushes').addEventListener('change', (e) => { state.pushes = e.target.checked; });
  $('applyBest').addEventListener('click', () => {
    if (!evolution || !evolution.best) return;
    state.demoParams = { ...evolution.best.params };
    setMode('demo');
  });

  window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
    const k = e.key.toLowerCase();
    keys.add(k);
    if ('wasdqe'.includes(k) || k.startsWith('arrow')) manual = true;
    if (k === 'tab') { e.preventDefault(); state.selected = (state.selected + 1) % robots.length; }
    if (k === ' ') { e.preventDefault(); kick(); }
    if (k === 'r') resetRobot(robots[state.selected], state.selected);
    if (k === 'f') state.overview = !state.overview;
  });
  window.addEventListener('keyup', (e) => keys.delete(e.key.toLowerCase()));
}

function kick() {
  const r = robots[state.selected];
  if (!r) return;
  const a = Math.random() * Math.PI * 2;
  r.robot.push({ x: Math.cos(a) * 1.3, y: 0.2, z: Math.sin(a) * 1.3 });
}

// ------------------------------------------------------------------ メインループ
let last = performance.now(), fps = 60, realtime = 1, acc = 0;

function frame(now) {
  const frameDt = Math.min(0.1, (now - last) / 1000);
  last = now;
  fps = fps * 0.95 + (1 / Math.max(frameDt, 1e-3)) * 0.05;

  if (!state.paused) {
    acc += frameDt * state.speed;
    const t0 = performance.now();
    let steps = 0;
    while (acc >= DT && steps < 80) { physicsStep(); acc -= DT; steps++; }
    if (steps >= 80) acc = 0; // 追いつけないときは遅く再生する
    const simMs = performance.now() - t0;
    realtime = realtime * 0.9 + (steps * DT / Math.max(frameDt, 1e-3)) * 0.1;
    window.__perf = { steps, simMs };
  }
  robots.forEach(syncMeshes);

  // カメラ: 選択中のロボットを追いかける
  const sel = robots[state.selected];
  const focus = state.overview || !sel
    ? new THREE.Vector3(gen.width / 2, 0, gen.depth / 2)
    : new THREE.Vector3().copy(sel.robot.position);
  // 注視点をなめらかに追従させ、カメラも同じだけ平行移動する (マウスで回した向きは保つ)
  const delta = new THREE.Vector3().subVectors(focus, controls.target);
  if (delta.length() < 5) delta.multiplyScalar(1 - Math.exp(-10 * frameDt));
  controls.target.add(delta);
  camera.position.add(delta);
  prevTarget.copy(controls.target);
  if (state.overview && camera.position.distanceTo(focus) < 20) camera.position.set(focus.x - 22, 24, focus.z - 26);
  sun.position.set(controls.target.x + 4, controls.target.y + 10, controls.target.z + 3);
  sun.target.position.copy(controls.target);
  controls.update();
  renderer.render(scene, camera);

  if (sel) {
    const v = sel.robot.velocityCore();
    const cmd = sel.cmd;
    const t = tileFor(state.selected);
    const modeText = state.mode === 'demo' ? `デモ (${manual ? 'キーボード操作' : 'ランダム指令'})` : `進化で学習  第 ${evolution.generation} 世代  評価 ${genTime.toFixed(1)} / ${EVAL_SECONDS} s`;
    $('status').textContent =
      `${modeText}\n` +
      `ロボット #${state.selected} / ${robots.length}   地形: ${TERRAIN_TYPES[t.col].label}  難易度 ${t.level}\n` +
      `指令  前 ${cmd.forward.toFixed(2)}  横 ${cmd.side.toFixed(2)}  旋回 ${cmd.yaw.toFixed(2)}\n` +
      `実際  前 ${v.z.toFixed(2)}  横 ${v.x.toFixed(2)} m/s   接地 ${sel.robot.footContact.map((c) => (c ? '■' : '□')).join('')}\n` +
      `物理 ${robots.length * 13} 剛体  実時間比 ×${realtime.toFixed(2)}  ${fps.toFixed(0)} fps`;
  }
  requestAnimationFrame(frame);
}

// ------------------------------------------------------------------ 起動
async function main() {
  resize();
  await RAPIER.init();
  gen = new TerrainGenerator({ levels: 4, tileSize: 8, seed: 3 });
  gen.generate();
  buildTerrainMeshes();
  setupUi();
  const params = new URLSearchParams(location.search);
  if (params.has('count')) { state.count = +params.get('count'); $('count').value = state.count; $('countLabel').textContent = state.count; }
  if (params.has('terrain')) { state.terrain = params.get('terrain'); $('terrain').value = state.terrain; }
  if (params.has('level')) { state.level = +params.get('level'); $('level').value = state.level; $('levelLabel').textContent = state.level; }
  if (params.has('speed')) state.speed = +params.get('speed');
  setMode(params.get('mode') === 'evolve' ? 'evolve' : 'demo');
  window.__sim = { state, robots: () => robots, evolution: () => evolution, keys, setManual: (v) => { manual = v; } };
  requestAnimationFrame((t) => { last = t; frame(t); });
}

main().catch((e) => { $('status').textContent = 'エラー: ' + e.message; console.error(e); });
