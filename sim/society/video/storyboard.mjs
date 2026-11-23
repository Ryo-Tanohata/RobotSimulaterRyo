// 絵コンテ (2026-11-23 本人「まず動画を作る時に絵コンテを作るようにしたいです」): 本番の前に、ナレーションの 1 文ごとに 1 枚の絵を撮って並べ、本人に見てもらう。
//   node storyboard.mjs <ナレーション.json> <音声フォルダ> <出力の名前 (拡張子なし)>   (環境変数は make_video.mjs と同じ: SLIM・DAYS・PEOPLE・CHROME・LIBS・GPU など)
//   ふつうは render_all.sh から:  bash render_all.sh --storyboard D1V
// make_video.mjs を STORYBOARD モードで動かす (ページの用意・カメラ・字幕は動画と同じ。文のまん中の 1 枚、1280×720)。そのあと:
//   <出力>.html … 1 行 1 カット (番号・秒・村の日と時刻・ナレーション・カメラ・映っている人・人ごとの活動と動き・絵・気になる点)。絵を中に入れるので git に入れない
//   storyboards/storyboard_<名前>.json … 絵のない小さな版 (git に入れてよい)
// 気になる点は自動で調べる: 人が小さい・画面の外・はみ出し・話に出る人が映っていない・名前の札の重なり・字幕や知らせが人にかかる
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const [narr, voice, outName] = process.argv.slice(2);
if (!outName) { console.error("usage: node storyboard.mjs <narration.json> <voice dir> <out name>"); process.exit(1); }
const item = path.basename(outName).replace(/^storyboard_/, "");
const raw = `${outName}.raw`;
const r = spawnSync("node", [path.join(HERE, "make_video.mjs"), narr, voice, outName], { stdio: "inherit", env: { ...process.env, STORYBOARD: raw } });
if (r.status !== 0) process.exit(r.status || 1);
const SB = JSON.parse(fs.readFileSync(`${raw}.json`, "utf8"));
fs.unlinkSync(`${raw}.json`);

const inter = (a, b) => (a && b ? Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1])) : 0);
const area = (a) => (a[2] - a[0]) * (a[3] - a[1]);
const MOTION = { idle: "立つ", walk: "歩く", search: "歩きさがす", look: "地面をさがす", pick: "拾う", probe: "両手で調べる", reach: "身をのり出す", stretch: "背のび",
  talk: "話す", give: "手渡す", eat: "食べる", lie: "横になる" };

function check(c) {
  const W = c.w, H = c.h, notes = [], inView = [], sizes = [];
  const people = c.people.filter((p) => p.shown);
  for (const p of people) {
    const hgt = p.foot[1] - p.head[1], wid = Math.max(12, hgt * 0.3);
    p.box = [Math.min(p.head[0], p.foot[0]) - wid, p.head[1], Math.max(p.head[0], p.foot[0]) + wid, p.foot[1]];
    p.px = Math.round(hgt);
    const behind = p.head[2] > 1 || p.foot[2] > 1;
    const outside = behind || p.box[2] < 0 || p.box[0] > W || p.box[3] < 0 || p.box[1] > H;
    p.inView = !outside;
    if (outside) continue;
    inView.push(p.name); sizes.push(hgt);
    if (p.box[0] < 0 || p.box[2] > W || p.box[1] < 0 || p.box[3] > H) notes.push(`${p.name} が画面からはみ出す`);
    if (hgt < 0.12 * H) notes.push(`${p.name} が小さい (${p.px} px)`);
    if (inter(p.box, c.boxes.caption) > 0.3 * area(p.box)) notes.push(`字幕が ${p.name} にかかる`);
    for (const t of c.boxes.toasts) if (inter(p.box, t) > 0.3 * area(p.box)) { notes.push(`知らせの帯が ${p.name} にかかる`); break; }
  }
  const out = people.filter((p) => !p.inView).map((p) => p.name);
  if (out.length) notes.push(`画面の外: ${out.join("・")}`);
  const named = people.filter((p) => c.text.includes(p.name) && !p.inView).map((p) => p.name);
  if (named.length) notes.push(`話に出る ${named.join("・")} が映っていない`);
  const L = people.filter((p) => p.inView && p.label);
  for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++)
    if (inter(L[i].label, L[j].label) > 0.2 * Math.min(area(L[i].label), area(L[j].label))) notes.push(`名前の札が重なる: ${L[i].name} と ${L[j].name}`);
  const med = sizes.length ? sizes.sort((a, b) => a - b)[Math.floor(sizes.length / 2)] : 0;
  const framing = !sizes.length ? "人なし" : med > 0.45 * H ? "寄り" : med > 0.2 * H ? "中くらい" : "引き";
  return { notes, inView, framing, med: Math.round(med) };
}

