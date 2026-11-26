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
const APP = path.join(HERE, "..", "app"), DATA = process.env.DATA_DIR || path.join(HERE, "..", "data");  // DATA_DIR: 写しのデータで試し撮りするとき
const [narrPath, voiceDir, outName, fromArg, toArg] = process.argv.slice(2);
// FPS=コマ数/秒 (2026-11-23、D1V から): クラウドの CPU で撮るときに、コマを減らす (render_all.sh があとでコマを重ねて 24 コマ/秒にする)。ないときは前と同じ 25
const FPS = Number(process.env.FPS) || 25, W = 1280, H = 720;
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const lines = JSON.parse(fs.readFileSync(narrPath, "utf8"));
const durs = JSON.parse(fs.readFileSync(path.join(voiceDir, "durations.json"), "utf8"));
// 日付の注釈 (2026-10-09 本人の希望): 日付は「10年31日目」(年は過ぎた年の数。最初の年は 0年) と表すが、この世界の 1 年は現実より短い。最初の数秒と最後のクレジットに出す
const YEAR_NOTE = "※ この世界の 1 年は 120 日 (夏・秋・冬・春が 30 日ずつ) で、現実の 1 年とは違います。「10年31日目」は、10 年たった年の 31 日目 (最初の年は 0年)";
// PEOPLE=フォルダ (2026-11-23、D1P から): 棒の人の代わりに、そのフォルダの人のモデル (<名前>.glb と .json) を動かす (app/replay3d_people.js)
// PEOPLE_CREDIT (D1V から): クレジットの「人のモデル」の行 (ないときは D1P と同じ「VRoid Studio で作成」)
const PEOPLE = process.env.PEOPLE || "";
const CREDIT = "ナレーション: VOICEVOX:ずんだもん<br>描画: three.js (MIT License)<br>効果音・BGM: プログラムで自作"
  + (PEOPLE ? `<br>人のモデル: ${process.env.PEOPLE_CREDIT || "VRoid Studio で作成"}<br>動き: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu)` : "")
  + `<br><span style="font-size:20px">${YEAR_NOTE}</span>`;

