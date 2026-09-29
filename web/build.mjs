// src/ を 1 つの JavaScript にまとめる (index.html / film.html をダブルクリックで開けるようにするため)。
//   dist/app.js       … シミュレータ (index.html)
//   dist/film.js      … 上映ページ (film.html)
//   dist/film-data.js … 学習結果 (checkpoints/*.json) を読み込むためのデータ
import { build } from 'esbuild';
import fs from 'node:fs';

// 同梱するライブラリのライセンス表示 (MIT / Apache-2.0 の条件: 著作権表示とライセンス文を添える)
const banner = '/*! 四足ロボット シミュレータ (Web 版)。同梱ライブラリ: three.js (MIT License, Copyright (c) 2010-2026 three.js authors), ' +
  'Rapier / @dimforge/rapier3d-compat (Apache License 2.0, Copyright 2020 Dimforge EURL)。ライセンス全文は THIRD_PARTY_LICENSES.txt を参照 */';
const common = { bundle: true, format: 'iife', target: 'es2020', minify: true, logLevel: 'info', banner: { js: banner }, legalComments: 'eof' };
await build({ ...common, entryPoints: ['src/main.js'], outfile: 'dist/app.js' });
await build({ ...common, entryPoints: ['src/film.js'], outfile: 'dist/film.js' });

// 第三者ライセンスの全文を node_modules から集めて 1 ファイルにする
const libs = [
  ['three.js', 'three', 'https://threejs.org/'],
  ['Rapier (@dimforge/rapier3d-compat)', '@dimforge/rapier3d-compat', 'https://rapier.rs/'],
];
let notices = 'このフォルダの dist/*.js には、以下のオープンソースソフトウェアが含まれています。\n' +
  'This software bundles the following open source components.\n\n';
for (const [name, pkg, url] of libs) {
  const meta = JSON.parse(fs.readFileSync(`node_modules/${pkg}/package.json`, 'utf8'));
  notices += `${'='.repeat(78)}\n${name} ${meta.version} — ${meta.license}\n${url}\n${'='.repeat(78)}\n\n`;
  notices += fs.readFileSync(`node_modules/${pkg}/LICENSE`, 'utf8').trim() + '\n\n';
}
fs.writeFileSync('THIRD_PARTY_LICENSES.txt', notices);

const data = {};
for (const stage of ['walk', 'posture', 'rough', 'obstacles', 'steer', 'wall1', 'walls3', 'imitate', 'natural']) {
  const f = `checkpoints/${stage}.json`;
  if (fs.existsSync(f)) data[stage] = JSON.parse(fs.readFileSync(f, 'utf8'));
}
fs.writeFileSync('dist/film-data.js', `window.FILM_DATA = ${JSON.stringify(data)};\n`);
console.log('dist/film-data.js:', Object.keys(data).join(', ') || '(学習データなし)');
