// 上映用ページ: 学習の各世代の「脳」を読み込んで場面ごとに再生し、字幕・世代・グラフを重ねる。
// 台本 (場面と字幕) は film-script.js。
// ・ブラウザで film.html を開いて「再生」→ そのまま見られる
// ・test/record-film.mjs が 1 コマずつ進めて撮影し、動画ファイルにする
import * as THREE from 'three';
import RAPIER from '@dimforge/rapier3d-compat';
import { createConfig } from './core.js';
import { Runner, STAGES, makeObstacles, buildArenaWorld, DECIMATION } from './arena.js';
import { randomParams, gaussianFrom, mulberry32, PARAM_COUNT } from './policy.js';
import { createRobotMeshFactory, syncRobotMeshes } from './robot-mesh.js';
import { SCENES, STAGE_LABELS } from './film-script.js';

export const FPS = 25;
const STEPS_PER_FRAME = 8; // 200 Hz ÷ 25 fps
const $ = (id) => document.getElementById(id);
const data = window.FILM_DATA || {};

// ------------------------------------------------------------------ 描画
const canvas = $('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(1280, 720, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xbfd4e6);
scene.fog = new THREE.Fog(0xbfd4e6, 25, 70);
const camera = new THREE.PerspectiveCamera(45, 1280 / 720, 0.05, 200);
scene.add(new THREE.HemisphereLight(0xffffff, 0x556070, 1.1));
const sun = new THREE.DirectionalLight(0xffffff, 1.7);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -9, right: 9, top: 9, bottom: -9, near: 0.5, far: 50 });
scene.add(sun, sun.target);

// 市松模様の地面
function checkerTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#9cc79a'; g.fillRect(0, 0, 128, 128);
  g.fillStyle = '#8bb889'; g.fillRect(0, 0, 64, 64); g.fillRect(64, 64, 64, 64);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(40, 40);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ map: checkerTexture(), roughness: 0.95 }));
ground.rotation.x = -Math.PI / 2;
ground.position.set(0, 0, 20);
ground.receiveShadow = true;
scene.add(ground);

const config = createConfig();
const meshFactory = createRobotMeshFactory(config);
const boxGeo = new THREE.BoxGeometry(1, 1, 1);
const wallMat = new THREE.MeshStandardMaterial({ color: 0xd9825b, roughness: 0.8 });
const stepMat = new THREE.MeshStandardMaterial({ color: 0x8f9bb3, roughness: 0.85 });
const goalMat = new THREE.MeshStandardMaterial({ color: 0xffc83d, emissive: 0x553300, roughness: 0.5 });

// 地面の目盛り: スタートラインと 1m ごとの線 (どれだけ進んだか分かるように)
function textSprite(text, color = '#ffffff') {
  const c = document.createElement('canvas');
  c.width = 256; c.height = 96;
  const g = c.getContext('2d');
  g.font = 'bold 60px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineWidth = 10; g.strokeStyle = 'rgba(0,0,0,0.55)'; g.strokeText(text, 128, 50);
  g.fillStyle = color; g.fillText(text, 128, 50);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthWrite: false }));
  sp.scale.set(0.8, 0.3, 1);
  return sp;
}
const markers = new THREE.Group();
scene.add(markers);
function buildMarkers(width, maxZ) {
  markers.clear();
  const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.75 });
  const startMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
  for (let z = 0; z <= maxZ; z++) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(width, z === 0 ? 0.08 : 0.03), z === 0 ? startMat : lineMat);
    m.rotation.x = -Math.PI / 2;
    m.position.set(0, 0.004, z);
    markers.add(m);
    if (z % 2 === 0) {
      const label = textSprite(z === 0 ? 'スタート' : `${z} m`);
      label.position.set(width / 2 + 0.5, 0.2, z);
      markers.add(label);
    }
  }
}

// ------------------------------------------------------------------ 学習データ
function decode(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Float32Array(bytes.buffer);
}

/** stage の generation 以下で一番近い保存済みの重み */
function checkpoint(stage, gen) {
  const d = data[stage];
  if (!d) throw new Error(`学習データ ${stage} がありません`);
  const cps = d.checkpoints;
  if (gen === 'last') gen = cps[cps.length - 1].generation;
  let best = cps[0];
  for (const c of cps) if (c.generation <= gen) best = c;
  return { generation: best.generation, params: decode(best.params) };
}

