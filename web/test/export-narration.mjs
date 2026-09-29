// 台本のナレーションを書き出す
//   node test/export-narration.mjs v3 md   → 確認用の原稿 (Markdown)
//   node test/export-narration.mjs v3 json → 音声合成用のセリフ一覧 (tools/voicevox/synth.py に渡す)
import { SCENES, EXTRA_SCRIPTS, STAGE_LABELS } from '../src/film-script.js';
const [name = 'v3', format = 'md'] = process.argv.slice(2);
const scenes = name === 'main' ? SCENES : EXTRA_SCRIPTS[name];
const id = (i, k) => `${name}_${String(i).padStart(2, '0')}_${k}`;
const strip = (h) => (h || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
if (format === 'json') {
  const lines = scenes.flatMap((s, i) => (s.narration || []).map((text, k) => ({ id: id(i, k), text })));
  console.log(JSON.stringify(lines, null, 1));
} else {
  let md = `# ナレーション原稿 (${name})\n\n話者: VOICEVOX:ずんだもん (ノーマル)。字幕にも同じ文を表示します。\n\n| # | 画面 | ナレーション |\n|---|---|---|\n`;
  scenes.forEach((s, i) => {
    const screen = s.kind === 'card' ? `【文字】${strip(s.title)}` :
      `${STAGE_LABELS[s.badgeStage ?? s.brainStage ?? s.stage] || s.kind} ${s.gen !== undefined ? `(世代 ${s.gen})` : ''}`.trim();
    md += `| ${i + 1} | ${screen} | ${(s.narration || []).join('<br>')} |\n`;
  });
  console.log(md);
}
