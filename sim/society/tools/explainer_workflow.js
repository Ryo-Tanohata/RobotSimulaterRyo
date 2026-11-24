export const meta = {
  name: 'village-explainer',
  description: 'Yearly explainer team for the village report dashboard and the stats page: 4 field explainers in parallel, an editor (top 3), then a fact checker who publishes reports/explain/year<Y>.json',
  whenToUse: 'At year end, after year_report.py made reports/year<Y>.html. args: {"year": Y}',
  phases: [
    { title: 'Data', detail: 'tools/explain_data.py --year Y (skipped with data_ready)' },
    { title: 'Explain', detail: '4 field explainers in parallel (notes, guide bubbles, highlight candidates)' },
    { title: 'Edit', detail: 'editor picks the top 3 and trims the bubbles (video lines only in big-event years)' },
    { title: 'Check', detail: 'fact checker verifies every number, fixes or drops claims, publishes' },
  ],
}
// 解説の係 (2026-11-24 本人が決めた案)。年報のダッシュボードと統計のページを、本人にやさしく説明する。
//   人口の係・くらし・食べ物の係・知恵・技術の係・よその村・町の係 (4 人いっしょに) → まとめ役 (その年の 3 つ) → 事実の確かめ (数をみな確かめて出す)
// 出すもの: sim/society/reports/explain/year<Y>.json (小さい。コミットする)。年報 (tools/year_report.py) と統計のページ (tools/build_stats.py) がこれを読む。
// 動かし方: Workflow で {"year": 250} (本人の PC は {"year": 250, "root": "<リポジトリの場所>", "py": "py -3"})。
//   シェルからは node sim/society/tools/run_workflow.mjs sim/society/tools/explainer_workflow.js '{"year":250}' (年の終わりの手順。HANDOFF.md「解説の係」)。
// args.data_ready: true なら、数を集める歩 (explain_data.py) を飛ばす (先に動かしたとき)。
const Y = Number(args && args.year)
if (!Y) throw new Error('args.year がない (例: {"year": 250})')
const ROOT = (args && args.root) || '/home/user/RobotSimulaterRyo'
const PY = (args && args.py) || 'python3.13'
const DATA = `/tmp/explain_data_${Y}.json`
const DRAFT = `/tmp/explain_draft_${Y}.json`
const TOOL = `${ROOT}/sim/society/tools/explain_data.py`
const OUT = `${ROOT}/sim/society/reports/explain/year${Y}.json`

const TEAMS = [
  { key: 'pop', name: '人口の係', covers: '人口・生まれた子・亡くなった人・平均寿命・年齢の円 (0〜14 歳・15〜54 歳・55 歳〜)・乳児死亡率。フェーズの物差しが d1 (人口の決まりの直し) の年はそれも' },
  { key: 'life', name: 'くらし・食べ物の係', covers: '蓄え・刈った草の種と種まき (seasons の seed/harvested)・仕事の円・食べ物の円・村の生産 (GDP にあたる)・ききん・持ち物の差・掟ともめごと' },
  { key: 'know', name: '知恵・技術の係', covers: '読める大人・手習いの子と教えた日・テクノロジー (はじめて届いた技術・届いた要素の数)・水の作業場の持ち場 (posts)・燃える石・水の道。フェーズの物差しが i4 の年はそれも' },
  { key: 'out', name: 'よその村・町の係', covers: 'よその村との出し入れ (moved・trade_in・partners・known)・川下の町の頼み (t5_rows: posted・done・failed)・子の薬と手当ての書きつけ (child_care)・物の値うち。フェーズの物差しが t5・p4 の年はそれも' },
]
const EXPRS = ['neutral', 'smile', 'concern', 'surprise']

const STYLE = `書き方の決まり (みな守る):
- 読む人は、この村を見守る本人 (専門家ではない)。やさしい日本語で、短く。1 つの文は 40 字くらいまで。
- 専門の言葉 (ジニ係数・乳児死亡率・合計特殊出生率・GDP・人日 など) を使うときは、ひとことで中身をそえる (例: 「人日 (1 人が 1 日働くと 1)」)。
- 数は、集めた数の JSON (${DATA}) にある数だけを使う。自分で計算した数 (差・倍・%) は、JSON の 2 つの数から出せるものだけ。丸めるときは「約」をつける。
- 年は「250年」のように書く。日付は「250年31日目」の形。
- やわらかい口調。こわがらせない。悪い知らせも、事実を短く、やさしく。
- 道具やモデルの名前、AI の話は書かない。`