/** 世代の「個体たち」: 代表の重み + 進化で使ったのと同じ大きさのばらつき */
function populationParams(stage, gen, count, randomBrains, seed) {
  if (randomBrains) return Array.from({ length: count }, (_, i) => ({ params: randomParams(i + 1), generation: 0 }));
  const cp = checkpoint(stage, gen);
  const sigma = (data[stage] && data[stage].sigma) || 0.04;
  const rand = mulberry32(seed);
  return Array.from({ length: count }, (_, i) => {
    if (i === 0) return cp;
    const p = new Float32Array(PARAM_COUNT);
    for (let k = 0; k < PARAM_COUNT; k++) p[k] = cp.params[k] + sigma * gaussianFrom(rand);
    return { params: p, generation: cp.generation };
  });
}

// ------------------------------------------------------------------ 場面
let current = null; // { def, lanes: [...], frame, frames }
const labelsEl = $('labels');

function clearScene() {
  if (!current) return;
  for (const lane of current.lanes) {
    lane.objects.forEach((o) => scene.remove(o));
    lane.world.free();
  }
  labelsEl.innerHTML = '';
  current = null;
}

function laneColor(i, n) { return new THREE.Color().setHSL((0.02 + i * 0.618) % 1, 0.62, 0.55); }

function makeLane(def, i, n, brain, seed) {
  const stageName = def.stage;
  const boxes = makeObstacles(stageName, seed);
  const world = buildArenaWorld(RAPIER, boxes);
  const runner = new Runner(RAPIER, world, stageName, brain.params, { x: 0, z: 0 }, config);
  runner.stage = { ...runner.stage, seconds: 1e9 }; // 場面の最後まで動かし続ける
  const spacing = def.spacing ?? 1.0;
  const offset = new THREE.Vector3((i - (n - 1) / 2) * spacing, 0, 0);
  const color = def.colors ? new THREE.Color(def.colors[i]) : laneColor(i, n);
  const objects = [];
  const meshes = meshFactory.create(scene, runner.robot, color);
  objects.push(...meshes);
  for (const b of boxes) {
    const m = new THREE.Mesh(boxGeo, b.kind === 'wall' ? wallMat : stepMat);
    m.scale.set(b.sx, b.h, b.sz);
    m.position.set(b.x + offset.x, b.h / 2, b.z);
    m.castShadow = true; m.receiveShadow = true;
    scene.add(m); objects.push(m);
  }
  if (runner.goal) {
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1.2, 12), goalMat);
    pole.position.set(runner.goal.x + offset.x, 0.6, runner.goal.z);
    const flag = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.25, 0.02), goalMat);
    flag.position.set(runner.goal.x + offset.x + 0.2, 1.05, runner.goal.z);
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.5, 0.6, 40), goalMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.set(runner.goal.x + offset.x, 0.01, runner.goal.z);
    scene.add(pole, flag, ring); objects.push(pole, flag, ring);
  }
  // 胴体の通った跡
  const trailGeo = new THREE.BufferGeometry();
  const trailPos = new Float32Array(3 * 2000);
  trailGeo.setAttribute('position', new THREE.BufferAttribute(trailPos, 3));
  trailGeo.setDrawRange(0, 0);
  const trail = new THREE.Line(trailGeo, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.85 }));
  scene.add(trail); objects.push(trail);

  let label = null;
  if (def.labels) {
    label = document.createElement('div');
    label.className = 'lane-label';
    label.textContent = def.labels[i];
    label.style.setProperty('--c', '#' + color.getHexString());
    labelsEl.appendChild(label);
  }
  return { world, runner, meshes, objects, offset, trail, trailPos, trailN: 0, label, brain };
}

