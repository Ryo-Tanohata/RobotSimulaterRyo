export const meta = {
  name: 'society2-seasons',
  description: 'Run Society 2.0 season by season (haiku role-play per adult + step runner) until a phase change, the end of Society 2.0, all deaths, or the step limit',
  phases: [{ title: 'Seasons', detail: 'season answers per adult, then step.py season' }],
}
// ROOT はリポジトリの場所。args.root で渡す (本人の PC では、その PC のリポジトリの場所。渡さなければクラウドの /home/user/RobotSimulaterRyo)
const ROOT = args.root || '/home/user/RobotSimulaterRyo'
// PY は使う Python。args.py で渡す (本人の PC は 'py -3' = Python 3.13。3.11 だと食べ物の数の最後の桁がずれる。渡さなければ python3)
const PY = args.py || 'python3'
const pad = (n) => String(n).padStart(3, '0')
function rp(d, n) {
  return `Read \`${ROOT}/sim/society/data/prompts/day${pad(d)}/season/${n}.md\` and follow its instructions exactly: role-play that character and produce ONLY the JSON object it asks for. Write that JSON (nothing else) to \`${ROOT}/sim/society/data/answers/day${pad(d)}/season/${n}.json\` with the Write tool. You MUST call the Write tool to create that file before replying. Do not read any other files. Reply "done".`
}
function rpf(d, n) {  // 代表でない大人: 気持ちと一言だけ (2026-10-09 本人の希望)
  return `Read \`${ROOT}/sim/society/data/prompts/day${pad(d)}/feeling/${n}.md\` and follow its instructions exactly: role-play that character and produce ONLY the JSON object it asks for. Write that JSON (nothing else) to \`${ROOT}/sim/society/data/answers/day${pad(d)}/feeling/${n}.json\` with the Write tool. You MUST call the Write tool to create that file before replying. Do not read any other files. Reply "done".`
}
function runner(cmd) {
  return `Run exactly this one shell command with the Bash tool (timeout 600000 ms), and nothing else. Do not edit any files. Then reply with the command's complete output, verbatim.\n\n\`\`\`\n${cmd}\n\`\`\``
}
const log_ = []
for (let k = 0; k < args.steps; k++) {
  const st = await agent(runner(`cd ${ROOT}/sim/society && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 ${PY} -c "import json,era2;s=json.load(open('data/state.json',encoding='utf-8'));print('DAY',s['day'],s['phase'],s.get('hold'));print('NAMES',' '.join(era2.answerers(s)));print('FEEL',' '.join(era2.feelers(s)))"`), { label: `step ${k} status`, model: 'haiku', phase: 'Seasons' })
  const dm = (st || '').match(/DAY (\d+) (\w+) (\w+)/), nm = (st || '').match(/NAMES ([^\n`]*)/)
  if (!dm || dm[2] !== 'season' || dm[3] === 'True' || !nm) return { stopped: k, why: 'bad status', out: st, log: log_ }
  const d = Number(dm[1]), names = nm[1].trim().split(/\s+/).filter(Boolean)
  const fm = (st || '').match(/FEEL ([^\n`]*)/), feel = fm ? fm[1].trim().split(/\s+/).filter(Boolean) : []
  if (!names.length) return { stopped: d, why: 'no adults', log: log_ }
  const pre = await agent(runner(`mkdir -p ${ROOT}/sim/society/data/answers/day${pad(d)}/season ${ROOT}/sim/society/data/answers/day${pad(d)}/feeling && ls ${ROOT}/sim/society/data/answers/day${pad(d)}/season/ && echo FEELING: && ls ${ROOT}/sim/society/data/answers/day${pad(d)}/feeling/`), { label: `d${d} have`, model: 'haiku', phase: 'Seasons' })
  const [preS, preF] = (pre || '').split('FEELING:')
  const todo = names.filter((n) => !(preS || '').includes(`${n}.json`))  // 再起動のあと: 答えのある人はとばす
  const todoF = feel.filter((n) => !(preF || '').includes(`${n}.json`))
  await parallel([...todo.map((n) => () => agent(rp(d, n), { label: `d${d} ${n}`, model: 'haiku', phase: 'Seasons' })),
                  ...todoF.map((n) => () => agent(rpf(d, n), { label: `d${d} ${n} (気持ち)`, model: 'haiku', phase: 'Seasons' }))])
  const ls = await agent(runner(`ls ${ROOT}/sim/society/data/answers/day${pad(d)}/season/`), { label: `d${d} check`, model: 'haiku', phase: 'Seasons' })
  const miss = names.filter((n) => !(ls || '').includes(`${n}.json`))
  if (miss.length) { log(`day ${d}: retry ${miss.join('、')}`); await parallel(miss.map((n) => () => agent(rp(d, n) + ' ', { label: `d${d} ${n} retry`, model: 'haiku', phase: 'Seasons' }))) }
  if (feel.length) {  // 気持ちの答えは、ない人がいても季節は進める (気持ちが前のまま)。1 回だけやり直す
    const lf = await agent(runner(`ls ${ROOT}/sim/society/data/answers/day${pad(d)}/feeling/`), { label: `d${d} check (気持ち)`, model: 'haiku', phase: 'Seasons' })
    const missF = feel.filter((n) => !(lf || '').includes(`${n}.json`))
    if (missF.length) await parallel(missF.map((n) => () => agent(rpf(d, n) + ' ', { label: `d${d} ${n} (気持ち) retry`, model: 'haiku', phase: 'Seasons' })))
  }
  const out = await agent(runner(`PY='${PY}' CLAUDE_SESSION_URL=${args.session || ''} bash ${ROOT}/sim/society/tools/season_step.sh`), { label: `d${d} season step`, model: 'haiku', phase: 'Seasons' })
  log_.push({ day: d, out: (out || '').slice(0, 1200) })
  if (!out || !/season exit=0/.test(out)) return { stopped: d, why: /exit=4/.test(out || '') ? 'all dead' : 'season failed', out, log: log_ }
  // G6: 町と記録がそろうと Society 2.0 の終わり (フェーズは進まない。step.py は「Society 2.0 が終わった」と表示して一時停止する)。
  // why の 'end' は「回数を終えた」に使っているので、別の言葉にする
  if (/Society 2\.0 が終わった/.test(out)) return { stopped: d, why: 'society2 end', out, log: log_ }
  if (/フェーズが .* に進んだ/.test(out)) return { stopped: d, why: 'phase', out, log: log_ }
  log(`day ${d} season done`)
}
return { stopped: 'steps', why: 'end', log: log_ }
