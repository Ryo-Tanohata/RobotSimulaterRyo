export const meta = {
  name: 'society2-seasons',
  description: 'Run Society 2.0 season by season (haiku role-play per adult + step runner) until a phase change, all deaths, or the step limit',
  phases: [{ title: 'Seasons', detail: 'season answers per adult, then step.py season' }],
}
// ROOT は自分の PC のリポジトリの場所に書きかえる (クラウドでは /home/user/RobotSimulaterRyo)
const ROOT = '/home/user/RobotSimulaterRyo'
const pad = (n) => String(n).padStart(3, '0')
function rp(d, n) {
  return `Read \`${ROOT}/sim/society/data/prompts/day${pad(d)}/season/${n}.md\` and follow its instructions exactly: role-play that character and produce ONLY the JSON object it asks for. Write that JSON (nothing else) to \`${ROOT}/sim/society/data/answers/day${pad(d)}/season/${n}.json\` with the Write tool. You MUST call the Write tool to create that file before replying. Do not read any other files. Reply "done".`
}
function runner(cmd) {
  return `Run exactly this one shell command with the Bash tool (timeout 600000 ms), and nothing else. Do not edit any files. Then reply with the command's complete output, verbatim.\n\n\`\`\`\n${cmd}\n\`\`\``
}
const log_ = []
for (let k = 0; k < args.steps; k++) {
  const st = await agent(runner(`cd ${ROOT}/sim/society && python3 -c "import json,era2;s=json.load(open('data/state.json'));print('DAY',s['day'],s['phase'],s.get('hold'));print('NAMES',' '.join(era2.answerers(s)))"`), { label: `step ${k} status`, model: 'haiku', phase: 'Seasons' })
  const dm = (st || '').match(/DAY (\d+) (\w+) (\w+)/), nm = (st || '').match(/NAMES ([^\n`]*)/)
  if (!dm || dm[2] !== 'season' || dm[3] === 'True' || !nm) return { stopped: k, why: 'bad status', out: st, log: log_ }
  const d = Number(dm[1]), names = nm[1].trim().split(/\s+/).filter(Boolean)
  if (!names.length) return { stopped: d, why: 'no adults', log: log_ }
  const pre = await agent(runner(`mkdir -p ${ROOT}/sim/society/data/answers/day${pad(d)}/season && ls ${ROOT}/sim/society/data/answers/day${pad(d)}/season/`), { label: `d${d} have`, model: 'haiku', phase: 'Seasons' })
  const todo = names.filter((n) => !(pre || '').includes(`${n}.json`))  // 再起動のあと: 答えのある人はとばす
  await parallel(todo.map((n) => () => agent(rp(d, n), { label: `d${d} ${n}`, model: 'haiku', phase: 'Seasons' })))
  const ls = await agent(runner(`ls ${ROOT}/sim/society/data/answers/day${pad(d)}/season/`), { label: `d${d} check`, model: 'haiku', phase: 'Seasons' })
  const miss = names.filter((n) => !(ls || '').includes(`${n}.json`))
  if (miss.length) { log(`day ${d}: retry ${miss.join('、')}`); await parallel(miss.map((n) => () => agent(rp(d, n) + ' ', { label: `d${d} ${n} retry`, model: 'haiku', phase: 'Seasons' }))) }
  const out = await agent(runner(`bash ${ROOT}/sim/society/tools/season_step.sh`), { label: `d${d} season step`, model: 'haiku', phase: 'Seasons' })
  log_.push({ day: d, out: (out || '').slice(0, 1200) })
  if (!out || !/season exit=0/.test(out)) return { stopped: d, why: /exit=4/.test(out || '') ? 'all dead' : 'season failed', out, log: log_ }
  if (/フェーズが .* に進んだ/.test(out)) return { stopped: d, why: 'phase', out, log: log_ }
  log(`day ${d} season done`)
}
return { stopped: 'steps', why: 'end', log: log_ }
