// film.html を 1 コマずつ進めて撮影し、動画 (mp4) にする。
//   node test/record-film.mjs out.mp4 [最初の場面] [最後の場面]
//   PREVIEW=1 にすると各場面から数コマだけ抜き出した一覧画像 (contact sheet) を作る
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const [out = 'film.mp4', fromArg, toArg] = process.argv.slice(2);
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto('file://' + path.join(root, 'film.html') + '?record=1');
await page.waitForFunction(() => window.film && window.film.ready, null, { timeout: 60000 });
const count = await page.evaluate(() => window.film.sceneCount);
const from = fromArg ? +fromArg : 0, to = toArg ? +toArg : count - 1;
const fps = await page.evaluate(() => window.film.FPS);
const preview = !!process.env.PREVIEW;

const tmp = fs.mkdtempSync('/tmp/film-');
let ff = null;
if (!preview) {
  ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23', '-preset', 'medium', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
}
const t0 = Date.now();
let total = 0;
for (let s = from; s <= to; s++) {
  const frames = await page.evaluate((i) => window.film.loadScene(i), s);
  const pick = new Set([0, Math.floor(frames / 3), Math.floor((2 * frames) / 3), frames - 1]);
  for (let f = 0; f < frames; f++) {
    if (f > 0) await page.evaluate(() => window.film.step());
    if (preview) {
      if (pick.has(f)) await page.screenshot({ path: `${tmp}/s${String(s).padStart(2, '0')}_${String(f).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 80 });
    } else {
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    }
    total++;
  }
  console.log(`scene ${s}: ${frames} frames  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
if (ff) { ff.stdin.end(); await new Promise((r) => ff.on('close', r)); }
if (preview) {
  const files = fs.readdirSync(tmp).sort();
  // 1 場面 = 1 行 (4 コマ) の一覧画像
  const rows = [];
  for (let s = from; s <= to; s++) rows.push(files.filter((f) => f.startsWith(`s${String(s).padStart(2, '0')}_`)).map((f) => `${tmp}/${f}`));
  const inputs = rows.flat();
  const args = ['-loglevel', 'error', '-y'];
  inputs.forEach((f) => args.push('-i', f));
  const filters = inputs.map((_, i) => `[${i}]scale=480:-1[v${i}]`);
  const rowLabels = rows.map((r, ri) => { const base = rows.slice(0, ri).flat().length; return `${r.map((_, k) => `[v${base + k}]`).join('')}hstack=inputs=${r.length}[r${ri}]`; });
  const all = `${rows.map((_, ri) => `[r${ri}]`).join('')}vstack=inputs=${rows.length}`;
  args.push('-filter_complex', [...filters, ...rowLabels, rows.length > 1 ? all : '[r0]copy'].join(';'), out);
  await new Promise((r) => spawn('ffmpeg', args, { stdio: 'inherit' }).on('close', r));
}
console.log(`${total} frames → ${out}`);
if (errors.length) { console.log('ERRORS:\n' + errors.join('\n')); process.exitCode = 1; }
await browser.close();