const NOTES_SCHEMA = {
  type: 'object',
  properties: {
    notes: { type: 'array', description: '図の見かた (a)。keep_note のない、自分の係の図ごとに 1 つ', items: { type: 'object', properties: { chart: { type: 'string' }, text: { type: 'string' } }, required: ['chart', 'text'] } },
    bubbles: { type: 'array', description: '今年のポイント (b)。案内役が話す吹き出し。0〜3 個', items: { type: 'object', properties: { chart: { type: 'string' }, expr: { type: 'string', enum: EXPRS }, text: { type: 'string' }, why: { type: 'string' } }, required: ['chart', 'expr', 'text'] } },
    candidates: { type: 'array', description: 'まとめ役に出す、今年の大事なことの候補 1〜2 個', items: { type: 'object', properties: { title: { type: 'string' }, text: { type: 'string' }, chart: { type: 'string' }, importance: { type: 'integer', minimum: 1, maximum: 5 } }, required: ['title', 'text', 'importance'] } },
    video_points: { type: 'array', description: '大きな年 (big_event.qualifies) のときだけ。動画で話すとよいこと 0〜3 個', items: { type: 'object', properties: { chart: { type: 'string' }, text: { type: 'string' } }, required: ['text'] } },
  },
  required: ['notes', 'bubbles', 'candidates'],
}
const EDIT_SCHEMA = {
  type: 'object',
  properties: {
    top3: { type: 'array', minItems: 1, maxItems: 3, items: { type: 'object', properties: { title: { type: 'string' }, text: { type: 'string' }, chart: { type: 'string' }, expr: { type: 'string', enum: EXPRS } }, required: ['title', 'text', 'expr'] } },
    bubbles: { type: 'array', maxItems: 10, items: { type: 'object', properties: { chart: { type: 'string' }, expr: { type: 'string', enum: EXPRS }, text: { type: 'string' }, team: { type: 'string' } }, required: ['chart', 'expr', 'text'] } },
    video_lines: { type: 'array', description: '大きな年のときだけ。ずんだもんが読む 6〜12 本 (1〜2 分)', items: { type: 'object', properties: { chart: { type: 'string' }, text: { type: 'string' }, say: { type: 'string' } }, required: ['text'] } },
  },
  required: ['top3', 'bubbles'],
}
const CHECK_SCHEMA = {
  type: 'object',
  properties: {
    published: { type: 'boolean' },
    path: { type: 'string' },
    numbers_checked: { type: 'integer' },
    fixed: { type: 'array', items: { type: 'string' } },
    dropped: { type: 'array', items: { type: 'string' } },
    problem: { type: 'string' },
  },
  required: ['published', 'fixed', 'dropped'],
}

if (!(args && args.data_ready)) {
  phase('Data')
  await agent(`Run exactly this one shell command with the Bash tool (timeout 600000 ms), and nothing else. Do not edit any files. Reply with its complete output, verbatim.\n\n\`\`\`\ncd ${ROOT} && ${PY} ${TOOL} --year ${Y} --out ${DATA}\n\`\`\``, { label: 'explain_data', effort: 'low' })
}

phase('Explain')
const team = await parallel(TEAMS.map((t) => () => agent(
  `あなたは川辺の村の年報の「解説の係」のうち、${t.name}です。受け持ち: ${t.covers}。\n\n` +
  `1. Read ツールで ${DATA} を読む (${Y}年の数。this_year と last_year・series_12y (12 年の線)・compo (円の中身)・seasons (季節ごとの種まきと刈った量)・d1_rows・t5_rows・i4_rows・child_care・tech・events・big_event・charts・guide)。ほかのファイルは読まない。\n` +
  `2. charts のうち team が "${t.key}" の図ごとに、出し方を選ぶ:\n` +
  `   (a) 図の見かた: where が "report" か "stats" で keep_note のない図には、かならず 1 つ。図が変わらないかぎり毎年同じに使う文なので、今年の数は入れない (めやすの線の数はよい)。何を表すか・どう読むか・どちらがよい向きか を 1〜2 文 (80 字くらいまで)。spec が図の中身。\n` +
  `   (b) 今年のポイント: 案内役 (いまの村に住む村人。名前は guide.name) が話す吹き出し。今年とくに伝えたいことがある図だけ (0〜3 個。tile の図にもつけてよい)。です・ます のやさしい話し言葉 (「〜ました」「〜ですね」)・60 字くらいまで・今年の数を 1〜2 つ。顔 expr を選ぶ: neutral (ふつう)・smile (よい知らせ)・concern (気がかり)・surprise (おどろき)。\n` +
  `   (c) 動画: big_event.qualifies が true の年だけ。動画で話すとよいことを video_points に (false なら空)。\n` +
  `3. まとめ役に出す候補 (candidates) を 1〜2 個: 見出し (15 字くらい) と 1〜2 文と、大事さ 1〜5。\n\n${STYLE}`,
  { label: t.name, phase: 'Explain', schema: NOTES_SCHEMA })))

const got = TEAMS.map((t, i) => ({ team: t.key, name: t.name, out: team[i] })).filter((x) => x.out)
const missing = TEAMS.filter((t, i) => !team[i]).map((t) => t.name)
if (missing.length) log(`返事がなかった係: ${missing.join('・')} (その係の図の見かたは、確かめの係が書く)`)
const notes = {}
for (const g of got) for (const n of g.out.notes || []) if (!notes[n.chart]) notes[n.chart] = n.text
const bubbles0 = got.flatMap((g) => (g.out.bubbles || []).map((b) => ({ ...b, team: g.team })))
const cands = got.flatMap((g) => (g.out.candidates || []).map((c) => ({ ...c, team: g.name })))
const vpoints = got.flatMap((g) => g.out.video_points || [])

