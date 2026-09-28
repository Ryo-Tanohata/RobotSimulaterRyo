// ヘッドレス Chromium で操作しながら動画を録画する (前進 → 旋回 → 蹴る → 進化モード)。
//   node test/record-video.mjs out_dir
import { chromium } from 'playwright-core';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const outDir = process.argv[2] || '/tmp/video';
fs.mkdirSync(outDir, { recursive: true });
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: outDir, size: { width: 1280, height: 720 } } });
const page = await context.newPage();
await page.goto('file://' + path.join(root, 'index.html') + '?count=8&terrain=rough');
await page.waitForTimeout(2500);
await page.keyboard.down('w'); await page.waitForTimeout(4000);
await page.keyboard.down('e'); await page.waitForTimeout(2500); await page.keyboard.up('e');
await page.waitForTimeout(1500);
await page.keyboard.press(' '); await page.waitForTimeout(2500);   // 蹴る
await page.keyboard.press(' '); await page.waitForTimeout(2500);
await page.keyboard.up('w'); await page.waitForTimeout(1500);
await page.keyboard.press('f'); await page.waitForTimeout(3000);   // 全体表示
await context.close();
await browser.close();
console.log(fs.readdirSync(outDir));
