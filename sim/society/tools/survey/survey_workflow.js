export const meta = {
  name: 'paper2-exp1-survey',
  description: 'Paper 2 experiment 1: one agent per LLM respondent answers the 2017 thesis questionnaire (54 items, 5-point) from its prompt file; returns all answers (writes no files)',
  whenToUse: 'Only after the user approved the cost in docs/research/humanity/paper2_exp1_prereg.md. Run a pilot first with args.limit.',
  phases: [{ title: 'Answer', detail: 'one agent per respondent (C0 sonnet, C1 sonnet, C2 sonnet + honne, C3 haiku, C4 opus); one retry if no valid answer' }],
}
// 論文 2・実験 1 (docs/research/humanity/paper2_exp1_prereg.md)。この台本はファイルを書かない。答えは agent の返す値として集め、
// 最後にまとめて返す。メインのセッションが save_answers.py で answers/<ID>.json に分ける (README.md)。
// args (みな省略できる):
//   root:       リポジトリの場所 (既定 /home/user/RobotSimulaterRyo)
//   conditions: 動かす条件 (既定 ['C0','C1','C2','C3','C4'])
//   limit:      条件ごとに最初の何人だけ動かすか (試しの回。例 2)
//   done:       もう answers/ にある ID の配列 (とばす。再開のとき)
const ROOT = args && args.root ? args.root : '/home/user/RobotSimulaterRyo'
const DIR = `${ROOT}/sim/society/tools/survey`
// items.py の CONDITIONS と同じ (変えたら両方を直す)
const CONDS = {
  C0: { n: 30, model: 'sonnet', honne: false },
  C1: { n: 100, model: 'sonnet', honne: false },
  C2: { n: 100, model: 'sonnet', honne: true },
  C3: { n: 30, model: 'haiku', honne: false },
  C4: { n: 30, model: 'opus', honne: false },
}
const ITEMS = []
for (let k = 1; k <= 35; k++) ITEMS.push('A' + String(k).padStart(2, '0'))
for (let k = 1; k <= 19; k++) ITEMS.push('B' + String(k).padStart(2, '0'))

function schema(honne) {
  const props = {}
  for (const i of ITEMS) {
    props[i] = honne
      ? { type: 'object', properties: { honne: { type: 'string' }, answer: { type: 'integer', minimum: 1, maximum: 5 } }, required: ['honne', 'answer'] }
      : { type: 'integer', minimum: 1, maximum: 5 }
  }
  return {
    type: 'object',
    properties: {
      respondent_id: { type: 'string' },
      answers: { type: 'object', properties: props, required: ITEMS },
    },
    required: ['respondent_id', 'answers'],
  }
}
const SCHEMA = { plain: schema(false), honne: schema(true) }

function prompt(id) {
  return `Use the Read tool once to read \`${DIR}/prompts/${id}.md\`. Do not use any other tool and do not read any other file. ` +
    `That file is a questionnaire (in Japanese). Answer it exactly as its instructions say, as the respondent it describes, ` +
    `answering all 54 items once each. Return the answers as your structured output, with respondent_id "${id}". Do not add explanations.`
}

const want = (args && args.conditions) || Object.keys(CONDS)
const done = new Set((args && args.done) || [])
const todo = []
for (const c of want) {
  const n = args && args.limit ? Math.min(args.limit, CONDS[c].n) : CONDS[c].n
  for (let k = 1; k <= n; k++) {
    const id = `${c}_${String(k).padStart(3, '0')}`
    if (!done.has(id)) todo.push({ id, cond: c, model: CONDS[c].model, honne: CONDS[c].honne })
  }
}
log(`${todo.length} respondents to ask (${want.join(', ')}${args && args.limit ? `, limit ${args.limit}` : ''}; skipped ${done.size} already done)`)

phase('Answer')
const results = await pipeline(todo, async (r) => {
  let attempts = 0, out = null
  while (attempts < 2 && !out) {  // 答えがない・ID が違うときは 1 回だけ聞き直す (prereg 9.)
    attempts++
    const a = await agent(prompt(r.id), {
      label: `${r.id} (${r.model})${attempts > 1 ? ' retry' : ''}`, phase: 'Answer', model: r.model,
      schema: r.honne ? SCHEMA.honne : SCHEMA.plain,
    })
    if (a && a.respondent_id === r.id && a.answers) out = a
  }
  return { id: r.id, condition: r.cond, model: r.model, attempts, ok: !!out, respondent_id: r.id, answers: out ? out.answers : null }
})
const ok = results.filter((x) => x && x.ok)
const missing = todo.map((r) => r.id).filter((id) => !ok.some((x) => x.id === id))
log(`answered ${ok.length}/${todo.length}; missing ${missing.length}`)
return { answered: ok.length, asked: todo.length, missing, retried: ok.filter((x) => x.attempts > 1).map((x) => x.id), results: ok }