// SLIM=1 (2026-11-22、1 日目の撮り直し D1 から): 撮る日 (DAYS) に要る分だけの小さな app_data.json を、メモリの中で作って配る。
// 全部のデータ (65 MB・3,855 人) だと、ページの用意に 3 分ほど、1 コマにも時間がかかるため。ファイルには書かない (data/ は読むだけ)。
// 人は D.people の頭から、撮る日にいる人の最後までをそのまま残す (並びと色が全部のデータのときと同じになるように)。
// 出来事・再生の行・グラフの数・家・しまった年の一覧は、撮る日まで (か、撮る日だけ) に切る。地図・草木・掟・ほかの村などはそのまま
function slimData(days) {
  const D = JSON.parse(fs.readFileSync(path.join(DATA, "app_data.json"), "utf8"));
  const want = new Set(days), maxDay = Math.max(...days), minDay = Math.min(...days);
  let last = 0;
  D.people.forEach((p, i) => {
    const here = days.some((d) => d >= (p.since || 0) && (p.born_day == null || p.born_day <= d) && !(p.left && p.left < d));
    if (here) last = i;
  });
  const S = { ...D, people: D.people.slice(0, last + 1) };
  const names = new Set(S.people.map((p) => p.name));
  S.resumes = (D.resumes || []).filter((r) => names.has(r.name));
  S.events = (D.events || []).filter((e) => want.has(e.day));
  S.days = Object.fromEntries(Object.entries(D.days || {}).filter(([d]) => want.has(Number(d))));
  S.stats = (D.stats || []).filter((x) => x.day <= maxDay);
  S.houses = (D.houses || []).filter((v) => v.start <= maxDay);
  if (D.archive) {
    const ys = new Set(days.filter((d) => d < D.archive.since).map((d) => Math.floor(d / 120)));
    S.archive = { ...D.archive, years: D.archive.years.filter((y) => ys.has(y.year)), keep: (D.archive.keep || []).filter((e) => e.day <= maxDay) };
  }
  // 育つ (2026-11-25、v2 の植物から): 撮る日までの「木の実の木が育った」の日と文 (しまった年は data/archive/events_YYYY.jsonl から)。前の動画は使わない
  S.grow = [];
  for (let y = 0; y <= Math.floor(maxDay / 120); y++) {
    const f = path.join(DATA, "archive", `events_${String(y).padStart(4, "0")}.jsonl`);
    if (!fs.existsSync(f)) continue;
    for (const ln of fs.readFileSync(f, "utf8").split("\n")) if (ln.includes('"育つ"')) { const e = JSON.parse(ln); if (e.type === "育つ" && e.day <= maxDay) S.grow.push({ day: e.day, text: e.text }); }
  }
  for (const e of D.events || []) if (e.type === "育つ" && e.day <= maxDay && !S.grow.some((g) => g.day === e.day && g.text === e.text)) S.grow.push({ day: e.day, text: e.text });
  // 飼っているヤギの数 (2026-11-25、v2 の動物から): 季節の終わりごとの頭数 (records/season_village.jsonl)。前の動画は使わない
  S.goats = [];
  const sv = path.join(DATA, "records", "season_village.jsonl");
  if (fs.existsSync(sv)) for (const ln of fs.readFileSync(sv, "utf8").split("\n")) {
    if (!ln) continue;
    const r = JSON.parse(ln);
    if (r.season_end_day <= maxDay + 120 && r.goats) S.goats.push({ from: r.season_start_day, to: r.season_end_day, n: r.goats.count || 0 });
  }
  // その日のヤギの数 (2026-11-26 見直し K9: 季節の終わりの数でまとめると、季節のとちゅうで捕まえたヤギが先に写る):
  // 前の季節の終わりの数 + その季節のはじめからその日までの出来事 (捕まえた +1・生まれた +N・いなくなった/つぶした −N)
  const goatEv = [];
  for (let y = 0; y <= Math.floor(maxDay / 120); y++) {
    const f = path.join(DATA, "archive", `events_${String(y).padStart(4, "0")}.jsonl`);
    if (!fs.existsSync(f)) continue;
    for (const ln of fs.readFileSync(f, "utf8").split("\n")) if (ln.includes('"type":"ヤギ"')) { const e = JSON.parse(ln); if (e.day <= maxDay) goatEv.push(e); }
  }
  for (const e of D.events || []) if (e.type === "ヤギ" && e.day <= maxDay && !goatEv.some((g) => g.id === e.id)) goatEv.push(e);
  const dGoat = (e) => {
    const t = e.text || "";
    if (/子ヤギ.*を捕まえて/.test(t)) return 1;
    let m = /子ヤギが (\d+) 頭生まれた/.exec(t); if (m) return +m[1];
    m = /ヤギ (\d+) 頭(がいなくなった|をつぶした)/.exec(t); if (m) return -m[1];
    return 0;
  };
  S.goatDay = {};
  for (const d of days) {
    const sn = S.goats.find((g) => d >= g.from && d <= g.to);
    if (!sn) continue;
    const prev = S.goats.find((g) => g.to === sn.from - 1);
    let n = prev ? prev.n : 0;
    for (const e of goatEv) if (e.day >= sn.from && e.day <= d) n += dGoat(e);
    S.goatDay[d] = Math.max(0, n);
  }
  const out = JSON.stringify(S);
  console.log(`SLIM: app_data.json ${(fs.statSync(path.join(DATA, "app_data.json")).size / 1e6).toFixed(1)} MB → ${(out.length / 1e6).toFixed(1)} MB (人 ${S.people.length}・日 ${minDay}〜${maxDay})`);
  return out;
}
const SLIM = process.env.SLIM && process.env.DAYS ? slimData(process.env.DAYS.split(",").map(Number)) : null;

