// ヘッドレス Chromium で index.html を開き、一定時間シミュレーションを進めてスクリーンショットを保存する。
//   node test/screenshot.mjs "?mode=demo&count=16" out.png 8000
import { chromium } from 'playwright-core';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const [query = '', out = 'shot.png', waitMs = '6000'] = process.argv.slice(2);
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const exe = ['/opt/pw-browsers/chromium', ...fs.readdirSync('/opt/pw-browsers').map((d) => `/opt/pw-browsers/${d}/chrome-linux/chrome`)]
  .find((p) => fs.existsSync(p) && fs.statSync(p).isFile());
const browser = await chromium.launch({ executablePath: exe, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto('file://' + path.join(root, 'index.html') + query);
await page.waitForTimeout(+waitMs);
await page.screenshot({ path: out });
const status = await page.$eval('#status', (e) => e.textContent);
console.log(status);
if (errors.length) { console.log('ERRORS:\n' + errors.join('\n')); process.exitCode = 1; }
await browser.close();
