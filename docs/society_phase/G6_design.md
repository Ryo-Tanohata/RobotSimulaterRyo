<!-- 設計書 (まだリポジトリのコードにはしていない)。2026-10-09、クラウドのセッションで、ワークフローで作った:
     3 つの角度 (小さく正しく / 史実 / 起きたことから) の設計 → 判定役が採点 (小さく 34・史実 33・起きたことから 38、50 点満点) →
     「起きたことから」の案をもとに、ほかの 2 つのよいところを足してまとめた。
     まとめ役は、このコードを写しの木 (/tmp) に入れて、メモリの中で試し回しをした (この文書の 0.)。リポジトリのコードとデータは変えていない -->

# G6 交易・町・記録: 設計書 (日本語の要約)

第 4 部「町と文字」(テル・ブラク LC2 → ウルク期) の仕組み。G6 に入ってから働き、G6 の前は何も変わらない (お題も state.json も、いまと同じ。写しで確かめた)。

**G6 で足すもの**
- **ほかの村**: 地図の外 (歩いて 1〜2 日) にある村。記録に残る出来事からだけ生まれる: (1) G5 で村を出た家の人たちの村、(2) G6 で来たよその群れが「…から来た」と言った村、(3) 交換をもとめて来た人の村。G6 の最初の季節の終わりには、必ず 1 つの村の人が交換をもとめて来る。ほかの村は Claude が演じず、決まりで動く (お金はかからない)
- **交換**: ほかの村の人が季節の終わりに来て、申し出をする (交換したい / 苦しい年なので草の種を貸してほしい / 借りた分を返す)。次の集まりで、村の物で受けるか、家の物で受けるか、受けないかを決める。自分たちから「交換に行く」こともできる (歩いて 1 日の村なら 3 日。1 人で運べるのは草の種 900 つかみ・土器 4 個ほど)。払いきれない分は「あとで返す」約束 (貸し借り) になる
- **町に人が集まる**: 交換している村から「ここで暮らしたい」人が来る (受け入れるかは、これまで通り大人が決める)。来た家は、来た村の方角の、キャンプから 250〜375 m の所に住まいを建てる (ブラクのまわりの、来たところごとの小さな集まり)
- **印と封**: 家の代表は家の印を作れる。印のある家の倉は封をする (よその家の人が開けると、封が割れているので分かり、必ずもめごとになる)。みんなが望めば、村の蓄えにも封をし、取るたびにその家の印の封のかけらが残る
- **覚え**: G6 では、記録のない量 (家ごとの村の蓄えへの出し入れ・もめごとの量・貸し借りの量) は「約 a〜b」の幅でしか分からない。家が多いほど、貸し借りが多いほど、幅が広い。言い出した家は損を多めに覚えていることがあり、覚えで払うと「多く払った」という覚え違いのもめごとが起きる
- **記録の道具** (本人と決めた順: 印 → 数え札 → 封筒 → 粘土の板): 次の道具は、その道具が答える困りごとが起きてから使えるようになる。使うかは人が決める
  - 数え札: 印で封をするようになり、記録のない量を覚えで決めることが起きたあと。仕事「記録をつける」(1 人 1 日に数え札 10 個ほど)
  - 封筒: ほかの村との貸し借りがあるとき (数え札を粘土の玉に入れ、印を押す。返すとき、どちらにも数が分かる)
  - 粘土の板 (物のしるしと数のしるしを分けて記す): 数え札で記録した季節が 4 つ以上になり、1 季節に数え札が 200 個以上要る季節があったあと (1 人 1 日に数え札 50 個分)
- **記録の使い道**: 記録のある量ははっきり分かり、もめごとや貸し借りを確かめられる (覚え違いが起きない)。記録のあるもめごとは、集まりで話し合える 2 つに数えない。村の蓄えの記録を全部残せた季節は、作る人・記録をつける人・交換に行った人の働いた日を「入れた」に数える (配給の記録)
- **黒曜石**: 2 つ目のよその村 (歩いて 2 日) は黒曜石を持つ。黒曜石の刃の鎌は割れにくい (半分)

**町の条件** (F3。季節の終わりに見る): 村が **50 人以上**、この 4 季節は毎季節ほかの村と交換した、相手の村が 2 つ以上、村がいちばん大きい相手の村の 2 倍以上、食べ物をとらない人 (作る人・記録をつける人。20 日以上) が大人の 1 割以上

**記録の条件** (F4): 物のしるしと数のしるしを分けて記した**粘土の板の記録で、量を確かめた**ことが 1 回以上 (数え札だけでは文字としない。ウルク IV の書き方)

**F (区切り)**: G6 の F1 村どうしの交換 / F2 印で封をする / F3 町 / F4 物と数を分けて記す。町と記録は別々で、どちらが先でもよく、届いた日を記録する。町だけ・記録だけでは止まらない。**両方そろうと「Society 2.0 の終わり」で止まる** (「フェーズが…に進んだ」とは書かない。ワークフローの止まる文を足す)

**人が決めること** (季節の答え): 申し出を村で受けるか・家で受けるか・受けないか (trade) / 交換に行く人と、行き先・持って行く物・ほしい物 (job) / 家の印を作るか (seal) / 村の蓄えに封をするか (seal_store) / 記録をつける人と、残すもの・残し方 (job) / ほかの村から来た人を受け入れるか (accept)。家族の代表の答えは家族の大人みんなの答え。家の物で受ける・印を作るのは家の代表だけ

**縮め方**
- 人数: ブラク LC2 (約 55 ha。1 ha に 50〜100 人として 2,750〜5,500 人) の約 1/55〜1/110 で、町を 50 人にした。ほかの村 (10〜25 人) は、まわりの小さな中心地 (10〜20 ha) の約 1/100
- 距離: 縮めない (歩いて 1〜2 日、約 25〜60 km。地図の外に置く)
- 時間: 現実の約 1,000 年 (ブラク LC2 → ウルク IV) を、ゲームの 5〜10 年に縮める (思いつくまでの待ち時間を縮める。計画 3.)
- 印: サビ・アビヤドの 60〜77 個の印のかわりに、家ごとに 1 つ

**G5 とのつながり**: G5 の仕組み (もめごと・まとめ役・祭り・罰・村が分かれる) は G6 でも続く。人が増えて家が増えるほど、もめごとが増え、村が分かれやすい。記録とまとめ役が、それをおさえる。村を出た家は「分かれた家の村」になり、のちに交換の相手になることがある。町が小さくなる (後もどり) ことも起きてよく、そのことも記録する

**試したこと** (写しの木で、メモリの中だけ。くわしくは 0.): G5 の本物の 5 季節 (1709〜1829 日目の答え) と台本の 6 季節 (村が分かれる季節をふくむ) で、お題・気持ちのお題・state.json が今のコードと同じだった。G6 にした写しで、台本の答えで 24〜40 季節を進めた (結果は 0.)。`step.py season` も写しのデータで 3 回進め、「Society 2.0 が終わった」で止まった

**本人に確かめること** (おすすめを先に書いた。数はすべて【仮定】)
1. 町の人数の目安: **50 人 (おすすめ)** / 40 人 / 60 人 / 100 人 (計画のまま)。今の 25 人から、交換を続け、村が分かれる季節が半分あるとき、50 人の町にそろう見込みは 8 年で 5 割、10 年で 8 割 (40 人なら 8 年で 8 割、60 人なら 10 年で 5 割、100 人なら 15 年でも 1 割)
2. 計画の「ほかの村との交換が 4 季節以上続く」を町の条件に**残す (おすすめ)**。相手は毎季節同じ村でなくてよく、4 季節で 2 つ以上の村とする。考古学では交換は町よりずっと古いので、F1 だけにする案もある
3. 交換している村から「ここで暮らしたい」人が来る仕組みを**入れる (おすすめ)**。ブラクは移り住む人で大きくなった。入れないと、50 人に 10 年でそろう見込みは 4 割ほど
4. ほかの村は記録に残る出来事からだけ作り、**G6 の最初の季節の終わりに、必ず 1 つの村の人が交換をもとめて来る**形でよいか (おすすめ)
5. 町と記録は、**一度届けば届いたまま**にする (おすすめ)。あとで町が小さくなったら、そのことも記録して報告する。別の案は「同じ季節に両方」
6. 止まるのは、**両方そろった「Society 2.0 の終わり」だけ** (おすすめ)。そのとき第 4 部のまとめと動画を作る
7. **覚え** (記録のない量を幅で見せる。覚え違いのもめごと) を入れる (おすすめ)。入れないと、記録をつけても世界は何も変わらない
8. 記録の条件を「**粘土の板で量を確かめた**」にする (おすすめ)。板が使えるようになる目安 (数え札の季節 4 つ・1 季節 200 個) はこれでよいか。記録が町より先にそろいそう (現実は町が先で、文字は約 900 年あと) なので、そのまま違いとして報告する
9. 「**交換に行く**」を最初から入れる (おすすめ)。ないと、毎季節の交換が、ほかの村の人が来るかどうかの運だけになる
10. **家の物で交換する** ("家") を入れる (おすすめ)。家ごとの差が広がることがある
11. **黒曜石** (鎌が割れにくくなる) を入れる (おすすめ)。貝の玉 (飾り) は入れない
12. **印は家ごとに 1 つ** (家の代表が作る。手間はかからない) でよいか (おすすめ)
13. F は **4 つ** (F1 交換 / F2 印で封 / F3 町 / F4 物と数を分けて記す) でよいか (おすすめ)。数え札・封筒・板は出来事「記録」として残す
14. **大きな倉 (神殿)** は、いまは入れない (おすすめ)。町の条件にもしない
15. **名前**: 作った名前 30 個はもうすぐ使い切り、「ソル2」のような名前になる (写しで G6 を進めると、すぐに出た)。G6 から、新しく作った名前 30 個を足してよいか (おすすめ。G5 のあいだは変えない)
16. **3D**: 村を出た家の住まいを、出た日から描かない・G5 の出来事 (もめごと・祭り・まとめ役・分かれる など) も夜の知らせに出す (おすすめ: どちらもする。G5 の表示も変わる)
17. **調べの文書の直し** (14 か所。この文書の 24.): G6 を作るときに直す (おすすめ)