phase('Edit')
const ed = await agent(
  `あなたは川辺の村の年報の「解説の係」のまとめ役です。4 つの分野の係が書いたものを読んで、${Y}年のいちばん大事なこと 3 つを選び、吹き出しを整えます。\n` +
  `数は Read ツールで ${DATA} を読んで確かめてよい (ほかのファイルは読まない)。\n\n` +
  `係の候補:\n${JSON.stringify(cands, null, 1)}\n\n係の吹き出し:\n${JSON.stringify(bubbles0, null, 1)}\n\n` +
  `やること:\n- top3: その年の大事なこと 3 つ (大事な順)。見出し 15 字くらい・文 1〜2 文 (70 字くらいまで)・関係する図 chart・案内役の顔 expr。同じ話を 2 つ入れない。よい話だけ・悪い話だけにかたよらない。\n` +
  `- bubbles: 係の吹き出しを 10 個までにしぼり、言葉をそろえる (同じ図に 2 つ以上なら 1 つに。top3 と同じ話はくり返さない)。team はそのまま。\n` +
  `- video_lines: big_event.qualifies が true のときだけ。ずんだもん (語尾「〜のだ」) が読む 6〜12 本 (合わせて 1〜2 分)。1 本目は「ずんだもんなのだ。」で始め、${Y}年の大きなこと (big_event.reasons) を数で見せる。chart にその文で見せる図。say は読み上げ用 (数字はそのまま、英字はカタカナ)。false なら空。\n` +
  `  動画の候補: ${JSON.stringify(vpoints)}\n\n${STYLE}`,
  { label: 'まとめ役', phase: 'Edit', schema: EDIT_SCHEMA })

phase('Check')
const draft = { year: Y, notes, bubbles: (ed && ed.bubbles) || bubbles0.slice(0, 10), top3: (ed && ed.top3) || [], video: { lines: (ed && ed.video_lines) || [] } }
const chk = await agent(
  `あなたは川辺の村の年報の「解説の係」の、事実の確かめの係です。出す前に、文の中の数をひとつ残らず確かめます。\n\n` +
  `1. Read ツールで ${DATA} (${Y}年の数) を読む。\n` +
  `2. 下の下書きの、図の見かた (notes)・吹き出し (bubbles)・3 つ (top3)・動画の文 (video.lines) の数と言い分を、ひとつずつ JSON の数とくらべる。\n` +
  `   - 数がちがう → 正しい数に直す (fixed に「どこ: 前 → 後」)。JSON から出せない数・言えない言い分 → その文を消すか、数のない言い方にする (dropped に書く)。\n` +
  `   - 向きのまちがい (ふえた/へった・よい/わるい) も直す。「去年」は last_year、12 年の動きは series_12y。\n` +
  `   - charts のうち where が "report" か "stats" で keep_note のない図に、図の見かたがなければ書きたす (今年の数は入れない)。keep_note のある図の見かたは消す (去年の文をそのまま使う)。\n` +
  `   - 言葉もみる: やさしい日本語・短く・専門の言葉にはひとことの中身。\n` +
  `3. 直した下書きを Write ツールで ${DRAFT} に書く。形は下書きと同じ {"year","notes":{図:文},"bubbles":[{"chart","expr","text","team"}],"top3":[{"title","text","chart","expr"}],"video":{"lines":[...]},"fixed":[...],"dropped":[...]}。\n` +
  `   JSON の数をそのまま使えないが正しい数 (たとえば 2 つの数の和) があるときだけ "allow": [{"num": "数の文字", "why": "どの数から出したか"}] を足す。\n` +
  `4. Bash で次を動かす: cd ${ROOT} && ${PY} ${TOOL} --year ${Y} --out ${DATA} --publish ${DRAFT}\n` +
  `   「出さなかった」と出たら、書かれたわけ (どの文のどの数か) を読んで下書きを直し、もう一度動かす (5 回まで)。「を書いた」と出たら終わり。\n` +
  `   ${OUT} はこの道具だけが書く (自分で書かない)。ほかのファイルは変えない。\n\n` +
  `下書き:\n${JSON.stringify(draft, null, 1)}\n\n${STYLE}`,
  { label: '事実の確かめ', phase: 'Check', schema: CHECK_SCHEMA })

if (!chk || !chk.published) {
  log(`出せなかった: ${(chk && chk.problem) || '確かめの係の返事がない'}`)
} else {
  log(`${OUT} を出した (直した ${chk.fixed.length}・消した ${chk.dropped.length})`)
}
return { year: Y, published: !!(chk && chk.published), out: OUT, top3: draft.top3.map((h) => h.title), fixed: chk ? chk.fixed : [], dropped: chk ? chk.dropped : [], missing }
