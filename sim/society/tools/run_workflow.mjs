#!/usr/bin/env node
// ワークフローの台本 (Workflow 用の .js) を、シェルから動かす小さな道具 (年の終わりの手順 /tmp/yearend.sh などから使う)。
//   node sim/society/tools/run_workflow.mjs <台本.js> '<args の JSON>' [--log <ログのファイル>]
// agent() は `claude -p` (ヘッドレス) を 1 回ずつ呼ぶ。schema があれば --json-schema で形をそろえた答えを返す。
// parallel()・pipeline()・phase()・log()・args・budget を台本に渡す (Workflow と同じ名前。budget は数えない)。
// 同時に動かす係は 4 人まで (RUN_WF_CONC で変えられる)。係はリポジトリの場所で動き、Read・Write・Edit・Bash・Grep・Glob を使える。
// 台本の返した値を、最後に JSON で標準出力に出す。
import { spawn } from 'node:child_process'
import { readFileSync, appendFileSync } from 'node:fs'
import path from 'node:path'

const [scriptPath, argJson, ...rest] = process.argv.slice(2)
if (!scriptPath) { console.error('使い方: node run_workflow.mjs <台本.js> \'{"year":250}\' [--log file]'); process.exit(2) }
const logFile = rest[0] === '--log' ? rest[1] : null
const args = argJson ? JSON.parse(argJson) : undefined
const ROOT = (args && args.root) || path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../..')
const CONC = Number(process.env.RUN_WF_CONC || 4)
const CLAUDE = process.env.CLAUDE_BIN || 'claude'

let phaseNow = ''
const say = (s) => { const line = `[${new Date().toISOString().slice(11, 19)}] ${s}`; console.error(line); if (logFile) appendFileSync(logFile, line + '\n') }
let running = 0
const queue = []
const slot = () => new Promise((res) => { if (running < CONC) { running++; res() } else queue.push(res) })
const free = () => { const n = queue.shift(); if (n) n(); else running-- }

async function agent(prompt, opts = {}) {
  await slot()
  const label = opts.label || 'agent'
  const ph = opts.phase || phaseNow
  say(`▶ ${ph ? ph + ' / ' : ''}${label}`)
  const a = ['-p', prompt, '--output-format', 'json', '--permission-mode', 'acceptEdits',
    '--allowedTools', 'Read', 'Write', 'Edit', 'Bash', 'Grep', 'Glob', '--no-session-persistence']
  if (opts.schema) a.push('--json-schema', JSON.stringify(opts.schema))
  if (opts.model) a.push('--model', opts.model)
  if (opts.effort) a.push('--effort', opts.effort)
  try {
    for (let t = 0; t < 2; t++) {
      const out = await new Promise((res) => {
        const p = spawn(CLAUDE, a, { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] })
        let so = '', se = ''
        p.stdout.on('data', (d) => { so += d })
        p.stderr.on('data', (d) => { se += d })
        p.on('close', (code) => res({ code, so, se }))
      })
      let j = null
      try { j = JSON.parse(out.so) } catch { /* 下で扱う */ }
      if (j && !j.is_error) {
        const v = opts.schema ? j.structured_output : j.result
        if (v !== undefined && v !== null) {
          say(`✔ ${label} (${j.num_turns} 回・$${(j.total_cost_usd || 0).toFixed(2)})`)
          return v
        }
      }
      say(`… ${label}: 答えがとれない (code ${out.code}) ${(out.se || out.so).slice(0, 300)}`)
    }
    say(`✖ ${label}: あきらめた (null を返す)`)
    return null
  } finally { free() }
}
async function parallel(thunks) {
  return Promise.all(thunks.map(async (f) => { try { return await f() } catch (e) { say(`✖ ${e.message}`); return null } }))
}
async function pipeline(items, ...stages) {
  return Promise.all(items.map(async (it, i) => {
    let v = it
    for (const st of stages) { try { v = await st(v, it, i) } catch (e) { say(`✖ ${e.message}`); return null } }
    return v
  }))
}
const phase = (t) => { phaseNow = t; say(`== ${t}`) }
const log = (m) => say(m)
const budget = { total: null, spent: () => 0, remaining: () => Infinity }

const src = readFileSync(scriptPath, 'utf8').replace(/^export const meta\s*=/m, 'const meta =')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const fn = new AsyncFunction('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget', src)
const result = await fn(agent, parallel, pipeline, phase, log, args, budget)
console.log(JSON.stringify(result, null, 1))