次にすること: 上の 1〜17 を本人と決めてから、この文書の 5. のコードを入れ (era2.py に約 1,100 行、world.py 3 行、step.py 約 20 行)、19. の試し方 A〜D で確かめ、計画書の 2.・2.2・5. に G6 の節を足す。

---

# G6 交易・町・記録: final implementation spec

This spec starts from the "emergent" design (nothing is declared; each mechanism answers a problem the villagers already have) and grafts in the best parts of the "minimal" and "historically faithful" designs. Every conflict between them is resolved explicitly in §1 and §2. All code in §5 was put into a scratch copy of the tree and run (§0); line numbers are at **HEAD `f8a9e46`** (era2.py 1829 lines), but every hook is given as a unified diff with context, so it also applies after small shifts.

## 0. What was verified, and how

**Remote diff (checked first, as the user asked).**
- At the start: `git fetch` showed local `claude/physics-engine-robot-simulator-xmyxdn` 1 commit ahead of origin (`bc2e440`, the live run's 「1829 日目から (季節)」, not yet pushed). The working tree was clean.
- During the session the remote moved twice: `f8a9e46` (another session: non-rep adults also answer a feeling and one line; `feelers`, `feeling_prompt`, `apply_feelings`, `p["feeling_day"]`, step.py and the workflow read `answers/dayNNNN/feeling/`) and then `ea1df79` (the live run's 「1859 日目から (季節)」). After that, HEAD = origin, 0 ahead / 0 behind. This spec is written against `f8a9e46` (era2.py, world.py, step.py are the same at `ea1df79`).
- Untracked files that are not mine: `sim/society/data/answers/day1859/` (earlier), `docs/research/historical_records.md`, `docs/research/modern_records.md`. I did not touch them, did not commit, did not run step.py or resume in the repo, and read state.json only with python3.

**Live state** (read-only): day 1889 (15年90日目), era G5, stage 2 opened at 1859 (15年60日目) through まとまり, no leader yet. At 1859: 25 people (16 adults, 9 children), 9 households, 6 family houses, 17 goats, 614 pots, 24 sickles, store 188,436 つかみ 草の種 + 14,205 木の実 (≈ 300 days), specialists ヨナ only, `next_name` 26 of 30, 0 fissions. The villagers have adopted many "report the amounts" laws since day 34 (L21, L59, L68, L86, L122) and, after the first 蓄え dispute, L141 「取った量と畑にまいた量を家ごとに分けて書き残そう」 (1739). The wish for records already exists; nothing in the world implements it yet.

**Checks run in a scratch tree** (`git archive HEAD sim/society` without `data/`, into `/tmp/g6judge/old` and `/tmp/g6judge/new`; §5 applied to `new`; inputs read from git or read-only from `data/state.json`):

| Check | Result |
|---|---|
| **A. Pre-G6 invariance.** OLD vs NEW, each in its own process. Start from `git show 5a17727:…/state.json` (day 1709). 5 real G5 seasons with the committed answers `answers/day1709 … day1829`, then 6 scripted G5 seasons whose answers carry every G6 field (`trade`, `seal`, `seal_store`, jobs 交換に行く / 記録をつける with `to`/`carry`/`what`/`how`), a feast, judge fields, and an injected stale dispute with `LEAVE_P` forced so that a **fission** happens in season 4. | All 11 seasons: season prompts and feeling prompts byte-identical; `json.dumps(state, sort_keys=True)` identical after removing the `g6_*` indicator keys; `"g6"` never created; `_rng` salts used {3, 7, 11, 29, 31, 37} in both (41 never); `answerers` identical (8 then 9 reps); the G6 jobs became 休む in both; 1 fission in both; the two result files were byte-identical. |
| **B. Unit checks.** | `_g6_side` (13 inputs), `_g6_goods` (aliases 麦/つぼ, unknown 石 dropped), `_tid`, `_g6_range` (200 draws: truth always inside, bounds multiples of 100, the truth is not the midpoint), `_g6_pay` (bad year pays no grain), zero indicators before G6, `check()` returns `"end"` exactly once, `_town` fails below 50 people. |
| **C. Trial runs** (G6 forced on a copy of the live state, scripted answers, policies open / trade / records / silent / closed, 4 seeds for open). | <!-- RESULTS_C --> |
| **D. `step.py season` smoke** (`SOC_DATA=/tmp/g6judge/smoke`, step.py patched as §18). | 3 seasons, exit 0 each. `*` lines show the G6 events and 「G6 の F1「村どうしの交換」に入った」; the G6 status line prints; with F3/F4 pre-filled, season 3 printed 「* Society 2.0 が終わった: 町 (1919 日目) と記録 (1889 日目) がそろった → 一時停止」, `hold` True, `g6.end` set, `status` printed 「一時停止中: Society 2.0 が終わったので、第 4 部のまとめ待ち」; app_data.json has `g6` and 3 edge places; node: `/Society 2\.0 が終わった/` matches, `/フェーズが .* に進んだ/` does not. |

**Note for the implementer.** A Bash heredoc of about 16k characters gets truncated; keep test scripts in a scratch directory. The scripts used here were `/tmp/g6judge/{patch.py, runA.py, runC.py, smokeD.sh, proj.py}` (scratch, not in the repo; §19 describes them so they can be rewritten).

---

## 1. Judging the three designs

Scores 1–10 (higher is better).

| Design | Historical fidelity at this scale | Emergence from people's decisions | Implementable, low risk to G3–G5 | Clarity of criteria / F | Factual narration | Total |
|---|---|---|---|---|---|---|
| **Minimal** (one abstract 南の村, `trade`/`seal`, 記録をとる, town 40 + pull, record by line count) | 5 | 5 | 9 | 8 | 7 | **34** |
| **Historical** (3 fixed NPC villages + daughters, trips, promises, envelopes, storehouse, obsidian, beads, satellite houses, town 60 + primacy) | 9 | 7 | 4 | 7 | 6 | **33** |
| **Emergent** (villages only from logged events, offers/loans/trips, 覚え, problem-first ladder, ration credit, town 50, record = tablet check) | 7 | 9 | 6 | 7 | 9 | **38** |

Why:
- **Minimal.** Very safe (one salt, few hooks, sound end branch), but the partner comes every season by rule, so trading is near-automatic and F1 is almost free; records only change prompt text and the talk limit; the record criterion (24 lines) is an arbitrary proxy for household count; people cannot go out to trade.
- **Historical.** Closest to the West Asian sequence (sealings → tokens → envelopes → number/kind signs; storehouse; obsidian; satellite clusters by origin), with an explicit scale table. But three villages exist by declaration (narration must say 「この世界の決まりで」), it is ~620 lines with promises, credit, beads, storehouse and spans of control, and trips count as household withdrawals (unfair G5 蓄え disputes).
- **Emergent.** Nothing is invented: another village exists only after a logged event (a fission, a visitor group saying where it came from, strangers coming to trade); every record tool opens only after the problem it solves has happened; 覚え gives records a real use. Weak points: partner demand (pots < people/2) is too small to sustain 4 seasons of exchange, trips charged to household flows, a midpoint-leaking memory range, a per-day RNG cache, an unused 「返して」 branch, and it moved the plan's 4-season exchange out of the town condition without asking.

**What was taken from each design**
- From **Emergent** (base): villages only from logged events (fission households, visitor origins, traders); offers 交換 / 貸して / 返す with answers "村" / "家" / false; the job 交換に行く with `then`; 覚え (ranges, complainant's claim, 覚え counter-incident); problem-first record ladder; token-need capacity (10 tokens/day, tablet 50); ration credit; record criterion = a check made with a tablet record; town = 50 + 2 partners + 2× the largest partner + 10% non-food producers; no new answerers.
- From **Minimal**: a guaranteed first contact at the end of the first G6 season; recorded disputes do not use the 2 talk slots; theft from a sealed store always becomes a dispute; extra house rings only in G6; the plan's 「交換が 4 季節以上続く」 kept in the town condition; `check()` returns `"end"` once and step.py prints 「Society 2.0 が終わった」 + a new workflow regex; test A with real G5 seasons; implementation in slices.
- From **Historical**: the explicit scale-factor table (§3); obsidian with a mechanical effect, using the same-draw-count trick in `_storage_season`; satellite house sites toward the village of origin (Brak clusters); randomness from a seed stored in state (`g6.seed`) instead of a per-day cache; per-season intake caps for partner demand; envelopes as a separate tool with a distinct effect; the storehouse kept as a question; the missing G5 event types in the 3D toasts; NAMES_G6 as a question; the literature list.

## 2. Overview and decisions (conflicts resolved)

| Question | Decision | Why |
|---|---|---|
| Where other villages come from | Only from logged G6 events: (1) every `g5.fissions` household becomes a dormant 「分かれた家」 node (also pre-G6 fissions; it is mentioned only when it first comes, so nothing is rewritten), (2) the base visitor group of a G6 season end is tagged with the stranger village it says it came from (existing or new), (3) strangers come to trade. **The first G6 season end always brings one stranger village.** At most 3 stranger villages. Off-map, 1–2 days' walk; never role-played. | Emergent (narration-safe) + Minimal (G6 starts visibly). Exchange existed since the first villages (obsidian), so we do not make the villagers "wait to invent" it (plan §3). |
| Town size | 50 (question 1). | 40 (Minimal) / 60 (Historical) / 50 (Emergent): 50 ≈ 1/55–1/110 of Brak LC2; projection §3. |
| 「交換が 4 季節以上続く」 | Kept in the town condition (plan, user-approved): a completed transfer in **each** of the last 4 G6 seasons, with **≥ 2 different villages** over those 4 seasons. F1 is the first exchange. | Minimal/Historical keep it; Emergent moved it out. Exchange predates towns, so question 2 offers the alternative. |
| How exchange happens | Offers at the meeting (village or household goods) **and** trips (交換に行く). Partner villages take goods only up to per-season caps and pay in the wanted good, else other goods; an unpaid remainder becomes a debt owed by the partner. | Without trips, 4 consecutive seasons would depend on chance; caps keep demand steady (Historical). |
| Who owns traded goods | "村" → village store / village pots, sickles, goats (owner None). "家" → that household's 倉 and goats. Pots, sickles and obsidian are always village things. Trips with village goods are **not** counted as the trader's household withdrawals. | Ur 2014 "great household"; avoids unfair 蓄え disputes (Emergent flaw). |
| Debts | Only partner → village/household (loans in a partner's bad year, unpaid trip remainders). No interest. No 「返して」 offers. | Interest-bearing debt is attested only ~2400 BC; the village never borrows in this design. |
| Unrecorded amounts | G6 only: per-household store flows are shown as ranges (independent lower and upper draws, so the truth is not the midpoint); disputes of kind 蓄え/刈る/倉/覚え carry the complainant's claim (true × U(1, 1+s)); paying by memory can raise a 覚え incident. Spread s = 0.05 × (households + open debts), ≤ 0.5; halved for a sealed household while the store was sealed. | Emergent; Johnson 1973 (information load). Debt-misremembering as *the* trigger of records is 【仮定】; stores and withdrawals are better attested, so both are used. |
| Record ladder | 印 (from G6 start) → 数え札 (after F2 and after one amount was settled by memory) → 封筒 (after tokens open and while a debt is open) → 板 (after ≥ 4 token seasons and one season needing ≥ 200 tokens). Use is chosen. | User's order 印 → トークン → 文字 (part2.md 6.3); problem first (Emergent); envelopes from Historical. |
| Record criterion | ≥ 1 amount checked with a 板 record (a dispute taken up at the meeting, or a debt repaid). | Uruk IV standard: number and kind signs separate (Englund 2011); counting tokens alone are not writing. |
| Holds | None at F1–F4 (区切り). One hold at the end of Society 2.0 (F3 and F4 both reached at any time; days are sticky). A town that later falls below the bar is logged (町). | Plan 2.1; going backwards is allowed. |
| Randomness | One new salt: `_rng(state, 41)` once per G6 season end (and once when `g6` is created at the first G6 meeting). All meeting/day randomness comes from `g6.seed`, the last draw of that stream (`_g6_r(state, k)`). | 41 % 31 = 10 is free. Historical's stored-seed idea is simpler and process-independent. |
| Storehouse, beads | Not built (question 14). | Keep G6 smaller; no criterion needs them. |

## 3. Scale-down factors

| Quantity | Real | Sim | Factor | Basis |
|---|---|---|---|---|
| Town | Tell Brak LC1–2 ≈ 55 ha 【文献】(Ur, Karsgaard & Oates 2007; Ur et al. 2011); low-density northern urbanism 【文献】(McMahon 2019) at 50–100 people/ha 【仮定】 → 2,750–5,500 | **50** | ≈ 1/55–1/110 | plan §2 allows 1/10–1/100 |
| Partner villages | LC small centres 10–20 ha 【文献】(Lawrence & Wilkinson 2015); village densities 83–139/ha 【文献】(Kramer 1982; Watson 1979) | 10–25 people | ≈ 1/100 | same scale as the town |
| Primacy | Brak 55 ha vs largest neighbour ≈ 15 ha (≈ 3.7×) 【文献】(Ur et al. 2007) | ≥ 2× the largest partner | lowered | 【仮定】 |
| Distance | walking with loads ≈ 30 km/day 【文献・二次】(Hallan Çemi → Nemrut Dağ, ~100 km in 3 days) | 1–2 days (≈ 25–60 km), off-map | 1/1 | research §7(c) asks ≥ 1 day |
| Satellites | Brak LC1–2 clusters 200–400 m from the central mound 【文献】(Ur et al. 2007) | G6 newcomers build 11–15 cells (275–375 m) toward their village | 1/1 | migration into Brak 【文献・二次】(isotope/dental studies 2020, 2022) |
| Seals | Sabi Abyad ≥ 60–77 seals 【文献】(Akkermans & Duistermaat 2004); Arslantepe A340 ≈ 30 seals on 175 sealings 【文献】(Frangipane et al. 2007) | 1 per household (9–20) | ≈ 1/3–1/10 | 【仮定】 |
| Load | – | 20 kg per traveller (草の種 900 つかみ, 土器 4, 鎌 10, 干し肉 100) | – | 【仮定】(porter rule of thumb, unverified) |
| Time | Brak LC2 (~4200 BC) → Uruk IV (3350–3200 BC) ≈ 1,000 years | expected 5–10 game years (20–40 seasons) | ≈ 1/100–1/200 | plan §3: compress waiting-to-invent, not biology |

**Projection** (Monte Carlo, 1,500 runs from today's 25 people, the code's birth/death/visitor rates, every known partner traded with every season, the town rule of §16; scratch `proj.py`). P(town reached within 5 / 8 / 10 / 15 years), median season:

| Town size | No fission | Fission in 50% of seasons |
|---|---|---|
| 40 | 0.63 / 0.93 / 0.98 / 1.00, median 18 | 0.40 / 0.80 / 0.91 / 0.99, median 23 |
| **50** | 0.33 / 0.85 / 0.96 / 1.00, median 24 | **0.12 / 0.53 / 0.77 / 0.95, median 31** |
| 60 | 0.06 / 0.59 / 0.84 / 0.99, median 30 | 0.01 / 0.23 / 0.46 / 0.86, median 39 |
| 100 | – / – / 0.04 / 0.55 | – / – / 0.00 / 0.13 |
| 50, no town pull | – / 0.19 / 0.38 / 0.72 | – |
| 50, people accept only half the groups | – | 0.00 / 0.05 / 0.11 / 0.35 |

Median population at +5 / +10 / +15 years: 46 / 73 / 102 (no fission), 38 / 58 / 77 (fission in half the seasons). The trial runs (§0 C) grew faster than this model, because each tagged visitor group can create a stranger village, so 3 partners appear within a few seasons.

## 4. State schema

Everything is created lazily by `_g6(state)` at the first G6 meeting (`apply_answers` → `_g6_new_season`). Before G6, `"g6" not in state["era2"]` (checked, §0 A).

```python
state["era2"]["g6"] = {
  "start": 1979,                 # G6 の最初の集まりの日 (G6 の条件は、ここからのことだけで数える)
  "seed": 123456789,             # 集まりと 30 日の乱数のもと (塩 41 の列から。季節の終わりに引き直す)
  "meets": [1980, 2010],         # G6 の集まりの step_day (「この 4 季節」を数える)
  "meet_first": 51234,           # この前の集まりの最初の出来事の番号 (お題の「この前の集まりから起きたこと」)
  "others": [{                   # ほかの村 (地図の外。決まりで動く。演じない)
      "id": "N1", "name": "東の村", "kind": "よその村" | "分かれた家", "household": None | "フウの家",
      "dir": "東", "way": "東へ", "days": 1 | 2, "edge": [79, 40],   # 3D で歩いて行く地図の端
      "since": 1979, "known": None | 1979,                           # 知った日 (分かれた家の村は、来るまで None)
      "people": 15, "goats": 6, "grain": 1500, "pots": 3, "sickles": 1, "obsidian": 0, "has_obsidian": False,
      "bad": None | 2099,         # 苦しい年 (夏のはじめに決まる日)
      "trust": 0.5,               # 来る見込みに効く (0〜1)
      "contacts": [2010, 2040]}], # 交換・貸し借り・返すが済んだ季節 (step_day)
  "next_other": 2, "next_offer": 1, "next_debt": 1, "next_trip": 1,
  "offers": [{"id": "T3", "other": "N1", "kind": "交換" | "貸して" | "返す", "give": {"ヤギ": 1}, "want": {"土器": 7, "鎌": 1, "草の種": 20},
              "debt": "D1",        # 返すときだけ
              "goats_in": [{"sex": "メス", "age": 2}], "mem": {"village": 1.12, "other": 0.91}, "day": 2009}],
  "debts": [{"id": "D1", "other": "N1", "lender": "村" | "ナギの家", "goods": {"草の種": 1800}, "day": 2010, "due": 2130,
             "proof": None | "数え札" | "封筒" | "板", "mem": {"village": 1.1, "other": 0.9},
             "status": "まだ" | "返した" | "返されない", "end": None}],
  "taken": {"N1": {"土器": 5}},  # この季節に、その村が受けとった物 (上限のため。季節の終わりに空にする)
  "moved": {"土器": 9, "ヤギ": 1},  # この季節に村が出し入れした物 (「交換」の記録の量。季節の終わりに空にする)
  "seals": {"川辺の家": {"day": 1980, "by": "セナ"}},
  "store_sealed": None | 2010,    # 村の蓄えに封をした季節の step_day
  "season_seals": {"川辺の家": 30, "(印なし)": 12}, "opened": {"蓄え:川辺の家": 2031},  # この季節の封のかけら (季節の終わりに空にする)
  "sealings": {"川辺の家": 120}, "seal_seasons": 2,     # 封のかけらの合計 / 2 つ以上の家の印で封をした季節の数 (F2)
  "jobs": {"ハユ": {"activity": "交換に行く", "to": "N1", "carry": {"土器": 4}, "want": "ヤギ", "then": "採集", "house": False},
           "セナ": {"activity": "記録をつける", "what": ["蓄え", "交換", "刈る"], "how": "数え札"}},   # 集まりで空にする
  "keep_days": {"セナ": 30}, "trips": {"ハユ": {...}},  # この季節 (集まりで空にする)
  "trip_log": [{"id": "R1", "who": "ハユ", "to": "N1", "start": 2010, "days": 1, "side": "村", "took": {...}, "got": {...},
                "back": {...}, "goats_in": [...], "debt": None | "D2", "state": "帰った", "end": 2012}],
  "records": [{"day": 2039, "keepers": {"セナ": [30, "数え札"]}, "need": {"蓄え": 229, "交換": 12, "刈る": 0},
               "done": {...}, "how": {"蓄え": "数え札", ...}, "complete": ["蓄え", "交換"], "envelope": None | "封筒" | "板"}],  # 最後の 8 季節
  "cover": {"蓄え": "数え札"},    # この季節に全部残せた記録 (もめごとと出し入れの見え方に使う)
  "credit": {"アルの家": 30},     # 配給の記録: 「入れた」に数える働いた日 (蓄えを全部残せた季節だけ)
  "open": {"印": 1979, "数え札": None, "封筒": None, "板": None},       # 使えるようになった日
  "token_seasons": 0, "big": 0,  # 数え札か板で記録した季節の数 / 1 季節に要った数え札のいちばん多い数
  "unchecked": 0, "misremember": 0, "checked": {"数え札": 0, "封筒": 0, "板": 0},
  "exchanges": 0, "joined": 0, "obsidian": 0, "obs_sickles": 0,
  "nonfood": ["ヨナ", "セナ"],   # この季節に、作ることか記録に 20 日以上を使った人
  "shown": {"day": 2039, "how": None | "数え札", "rows": {"アルの家": [[700, 1100], [0, 0]]}},  # 前の季節の出し入れの見え方
  "town_seen": None, "town_low": 0, "log": [...], "end": None | {"day", "town", "record", "first"}}
person["from_village"] = "N1"            # G6 でほかの村から来た人だけ
person["today"]["away"] = True           # 交換に行っている日 (G6 だけ)
dispute["record"] = "数え札" | "板"        # G6: 記録のあるもめごと
dispute["harm_true"], dispute["mem"]     # G6: 記録のないもめごと (harm は言い出した家の覚え)
dispute["checked"] = day                 # G6: 集まりで記録を見て確かめた
incident["sealed"] = True                # G6: 封をした倉の封が割れていた
visitor_group["from"], ["seed"]          # G6: 来たほかの村 / G6 の群れの乱数
```

No key is added to `_house()`, `e2["jobs"]`, `KINDS`, `answerers()` or `feelers()`.

---

## 5. Code

### 5.1 New section in `era2.py`

**Where:** after `_pay` (ends L1059 at f8a9e46) and before `def _sow` (L1061). It uses `GRAIN`, `DAY_FOOD`, `_homes`, `_leader`, `_g5`, `_incident`, `_num`, `_yes`, `_house`, `_homes_built`, `store_days`, `_name`, all defined earlier or resolved at call time.

<!-- CODE:SECTION -->

### 5.2 Hooks in existing `era2.py` functions

Unified diff against `f8a9e46` (the two new blocks are shown as one-line placeholders; they are §5.1 and §5.4). Every changed line is either gated by `era_at_least(state, "G6")` or reads a key that only G6 code creates (`seed`, `from`, `sealed`, `record`, `harm_true`, `away`), so the arithmetic and the order of random draws before G6 are unchanged (§0 A).

<!-- CODE:ERA2_HOOKS -->

What each hook does:
- `acts2`: 交換に行く from G6; 記録をつける only after 数え札 opens (read with `.get`, never creates state).
- `apply_answers`: `_g6_new_season` at the start (resets jobs, keep days, trips; records the meeting); `_g6_job` after a plan is set (details go to `g6.jobs`, never `e2["jobs"]`); `_g6_collect` after `_g5_collect` (respects `own`); `_g6_meeting` after `_g5_meeting`, before `_settle_visitors`.
- `_settle_visitors`: a G6 group (with `seed`) creates its members from its own `random.Random(seed)`; members get `from_village`; the 加わる text keeps 「よそから来た A・B が、」 so `_sync_households` still parses it; refusal says 「…へ帰っていった」; `_g6_settled` updates the partner.
- `_day`: 記録をつける in the work chain; `_g6_trips_day` after the chain (before the evening takes, `_feed` and `world.evening`, so a raised `spent` is eaten); travellers (`today.away`) neither pick nor harvest.
- `_feed` / `_flow`: sealing pieces when a sealed household opens its 倉 or takes from the sealed village store (1 per household per day).
- `_craft`, `_storage_season`: obsidian blades; the sickle loop still draws once per item, so the salt-31 stream is unchanged.
- `_house_site(state, h)`: identical sequence before G6 (the ring check moved into `ok()`); in G6 rings 11/13/15, and households from a partner village try the ±60° sector toward it first.
- `_steal`, `_incident`: sealed stores are robbed last; a broken seal logs 封 and the incident is `sealed` (always becomes a dispute, `_g5_season_end`); in G6 the theft text has no amount.
- `_dispute`, `_g5_season_end`: record or claim on new disputes; G6 texts without exact amounts when there is no record; merging keeps the claim ratio; ration credit only in the 蓄え comparison (`last_flow` is still the raw flow).
- `_g5_meeting`: a recorded dispute is checked (確かめる) and does not use a talk slot.
- `_verdict`: after a つぐなう payment without a law, `_g6_after_pay` (覚え incident).
- `_season_end`: `_g6_records` before `_g5_season_end` (so new disputes know the record), `_g6_season_end` after it (so a fission in this season already becomes a dormant village), `_note_mode` last.
- `indicators`, `CRITERIA`, `SUBSTEPS`, `check`: §16. `_g5_text`, `season_prompt`: §15.

### 5.3 `world.py`

<!-- CODE:WORLD -->

Before G6 these acts are never planned (`apply_answers` filters by `acts2`), so nothing changes. At camp the predator check never draws, so the per-person random sequence is the same as for 土器づくり.

### 5.4 Prompt code (place before `def season_prompt`)

<!-- CODE:PROMPT -->

---

## 6. Other villages

- **Dormant daughters.** At every G6 season end, each `g5.fissions` entry without a node becomes one: `kind` 分かれた家, name 「フウの村」 (household name without の家), 1 day away, people = those who left, goats and grain = what they took, `known` None. It appears in prompts only after its first contact: 「前に村を出たフウの家の人たちが、村に来た。いまは フウの村 (東へ歩いて 1 日) で暮らしているという」. Texts never name individual leavers as alive (they are `alive=False, left=day` and stay so).
- **Visitor origins.** If the base visitor roll (salt 7, unchanged) created a group at this season end, G6 tags it with a stranger village: an existing one with p 0.5 (always when 3 exist), else a new one. Logged 「よその群れの A・B は、東の村 (東へ歩いて 1 日) から来たと言った」. Groups that came before G6 keep 「よその群れから」.
- **Traders.** If fewer than 3 stranger villages exist: always at the first G6 season end (if none exists), afterwards with p 0.10 per season. 10–25 people, goats 0.4/person, grain 100/person, pots people/4, sickles people/8. The 2nd stranger village is 2 days away and has obsidian (20, +8 per season up to 40).
- **Directions** are drawn among unused 南 (39,79, river exit), 北 (49,0, river exit), 東 (79,40), 西 (0,40). Labels say only direction and days (「川にそって南へ歩いて 2 日」); the world has no river flow direction, so never 上流/川下.
- **Season dynamics** (salt-41 stream): +1 person with p = people × 0.005; at the start of summer a bad year with p 0.2 (grain falls to 20/person; otherwise +100/person up to 300/person); goats ×1.3 in spring up to the number of people; pots −3%, sickles −5% per season.
- **Contact**: each known or dormant node comes with p = min(0.8, CONTACT_P × trust / 0.5) (分かれた家 0.35, よその村 0.15), or 0.8 when a debt it owes is due; not if villagers visited it this season. trust +0.1 per completed transfer or accepted group, −0.1 per refused offer or group, −0.2 per 覚え on repayment or an unpaid debt after a year.
- **Offers** (in this order): bad year and grain < 60/person → 貸して (草の種 = people × 120, rounded to 100, ≤ 3000); a due debt it can at least half repay → 返す (brings the exact amount if the debt has an envelope or tablet proof, otherwise its own memory = true × U(1−s, 1)); otherwise 交換: up to 3 goats (keeping 2), or obsidian (5–15), for its wants of equal value in the order 土器, 鎌, 草の種. Goat sexes/ages and memory factors are drawn at the season end and stored in the offer, so the meeting is deterministic.
- **Per-season caps** (what a partner takes in one season): 土器 max(3, people/3), 鎌 max(1, people/6), 草の種 10/person (100 in a bad year).

## 7. Exchange at the meeting, loans and repayment

- Answer `"trade": {"T3": "村" | "家" | false}`; rep-weighted (`fam`), a non-rep leader counts only for themself and cannot answer "家".
- "村" by more than half of adults, **or by the leader alone**, → village goods. Otherwise the households whose reps answered "家" and can pay; the one with the most food in its 倉 takes it. Otherwise refused (trust −0.1, logged 「…の申し出 [T3] は受けなかった (村 a・家 b・受けない c / 大人 n)」).
- 交換: our goods to the partner, its goods to us (goats with the pre-drawn sexes/ages; owner None or the household). 貸して: a debt `D#` (lender 村 or household, due one year later).
- 返す (not voted): the goods go to the lender (to the village if the household has left). Proof 封筒 or 板 → exact, 確かめる, `checked[proof] += 1`; proof 数え札 → the village knows the exact number, the partner brings its memory, the shortfall stays as an open debt, 確かめる; no proof → the debt closes, `unchecked += 1`, and if the village's memory (true × U(1, 1+s)) exceeds what was brought by more than 25%: 覚え event, trust −0.2.
- Every completed transfer appends the season's `step_day` to the partner's `contacts`, `exchanges += 1`.

## 8. Trips (job 交換に行く)

- Job: `{"activity": "交換に行く", "place": "camp", "to": "N1", "carry": {"土器": 4}, "want": "ヤギ", "then": "採集", "house": false}` (job or family). `then` must be in `acts2` (default 休む). `house: true` only for the household's own rep answer and only for a household with a built home.
- **Departure** on the season's first day: the load is scaled so that Σ n / LOAD ≤ 1 (goats ≤ 4 extra). Goods leave the village stocks (or the household's 倉 and goats). If the target is unknown, the person is injured that day, or nothing could be taken: 「…は、…、交換に行かなかった」 and the plan switches to `then`.
- **Schedule** (D = days): walk on days 0…D−1, trade on day D, walk back D+1…2D, the plan becomes `then` after day 2D. 3 days for D = 1, 5 for D = 2. On walking days `today.spent += world._walk_kcal(p, 30000) × 1.4` (the load). `today.away` on all trip days.
- **Barter**: the partner takes only what is under its caps; pays in `want`, else ヤギ / 黒曜石 / 草の種 (keeping 2 goats; no grain in a bad year); unwanted goods come back; a remaining value ≥ 50 becomes a debt in the wanted good (if worth ≥ half a unit) or in 草の種, due two seasons later.
- **Return**: p 0.03 a goat strays or 10% of the grain is spilled; p 0.005 × 2D the traveller is hurt (`injured = 2`). Goods go to the side that carried them. Trip goods are **not** household withdrawals or deposits (the village account is the 「交換」 record).
- A season cut short by a famine break returns unfinished trips at the season end.
- Note (observed in the trial): 4 pots (160) cannot buy a goat (375); goats come mostly from offers at the meeting, trips bring grain or obsidian, or several travellers go together. This follows from the values and is left to the players.

## 9. Seals and sealings

- `"seal": true` from a household's own rep: the household seal (once). From then on its 倉 is sealed; theft from it is logged as 封 (「ナギの家の倉の封が割れていた: …」) and always becomes a dispute; sealed stores are robbed last.
- `"seal_store": true` by more than half of adults or by the leader: the village store is sealed this season. Every day a household takes from it leaves one piece with its seal, or an unstamped piece (「(印なし)」); a household opening its own sealed 倉 also leaves one.
- Season end: event 封 「この季節、印で封をした倉や村の蓄えが開けられた (割った封のかけらは取っておいた): 川辺の家の印 30 回、…」. **F2** = a season in which pieces from ≥ 2 households' seals were left (`seal_seasons ≥ 1`).
- Narration says 「家の印」「封をした」, never 「持ち主の印」 (both the communal-storage and private-property readings exist: Akkermans & Duistermaat 1996/97; Duistermaat 2012).

## 10. Memory (覚え), G6 only

- Display (§15): per-household flows of the last season are exact if that season's 蓄え record was complete, otherwise `[lo, hi]` with lo = true × U(1−s, 1) and hi = true × U(1, 1+s), rounded down/up to 100, drawn at the season end and stored in `g6.shown` (prompts stay deterministic).
- Disputes created in G6 (蓄え, 刈る, 倉, 覚え; not ヤギ, whose damage is visible): with a complete record of the same kind (蓄え, 刈る) → `record`, exact. Otherwise `harm_true`, `harm` = true × U(1, 1+s) (the complainant's claim), `mem` = U(1−s, 1) (the other house's memory factor). The dispute and incident texts drop exact numbers.
- After a つぐなう payment without a record or law: `unchecked += 1`; if paid > true × mem × 1.25 → event 覚え and an incident of kind 覚え (payer → complainant). 覚え disputes do not create further 覚え incidents. 覚え is **not** added to `KINDS`, so `_penalty` parsing is unchanged.

## 11. Records: ladder, keeper, ration credit

- **Ladder** (each opening logs 記録 with `tool=`; FACTS for a tool appear only after it opens; nothing is said about unopened tools):
  - 数え札: `seal_seasons ≥ 1` and `unchecked ≥ 1`.
  - 封筒: 数え札 open and a debt is open.
  - 板: 数え札 open, `token_seasons ≥ 4`, `big ≥ 200`.
- **Keeper** (job 記録をつける, camp): `{"what": ["蓄え", "交換", "刈る"], "how": "数え札" | "封筒" | "板"}` (opened tools only; default 数え札, all three). Daily event 記録をつける 「セナ がキャンプで、粘土の数え札を作り、村の蓄えへの家ごとの出し入れ … を数えた」.
- **Season record** (`_g6_records`, before `_g5_season_end`): tokens needed — 蓄え = (in + out + own-field sowing) / 100 つかみ + work days / 10; 交換 = units moved (TOKEN per good) + debts made this season; 刈る = reaped-for-others / 100. Capacity = days × 10 (数え札, 封筒) or × 50 (板), filled in each keeper's `what` order. A complete kind sets `cover[kind]` (板 if a tablet keeper contributed). A complete 交換 record gives this season's debts `proof` 封筒 / 板 (if such a keeper recorded 交換) or 数え札. Event 記録 「セナ が、この季節の 村の蓄えへの家ごとの出し入れ (全部残せた。229 / 229 個分) … を残した」.
- **Ration credit**: with a complete 蓄え record, each household's craft, keeping and trip days × DAY_FOOD count as 入れた in the G5 蓄え comparison (rations in proto-cuneiform: Englund 2011; Arslantepe meal distribution: Frangipane et al. 2007; the credit rule is 【仮定】). Specialists' households otherwise look like over-takers (アルの家 took 1425 and put in 0 in spring 1769).
- **Use**: recorded disputes are checked (確かめる) at the meeting and do not use a talk slot; debts with proof are checked on repayment.

## 12. Town pull, satellite houses, obsidian, names

- **Town pull**: each known partner with ≥ 12 people and a transfer in the last 4 meetings sends a group with p 0.15 × min(1, store_days/120) × (2 in its bad year) per season. Group [1,2,2,3], ages as visitors, names `_g6_name` (= `_name(next_name)` now; NAMES_G6 if question 15 is approved), appended to `e2["visitors"]` with `from` and `seed`; logged 訪れる 「東の村 (東へ歩いて 1 日) から ヨナ2 (男、26 歳)、… がやって来て、「ここで暮らしたい」と言った」. Accepted → partner people decrease, `joined += n`. Migration into Brak 【文献・二次】; the rate is 【仮定】.
- **Satellite houses**: §5.2 `_house_site` (Brak clusters by origin).
- **Obsidian**: village obsidian (from trade) goes into sickles made by 道具づくり (1 per sickle); those break at half rate.
- **Names**: NAMES has 30; the trial already produced ソル2, ユノ2, ヨナ2 (question 15). If adopted, `_g6_name` takes from a new list `NAMES_G6` (30 invented names, each checked against real words as for NAMES) once `next_name ≥ 30`, only in G6.

## 13. Order of computation

- **Meeting** (`apply_answers`): `_g6_new_season` → per answer (`_g6_job`, `_g6_collect`) → talk → laws → `_g5_meeting` (recorded disputes 確かめる, verdicts may raise 覚え incidents) → `_g6_meeting` (seals → village store seal → offers: 交換 / 貸して / 返す) → `_settle_visitors` (base and partner groups) → `_eat_goats`. `apply_feelings` follows (step.py).
- **Day**: `world.simulate_day` → work chain (+ 記録をつける) → `_g6_trips_day` → evening takes / sowing / harvest (travellers skip) → `_feed` (sealing pieces, theft) → `world.evening`.
- **Season end**: … G3 storage → `_sync_households` → `_g6_records` → `_g5_season_end` → `_g6_season_end` (unfinished trips → dormant daughters → visitor origins → traders → node dynamics → contacts and offers → partner groups → overdue debts → sealing summary and F2 → shown flows → non-food list → ladder → town → log → reset → `seed`) → `_note_mode`.
- **check** (step.py): `check_substeps` (F1–F4 区切り) → indicators → end branch.

## 14. Events

`G6_EVENTS = ("よその村", "交換", "貸し借り", "覚え", "印", "封", "記録", "確かめる", "町")` (prompt list since the meeting; step.py printer). Daily per-person types, not in G6_EVENTS: 交換に行く, 記録をつける. Reused: 訪れる, 加わる, 去る, もめごと, 区切り, フェーズ. Data keys: `other, offer, debt, trip, household, dispute, how, tool, count, owner, home` — never `kind`, `who`, `text`. No text contains 「フェーズが…に進んだ」 except the real phase change.

| Type | When | Text (template) |
|---|---|---|
| よその村 | first contact (trader) | 「東の村 (東へ歩いて 1 日) の人たちが、交換をもとめて村に来た。ヤギ 1 頭 を出すので、土器 7 個・鎌 1 本・草の種 20 つかみ がほしいと言った [T2]」 |
| よその村 | first contact (daughter) | 「前に村を出たフウの家の人たちが、村に来た。いまは フウの村 (東へ歩いて 1 日) で暮らしているという。…」 |
| よその村 | origin of a visitor group | 「よその群れの コハ・スイ は、西の村 (西へ歩いて 2 日) から来たと言った」 |
| よその村 | refused offer | 「季節の集まりで、東の村 の申し出 [T3] は受けなかった (村 2・家 0・受けない 9 / 大人 16)」 |
| 交換 | at the meeting | 「季節の集まりで、村は、村の物で 東の村 の申し出 [T2] を受け、土器 7 個・鎌 1 本・草の種 20 つかみ を ヤギ 1 頭 (メス 2 歳) と取り替えた (村 12・家 0・受けない 0 / 大人 16)」 |
| 交換 | on a trip | 「サエ は 南の村 で、草の種 600 つかみ・鎌 2 本 を渡し、黒曜石 18 個 を受けとった (受けとってもらえなかった 鎌 1 本 は持ち帰る)」 |
| 貸し借り | loan / repaid by memory / unpaid | 「季節の集まりで、村は、村の物で 南の村 に 草の種 1800 つかみ を貸した [D1] (1 年のうちに同じ量を返すと言った。…)」 / 「…の分として 草の種 1500 つかみ を返した (村が受けとった。記録はなく、量は覚えで決めた)」 / 「[D1] (…) は、返されないまま 1 年たった」 |
| 覚え | repayment or payment by memory | 「南の村 の人は、[D1] の分として 草の種 1500 つかみ を返した。村の覚えでは 草の種 2000 つかみ を貸したはずだった (記録はない)」 / 「トワの家は、もめごと [M10] でスイの家に草の種にして 約 20 つかみ 分を払ったが、トワの家の覚えでは 約 15 つかみ 分だった (記録はない)」 |
| 印 | seal made | 「川辺の家の代表の セナ が、家の印 (焼いた粘土に形を刻んだもの) を作った。これから川辺の家の倉の口は、粘土でふさいで川辺の家の印を押しておく」 |
| 封 | store sealed / pieces / broken seal | 「この季節は、村の蓄えの土器の口を粘土でふさぐことになった。…」 / 「この季節、印で封をした倉や村の蓄えが開けられた (割った封のかけらは取っておいた): …」 / 「ナギの家の倉の封が割れていた: ひどく空腹の X (Yの家) が、封を割って食べ物を取って食べた」 |
| 記録 | season record / tool opens | 「セナ が、この季節の … を残した」 / 「印で封をするようになり、記録のない量を覚えで決めることも起きた。これからは、粘土の数え札で量を数えて残せる (主な仕事「記録をつける」)」 |
| 確かめる | dispute / repayment checked | 「季節の集まりで、もめごと [M13] の量を、数え札の記録で確かめた (草の種にして 56 つかみ 分)」 / 「…封筒を割って、貸した数 (…) を確かめ、村は … を受けとった」 |
| 町 | town first reached / below for 1 year | 「村の人は 52 人で、交換した村のうちいちばん大きい村 (約 21 人) の 2 倍をこえた。この 4 季節は毎季節ほかの村と交換し、相手の村は 2 つ。…」 / 「町の目安を下回ったまま 1 年たった (…)」 |
| 交換に行く (daily) | depart / walk / return / not gone | 「ハユ が、村の 土器 4 個 を持って、東の村 (東へ歩いて 1 日) へ交換に行った」 / 「ハユ が、東の村 への道を歩いた」 / 「ハユ が 東の村 から帰った (草の種 160 つかみ を持ち帰った)」 / 「ハユ は、行き先の村が分からず、交換に行かなかった」 |
| 記録をつける (daily) | keeper | 「セナ がキャンプで、粘土の板に、物のしるしと数のしるしを分けて押し、村の蓄えへの家ごとの出し入れ を記した」 |
| フェーズ | end of Society 2.0 (step.py) | 「Society 2.0 の終わり: 町 (2399 日目) と記録 (2219 日目) がそろった (先にそろったのは 記録)」 |

Dates in event texts and prompts stay serial 「N 日目」. Everything shown to the user (app, video, narration, reports) uses 「15年60日目」 (day // 120 年, day % 120 + 1 日目; daily_run.md, 2026-10-09); documents add the serial day.

## 15. Prompt changes (all empty before G6)

- **FACTS** (§5.4): `FACTS_G6` always in G6 (ほかの村 / 交換に行く / 値うち / 覚え / 印); `FACTS_TOKEN`, `FACTS_ENVELOPE`, `FACTS_TABLET` only after each opens; `FACTS_OBSIDIAN` after the obsidian village is known or the village has obsidian. The town pull, the criteria and unopened tools are not revealed (as in earlier phases).
- **`_g6_text`** 「## ほかの村・印・記録」 after the G5 section: known villages (id, direction, days, kin or stranger, people rounded to 5, what they can give, what they want, first day, seasons traded, bad year), offers, open debts (exact with proof, else the village's memory), seals, whether the store was sealed, last season's record, opened tools, village obsidian, last season's flows (exact or ranges), G6 events since the meeting (last 12). In G6 the G5 section no longer prints the exact `last_flow` line.
- **G5 dispute rows** in G6: 「(草の種にして 56 つかみ 分。数え札の記録がある)」 + 「この季節の集まりで、記録を見て確かめる」, or 「(言い出した家の覚えでは、草の種にして 約 72 つかみ 分。記録はない)」.
- **いま**: item 「8. ほかの村・印・記録」; 「今の気持ち」 becomes 9 (`7 + bool(g5_now) + bool(g6_now)`); a line under 2. 「交換に行く・記録をつけるは camp と書く (…)」; the rep's family text adds 「・申し出 (trade)・村の蓄えの封」.
- **Visitors**: in G6 all groups are listed, one line each with its origin; `accept` names every group.
- **JSON**: `"trade": {"T3": "..."}, ` (if offers), `"seal": false, ` (own rep, household without seal), `"seal_store": false, `.
- Placeholder policy: "..." for trade (unparseable → not counted); false for seal and seal_store (false = no); job examples are given in the 8. text, not in the JSON.
- Size: about +3–4k characters in a full G6 prompt.

**Rendered example** (trial run "open", seed 0, after 8 seasons; rep of a household; excerpt):

<!-- PROMPT_EXAMPLE -->

## 16. Indicators, CRITERIA, SUBSTEPS, end of Society 2.0

- `_g6_indicators` (§5.1) adds 20 keys, all prefixed `g6_`, with a zero base before G6 (test A strips `g6_*`).
- **F1 村どうしの交換**: `exchanges ≥ 1`. **F2 印で封をする**: `seal_seasons ≥ 1`. **F3 町**: `_town(state)["ok"]`. **F4 物と数を分けて記す**: `checked["板"] ≥ 1`. Logged once each as 区切り with the day (`check_substeps`), any order.
- **Town** (`_town`): alive people ≥ 50; the last 4 G6 meetings each have a completed transfer with some village; ≥ 2 villages over those 4; people ≥ 2 × the largest of those partners; non-food producers this season (G3 specialists with ≥ 20 craft days ∪ keepers with ≥ 20 days) ≥ 10% of adults.
- **CRITERIA["G6"]**: both `g6_town_day` and `g6_record_day` set (from the G6 F3/F4 substeps), i.e. each reached at least once.
- **`check()`**: if met and era is the last era and `g6.end` is unset → set `g6.end = {day, town, record, first}` and return `"end"` once; afterwards False. **`"end"` is truthy**, so step.py must test `r == "end"` before the old phase branch (§18), or it would log 「フェーズが G6 … に進んだ」.
- **Why the criteria cannot pass by accident**: every counter starts at the first G6 meeting; F1 needs a transfer someone agreed to; F2 needs seals made by reps and a sealed store or 倉 opened by two households; tokens need an amount settled by memory; tablets need 4 token seasons that people chose to keep and a busy season; F4 needs a recorded amount actually checked; the town needs G6 trading in 4 consecutive seasons with 2 villages, growth to 50 and specialists that season. Pre-G6 pots, houses and people never satisfy anything alone. Earliest: F2 at the end of G6 season 1 or 2, F1 season 2, F4 around season 8, F3 bound by population.

## 17. Interaction with G5 (all G5 mechanics keep running)

- **Leader**: can decide village trade and the store seal alone (like the feast; Stein 1994), judges recorded disputes (checked), can `call` 交換に行く or 記録をつける (joint work counts as before), is not automatically non-food. A non-rep leader cannot seal or answer "家".
- **Disputes**: more households (partner groups) → stress up to 0.9 at 10 households → more disputes; 覚え adds a fifth source. Records cut 覚え disputes and free talk slots; the leader judges any number. This is the intended link records → fewer stale disputes → less fission → the town holds.
- **Fission**: unchanged (≤ 1 household a year, guards). A G6 fission becomes a dormant daughter village at the same season end; its house stays drawn unless question 16 is approved; the town may drop below the bar (logged after 4 seasons). Daughters are never merged back; their people stay `left`.
- **Rep mode**: no new answerers; one answer per household rep (+ leader); non-rep adults keep answering only the feeling prompt (`feelers`, f8a9e46), which does not show G6 sections.

## 18. step.py, resume.py, workflow, app, charts, docs

**step.py** (diff against f8a9e46; tested in §0 D):

<!-- CODE:STEP -->

**tools/society2_seasons_workflow.js**, before the phase regex (L43):
```js
  if (/Society 2\.0 が終わった/.test(out)) return { stopped: d, why: 'society2 end', out, log: log_ }
```
(`why: 'end'` is already used for "steps done", so use a different word.) A hold also stops the next loop at the status check ('bad status').

**resume.py**: L55 work types += 交換に行く, 記録をつける; `firsts` (L65) += 「交換に行く": "初めてほかの村へ交換に行く」, 「記録をつける": "初めて記録をつける」, 「印": "家の印を作る」; L76 history types += 印.

**app/replay3d.js**:
- L17 `WORK_EVENTS` += 交換に行く, 記録をつける. L19 `NIGHT_EVENTS` += the G6 types (よその村, 交換, 貸し借り, 覚え, 印, 封, 記録, 確かめる, 町) and, if question 16 is approved, the missing G5 types (もめごと, 収める, 裁き, 罰, 祭り, まとめ役, 分かれる, 段階, 共同の仕事, 倉から取る).
- `buildWorld` (L96): for each `D.g6.others` entry, 3 small grey huts just inside the map edge at `edge` and a faint path from the camp, visible from `known` (an `othersOn(day)` helper like `housesOn`); a label 「東の村 (歩いて 1 日)」.
- Travellers: `day_summaries` already sends them to the edge place on trip days (the edge places are exported in `places` with `far: true`).
- `houseAt` (L193): `return null` when `v.left <= day` (export `houses[i].left` from `g5.fissions`) — question 16.
- L187 `HOME_COLORS`: HSL fallback beyond 10 households.
- index.html: optional G6 F chips (substeps) and the status line.

**tools/progress_chart.py** `series` (L45): G6 rows from `g6.log` (population vs 50, known and partner villages, consecutive trade seasons, joined, sealing pieces, tools, tokens, checks, non-food share, town now).

**Docs**: `docs/society2_phase_plan.md` §2 G6 row (after the decisions), §2.2 G6 F row, a new §5 「G6 交易・町・記録」 in the style of the G5 subsection; `sim/society/HANDOFF.md` §1/§4; `sim/society/daily_run.md`: the end-of-Society-2.0 routine (第 4 部のまとめ・通しの動画・次の相談) and consultation rules — no exchange for 8 G6 seasons; 数え札 open for 8 seasons and nobody keeps records; all partner villages gone; `store_days < 120` after trading; town reached and lost for a year.

## 19. Tests

All tests use scratch copies (`git archive` trees, in-memory deep copies, `SOC_DATA=/tmp/...`). Never write to `sim/society/data/*`; never run step.py season or resume in the repo.

**A. Pre-G6 invariance (mandatory; already passed once, §0).**
- OLD = `git archive HEAD sim/society` (without data/), NEW = the edited tree; each run in its own process (`sys.path` = its own `sim/society`) so world.py differences count.
- Start: `git show 5a17727:sim/society/data/state.json` (day 1709). Real seasons with the committed answers `answers/day1709 … day1859` (and later ones once committed; feeling answers from `answers/dayNNNN/feeling/` from 1859 on). Per season: render every `season_prompt` (answerers) and `feeling_prompt` (feelers), `apply_answers`, `apply_feelings`, `simulate_season`, `last_first`, `check` (hold + phase log as step.py).
- Then ≥ 6 scripted G5 seasons whose answers include every G6 field, a feast, judge answers, and one injected stale dispute with `LEAVE_P` raised in both trees (a fission).
- Assert: prompts and feeling prompts byte-identical; `json.dumps(state, sort_keys=True)` equal after deleting `g6_*` keys from `era_info.indicators` and `era_log[*].indicators`; `"g6" not in era2`; salts recorded by a monkeypatched `_rng` never include 41; `answerers`/`feelers` equal; the G6 jobs became 休む; `export()` without a `g6` key and with the same `places`/`days`; `_house_site` returns the same sites (also with 20 homes forced).

**B. Unit checks** (NEW, deep copy forced to G6):
- Parsers: `_g6_side` ("村", 「村で受ける」, 「村の物で受ける」 → 村; "家", 「自分の家の倉で」 → 家; false, "false", 「受けない」, 「交換しない」 → False; "...", 「村か家」, None → None; True → 村), `_g6_goods` (麦/つぼ aliases, unknown goods dropped), `_g6_node` ("N1", 「東の村へ」, unknown → None), `_tid`, `_g6_job` (then not in acts2 → 休む; how not open → 数え札; what order kept).
- Exchange: `_g6_pay` (want first; keep 2 goats; no grain in a bad year; remainder), caps per season (two traders to one village: the second is told 「もう足りている」), `_g6_take`/`_g6_put` conservation (village and household; goats owner; pots/sickles/obsidian always village), debts from remainders.
- Meeting: majority 村 9/16; leader alone 村; "家" by a non-rep leader ignored; "家" chooses the richest able household; refusal lowers trust; 返す with 封筒/板 (exact, closed), 数え札 (shortfall stays), none (closed, 覚え iff memory > 1.25 × brought).
- Seals: one per household; sealed store pieces ≤ 1 per household per day; `_steal` order (sealed last); sealed theft → 封 + certain dispute.
- Memory: `_g6_spread` for H = 4/8/12 and open debts; `_g6_range` contains the truth, not centred; claims in [1, 1+s] × true; `_g6_after_pay` raises 覚え iff paid > 1.25 × true × mem; 覚え disputes never chain.
- Records: capacity and order (`what`), complete vs partial, tablet flag, debts get proof, ration credit only with a complete 蓄え record, `last_flow` unchanged by credit.
- Ladder: each opening condition true/false at its edge; `acts2` shows 記録をつける only after 数え札.
- Town table: 49 vs 50 people; 3 vs 4 consecutive meetings; 1 vs 2 partners; ratio 1.9 vs 2.0; non-food 9% vs 10%. `_record_ok` counts only 板.
- `check()` → "end" once; no G6 text matches `/フェーズが .* に進んだ/`; grep shows no `log(…, kind=|who=|text=…)` data keys.

**C. Multi-season trials in memory** (G6 forced on a copy of the live state, ≥ 24–40 seasons, scripted answers; policies: open = accept everything, seal, seal the store, 2 traders and 1–2 keepers; trade = trade only; records = seals and keepers only; silent = no G6 fields; closed = refuse everything). Hard invariants every season: no exception, village not empty, pots/sickles/obsidian ≥ 0, unique goat ids, node stocks ≥ 0, `check` "end" at most once, ≤ 1 fission a year. Report F days, population, joined, disputes, fissions, tools, checks, store days. Results of the first run are in §0.

**D. `step.py season` smoke** (`SOC_DATA` scratch, step.py patched): 2 G6 seasons with answers for `answerers` (seals, store seal, trade 村, one trader) → exit 0, G6 `*` lines, the G6 status line, prompts with 「## ほかの村・印・記録」, `"trade"`, `"seal": false` only for reps without a seal, 交換に行く in the activity list, 記録をつける only after 数え札; then pre-fill G6 F3/F4 → 「* Society 2.0 が終わった」, hold, `status` message, `app_data.json` with `g6` and edge places, node regex check.

**E. Optional haiku dry run** on a scratch clone, forced G6, workflow `{steps: 3}`: share of parseable `trade`/`seal`/`seal_store`/trip/keeper answers, whether haiku over-trades grain or pots (store_days before and after), prompt size.

## 20. Risks

- **Size.** About 1,100 new lines in era2.py (section ≈ 930 incl. comments, prompts ≈ 150, hooks ≈ 100), more than twice G5. Mitigation: implement in 3 slices and run test A after each — (1) villages, offers, seals, criteria, end, prompt; (2) memory, records, ladder, credit; (3) trips, town pull, satellites, obsidian, 3D. Trips (≈ 120 lines) can be cut if question 9 is "no".
- **Growth may be fast.** In the trial "open" run population went 25 → 44 in 8 seasons (all groups accepted, 3 partners within 3 seasons). Town (50) may come within 3–5 years if people accept everyone, much slower if they refuse (projection: 0.11 within 10 years when only half the groups are accepted). Both are legitimate outcomes; consult the user after 8 seasons without growth instead of changing rules mid-run.
- **Record before town** (historically inverted: Brak's town ~900 years before writing). Report it; the tablet threshold (4 token seasons, 200 tokens) is the parameter to tune if the user wants writing to depend more on scale.
- **Information shown shrinks in G6** (ranges, claims). Haiku may be confused; FACTS explain it; ranges are deterministic.
- **覚え loop** could add disputes and fissions before records exist (stress already 0.72 at 9 households). Bounds: MAX_NEW 3, merging, DROP_AGE, feasts, the leader; 覚え does not chain.
- **Grain and pots drain.** Trading and lending can lower store days (trial: 279 → 116 days in 8 seasons while population grew). Partner caps limit it; daily_run consultation rule at `store_days < 120`.
- **Goats pile up** when people always want goats (trial: 17 → 93 in 8 seasons); untended herds still lose 15% a season.
- **Names**: suffix names appear at once (question 15).
- **Answer load and data**: one more rep per accepted group (≈ 15–20 answers a season at 50 people); app_data.json (≈ 15 MB now) may reach 40–60 MB; the daily keeper and traveller events add ≈ 30–60 events a season.
- **Narration**: other villages are model constructs created by logged events; captions quote only those events; pre-G6 visitors get no origin; 「家の印」, not 「持ち主の印」.
- **Contested archaeology**: token meaning and token → word signs, down-the-line exchange, debt as the trigger of records — never stated as fact (§24).
- **Live run**: the checkout is shared with the live run (and other sessions push code). Implement only after the decisions, rebase the diffs on the current HEAD, and re-run test A with the newest committed answers.

## 21. Decisions for 本人 (recommendation first)

Same 17 items as the Japanese summary. In short: (1) town 50; (2) keep the 4-season exchange in the town condition, ≥ 2 villages; (3) town pull yes; (4) villages only from logged events + a guaranteed first trader; (5) days sticky; (6) hold only at the end; (7) 覚え yes; (8) record = checked with a tablet, thresholds as given, report record-before-town; (9) trips yes; (10) household trade yes; (11) obsidian yes, no beads; (12) one seal per household; (13) four F; (14) no storehouse now; (15) NAMES_G6 from G6; (16) hide houses after fission and add G5 toasts; (17) fix the research docs when G6 is built.

## 22. Flaws found in the three designs → fixes in this spec

| Design | Flaw | Fix |
|---|---|---|
| Emergent | Partner demand pots < people/2 → no steady exchange, 4 seasons unreachable | per-season intake caps (§6) |
| Emergent | trip goods counted as the trader's household withdrawals → unfair 蓄え disputes | village account only (§8) |
| Emergent | memory range true × (1 ± s) puts the truth at the midpoint | independent lower and upper draws (§10) |
| Emergent | per-day RNG cache keyed by (seed, day), process-sensitive | `g6.seed` stored in state, drawn from salt 41 (§2) |
| Emergent | 「返して」 offers can never happen (the village never borrows) | removed |
| Emergent | unnoticed theft (`seen=False`) hides logged events | removed; G6 theft texts omit the amount instead |
| Emergent | daughter texts name individual leavers as alive | household-level wording (§6) |
| Emergent | the plan's 4-season exchange moved out of the town condition without asking | kept, question 2 |
| Minimal | partner comes every season by rule; exchange near-automatic | offers by contact chance + trips by choice |
| Minimal | record = 24 lines (proxy for household count) | tablet check, load-based opening (§11) |
| Minimal | records change only text | 覚え, checks, talk slots, ration credit |
| Historical | three villages by declaration | logged events only |
| Historical | span of control (Johnson's 6) used for token coverage | token capacity per day (load) |
| Historical | storehouse, beads, credit promises enlarge the code | left out / question |
| All | `check()` returning `"end"` is truthy → step.py would log 「フェーズが G6…に進んだ」 | `r == "end"` branch first (§18) |
| All | NAMES runs out (seen in the trial) | question 15 |

## 23. Literature (【文献】 = literature basis; 【文献・二次】 = seen only in a secondary summary; (memory, unverified) = not checked this session)

Exchange and obsidian
- Renfrew, Dixon & Cann 1968, Proc. Prehist. Soc. 34:319–331 — fall-off curves; supply zone ≤ ~300 km 【文献】
- Renfrew 1975, "Trade as action at a distance" (Sabloff & Lamberg-Karlovsky eds.) — modes of exchange 【文献】; Renfrew 1977 — monotonic decrement 【文献】
- Hodder & Orton 1976 — equifinality of fall-off curves 【文献・二次】
- Ortega, Ibáñez, Khalidi, Méndez, Campos & Teira 2014, J. Archaeol. Method Theory 21:461–485; Ibáñez et al. 2015, J. R. Soc. Interface 12:20150210 — down-the-line alone cannot explain the spread; small-world networks 【文献・二次】
- Yacobi & Gopher 2023, Camb. Archaeol. J. 33(3):431–448 — kin-based trade partnerships 【文献】
- Carter et al. 2006/2007/2008 — Çatalhöyük obsidian sources 【文献】
- Davidson & McKerrell 1976, Iraq 38:45–56; 1980, Iraq 42:155–167 — Halaf pottery moved between sites 【文献】
- Hamoukar LC1–2 obsidian (~85% Nemrut Dağ), Oriental Institute reports 2005–2007 【文献】
- Hallan Çemi → Nemrut Dağ ≈ 100 km in 3 days 【文献・二次】

Seals, sealings, tokens, writing
- Duistermaat 1996; Akkermans & Duistermaat 1996/97, Paléorient 22(2):17–44; Akkermans & Duistermaat 2004, Levant 36:1–11 — Sabi Abyad sealings (~6175–6125 cal BC, level 8B; Burnt Village ~6000 BC) 【文献】
- Duistermaat 2012, OLA 219:1–16 — non-administrative origins of seals 【文献】 (text not read)
- Frangipane et al. 2007, *Arslantepe Cretulae* — >2,200 impressed sealings; A340 ≈ 30 seals on 175 sealings; Temple C bowls 【文献】
- McMahon 2009, Iraq 71 — Brak sealings 【文献】
- Schmandt-Besserat 1992, *Before Writing* — tokens → envelopes → tablets (her interpretation) 【文献】
- Bennison-Chapman 2018, Levant 50(3); 2019, Camb. Archaeol. J. 29(2) — tokens multifunctional, from the 10th millennium cal BC 【文献】
- Englund 1993, Science; Englund 2011, "Accounting in proto-cuneiform"; Damerow & Englund 1987 — numerical tablets (Uruk V), number and kind signs (Uruk IV), ~85% administrative 【文献】
- Zimansky 1993, J. Field Archaeol. 20(4):513–517; Michalowski 1993, Am. Anthropol.; Friberg 1994; Kelley, Cartolano & Ferrara 2024, Antiquity — critiques of token → word signs 【文献】

Towns and information
- Childe 1950, Town Planning Review 21:3–17 — urban revolution criteria 【文献】
- Johnson 1973, Anthropol. Pap. 51 (Univ. Michigan) — information processing and state origins 【文献】; Johnson 1982 — scalar stress (used in G5) 【文献】
- Wright & Johnson 1975, Am. Anthropol. 77:267–289 — administrative hierarchy and settlement tiers 【文献】
- Shin et al. 2020, Nat. Commun. 11 — scale threshold before information threshold 【文献】
- Ur, Karsgaard & Oates 2007, Science; Ur et al. 2011, Iraq 73; Oates et al. 2007, Antiquity 81:585–600 — Tell Brak LC 【文献】
- McMahon, Sołtysiak & Weber 2011, J. Field Archaeol. 36:201–220 — Tell Majnuna 【文献】
- Brak isotope and dental studies 2020 (Archaeol. Anthropol. Sci., doi 10.1007/s12520-020-01104-3) and 2022 (J. Anthropol. Archaeol.) — migration 【文献・二次】
- Lawrence & Wilkinson 2015, Antiquity — "Hubs and upstarts" 【文献】
- McMahon 2019, J. Archaeol. Res. — low-density early cities 【文献】
- Ur 2014, Camb. Archaeol. J. 24(2):249–268 — households and the emergence of cities 【文献】
- Kramer 1982; Watson 1979 — village densities 【文献】; Nissen 2003 — Uruk ≈ 40,000 【文献・二次】
- Bandy 2004, Am. Anthropol. 106 — fission size (G5) 【文献】; Stein 1994; Fried; Flannery 2002 (G5) 【文献】
- Halstead & O'Shea 1982 — social storage (memory, unverified); Hudson — debt cancellations after ~2400 BC 【文献・二次】

## 24. Corrections to the research docs (fix when G6 is built; question 17)

1. society2_research.md L262 「村から村へ手渡しで運ばれた」: contested; down-the-line cannot reach far unless villages are ~100 km apart or pass on ~90% (Ortega et al. 2014; Ibáñez et al. 2015); small-world/kin networks fit better.
2. L262 「それより遠いと急に減る」: the decline is smooth (log-linear); the 300 km / 80% zone thresholds lack an ethnographic basis.
3. L260 「約 200 km」: usually ~190 km (unverified); Çatalhöyük also received eastern Anatolian obsidian >600 km away (Carter et al. 2008).
4. L263, L275 「前8000年頃から…形ごとに穀物1かご・ヒツジ1頭」: Schmandt-Besserat's interpretation with uncalibrated dates; tokens from the 10th millennium cal BC, multifunctional (Bennison-Chapman 2018, 2019).
5. L264–265 「数の記号と物の記号に分かれ、文字」: accepted for number signs; weak for word signs from complex tokens (Zimansky 1993; Michalowski 1993; Englund 1993; Kelley et al. 2024); tokens continued after writing.
6. L266 「約9割は役所の帳簿」: ~85% overall; Uruk IV almost all administrative, Uruk III ~80% (Englund 2011).
7. L267, L278 「最初の町の人口」 for Uruk: Brak (LC2) and Hamoukar are earlier towns; 40–50k is an estimate (Nissen 2003 ~40,000).
8. L277 「トークン → 文字 約5000年」: ~4,800–6,500 years depending on the start date.
9. periodization.md L56 「約 300 ha は根拠がなく…」: partly wrong; ~300 ha is Ur's figure for the whole complex over all periods; not the size of any one LC phase (55 ha and 130 ha stand).
10. periodization.md L19, L56 「LC2 (前 4,200〜3,800)」: the 55 ha is for LC1–2; some sources end LC2 ~3900 BC.
11. periodization.md L40 「トークン 前 8,000/7,500 年ごろ〜」「サビ・アビヤドの印章 前 6,200」: stamp seals already late 8th millennium (Bouqras, Çatalhöyük); what is new at Sabi Abyad is the sealing (level 8B, ~6175–6125 cal BC).
12. society2_phase_plan.md L21 G6 町: exchange predates towns by millennia; 100 people is unreachable for decades (§3) — update after question 1 and 2.
13. part2.md L61 and plan L41 「持ち主の印」: both communal-storage (Akkermans & Duistermaat) and private-property (Duistermaat 2010/2013) readings exist; narration says 「家の印」「封をした」.
14. research §7(c), §9 「記録なしの貸し借りの覚え違い」: 【仮定】; stores, withdrawals, rations and transfers are better attested triggers (§2, §11).
