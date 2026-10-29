export const meta = {
  name: 'paper2-exp2-survey',
  description: 'Paper 2 experiment 2: one agent per LLM respondent with a life-situation persona answers the 2017 thesis questionnaire (54 items, 5-point) plus a one-phrase reason for 5 items; returns all answers (writes no files)',
  whenToUse: 'Only after the user approved the cost in docs/research/humanity/paper2_exp2_prereg.md. Run a pilot first with args.limit.',
  phases: [{ title: 'Answer', detail: 'one agent per respondent (D1 sonnet, D2 sonnet + recent surroundings, D3 opus); one retry if no valid answer' }],
}
// 論文 2・実験 2 (docs/research/humanity/paper2_exp2_prereg.md)。実験 1 の survey_workflow.js と同じ作り。ファイルは書かない。
// 答えは agent の返す値として集め、最後にまとめて返す。メインのセッションが `save_answers.py --exp 2` で answers_exp2/<ID>.json に分ける。
// args (みな省略できる):
//   root:       リポジトリの場所 (既定 /home/user/RobotSimulaterRyo)
//   conditions: 動かす条件 (既定 ['D1','D2','D3'])
//   limit:      条件ごとに最初の何人だけ動かすか (試しの回。例 2)
//   done:       もう answers_exp2/ にある ID の配列 (とばす。再開のとき)
const ROOT = args && args.root ? args.root : '/home/user/RobotSimulaterRyo'
const DIR = `${ROOT}/sim/society/tools/survey`
// items.py の CONDITIONS_EXP2 と同じ (変えたら両方を直す)
const CONDS = {
  D1: { n: 100, model: 'sonnet' },
  D2: { n: 100, model: 'sonnet' },
  D3: { n: 30, model: 'opus' },
}
const ITEMS = []
for (let k = 1; k <= 35; k++) ITEMS.push('A' + String(k).padStart(2, '0'))
for (let k = 1; k <= 19; k++) ITEMS.push('B' + String(k).padStart(2, '0'))
const REASON_ITEMS = ['A08', 'A09', 'A23', 'B08', 'B11']  // items.py の REASON_ITEMS と同じ

const answerProps = {}
for (const i of ITEMS) answerProps[i] = { type: 'integer', minimum: 1, maximum: 5 }
const reasonProps = {}
for (const i of REASON_ITEMS) reasonProps[i] = { type: 'string' }
// 並び: respondent_id → answers (数) → reasons (わけ)。数を先に決めてから、わけを書く (prereg 5.)
const SCHEMA = {
  type: 'object',
  properties: {
    respondent_id: { type: 'string' },
    answers: { type: 'object', properties: answerProps, required: ITEMS },
    reasons: { type: 'object', properties: reasonProps, required: REASON_ITEMS },
  },
  required: ['respondent_id', 'answers', 'reasons'],
}

function prompt(id) {
  return `Use the Read tool once to read \`${DIR}/prompts_exp2/${id}.md\`. Do not use any other tool and do not read any other file. ` +
    `That file is a questionnaire (in Japanese). Answer it exactly as its instructions say, as the respondent it describes, ` +
    `answering all 54 items once each, then the short reasons for the 5 items it names. ` +
    `Return the answers as your structured output, with respondent_id "${id}". Do not add explanations.`
}

const want = (args && args.conditions) || Object.keys(CONDS)
const done = new Set((args && args.done) || [])
const todo = []
for (const c of want) {
  const n = args && args.limit ? Math.min(args.limit, CONDS[c].n) : CONDS[c].n
  for (let k = 1; k <= n; k++) {
    const id = `${c}_${String(k).padStart(3, '0')}`
    if (!done.has(id)) todo.push({ id, cond: c, model: CONDS[c].model })
  }
}
log(`${todo.length} respondents to ask (${want.join(', ')}${args && args.limit ? `, limit ${args.limit}` : ''}; skipped ${done.size} already done)`)

phase('Answer')
const results = await pipeline(todo, async (r) => {
  let attempts = 0, out = null
  while (attempts < 2 && !out) {  // 答えがない・ID が違うときは 1 回だけ聞き直す (prereg 9.)
    attempts++
    const a = await agent(prompt(r.id), {
      label: `${r.id} (${r.model})${attempts > 1 ? ' retry' : ''}`, phase: 'Answer', model: r.model, schema: SCHEMA,
    })
    if (a && a.respondent_id === r.id && a.answers) out = a
  }
  return { id: r.id, condition: r.cond, model: r.model, attempts, ok: !!out, respondent_id: r.id,
    answers: out ? out.answers : null, reasons: out ? (out.reasons || null) : null }
})
const ok = results.filter((x) => x && x.ok)
const missing = todo.map((r) => r.id).filter((id) => !ok.some((x) => x.id === id))
log(`answered ${ok.length}/${todo.length}; missing ${missing.length}`)
return { answered: ok.length, asked: todo.length, missing, retried: ok.filter((x) => x.attempts > 1).map((x) => x.id), results: ok }
