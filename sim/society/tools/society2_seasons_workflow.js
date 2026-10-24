export const meta = {
  name: 'society2-seasons',
  description: 'Run Society 2.0 season by season (role-play per adult: representatives sonnet/opus, feelings haiku; haiku step runner) until a phase change, the end of a part (HOLD line), all deaths, or the step limit. From G7: mode year (answers only at the yearly meeting, zoom seasons and the autumn meeting)',
  phases: [{ title: 'Seasons', detail: 'season answers per adult, then step.py season' }],
}
// args.mode: 'season' (G6 まで。1 回 = 1 季節、毎季節答える。args.steps 回) / 'year' (G7 から。1 回 = 1 季節のまま、答えるのは年の集まりと寄る季節と毎年の秋の集まりだけ。
//   args.years 回の年の終わりをすぎたら止まる)。G7 なのに 'season' で、G6 なのに 'year' で動かしたら、進めずに止まる (docs/society_phase/G7_design.md 4.E.5)
const MODE = args.mode || 'season'
// ROOT はリポジトリの場所。args.root で渡す (本人の PC では、その PC のリポジトリの場所。渡さなければクラウドの /home/user/RobotSimulaterRyo)
const ROOT = args.root || '/home/user/RobotSimulaterRyo'
// PY は使う Python。args.py で渡す (本人の PC は 'py -3' = Python 3.13。3.11 だと食べ物の数の最後の桁がずれる。渡さなければ python3)
const PY = args.py || 'python3'
// DATA はデータの置き場所 (リポジトリからの道。2026-10-24。実験 C の試しの村は args.data = 'sim/society/data_C')。渡さなければ本物の村 'sim/society/data'
const DATA = args.data || 'sim/society/data'
const ENV = DATA === 'sim/society/data' ? '' : `SOC_DATA=${ROOT}/${DATA} SOC_DATA_REL=${DATA} `
const pad = (n) => String(n).padStart(3, '0')
// 答えるモデル (2026-10-23 本人の決め「代表だけ sonnet/opus」)。季節の答え (家の代表とまとめ役) と、まわりの集落の集まりは sonnet、
// そのうち名前から決まる約 8 人に 1 人は opus (乱数なし。同じ人はずっと同じモデル)。気持ちだけ答える人と、コマンドを動かす係は haiku。
// args.models === 'haiku' で前と同じ (みな haiku)。使ったモデルは答えの置き場所の models.json に書く
const ALL_HAIKU = args.models === 'haiku'
function fnv(s) { let x = 2166136261; for (const ch of s) { x ^= ch.codePointAt(0); x = Math.imul(x, 16777619) >>> 0 } return x }
const repModel = (n) => ALL_HAIKU ? 'haiku' : fnv(n) % 8 === 0 ? 'opus' : 'sonnet'
const councilModel = () => ALL_HAIKU ? 'haiku' : 'sonnet'
function rp(d, n) {
  return `Read \`${ROOT}/${DATA}/prompts/day${pad(d)}/season/${n}.md\` and follow its instructions exactly: role-play that character and produce ONLY the JSON object it asks for. Write that JSON (nothing else) to \`${ROOT}/${DATA}/answers/day${pad(d)}/season/${n}.json\` with the Write tool. You MUST call the Write tool to create that file before replying. Do not read any other files. Reply "done".`
}
function rpf(d, n) {  // 代表でない大人: 気持ちと一言だけ (2026-10-09 本人の希望)
  return `Read \`${ROOT}/${DATA}/prompts/day${pad(d)}/feeling/${n}.md\` and follow its instructions exactly: role-play that character and produce ONLY the JSON object it asks for. Write that JSON (nothing else) to \`${ROOT}/${DATA}/answers/day${pad(d)}/feeling/${n}.json\` with the Write tool. You MUST call the Write tool to create that file before replying. Do not read any other files. Reply "done".`
}
function rc_(d, n) {  // G7: まわりの集落の集まり (分かれ目の年だけ。答えがなければ step.py が決まりで選ぶ)
  return `Read \`${ROOT}/${DATA}/prompts/day${pad(d)}/council/${n}.md\` and follow its instructions exactly: role-play that settlement's council and produce ONLY the JSON object it asks for. Write that JSON (nothing else) to \`${ROOT}/${DATA}/answers/day${pad(d)}/council/${n}.json\` with the Write tool. You MUST call the Write tool to create that file before replying. Do not read any other files. Reply "done".`
}
function runner(cmd) {
  return `Run exactly this one shell command with the Bash tool (timeout 600000 ms), and nothing else. Do not edit any files. Then reply with the command's complete output, verbatim.\n\n\`\`\`\n${cmd}\n\`\`\``
}
const log_ = []
const STEPS = MODE === 'year' ? (args.years || 1) * 12 : args.steps  // year: 1 年は 4 歩 (集まり直しがあると増える)。上限は年の 3 倍の歩
let years = 0
for (let k = 0; k < STEPS; k++) {
  // 状態は step.py who で読む (読むだけ。DAY・PHASE・HOLD・MODE・MEET・NAMES・FEEL・COUNCIL・ASKLOG の行)
  const st = await agent(runner(`cd ${ROOT}/sim/society && ${ENV}PYTHONUTF8=1 PYTHONIOENCODING=utf-8 ${PY} step.py who`), { label: `step ${k} status`, model: 'haiku', phase: 'Seasons' })
  const dm = (st || '').match(/DAY (\d+) (\w+) (\w+)/), nm = (st || '').match(/NAMES[ \t]*([^\n`]*)/)  // 空の行 (集まりのない歩) は「NAMES」だけになることがある (行の終わりの空白が落ちても読む)
  if (!dm || dm[2] !== 'season' || dm[3] === 'True' || !nm) return { stopped: k, why: 'bad status', out: st, log: log_ }
  const mm = (st || '').match(/MODE (\w+)/), me = (st || '').match(/MEET (\S+)/), cm = (st || '').match(/COUNCIL[ \t]*([^\n`]*)/)
  if (!mm || mm[1] !== MODE) return { stopped: k, why: `mode: the world is in ${mm ? mm[1] : '?'} mode (run with mode ${mm ? mm[1] : '?'})`, out: st, log: log_ }
  const meet = MODE === 'season' || (me && me[1] !== 'none')  // year: 答えるのは集まりの歩だけ (MEET 年 / 寄る / 集まり直し / 秋 (毎年の秋の集まり))
  // 仕事の理由 (2026-10-14 本人が決めた: 次に村を進めるときから)。まだ一度も step.py ask_why を動かしていなければ、進めずに止まる (daily_run.md)
  if (!/ASKLOG True/.test(st)) return { stopped: k, why: 'ask_why not started: run step.py ask_why once, commit the prompts, then run again', out: st, log: log_ }
  const d = Number(dm[1]), names = nm[1].trim().split(/\s+/).filter(Boolean)
  const fm = (st || '').match(/FEEL[ \t]*([^\n`]*)/), feel = fm ? fm[1].trim().split(/\s+/).filter(Boolean) : []
  const council = cm ? cm[1].trim().split(/\s+/).filter(Boolean) : []
  if (meet && !names.length) return { stopped: d, why: 'no adults', log: log_ }
  if (meet) {  // 答える歩 (season は毎回。year は MEET のある歩だけ)
    const pre = await agent(runner(`mkdir -p ${ROOT}/${DATA}/answers/day${pad(d)}/season ${ROOT}/${DATA}/answers/day${pad(d)}/feeling && ls ${ROOT}/${DATA}/answers/day${pad(d)}/season/ && echo FEELING: && ls ${ROOT}/${DATA}/answers/day${pad(d)}/feeling/`), { label: `d${d} have`, model: 'haiku', phase: 'Seasons' })
    const [preS, preF] = (pre || '').split('FEELING:')
    const todo = names.filter((n) => !(preS || '').includes(`${n}.json`))  // 再起動のあと: 答えのある人はとばす
    const todoF = feel.filter((n) => !(preF || '').includes(`${n}.json`))
    await parallel([...todo.map((n) => () => agent(rp(d, n), { label: `d${d} ${n} (${repModel(n)})`, model: repModel(n), phase: 'Seasons' })),
                    ...todoF.map((n) => () => agent(rpf(d, n), { label: `d${d} ${n} (気持ち)`, model: 'haiku', phase: 'Seasons' }))])
    const ls = await agent(runner(`ls ${ROOT}/${DATA}/answers/day${pad(d)}/season/`), { label: `d${d} check`, model: 'haiku', phase: 'Seasons' })
    const miss = names.filter((n) => !(ls || '').includes(`${n}.json`))
    if (miss.length) { log(`day ${d}: retry ${miss.join('、')}`); await parallel(miss.map((n) => () => agent(rp(d, n) + ' ', { label: `d${d} ${n} retry`, model: repModel(n), phase: 'Seasons' }))) }
    if (feel.length) {  // 気持ちの答えは、ない人がいても季節は進める (気持ちが前のまま)。1 回だけやり直す
      const lf = await agent(runner(`ls ${ROOT}/${DATA}/answers/day${pad(d)}/feeling/`), { label: `d${d} check (気持ち)`, model: 'haiku', phase: 'Seasons' })
      const missF = feel.filter((n) => !(lf || '').includes(`${n}.json`))
      if (missF.length) await parallel(missF.map((n) => () => agent(rpf(d, n) + ' ', { label: `d${d} ${n} (気持ち) retry`, model: 'haiku', phase: 'Seasons' })))
    }
    if (council.length) {  // G7: まわりの集落の集まり (1 回だけやり直す。なければ step.py が決まりで選ぶ)
      const once = async () => {
        const lc = await agent(runner(`mkdir -p ${ROOT}/${DATA}/answers/day${pad(d)}/council && ls ${ROOT}/${DATA}/answers/day${pad(d)}/council/`), { label: `d${d} check (集まり)`, model: 'haiku', phase: 'Seasons' })
        return council.filter((n) => !(lc || '').includes(`${n}.json`))
      }
      for (let t = 0; t < 2; t++) {
        const missC = await once()
        if (!missC.length) break
        await parallel(missC.map((n) => () => agent(rc_(d, n) + (t ? ' ' : ''), { label: `d${d} 集まり ${n}${t ? ' retry' : ''}`, model: councilModel(), phase: 'Seasons' })))
      }
    }
  } else {
    log(`day ${d}: no meeting (yearly plan)`)
  }
  if (meet) {  // 使ったモデルを残す (季節の答えの置き場所のとなり。step.py は読まない)
    const mj = JSON.stringify({ season: Object.fromEntries(names.map((n) => [n, repModel(n)])), feeling: Object.fromEntries(feel.map((n) => [n, 'haiku'])), council: Object.fromEntries(council.map((n) => [n, councilModel()])) })
    await agent(runner(`printf '%s\\n' '${mj}' > ${ROOT}/${DATA}/answers/day${pad(d)}/models.json`), { label: `d${d} models`, model: 'haiku', phase: 'Seasons' })
  }
  const out = await agent(runner(`${ENV}PY='${PY}' CLAUDE_SESSION_URL=${args.session || ''} bash ${ROOT}/sim/society/tools/season_step.sh`), { label: `d${d} season step`, model: 'haiku', phase: 'Seasons' })
  log_.push({ day: d, out: (out || '').slice(0, 1200) })
  // exit=4: 生きている人がいない / exit=5: G7 の札の表 (よその便り) が変わった (直したなら step.py cards "<note>" のあとで、また動かす)
  // exit=6 (行の頭の「RECORDS failed …」): 季節は進んだが記録 (records/) を作れなかった。直して build_records.py で作り直してから、また動かす (2026-10-22)
  if (!out || !/season exit=0/.test(out)) return { stopped: d, why: /exit=4/.test(out || '') ? 'all dead' : /exit=5/.test(out || '') ? 'cards changed' : /exit=6/.test(out || '') || /^RECORDS failed/m.test(out || '') ? 'records failed' : 'season failed', out, log: log_ }
  if (/^RECORDS failed/m.test(out)) return { stopped: d, why: 'records failed', out, log: log_ }
  // 止まる合図 (docs/society_phase/G7_design.md 4.E.2): step.py は一時停止したとき、機械用の 1 行「HOLD …」を行の頭から出す。
  // 村の人の文 (掟など。表示は「* 」で始まる) からは出ないので、これで止まる。G1〜G5 のフェーズが進んだ (phase)・G6 の第 4 部の終わり (part_end)・
  // G7 からの部の終わり・次の G を待つ (wait)・工業の入口 (entrance)・止めて相談する (consult)。why の 'end' は「回数を終えた」に使っている
  // 2026-10-17: 前の合図 (「Society 2.0 が終わった」「フェーズが … に進んだ」の文) は外した。step.py の G6 の終わりの文から「Society 2.0 が終わった」を
  // 消したのと同じコミット (第 4 部の終わりは Society 2.0 の終わりではない)。G6 の終わりは、今は 'part end' で止まる (前は 'society2 end')
  const hold = (out || '').match(/^HOLD (part_end|wait|entrance|consult|phase)$/m)
  if (hold) return { stopped: d, why: { part_end: 'part end', wait: 'wait', entrance: 'entrance', consult: 'consult', phase: 'phase' }[hold[1]], out, log: log_ }
  // args.stop_on_town: 町の条件がそろったら止める (2026-10-15 本人が決めた: 町に届くか 45年までで止めて相談する)。状態の行は「町 43年120日目」のように日付になる
  if (args.stop_on_town && MODE === 'season' && /町 (?!まだ)[0-9]/.test(out)) return { stopped: d, why: 'town', out, log: log_ }
  log(`day ${d} season done`)
  // year: 年の終わり (年の最後の日まで進んだ歩) を args.years 回すぎたら止まる
  const end = (out || '').match(/(\d+) 日目まで進んだ/)
  if (MODE === 'year' && end && (Number(end[1]) + 1) % 120 === 0 && ++years >= (args.years || 1)) return { stopped: Number(end[1]), why: 'end', years, log: log_ }
}
return { stopped: 'steps', why: 'end', log: log_ }