export async function loadScene(index) {
  clearScene();
  const def = SCENES[index];
  const frames = Math.round(def.seconds * FPS);
  const lanes = [];
  if (def.kind === 'population') {
    const brains = populationParams(def.stage, def.gen, def.count ?? 6, def.randomBrains, 1000 + index);
    brains.forEach((b, i) => lanes.push(makeLane(def, i, brains.length, b, def.terrainSeed ?? 7)));
  } else if (def.kind === 'race') {
    def.gens.forEach((g, i) => {
      const b = g === 'random' ? { params: randomParams(3), generation: 0 } : checkpoint(def.stage, g);
      lanes.push(makeLane(def, i, def.gens.length, b, def.terrainSeed ?? 7));
    });
  }
  const spacing = def.spacing ?? 1.0;
  if (def.kind !== 'card' && def.markers !== false) buildMarkers(Math.max(2, lanes.length * spacing + 0.6), def.markerLength ?? 12);
  else markers.clear();
  current = { def, lanes, frame: 0, frames, index };
  setupOverlay(def);
  placeCamera(true);
  render();
  return frames;
}

// ------------------------------------------------------------------ 1 コマ進める
export function step() {
  if (!current) return true;
  const { def } = current;
  if (def.kind !== 'card') {
    for (let s = 0; s < STEPS_PER_FRAME; s++) {
      for (const lane of current.lanes) {
        lane.runner.control();
        lane.world.step();
        lane.runner.afterStep();
      }
    }
  }
  current.frame++;
  updateOverlay();
  placeCamera(false);
  render();
  return current.frame >= current.frames;
}

function render() {
  if (current) for (const lane of current.lanes) {
    syncRobotMeshes(lane.runner.robot, lane.meshes);
    lane.meshes.forEach((m) => m.position.add(lane.offset));
    // 跡
    const p = lane.runner.robot.position;
    if (lane.trailN < 2000 && current.frame % 2 === 0) {
      lane.trailPos.set([p.x + lane.offset.x, 0.03, p.z], lane.trailN * 3);
      lane.trailN++;
      lane.trail.geometry.setDrawRange(0, lane.trailN);
      lane.trail.geometry.attributes.position.needsUpdate = true;
    }
    if (lane.label) {
      const v = new THREE.Vector3(p.x + lane.offset.x, p.y + 0.35, p.z).project(camera);
      lane.label.style.left = `${(v.x * 0.5 + 0.5) * 1280}px`;
      lane.label.style.top = `${(-v.y * 0.5 + 0.5) * 720}px`;
      lane.label.style.display = v.z < 1 ? 'block' : 'none';
    }
  }
  renderer.render(scene, camera);
}

// ------------------------------------------------------------------ カメラ
const camTarget = new THREE.Vector3();
function placeCamera(snap) {
  if (!current || !current.lanes.length) return;
  const { def } = current;
  const c = new THREE.Vector3();
  let maxZ = -1e9;
  for (const lane of current.lanes) {
    const p = lane.runner.robot.position;
    c.add(new THREE.Vector3(p.x + lane.offset.x, 0.2, p.z));
    maxZ = Math.max(maxZ, p.z);
  }
  c.divideScalar(current.lanes.length);
  if (def.followLead) c.z = c.z * 0.4 + maxZ * 0.6;
  if (def.fixedTarget) c.set(...def.fixedTarget);
  const k = snap ? 1 : 0.06;
  camTarget.lerp(c, k);
  const off = new THREE.Vector3(...(def.camera || [5.2, 2.6, -1.2]));
  camera.position.copy(camTarget).add(off);
  camera.lookAt(camTarget.x, camTarget.y, camTarget.z + (def.lookAhead ?? 0.8));
  sun.position.set(camTarget.x + 4, 12, camTarget.z + 2);
  sun.target.position.copy(camTarget);
}

// ------------------------------------------------------------------ 字幕・世代・グラフ
function setupOverlay(def) {
  const isCard = def.kind === 'card';
  $('card').hidden = !isCard;
  if (isCard) {
    $('cardTitle').innerHTML = def.title || '';
    $('cardBody').innerHTML = def.body || '';
  }
  $('badge').hidden = isCard || !def.badge;
  if (def.badge) {
    $('badgeStage').textContent = STAGE_LABELS[def.stage] || '';
    $('badgeGen').innerHTML = def.badge;
  }
  $('graphBox').hidden = isCard || !def.graph;
  $('caption').hidden = true;
  updateOverlay();
}

function updateOverlay() {
  const { def, frame } = current;
  const t = frame / FPS;
  let text = null;
  for (const [at, s] of def.captions || []) if (t >= at) text = s;
  $('caption').hidden = !text;
  if (text) $('captionText').innerHTML = text;
  if (def.graph) drawGraph(def);
}

