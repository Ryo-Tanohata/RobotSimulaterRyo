// src/ を 1 つの JavaScript (dist/app.js) にまとめる。index.html をダブルクリックで開けるようにするため。
import { build } from 'esbuild';
await build({
  entryPoints: ['src/main.js'],
  bundle: true,
  format: 'iife',
  target: 'es2020',
  outfile: 'dist/app.js',
  minify: true,
  sourcemap: false,
  logLevel: 'info',
});
