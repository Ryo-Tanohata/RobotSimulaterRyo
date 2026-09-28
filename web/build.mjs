// src/ を 1 つの JavaScript にまとめる (index.html / film.html をダブルクリックで開けるようにするため)。
//   dist/app.js       … シミュレータ (index.html)
//   dist/film.js      … 上映ページ (film.html)
//   dist/film-data.js … 学習結果 (checkpoints/*.json) を読み込むためのデータ
import { build } from 'esbuild';
import fs from 'node:fs';

const common = { bundle: true, format: 'iife', target: 'es2020', minify: true, logLevel: 'info' };
await build({ ...common, entryPoints: ['src/main.js'], outfile: 'dist/app.js' });
await build({ ...common, entryPoints: ['src/film.js'], outfile: 'dist/film.js' });

const data = {};
for (const stage of ['walk', 'rough', 'obstacles']) {
  const f = `checkpoints/${stage}.json`;
  if (fs.existsSync(f)) data[stage] = JSON.parse(fs.readFileSync(f, 'utf8'));
}
fs.writeFileSync('dist/film-data.js', `window.FILM_DATA = ${JSON.stringify(data)};\n`);
console.log('dist/film-data.js:', Object.keys(data).join(', ') || '(学習データなし)');