function drawGraph(def) {
  const d = data[def.stage];
  const cv = $('graph'), g = cv.getContext('2d');
  const W = cv.width, H = cv.height;
  g.clearRect(0, 0, W, H);
  if (!d) return;
  $('graphTitle').textContent = def.graphTitle || '8 秒間に進んだ距離 (世代ごと)';
  const hist = d.history;
  const key = def.graphKey || 'progress';
  const vals = hist.map((h) => h[key]);
  const lo = Math.min(0, ...vals), hi = Math.max(...vals) * 1.05;
  const pad = { l: 34, r: 8, t: 8, b: 22 };
  const X = (gen) => pad.l + (gen / hist[hist.length - 1].generation) * (W - pad.l - pad.r);
  const Y = (v) => H - pad.b - ((v - lo) / (hi - lo)) * (H - pad.t - pad.b);
  g.strokeStyle = 'rgba(255,255,255,0.15)'; g.lineWidth = 1;
  g.fillStyle = '#9aa7bd'; g.font = '11px sans-serif';
  for (let v = Math.ceil(lo); v <= hi; v += Math.max(1, Math.round((hi - lo) / 4))) {
    g.beginPath(); g.moveTo(pad.l, Y(v)); g.lineTo(W - pad.r, Y(v)); g.stroke();
    g.fillText(`${v}m`, 4, Y(v) + 4);
  }
  g.fillText('世代 →', W - 48, H - 6);
  // 学習曲線 (移動平均でなめらかに)
  g.strokeStyle = '#ffb84f'; g.lineWidth = 2.5; g.beginPath();
  hist.forEach((h, i) => {
    const a = Math.max(0, i - 3), b = Math.min(hist.length - 1, i + 3);
    let s = 0; for (let k = a; k <= b; k++) s += vals[k];
    const v = s / (b - a + 1);
    i ? g.lineTo(X(h.generation), Y(v)) : g.moveTo(X(h.generation), Y(v));
  });
  g.stroke();
  // 今の世代の印
  const marks = def.kind === 'race' ? def.gens.filter((x) => x !== 'random') : [def.randomBrains ? 0 : def.gen];
  for (const m0 of marks) {
    const m = m0 === 'last' ? hist[hist.length - 1].generation : m0;
    g.strokeStyle = '#4fd1ff'; g.lineWidth = 2;
    g.beginPath(); g.moveTo(X(m), pad.t); g.lineTo(X(m), H - pad.b); g.stroke();
    g.fillStyle = '#4fd1ff'; g.beginPath(); g.arc(X(m), Y(vals[Math.min(vals.length - 1, hist.findIndex((h) => h.generation >= m))] ?? 0), 5, 0, Math.PI * 2); g.fill();
  }
}

// ------------------------------------------------------------------ 再生 (ブラウザで見る用)
let playing = false;
async function playAll() {
  playing = true;
  for (let i = 0; i < SCENES.length && playing; i++) {
    await loadScene(i);
    $('sceneInfo').textContent = `場面 ${i + 1} / ${SCENES.length}`;
    await new Promise((res) => {
      let last = performance.now(), acc = 0;
      const tick = (now) => {
        acc += (now - last) / 1000; last = now;
        let done = false;
        while (acc >= 1 / FPS && !done) { done = step(); acc -= 1 / FPS; }
        if (done || !playing) res(); else requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }
  playing = false;
}

function fit() {
  const s = Math.min(window.innerWidth / 1280, window.innerHeight / 720);
  document.getElementById('stage').style.setProperty('--fit', s);
}

async function main() {
  fit();
  window.addEventListener('resize', fit);
  await RAPIER.init();
  const params = new URLSearchParams(location.search);
  if (params.has('record')) document.body.classList.add('recording');
  window.film = { loadScene, step, sceneCount: SCENES.length, FPS, ready: true };
  $('play').addEventListener('click', () => { if (!playing) playAll(); });
  if (params.has('scene')) { await loadScene(+params.get('scene')); }
  else if (!params.has('record')) { await loadScene(0); }
}

main().catch((e) => { document.body.innerHTML = `<pre style="color:#f88">${e.stack}</pre>`; console.error(e); });
