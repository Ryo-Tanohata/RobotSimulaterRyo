// 川辺の五人: アプリの「3D で見る」を 1 コマずつ撮って、ずんだもんのナレーション付きの動画を作る。
//   node make_video.mjs <ナレーション.json> <音声フォルダ (durations.json と nXX.wav)> <出力の名前 (拡張子なし)> [最初の日] [最後の日]
// 出力: <名前>_silent.mp4 (映像だけ) と <名前>.timeline.json (ナレーションの時刻、tools/audio/mix.py 用)
// ナレーションの各文は、その日のその場面 (dawn / go / work / back / eve / night) で流す。場面は文の長さに合わせて伸ばす。
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.join(HERE, "..", "app"), DATA = path.join(HERE, "..", "data");
const [narrPath, voiceDir, outName, fromArg, toArg] = process.argv.slice(2);
const FPS = 25, W = 1280, H = 720;
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const lines = JSON.parse(fs.readFileSync(narrPath, "utf8"));
const durs = JSON.parse(fs.readFileSync(path.join(voiceDir, "durations.json"), "utf8"));
const CREDIT = "ナレーション: VOICEVOX:ずんだもん<br>描画: three.js (MIT License)<br>効果音・BGM: プログラムで自作";

// アプリのファイルをこの PC の中だけで配る (file:// では JSON を読めないため)
const server = http.createServer((req, res) => {
  const name = decodeURIComponent(req.url.split("?")[0]).replace(/^\//, "") || "index.html";
  const file = name === "app_data.json" ? path.join(DATA, name) : path.join(APP, name);
  if (!fs.existsSync(file)) { res.writeHead(404); return res.end(); }
  const type = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json", ".mp4": "video/mp4" }[path.extname(file)] || "application/octet-stream";
  res.writeHead(200, { "content-type": type });
  if (name === "index.html") return res.end("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>" + fs.readFileSync(file, "utf8"));
  fs.createReadStream(file).pipe(res);
}).listen(0);
const port = server.address().port;

const VIDEO_CSS = `
  [hidden] { display: none !important; }
  .wrap > *:not(#p-r3) { display: none !important; }
  #p-r3 { position: fixed; inset: 0; padding: 0; border: 0; border-radius: 0; }
  #p-r3 > h2, #p-r3 > .explain, .r3-bar { display: none !important; }
  .r3-stage { position: fixed; inset: 0; aspect-ratio: auto; border-radius: 0; }
  .r3-clock { font-size: 18px; padding: 4px 12px; }
  .r3-toast { top: 52px; bottom: auto; left: auto; right: 14px; justify-items: end; font-size: 16px; }
  .r3-label { font-size: 16px; } .r3-label .b { font-size: 16px; max-width: 18em; }
  .v-cap { position: absolute; left: 50%; bottom: 26px; transform: translateX(-50%); width: max-content; max-width: 84%;
    background: rgba(12, 16, 13, 0.78); color: #fff; font-size: 26px; line-height: 1.5; padding: 8px 20px; border-radius: 10px; text-align: center; }
  .v-title { position: absolute; inset: 0; display: grid; place-items: center; font-family: var(--display); font-size: 80px; color: #fff;
    text-shadow: 0 4px 18px rgba(0,0,0,.6); letter-spacing: 0.05em; }
  .v-credit { position: absolute; inset: 0; display: grid; place-items: center; background: rgba(12, 16, 13, 0.82); color: #fff; font-size: 28px; line-height: 2; text-align: center; }
`;

const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--no-sandbox", "--hide-scrollbars", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage();
await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
page.on("pageerror", (e) => console.error("page error:", e.message));
await page.goto(`http://localhost:${port}/index.html`, { waitUntil: "networkidle0" });
await page.addStyleTag({ content: VIDEO_CSS });
await page.waitForFunction(() => document.querySelector(".r3-stage canvas"), { timeout: 60000 });
await page.evaluate(() => {
  const st = document.querySelector(".r3-stage");
  for (const c of ["v-cap", "v-title", "v-credit"]) { const d = document.createElement("div"); d.className = c; d.hidden = true; st.appendChild(d); }
  window.dispatchEvent(new Event("resize"));
  Replay3D.setAutoCamera(true);
});
await new Promise((r) => setTimeout(r, 800));

const from = Number(fromArg || 1), to = Number(toArg || Math.max(...lines.map((l) => l.day)));

// 日ごとに場面の長さを決め、ナレーションの時刻を並べる
const plan = [], narration = [];
let offset = 0;
for (let d = from; d <= to; d++) {
  const base = await page.evaluate((d) => Replay3D.timeline(d), d);
  const secs = {};
  for (const s of base.segs) {
    const mine = lines.filter((l) => l.day === d && l.seg === s.key);
    const need = mine.reduce((a, l) => a + durs[l.id] + 0.45, 0) + (mine.length ? 1.0 : 0) + (d === to && s.key === "night" ? 6 : 0);
    secs[s.key] = Math.max(s.v1 - s.v0, need);
  }
  await page.evaluate((d, secs) => Replay3D.setSegments(d, secs), d, secs);
  const tl = await page.evaluate((d) => Replay3D.timeline(d), d);
  for (const s of tl.segs) {
    let t = s.v0 + 0.6;
    for (const l of lines.filter((l) => l.day === d && l.seg === s.key)) {
      narration.push({ id: l.id, text: l.text, start: offset + t, duration: durs[l.id] });
      t += durs[l.id] + 0.45;
    }
  }
  plan.push({ day: d, start: offset, total: tl.total, night0: tl.segs.find((s) => s.key === "night").v0 });
  offset += tl.total;
}
const total = offset;
fs.writeFileSync(`${outName}.timeline.json`, JSON.stringify({ fps: FPS, duration: total, narration, events: [], days: plan }, null, 1));
console.log(`長さ ${total.toFixed(1)} 秒、${Math.round(total * FPS)} コマ`);

const ff = spawn("ffmpeg", ["-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium", "-movflags", "+faststart", `${outName}_silent.mp4`], { stdio: ["pipe", "inherit", "inherit"] });
const t0 = Date.now();
const N = Math.round((process.env.LIMIT ? Math.min(total, Number(process.env.LIMIT)) : total) * FPS);  // LIMIT=秒 で試し撮り
for (let f = 0; f < N; f++) {
  const t = f / FPS;
  const P = plan.filter((p) => p.start <= t).pop();
  const v = t - P.start;
  const cap = narration.find((n) => t >= n.start && t < n.start + n.duration + 0.3);
  const title = v < 2.2 ? `${P.day} 日目` : "";
  const credit = P.day === to && P.total - v < 5.5;
  await page.evaluate((d, v, cap, title, credit, CREDIT) => {
    Replay3D.seek(d, v);
    const st = document.querySelector(".r3-stage");
    const c = st.querySelector(".v-cap"); c.hidden = !cap; if (cap) c.textContent = cap;
    const ti = st.querySelector(".v-title"); ti.hidden = !title; ti.textContent = title;
    const cr = st.querySelector(".v-credit"); cr.hidden = !credit; cr.innerHTML = CREDIT;
  }, P.day, v, cap ? cap.text : "", title, credit, CREDIT);
  const buf = await page.screenshot({ type: "jpeg", quality: 90 });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  if (f % (FPS * 10) === 0) console.log(`${(t).toFixed(0)} / ${total.toFixed(0)} 秒 (${((Date.now() - t0) / 1000).toFixed(0)} 秒経過)`);
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
await browser.close();
server.close();
console.log(`→ ${outName}_silent.mp4`);