const rows = SB.cuts.map((c) => {
  const k = check(c);
  const doing = c.people.filter((p) => p.shown).map((p) => ({ name: p.name, activity: p.activity, motion: p.motion, motion_ja: MOTION[p.motion] || null, px: p.inView ? p.px : 0, inView: p.inView }));
  return { cut: c.cut, id: c.id, start: c.start, end: c.end, at: c.at, clock: c.clock, text: c.text,
    camera: { framing: k.framing, dist: +c.camera.dist.toFixed(1), person_px: k.med, in_view: k.inView },
    featured: c.people.filter((p) => p.shown && (c.text.includes(p.name) || p.bubble || (c.featured || []).includes(p.name))).map((p) => p.name),
    doing, notes: k.notes, jpg: c.jpg };
});

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (x) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[x]));
const html = `<!doctype html><meta charset="utf-8"><title>絵コンテ ${esc(item)}</title>
<style>body{font-family:sans-serif;margin:16px;background:#f4f2ec;color:#222}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:6px;vertical-align:top;font-size:14px;background:#fff}
th{background:#e4e0d4;position:sticky;top:0}img{width:420px;display:block}.n{color:#a33}.ok{color:#383}.s{white-space:nowrap}</style>
<h1>絵コンテ ${esc(item)}</h1>
<p>長さ ${SB.duration.toFixed(1)} 秒・${rows.length} カット (ナレーションの 1 文に 1 枚。絵は文のまん中の時刻)。${SB.people ? "人のモデル" : "棒の人"}。
見たら「よい」か、直したいところ (カットの番号と中身) を伝えてください。本番はそのあと撮ります。</p>
<table><tr><th>#</th><th>秒</th><th>村の日と時刻</th><th>ナレーション</th><th>カメラ</th><th>人 (活動・動き)</th><th>絵</th><th>気になる点</th></tr>
${rows.map((r) => `<tr><td>${r.cut}</td><td class="s">${r.start.toFixed(1)}–${r.end.toFixed(1)}</td><td>${esc(r.clock)}</td><td>${esc(r.text)}</td>
<td>${esc(r.camera.framing)}<br>距離 ${r.camera.dist}<br>人の高さ ${r.camera.person_px} px<br>映る: ${esc(r.camera.in_view.join("・") || "なし")}</td>
<td>${r.doing.map((d) => `${r.featured.includes(d.name) ? "<b>" : ""}${esc(d.name)}${r.featured.includes(d.name) ? "</b>" : ""}: ${esc(d.activity || "")}${d.motion ? ` / ${esc(d.motion_ja || d.motion)}` : ""}${d.inView ? "" : " (画面の外)"}`).join("<br>")}</td>
<td><img src="data:image/jpeg;base64,${r.jpg}"></td><td>${r.notes.length ? r.notes.map((n) => `<div class="n">${esc(n)}</div>`).join("") : '<span class="ok">なし</span>'}</td></tr>`).join("\n")}
</table>`;
fs.mkdirSync(path.dirname(outName), { recursive: true });
fs.writeFileSync(`${outName}.html`, html);
const small = path.join(HERE, "storyboards", `storyboard_${item}.json`);
fs.mkdirSync(path.dirname(small), { recursive: true });
fs.writeFileSync(small, JSON.stringify({ item, duration: +SB.duration.toFixed(2), people: SB.people, cuts: rows.map(({ jpg, ...r }) => r) }, null, 1) + "\n");
console.log(`→ ${outName}.html (${(html.length / 1e6).toFixed(1)} MB)\n→ ${small}`);
console.log(`気になる点: ${rows.reduce((a, r) => a + r.notes.length, 0)} 件 (${rows.filter((r) => r.notes.length).length} カット)`);