// アプリのファイルをこの PC の中だけで配る (file:// では JSON を読めないため)
const server = http.createServer((req, res) => {
  const name = decodeURIComponent(req.url.split("?")[0]).replace(/^\//, "") || "index.html";
  // しまった年の出来事と再生の行 (archive/、2026-10-10) も、app_data.json と同じデータの場所から配る
  const file = name === "app_data.json" || name.startsWith("archive/") ? path.join(DATA, name)
    : PEOPLE && name.startsWith("people/") ? path.join(PEOPLE, path.basename(name)) : path.join(APP, name);
  // アプリに入れた動画は撮影に使わない (読み込みが終わらず、ページの読み込み待ちが切れるため)
  if (!fs.existsSync(file) || name.endsWith(".mp4")) { res.writeHead(404); return res.end(); }
  const type = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json", ".jsonl": "application/x-ndjson", ".mp4": "video/mp4", ".glb": "model/gltf-binary" }[path.extname(file)] || "application/octet-stream";
  res.writeHead(200, { "content-type": type });
  if (SLIM && name === "app_data.json") return res.end(SLIM);
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
  .v-cap { z-index: 50; position: absolute; left: 50%; bottom: 26px; transform: translateX(-50%); width: max-content; max-width: 84%;
    background: rgba(12, 16, 13, 0.78); color: #fff; font-size: 26px; line-height: 1.5; padding: 8px 20px; border-radius: 10px; text-align: center; }
  .v-title { z-index: 50; position: absolute; inset: 0; display: grid; place-items: center; font-family: var(--display); font-size: 80px; color: #fff;
    text-shadow: 0 4px 18px rgba(0,0,0,.6); letter-spacing: 0.05em; }
  .v-credit { z-index: 60; position: absolute; inset: 0; display: grid; place-items: center; background: rgba(12, 16, 13, 0.82); color: #fff; font-size: 28px; line-height: 2; text-align: center; }
  .v-note { z-index: 50; position: absolute; left: 14px; top: 56px; max-width: 46%; background: rgba(12, 16, 13, 0.72); color: #fff; font-size: 17px; line-height: 1.5; padding: 4px 12px; border-radius: 8px; }
`;

// GPU=1: 自分の PC の GPU (内蔵 GPU でもよい) で 3D を描く。なければ CPU で描く swiftshader (クラウド用。とても遅い)
const GL_ARGS = process.env.GPU ? ["--ignore-gpu-blocklist", "--enable-gpu-rasterization"] : ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"];
const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", protocolTimeout: 600000, args: ["--no-sandbox", "--hide-scrollbars", ...GL_ARGS] });
const page = await browser.newPage();
await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
page.on("pageerror", (e) => console.error("page error:", e.message));
// LIBS=フォルダ (npm で入れた three・marked の node_modules がある所): CDN に出られない環境では、CDN の代わりにそこから読む。フォントは使わない
if (process.env.LIBS) {
  const LOCAL = { "three.min.js": "three/build/three.min.js", "OrbitControls.js": "three/examples/js/controls/OrbitControls.js", "GLTFLoader.js": "three/examples/js/loaders/GLTFLoader.js", "marked.min.js": "marked/marked.min.js" };
  await page.setRequestInterception(true);
  page.on("request", (req) => {
    const u = new URL(req.url());
    if (u.hostname === "localhost") return req.continue();
    const key = Object.keys(LOCAL).find((k) => u.pathname.endsWith("/" + k));
    if (!key) return req.abort();
    req.respond({ status: 200, contentType: "text/javascript", body: fs.readFileSync(path.join(process.env.LIBS, "node_modules", LOCAL[key])) });
  });
}
// 読み込みの終わりを待つ (2026-10-08: 「通信が止まるまで」は、Society 2.0 のデータで終わらないことがあったため、load と 3D の画面を待つ)
// (2026-11-22: Society 3.0 のデータ 65 MB (700 人) で、本人の PC でも、データを読んだあと 3D がそろうまで 3 分ほどページが手をはなせない。待ちを 10 分に)
await page.goto(`http://localhost:${port}/index.html`, { waitUntil: "load", timeout: 600000 });
await page.waitForFunction(() => window.Replay3D && window.THREE, { timeout: 600000 });
await page.addStyleTag({ content: VIDEO_CSS });
// HIDE_TOASTS=1 (D1V から。本人の選んだ案 C): 上に重なる出来事の帯を出さない (代わりに PEOPLE_VIEW の bubbles で、した人の頭の上に短い吹き出し)
if (process.env.HIDE_TOASTS) await page.addStyleTag({ content: ".r3-toast { visibility: hidden !important; }" });
await page.waitForFunction(() => document.querySelector(".r3-stage canvas"), { timeout: 600000 });
await page.evaluate(() => {
  const st = document.querySelector(".r3-stage");
  for (const c of ["v-cap", "v-title", "v-credit", "v-note"]) { const d = document.createElement("div"); d.className = c; d.hidden = true; st.appendChild(d); }
  window.dispatchEvent(new Event("resize"));
  Replay3D.setAutoCamera(true);
});
if (PEOPLE) {  // 人のモデル: three の glb を読む道具と、モデルを動かす replay3d_people.js を足して、モデルを読む
  await page.addScriptTag({ url: "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js" });
  await page.addScriptTag({ url: `http://localhost:${port}/replay3d_people.js` });
  // PEOPLE_CAM={"min":3.5,...} (D1V から): 人に寄るカメラの近さ (replay3d.js の autoCamera が読む。min・add・k・max)。ないときは replay3d_people.js のまま
  // PEOPLE_VIEW={"split":true,"noPlants":true,...} (D1V から): replay3d_people.js の opts (画面を分ける・赤い玉を隠す・カメラの近さ)
  if (process.env.PEOPLE_VIEW) await page.evaluate((o) => Object.assign(Replay3DPeople.opts, o), JSON.parse(process.env.PEOPLE_VIEW));
  if (process.env.PEOPLE_CAM) await page.evaluate((c) => Object.assign(Replay3DPeople.camera, c), JSON.parse(process.env.PEOPLE_CAM));
  const got = await page.evaluate(async () => { const n = await Replay3DPeople.load("people/"); Replay3D.setPeople(Replay3DPeople); return n; });
  console.log(`PEOPLE: ${got.join("・")} (${PEOPLE})`);
}
await new Promise((r) => setTimeout(r, 800));
// NO_RAF=1 (D1V から): アプリの毎フレームの描画 (requestAnimationFrame) を止める。撮るコマは seek が描くので、絵は同じ。
// CPU で描く (swiftshader) ときは、1 コマに描画が 2 回になって倍の時間がかかるため
if (process.env.NO_RAF) await page.evaluate(() => { window.requestAnimationFrame = () => 0; });

const from = Number(fromArg || 1), to = Number(toArg || Math.max(...lines.map((l) => l.day)));
// DAYS=21,28,29 のように、飛び飛びの日をつなぐこともできる
const dayList = process.env.DAYS ? process.env.DAYS.split(",").map(Number) : Array.from({ length: to - from + 1 }, (_, i) => from + i);
const lastDay = dayList[dayList.length - 1];
await page.evaluate((ds) => Replay3D.need(ds), dayList);  // しまった年の日は、その年のファイルを先に読む (2026-10-10)
const LABEL = {};  // 日ごとの「10年31日目」(アプリと同じ書き方。replay3d.js の dayLabel)
for (const d of dayList) LABEL[d] = await page.evaluate((d) => Replay3D.dayLabel(d), d);
// 人の多い日 (2026-11-22): 3D の名前は、その日のナレーションに出る人 (と話している人・知らせに出る人) だけにする
for (const d of dayList) await page.evaluate((d, texts) => Replay3D.setFeatured(d, texts.flatMap((t) => Replay3D.namesIn(t))), d, lines.filter((l) => l.day === d).map((l) => l.text));

// 日ごとに場面の長さを決め、ナレーションの時刻を並べる
const plan = [], narration = [];
let offset = 0;
for (const d of dayList) {
  const base = await page.evaluate((d) => Replay3D.timeline(d), d);
  const secs = {};
  for (const s of base.segs) {
    const mine = lines.filter((l) => l.day === d && l.seg === s.key);
    const need = mine.reduce((a, l) => a + durs[l.id] + 0.45, 0) + (mine.length ? 1.0 : 0) + (d === lastDay && s.key === "night" ? 6 : 0);
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
// 人のモデルで画面を分けるとき (D1V): カット (ナレーションの 1 文) の始まりを渡す。分け方はカットの途中では変えない
if (PEOPLE) {
  const cuts = {};
  for (const n of narration) { const P = plan.filter((p) => p.start <= n.start + 1e-6).pop(); (cuts[P.day] = cuts[P.day] || []).push(n.start - P.start); }
  await page.evaluate((c) => { if (window.Replay3DPeople) Replay3DPeople.opts.cuts = c; }, cuts);
}
fs.writeFileSync(`${outName}.timeline.json`, JSON.stringify({ fps: FPS, duration: total, narration, events: [], days: plan }, null, 1));
console.log(`長さ ${total.toFixed(1)} 秒、${Math.round(total * FPS)} コマ`);

// FROM_SEC・TO_SEC・PART=出力ファイル: その区間だけ撮る (途中で止まっても、撮り終えた区間を残してつなげるため。2026-10-07)
// 動画の t 秒の絵を出す (3D・字幕・日付の大きな字・クレジット・注釈)。撮るときと絵コンテ (STORYBOARD) で同じもの
async function showAt(t) {
  const P = plan.filter((p) => p.start <= t).pop();
  const v = t - P.start;
  const cap = narration.find((n) => t >= n.start && t < n.start + n.duration + 0.3);
  const title = v < 2.2 ? LABEL[P.day] : "";
  const credit = P.day === lastDay && P.total - v < 5.5;
  const note = t < 10 && !credit;  // 日付の注釈は最初の 10 秒
  await page.evaluate((d, v, cap, title, credit, CREDIT, note, YEAR_NOTE) => {
    Replay3D.seek(d, v);
    const st = document.querySelector(".r3-stage");
    const c = st.querySelector(".v-cap"); c.hidden = !cap; if (cap) c.textContent = cap;
    const ti = st.querySelector(".v-title"); ti.hidden = !title; ti.textContent = title;
    const cr = st.querySelector(".v-credit"); cr.hidden = !credit; cr.innerHTML = CREDIT;
    const no = st.querySelector(".v-note"); no.hidden = !note; no.textContent = YEAR_NOTE;
  }, P.day, v, cap ? cap.text : "", title, credit, CREDIT, note, YEAR_NOTE);
  return P;
}

// STORYBOARD=出力の名前 (2026-11-23、絵コンテ。storyboard.mjs から): ナレーションの 1 文ごとに、文のまん中の 1 枚を撮り、
// カメラ・人の画面の上の場所・名前の札・字幕などの四角といっしょに <名前>.json に書く (画像は base64 の jpg)。動画は作らない。
// カメラは少しずつ寄る動きなので、撮る前に PREROLL 秒 (なければ 2 秒) を、撮らずに進めておく
if (process.env.STORYBOARD) {
  const pre = Number(process.env.PREROLL || 2), cuts = [];
  let last = -1;
  for (const [k, n] of narration.entries()) {
    const tm = n.start + n.duration / 2;
    for (let t = Math.max(last + 1 / FPS, tm - pre); t < tm; t += 1 / FPS) await showAt(t);
    const P = await showAt(tm); last = tm;
    const jpg = await page.screenshot({ type: "jpeg", quality: 80 });
    const info = await page.evaluate(() => {
      const st = document.querySelector(".r3-stage"), box = (e) => { if (!e || e.hidden) return null; const r = e.getBoundingClientRect(); return r.width ? [r.left, r.top, r.right, r.bottom] : null; };
      return { ...Replay3D.inspect(), clock: st.querySelector(".r3-clock").textContent,
        boxes: { caption: box(st.querySelector(".v-cap")), clock: box(st.querySelector(".r3-clock")), note: box(st.querySelector(".v-note")), title: box(st.querySelector(".v-title")),
          toasts: getComputedStyle(st.querySelector(".r3-toast")).visibility === "hidden" ? [] : [...st.querySelectorAll(".r3-toast > *")].map(box).filter(Boolean) } };
    });
    cuts.push({ cut: k + 1, id: n.id, start: +n.start.toFixed(2), end: +(n.start + n.duration).toFixed(2), at: +tm.toFixed(2), day: P.day, text: n.text, ...info, jpg: jpg.toString("base64") });
    console.log(`絵コンテ ${k + 1} / ${narration.length} (${tm.toFixed(1)} 秒)`);
  }
  fs.writeFileSync(`${process.env.STORYBOARD}.json`, JSON.stringify({ name: path.basename(outName), duration: total, fps: FPS, people: !!PEOPLE, cuts }));
  await browser.close(); server.close(); process.exit(0);
}

const OUT = process.env.PART || `${outName}_silent.mp4`;
const ff = spawn("ffmpeg", ["-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium", "-movflags", "+faststart", OUT], { stdio: ["pipe", "inherit", "inherit"] });
const t0 = Date.now();
const N = Math.round((process.env.LIMIT ? Math.min(total, Number(process.env.LIMIT)) : total) * FPS);  // LIMIT=秒 で試し撮り
const F0 = Math.round(Number(process.env.FROM_SEC || 0) * FPS), F1 = process.env.TO_SEC ? Math.min(N, Math.round(Number(process.env.TO_SEC) * FPS)) : N;
if (process.env.PLAN_ONLY) { ff.stdin.end(); await browser.close(); server.close(); process.exit(0); }
// PREROLL=秒 (D1V から): 区間の始まりの前を、撮らずに進めておく (カメラが少しずつ寄る動きを、前の区間の終わりとそろえるため)
for (let f = Math.max(0, F0 - Math.round(Number(process.env.PREROLL || 0) * FPS)); f < F0; f++) {
  const t = f / FPS, P = plan.filter((p) => p.start <= t).pop();
  await page.evaluate((d, v) => Replay3D.seek(d, v), P.day, t - P.start);
}
for (let f = F0; f < F1; f++) {
  const t = f / FPS;
  await showAt(t);
  const buf = await page.screenshot({ type: "jpeg", quality: 90 });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  if (f % (FPS * 10) === 0) console.log(`${(t).toFixed(0)} / ${total.toFixed(0)} 秒 (${((Date.now() - t0) / 1000).toFixed(0)} 秒経過)`);
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
await browser.close();
server.close();
console.log(`→ ${OUT} (${F1 - F0} コマ、1 コマ ${((Date.now() - t0) / 1000 / Math.max(1, F1 - F0)).toFixed(2)} 秒)`);
