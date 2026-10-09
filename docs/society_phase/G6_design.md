<!-- 設計書 (まだリポジトリのコードにはしていない)。2026-10-09、クラウドのセッションで、ワークフローで作った:
     3 つの角度 (小さく正しく / 史実 / 起きたことから) の設計 → 判定役が採点 (小さく 34・史実 33・起きたことから 38、50 点満点) →
     「起きたことから」の案をもとに、ほかの 2 つのよいところを足してまとめた。
     まとめ役は、このコードを写しの木 (/tmp) に入れて、メモリの中で試し回しをした (この文書の 0.)。リポジトリのコードとデータは変えていない -->

# G6 交易・町・記録: 設計書 (日本語の要約)

第 4 部「町と文字」(テル・ブラク LC2 → ウルク期) の仕組み。G6 に入ってから働き、G6 の前は何も変わらない (お題も state.json も、いまと同じ。写しで確かめた)。

**G6 で足すもの**
- **ほかの村**: 地図の外 (歩いて 1〜2 日) にある村。記録に残る出来事からだけ生まれる: (1) G5 で村を出た家の人たちの村、(2) G6 で来たよその群れが「…から来た」と言った村、(3) 交換をもとめて来た人の村。G6 の最初の季節の終わりには、必ず 1 つの村の人が交換をもとめて来る。ほかの村は Claude が演じず、決まりで動く (お金はかからない)
- **交換**: ほかの村の人が季節の終わりに来て、申し出をする (交換したい / 苦しい年なので草の種を貸してほしい / 借りた分を返す)。次の集まりで、村の物で受けるか、家の物で受けるか、受けないかを決める。自分たちから「交換に行く」こともできる (歩いて 1 日の村なら 3 日。1 人で運べるのは草の種 900 つかみ・土器 4 個ほど)。払いきれない分は「あとで返す」約束 (貸し借り) になる
- **町に人が集まる**: 交換している村から「ここで暮らしたい」人が来る (受け入れるかは、これまで通り大人が決める)。来た家は、来た村の方角の、キャンプから 275〜375 m の所に住まいを建てる (ブラクのまわりにあった小さな集まりをまねた。集まりは来たところごとに分かれていたという読みがある。距離は縮めた【仮定】)
- **印と封**: 家の代表は家の印を作れる。印のある家の倉は封をする (よその家の人が開けると、封が割れているので分かり、必ずもめごとになる)。みんなが望めば、村の蓄えにも封をし、取るたびにその家の印の封のかけらが残る
- **覚え**: G6 では、記録のない量 (家ごとの村の蓄えへの出し入れ・もめごとの量・貸し借りの量) は「約 a〜b」の幅でしか分からない。家が多いほど、貸し借りが多いほど、幅が広い。言い出した家は損を多めに覚えていることがあり、覚えで払うと「多く払った」という覚え違いのもめごとが起きる
- **記録の道具** (本人と決めた順: 印 → 数え札 → 封筒 → 粘土の板): 次の道具は、その道具が答える困りごとが起きてから使えるようになる。使うかは人が決める
  - 数え札: 印で封をするようになり、記録のない量を覚えで決めることが起きたあと。仕事「記録をつける」(1 人 1 日に数え札 10 個ほど)
  - 封筒: 数え札が使えるようになり、ほかの村との貸し借りがあるとき (数え札を粘土の玉に入れ、印を押す。返すとき、どちらにも数が分かる)
  - 粘土の板 (物のしるしと数のしるしを分けて記す): 数え札で記録した季節が 4 つ以上になり、1 季節に数え札が 200 個以上要る季節があったあと (1 人 1 日に数え札 50 個分)
- **記録の使い道**: 記録のある量ははっきり分かり、もめごとや貸し借りを確かめられる (覚え違いが起きない)。記録のあるもめごとは、集まりで話し合える 2 つに数えない。村の蓄えの記録を全部残せた季節は、作る人・記録をつける人・交換に行った人の働いた日を「入れた」に数える (配給の記録)
- **黒曜石**: 2 つ目のよその村 (歩いて 2 日) は黒曜石を持つ。黒曜石の刃の鎌は割れにくい (半分)

**町の条件** (F3。季節の終わりに見る): 村が **50 人以上**、この 4 季節は毎季節ほかの村と交換した、相手の村が 2 つ以上、村がいちばん大きい相手の村の 2 倍以上、食べ物をとらない人 (作る人・記録をつける人。20 日以上) が大人の 1 割以上

**記録の条件** (F4): 物のしるしと数のしるしを分けて記した**粘土の板の記録で、量を確かめた**ことが 1 回以上 (数え札だけでは文字としない。ウルク IV の書き方)

**F (区切り)**: G6 の F1 村どうしの交換 / F2 印で封をする / F3 町 / F4 物と数を分けて記す。町と記録は別々で、どちらが先でもよく、届いた日を記録する。町だけ・記録だけでは止まらない。**両方そろうと「Society 2.0 の終わり」で止まる** (「フェーズが…に進んだ」とは書かない。ワークフローの止まる文を足す)

**人が決めること** (季節の答え): 申し出を村で受けるか・家で受けるか・受けないか (trade) / 交換に行く人と、行き先・持って行く物・ほしい物 (job) / 家の印を作るか (seal) / 村の蓄えに封をするか (seal_store) / 記録をつける人と、残すもの・残し方 (job) / ほかの村から来た人を受け入れるか (accept)。家族の代表の答えは家族の大人みんなの答え。家の物で受ける・印を作るのは家の代表だけ

**縮め方**
- 人数: ブラク LC2 (約 55 ha。1 ha に 50〜100 人として 2,750〜5,500 人。1 ha の人数は【仮定】) の約 1/55〜1/110 で、町を 50 人にした。ほかの村 (10〜25 人) は、まわりの小さな中心地 (10〜20 ha。この広さは元の論文で確かめきれていない) の約 1/100
- 距離: 縮めない (歩いて 1〜2 日、約 25〜60 km。地図の外に置く)
- 時間: 現実の約 900〜1,000 年 (ブラク LC2 → ウルク IV) を、ゲームの 5〜10 年に縮める (思いつくまでの待ち時間を縮める。計画 3.)
- 印: サビ・アビヤドの、少なくとも約 60 個の印 (封泥に押されていた印の数。紹介文による数で、元の報告では確かめていない) のかわりに、家ごとに 1 つ

**G5 とのつながり**: G5 の仕組み (もめごと・まとめ役・祭り・罰・村が分かれる) は G6 でも続く。人が増えて家が増えるほど、もめごとが増え、村が分かれやすい。記録とまとめ役は、それをおさえる向きに働くように作った (ねらい。試しの台本はもめごとを全部収めたので、本当におさえるかはまだ確かめていない)。村を出た家は「分かれた家の村」になり、のちに交換の相手になることがある。町が小さくなる (後もどり) ことも起きてよく、そのことも記録する

**試したこと** (写しの木で、メモリの中だけ。くわしくは 0.): G5 の本物の 5 季節 (14年30日目〜15年30日目 (1709〜1829 日目) の答え) と台本の 6 季節 (村が分かれる季節をふくむ) で、お題・気持ちのお題・state.json が今のコードと同じだった。G6 にした写しで、台本の答えで 24〜40 季節を進めた (約 300 季節。止まるような誤りはなかった)。みんなで交換・印・記録をする答えでは、印で封をする (F2) が G6 の 1 季節目、交換 (F1) が 2 季節目、記録 (F4) が 9〜10 季節目、町 (F3) が 11〜35 季節目で、4 回とも記録が先にそろった。交換だけ・記録だけ・答えない・受けない、の答えでは、それぞれ記録・町・どちらもがそろわなかった。`step.py season` も写しのデータで 3 回進め、「Society 2.0 が終わった」で止まった

**2 回目の確かめ** (2026-10-09、別の確かめ役。くわしくは 0.1): この文書のコードをそのまま取り出して写しの木に入れ、もう一度試した。誤りが 10 か所あり、この文書で直した (小さな村が交換を申し出られない・最初の季節の終わりの交換が来ないことがある・飢えで区切った季節に物が増える・ヤギを持って行くと別のヤギになって帰る・3D で交換の日に村にいるように見える など)。直したあと、G6 の前は、お題と state.json がそのまま同じ (14 季節。消して比べる鍵もない)。G6 にした写しで 344 季節、止まる誤りはなかった。交換 (F1) と印で封 (F2) は 2 季節目、記録 (F4) は 11〜13 季節目、町 (F3) は 6 回のうち 1 回 (14 季節目)。町にそろわなかったのは、台本の答えでは畑仕事が足りず、蓄えが尽きて人が出ていったため (G6 を使わない答えでも同じように蓄えが減った。G6 のせいではない)

**決まった (2026-10-09、本人「お勧め通りですし、皆さんに決めてもらいます」): 下の 1〜17 はすべておすすめの通り。これから出てくる細かい決めごとも、おすすめを選んで進め、報告で伝える**

**本人に確かめること** (おすすめを先に書いた。数はすべて【仮定】)
1. 町の人数の目安: **50 人 (おすすめ)** / 40 人 / 60 人 / 100 人 (計画のまま)。15年60日目 (1859 日目) の 25 人から (16年30日目 (1949 日目) は 26 人)、交換を続け、村が分かれる季節が半分あるとき、50 人の町にそろう見込みは 8 年で 5 割、10 年で 8 割 (40 人なら 8 年で 8 割、60 人なら 10 年で 5 割、100 人なら 15 年でも 1 割)
2. 計画の「ほかの村との交換が 4 季節以上続く」を町の条件に**残す (おすすめ)**。相手は毎季節同じ村でなくてよく、4 季節で 2 つ以上の村とする。考古学では交換は町よりずっと古いので、F1 だけにする案もある
3. 交換している村から「ここで暮らしたい」人が来る仕組みを**入れる (おすすめ)**。ブラクには、よそから移り住んだ人が加わって大きくなったとする調べがある (歯の形の調べ。紹介文で見ただけ)。入れないと、50 人に 10 年でそろう見込みは 4 割ほど (村が分かれないときの見積もり)
4. ほかの村は記録に残る出来事からだけ作り、**G6 の最初の季節の終わりに、必ず 1 つの村の人が交換をもとめて来る**形でよいか (おすすめ)
5. 町と記録は、**一度届けば届いたまま**にする (おすすめ)。あとで町が小さくなったら、そのことも記録して報告する。別の案は「同じ季節に両方」
6. 止まるのは、**両方そろった「Society 2.0 の終わり」だけ** (おすすめ)。そのとき第 4 部のまとめと動画を作る
7. **覚え** (記録のない量を幅で見せる。覚え違いのもめごと) を入れる (おすすめ)。入れないと、記録をつけても世界は何も変わらない
8. 記録の条件を「**粘土の板で量を確かめた**」にする (おすすめ)。板が使えるようになる目安 (数え札の季節 4 つ・1 季節 200 個) はこれでよいか。記録が町より先にそろいそう (現実は町が先で、文字は約 900 年あと) なので、そのまま違いとして報告する
9. 「**交換に行く**」を最初から入れる (おすすめ)。ないと、毎季節の交換が、ほかの村の人が来るかどうかの運だけになる
10. **家の物で交換する** ("家") を入れる (おすすめ)。家ごとの差が広がることがある。ただし、交換の申し出は土器・鎌をほしがり、土器・鎌はいつも村のものなので、集まりで家の物で受けられるのは「貸して」(草の種) だけになる。家の物での交換は、おもに「交換に行く」で家の倉の草の種を持って行くとき (手に入れたヤギは家のもの) に起きる (2026-10-09 確かめ役が見つけた)。集まりの交換の申し出も家で受けられるようにするなら、家には草の種だけをもとめる形にする (仕組みを変えるので、本人に聞く)
11. **黒曜石** (鎌が割れにくくなる) を入れる (おすすめ)。貝の玉 (飾り) は入れない
12. **印は家ごとに 1 つ** (家の代表が作る。手間はかからない) でよいか (おすすめ)。印は決めた通り G6 の記録の始まりとして入れるが、文では「持ち主の印」ではなく「家の印」と書く (おすすめ。昔の印が持ち主を示したのか、みんなの倉に封をした印なのかは、考古学で読みが分かれているため)
13. F は **4 つ** (F1 交換 / F2 印で封 / F3 町 / F4 物と数を分けて記す) でよいか (おすすめ)。数え札・封筒・板は出来事「記録」として残す
14. **大きな倉 (神殿)** は、いまは入れない (おすすめ)。町の条件にもしない
15. **名前**: 作った名前 30 個はもうすぐ使い切り、「ソル2」のような名前になる (写しで G6 を進めると、すぐに出た)。G6 から、新しく作った名前 30 個を足してよいか (おすすめ。G5 のあいだは変えない)
16. **3D**: 村を出た家の住まいを、出た日から描かない・G5 の出来事 (もめごと・祭り・まとめ役・分かれる など) も夜の知らせに出す (おすすめ: どちらもする。G5 の表示も変わる)
17. **調べの文書の直し** (14 か所を見直し、直すのは 12 か所。2 か所は確かめた結果、今のままでよかった。この文書の 24.): G6 を作るときに直す (おすすめ)。本人と決めたことを書いた part2.md は書きかえず、12. が決まったら注をそえるだけにする

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
| **C. Trial runs** (G6 forced on a copy of the live state, scripted answers, policies open / trade / records / silent / closed, 4 seeds for open). | No exception in about 300 seasons. **open** (4 seeds × 40 seasons): F2 at the end of G6 season 1, F1 season 2, F4 (a tablet check) seasons 9–10, F3 (town) seasons 11 / 24 / 25 / 35 → Society 2.0 ended once in every seed, the record first each time. 14–17 groups joined, 58–68 disputes, 18–21 覚え events, 24–29 checks, 0 fissions (the script settled every dispute). **trade only** (32 seasons): F1, F3 at season 11, no F2/F4. **records only** (32): F1 (offers at the meeting), F2, F4 at season 9, no town (without trips no 4-season run). **silent / closed** (24 each): no F; offers came and were not taken; 13–17 覚え events. In the long runs the store ran down near the end (the script farmed little while people grew; famine leave then cut the town) and goats grew into the thousands — the latter is the existing G2 herd rule (no pasture limit), not G6. Names ran out at once (ソル2, ユノ2, ヨナ2). |
| **D. `step.py season` smoke** (`SOC_DATA=/tmp/g6judge/smoke`, step.py patched as §18). | 3 seasons, exit 0 each. `*` lines show the G6 events and 「G6 の F1「村どうしの交換」に入った」; the G6 status line prints; with F3/F4 pre-filled, season 3 printed 「* Society 2.0 が終わった: 町 (1949 日目) と記録 (1919 日目) がそろった → 一時停止 (第 4 部のまとめ待ち)」, `hold` True, `g6.end` set, `status` printed 「一時停止中: Society 2.0 が終わったので、第 4 部のまとめ待ち」; app_data.json has `g6` and an edge place for each known village; node: `/Society 2\.0 が終わった/` matches, `/フェーズが .* に進んだ/` does not. |

### 0.1 Second check: code feasibility (2026-10-09, a separate adversarial reviewer)

**Remote diff first.** `git fetch`: origin had nothing new; local was 1 commit ahead (`04899a3`, the live run's 「1919 日目から (季節)」). This file was modified in the working tree (other reviewers editing in parallel) and `sim/society/app/records_demo.html` was untracked (not touched). `era2.py`, `world.py`, `step.py`, `resume.py` and `app/replay3d.js` are unchanged since `f8a9e46`, so every line number in §5 and §18 still holds. Live state (read-only copy): day 1949, 26 people (15 adults), 9 households, 23 goats, 570 pots, 23 sickles, store ≈ 329 days, no penalty law, no leader, `next_name` 30 (the 30 names are already used up).

**Method.** §5.1, §5.2, §5.3, §5.4 and the §18 step.py diff were extracted mechanically from this file and applied with `patch` to `git archive HEAD sim/society` (no data). All hunks apply without fuzz; `py_compile` passes; `ruff --select F` finds no undefined name (only the existing unused `day` in `indicators` and `_field_work`); no `log()` call uses `kind`/`who`/`text` as a data key.

**Bugs found and fixed in this file** (each was reproduced with a unit check, then re-checked on the fixed code):
1. A partner village of 5–11 people never made a 交換 offer (its wants were worth 245–305 < one goat, 375): about 1 in 8 new stranger villages and most daughter villages. Now a goat is offered when the wants are worth at least half a goat (§5.1 `_g6_offer_new`, §6).
2. The "guaranteed" first trader failed when a visitor group arrived at the first G6 season end (step 2 created the stranger village, so step 3's `not st` was false): no offer in 156 of 200 such cases. Now the first G6 season end always brings an offer, from the visitors' village if it exists (0 of 60 after the fix).
3. A season cut short by famine after a barter in which the partner paid nothing returned the carried goods although the partner kept them (pots duplicated: 570 → 570 instead of 566). Now `tr["bartered"]` decides what comes back.
4. Travellers could carry goats, meat and obsidian, but partners take only 草の種・土器・鎌 (`_g6_cap`), so these always came back, and returned goats were re-created as 2-year-old females (a free change of sex and age in the herd). Carrying is now limited to the three goods partners take; FACTS and §8 say so.
5. `obs_sickles` could exceed the village's sickles after sickles were traded away; capped in `_g6_take`.
6. Newcomers copy the most common job for their first season; if that was 交換に行く they had no destination and idled 30 days. They now ignore 交換に行く/記録をつける (no-op before G6).
7. Before G6, `_g6_indicators` added 20 zero-valued `g6_*` keys to `era_info` and `era_log` (state.json changed bytes; test A had to strip them). It now returns `{}` before G6.
8. 3D replay: on the barter day the traveller's only event is type 交換, which `day_summaries` did not map, so the replay drew them resting at camp. step.py now maps a 交換 event with a `who` to 交換に行く (meeting exchanges have no `who`).
9. With the ration credit, the 蓄え dispute text said 「入れたのは 約 X」 with credited work days inside X; the text now says the amount includes them (narration stays factual).
10. The first G6 prompt (before `g6` exists) printed an empty 「使える記録の道具: 」; now 「印」. `step.py season` under the end-of-Society-2.0 hold printed 「フェーズ G6 に進んだので評価待ち」; now the end reason. The step.py day_summaries hunk had no trailing context (patch read it as end-of-file); fixed, and all hunk headers recomputed.

**Results on the fixed spec.**

| Check | Result |
|---|---|
| **A** (own runner; OLD = HEAD, NEW = fixed spec; separate processes) | From `5a17727` (day 1709): 8 real seasons 1709–1919 with the committed season and feeling answers (8–9 reps, 6–7 feelers), then 6 scripted G5 seasons carrying every G6 field (trade, seal, seal_store, 交換に行く/記録をつける with to/carry/what/how/house), a feast, judge, leader 「なし」, and an injected stale dispute with `LEAVE_P` forced (1 fission). Season prompts, feeling prompts and the **whole** `state.json` (nothing stripped) byte-identical every season; `"g6"` never created; salts {3, 7, 11, 29, 31, 37} in both. |
| **C** (live copy at day 1949 forced to G6; scripted answers; invariants every season: no exception, no negative village or partner stock, unique goat ids, `check` "end" at most once) | No exception or invariant failure in 344 seasons. **open** (whole families of 2 reps trade, of 2 reps keep records; 3 seeds × 40): F1 and F2 at G6 season 2, F4 at season 11 (all three), F3 at season 14 (1 of 3, 52 people → Society 2.0 ended once, record first). **open2** (only the rep trades/keeps, families farm; 2 seeds × 40): F1/F2 season 2, F4 season 13, population peaked at 52 and 57 but no town (non-food share 3 of 35 adults < 10%, then the store ran out). **trade** (32): F1 only. **records** (32): F2 season 2, F4 season 11 with no trade at all (tablet-checked disputes). **house** (32, "家" answers and `house: true` trips): 113 trips on household grain; no 交換 offer could be taken by a household (see §7). **silent / closed** (24 each): no F. In every policy, including silent and closed, the store fell from ≈ 330 days to < 80 within 16–20 seasons and famine leave cut the population: this is the scripts' farming (the live, haiku-played village has kept ≈ 300 days since day 1709), not a G6 drain (G6 moves at most a few hundred つかみ of grain a season, plus loans ≤ 3000). Max prompt ≈ 37k characters. |
| **D** (`SOC_DATA` scratch copy, fixed step.py) | 3 seasons exit 0; the first season end logged the visitors' village and its trader offer [T1]; season 2 took it (村 17 / 大人 17), F1 and F2 区切り printed; with F3/F4 pre-filled, season 3 printed 「* Society 2.0 が終わった: 町 (2009 日目) と記録 (1979 日目) がそろった → 一時停止 (第 4 部のまとめ待ち)」; `status` printed the end reason; one more `season` exited 3 with the end reason. `app_data.json`: `g6` key, edge place N1 `far: true`, travellers placed at N1 on all trip days including the barter day. node: `/Society 2\.0 が終わった/` true, `/フェーズが .* に進んだ/` false. Prompts: 「## ほかの村・印・記録」, 交換に行く in the job list, 記録をつける not yet, `"seal": false` only for the one rep without a seal. |

**Remaining (not changed here; for the implementer or 本人):** "家" can take only 貸して at the meeting (question 10); the town is gated by food and by the 10% non-food share rather than by G6 rules, so whether 50 people can be fed depends on the villagers' farming (consult rule `store_days < 120`, §18); F4 came 1–3 seasons before or without the town in every run (report as the known inversion, question 8); daughter villages with no goats or obsidian never offer 交換 (only loans/repayments); with more than 4 villages, directions repeat and huts overlap in 3D; `_g6_r` keys (200+trip, 300+trip, 1000+dispute) can coincide in very long runs (harmless correlation, same day only).

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
| Debts | Only partner → village/household (loans in a partner's bad year, unpaid trip remainders). No interest. No 「返して」 offers. | Interest-bearing grain loans are first clearly attested in the mid-3rd millennium BC (Early Dynastic Lagash; Enmetena's debt cancellation c. 2400 BC) 【文献・二次】(Hudson 2018); the village never borrows in this design. |
| Unrecorded amounts | G6 only: per-household store flows are shown as ranges (independent lower and upper draws, so the truth is not the midpoint); disputes of kind 蓄え/刈る/倉/覚え carry the complainant's claim (true × U(1, 1+s)); paying by memory can raise a 覚え incident. Spread s = 0.05 × (households + open debts), ≤ 0.5; halved for a sealed household while the store was sealed. | Emergent; Johnson 1978, 1982 (information load, scalar stress). Debt-misremembering as *the* trigger of records is 【仮定】; stores and withdrawals are better attested, so both are used. |
| Record ladder | 印 (from G6 start) → 数え札 (after F2 and after one amount was settled by memory) → 封筒 (after tokens open and while a debt is open) → 板 (after ≥ 4 token seasons and one season needing ≥ 200 tokens). Use is chosen. | User's order 印 → トークン → 文字 (part2.md 6.3); problem first (Emergent); envelopes from Historical. |
| Record criterion | ≥ 1 amount checked with a 板 record (a dispute taken up at the meeting, or a debt repaid). | Uruk IV standard: number and kind signs separate (Englund 2011); counting tokens alone are not writing. |
| Holds | None at F1–F4 (区切り). One hold at the end of Society 2.0 (F3 and F4 both reached at any time; days are sticky). A town that later falls below the bar is logged (町). | Plan 2.1; going backwards is allowed. |
| Randomness | One new salt: `_rng(state, 41)` once per G6 season end (and once when `g6` is created at the first G6 meeting). All meeting/day randomness comes from `g6.seed`, the last draw of that stream (`_g6_r(state, k)`). | 41 % 31 = 10 is free. Historical's stored-seed idea is simpler and process-independent. |
| Storehouse, beads | Not built (question 14). | Keep G6 smaller; no criterion needs them. |

## 3. Scale-down factors

| Quantity | Real | Sim | Factor | Basis |
|---|---|---|---|---|
| Town | Tell Brak LC2 (c. 4200–3900/3800 BC) ≈ 55 ha (central mound + satellite clusters; 130 ha in LC3–4) 【文献】(Ur's Brak project summary of Ur, Karsgaard & Oates 2007 and Ur et al. 2011; some summaries say LC1–2); low-density northern urbanism 【文献】(McMahon 2019/2020 abstract) at 50–100 people/ha 【仮定】 → 2,750–5,500 | **50** | ≈ 1/55–1/110 | plan §2 allows 1/10–1/100 |
| Partner villages | LC small centres 10–20 ha (Lawrence & Wilkinson 2015 — paper confirmed, the 10–20 ha figure not re-checked) 【未確認】; ethnographic village densities ≈ 100–200/ha are the usual range (Kramer's ≈ 120/ha, cited via Hassan 1981) 【文献・二次】 — the earlier 「83–139/ha (Kramer 1982; Watson 1979)」 was not found | 10–25 people | ≈ 1/100 | same scale as the town |
| Primacy | Brak 55 ha vs a neighbour of ≈ 13–16 ha (Hamoukar's walled LC core, Oriental Institute) — but Hamoukar's LC1–2 southern extension is a dispersed scatter of ≈ 280–300 ha (Ur 2010), so the ratio depends on what is measured; the earlier 「≈ 15 ha, 3.7× (Ur et al. 2007)」 was not found in that paper 【文献・二次】 | ≥ 2× the largest partner | lowered | 【仮定】 |
| Distance | walking with loads ≈ 30 km/day 【文献・二次】(Hallan Çemi → Nemrut Dağ, ~100 km in 3 days) | 1–2 days (≈ 25–60 km), off-map | 1/1 | research §7(c) asks ≥ 1 day |
| Satellites | Brak late-5th-millennium sherd clusters roughly 500 m (N, E) to 1,000 m (SW) from the central mound 【文献・二次】(Harvard Magazine on Ur's survey; the earlier 「200–400 m (Ur et al. 2007)」 was not found) | G6 newcomers build 11–15 cells (275–375 m) toward their village | ≈ 1/2 【仮定】 | migration into Brak 【文献・二次】(dental-morphology study of LC Brak, J. Anthropol. Archaeol., c. 2022, seen only in a press summary: migrants in neighbourhoods by origin) |
| Seals | Sabi Abyad: hundreds of sealings (≈ 300), at least ≈ 60 different seals (61 per a Wikipedia summary, not checked in the reports), 27 design types (Duistermaat 1996) 【文献・二次】; Arslantepe VI A storeroom A340: 30 seals on 175 cretulae 【文献】(Frangipane et al. 2007, as reported in Weingarten's 2009 AJA review) | 1 per household (9–20) | ≈ 1/3–1/10 | 【仮定】 |
| Load | – | 20 kg per traveller (草の種 900 つかみ, 土器 4, 鎌 10, 干し肉 100) | – | 【仮定】(porter rule of thumb, unverified) |
| Time | Brak LC2 (~4200 BC) → Uruk IV (3350–3200 BC) ≈ 900–1,000 years | expected 5–10 game years (20–40 seasons) | ≈ 1/100–1/200 | plan §3: compress waiting-to-invent, not biology |

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

```python
# ---------------- G6 交易・町・記録: ほかの村・交換・貸し借り・印と封・覚え・数え札 → 封筒 → 粘土の板・町 (G6 に入ってから働く) ----------------
# 第 4 部「町と文字」(計画 2.1)。町と記録は別々の条件で、どちらが先でもよい (届いた日を区切り F3・F4 に残す)。両方そろうと Society 2.0 の終わり
# 考え方: 目標を上から置かない。ほかの村は、記録に残る出来事 (村を出た家・G6 で来たよその群れの来たところ・交換をもとめて来た人) からだけ生まれる。
#   記録の道具は、それが答える困りごとが起きてから使えるようになる (印 → 数え札 → 封筒 → 粘土の板。順は本人と決めた。part2.md 6.3)。使うかは人が決める
# 【文献】Renfrew, Dixon & Cann 1968・Ortega ほか 2014・Ibáñez ほか 2015: 黒曜石は 300 km ほどまで多く届き、遠くへは少しずつ (模型では、手渡しだけでは
#   300 km より遠くへ届きにくく、遠くの相手をもつ村があると説明しやすい)。Yacobi & Gopher 2023: 親族どうしの交換 (という読み)。Davidson & McKerrell 1976・1980: ハラフの土器も村から村へ動いた
# 【文献】Duistermaat 1996・Akkermans & Duistermaat 1996/97・2004: サビ・アビヤドの封泥 (前 6,300〜6,000 年ごろ。多くは焼けた村、前 6,000 年ごろ)。入れ物に封をし、開けたあとの封のかけらを
#   取っておいた。Frangipane ほか 2007: アルスランテペの宮殿 (前 3,400〜3,000 年ごろ) の 1 つの倉に 30 の印 (取り出す多くの人の印という読み)。印が「持ち主」を示したかは
#   議論がある (Duistermaat 2012・2013) ので、文は「封をした家の印」とする
# 【文献】Johnson 1978・1982・Wright & Johnson 1975・Shin ほか 2020: 扱う量と決める単位が増えると、記録の道具が要る。Englund 2011: ウルク IV の粘土板は、数のしるしと物のしるしを分けて記す
#   (原楔形文字の約 85% は帳簿)。数のしるしが押したトークンから来たことは広く認められるが、物のしるしがトークンから来たかは弱い (Zimansky 1993・Michalowski 1993・Englund 1993。
#   Kelley ほか 2024 は、一部の物のしるしは印の絵から来たとする)
# 【文献】Ur, Karsgaard & Oates 2007・Ur ほか 2011: テル・ブラク LC2 (前 4,200〜3,900/3,800 年ごろ) は約 55 ha (まん中の丘と、まわりの小さな集まり)。集まりが内へ広がり、LC3〜4 に約 130 ha。
#   よそから移り住んだ人が加わったとする調べがある (歯の形の調べ。【文献・二次】)。Childe 1950: 町には食べ物をとらない専門の人がいる
# 【仮定】数: よその村は 3 つまで (最初の G6 の季節の終わりに必ず 1 つ来る)。来る見込み: 分かれた家 0.35・よその村 0.15 (信頼で変わる)。
#   よその村の人は 10〜25 人。交換している村から住みたい人が来る見込み 1 季節 0.15。苦しい年 1 年 0.2。値うち (草の種のつかみ): ヤギ 375・鎌 75・土器 40・黒曜石 40・干し肉 6。
#   1 人が運べるのは 20 kg ほど (草の種 900 つかみ)。覚えのずれ 0.05 × (家の数 + 返されていない貸し借り)、0.5 まで。
#   数え札 1 個 = 草の種 100 つかみ・ヤギ 1 頭・土器や鎌 10 個・働いた日 10 日。1 人 1 日に数え札 10 個 (板なら 50 個分)。
#   粘土の板が使えるようになるのは、数え札で記録した季節が 4 つ以上で、1 季節に数え札が 200 個以上要る季節があったとき。
#   町: 50 人以上 (ブラク LC2 の約 1/55〜1/110)、この 4 季節は毎季節交換し、相手の村が 2 つ以上、いちばん大きい相手の 2 倍以上、食べ物をとらない人が大人の 1 割以上
G6_SALT = 41  # 41 を 31 で割った余り 10 は、前からの塩 3・7・11・23・29・31・37 の余り 3・7・11・23・29・0・6 と重ならない
ACTS_G6, ACT_RECORD = ["交換に行く"], "記録をつける"
G6_EVENTS = ("よその村", "交換", "貸し借り", "覚え", "印", "封", "記録", "確かめる", "町")  # お題と step.py で見せる (毎日の「交換に行く」「記録をつける」は入れない)
DIRS = {"南": ("川にそって南へ", (39, 79)), "北": ("川にそって北へ", (49, 0)), "東": ("東へ", (79, 40)), "西": ("西へ", (0, 40))}
MAX_STRANGERS, STRANGER_P, JOIN_P, JOIN_MIN, BAD_P = 3, 0.10, 0.15, 12, 0.2
CONTACT_P = {"分かれた家": 0.35, "よその村": 0.15}
USE_OBSIDIAN, OBS_BREAK = True, 0.5
VALUE = {"草の種": 1, "干し肉": 6, "ヤギ": 375, "土器": 40, "鎌": 75, "黒曜石": 40}
LOAD = {"草の種": 900, "土器": 4, "鎌": 10}  # 1 人が運べる量。持って行けるのは、ほかの村が受けとる物 (_g6_cap と同じ 3 つ) だけ
TRIP_WALK, TRIP_LOAD, TRIP_HURT, TRIP_LOSS = 30000, 1.4, 0.005, 0.03
SPREAD, SPREAD_MAX, BLAME = 0.05, 0.5, 1.25
TOKEN = {"草の種": 100, "干し肉": 16, "ヤギ": 1, "土器": 10, "鎌": 10, "黒曜石": 10, "日": 10}
RATE = {"数え札": 10, "封筒": 10, "板": 50}
WHATS = ("蓄え", "交換", "刈る")
WHAT_WORDS = {"蓄え": "村の蓄えへの家ごとの出し入れ", "交換": "ほかの村との交換と貸し借り", "刈る": "よその家の畑で刈った量"}
TABLET_SEASONS, TABLET_TOKENS, KEEPER_DAYS = 4, 200, 20
TOWN_POP, TOWN_RUN, TOWN_PARTNERS, CENTRE, NONFOOD = 50, 4, 2, 2, 0.10
GOOD_WORDS = (("黒曜石", "黒曜石"), ("黒い石", "黒曜石"), ("干し肉", "干し肉"), ("肉", "干し肉"), ("土器", "土器"), ("つぼ", "土器"), ("壺", "土器"),
              ("器", "土器"), ("鎌", "鎌"), ("ヤギ", "ヤギ"), ("山羊", "ヤギ"), ("草の種", "草の種"), ("麦", "草の種"), ("穀", "草の種"), ("種", "草の種"))
UNIT = {"草の種": "つかみ", "干し肉": "切れ", "ヤギ": "頭", "土器": "個", "鎌": "本", "黒曜石": "個"}
FOOD_KCAL = {"草の種": GRAIN, "干し肉": UNITS["干し肉"][1]}
NODE_KEY = {"ヤギ": "goats", "草の種": "grain", "土器": "pots", "鎌": "sickles", "黒曜石": "obsidian"}


def _g6(state):
    """G6 の状態 (G6 の最初の集まりで作る。start から数えるので、G6 の前のことは G6 の条件に数えない)"""
    e2 = state["era2"]
    if "g6" not in e2:
        e2["g6"] = {"start": state["day"], "seed": _rng(state, G6_SALT).getrandbits(31), "meets": [], "meet_first": None,
                    "others": [], "next_other": 1, "offers": [], "next_offer": 1, "debts": [], "next_debt": 1, "next_trip": 1,
                    "taken": {}, "moved": {}, "seals": {}, "store_sealed": None, "season_seals": {}, "opened": {}, "sealings": {}, "seal_seasons": 0,
                    "jobs": {}, "keep_days": {}, "trips": {}, "trip_log": [], "records": [], "cover": {}, "credit": {},
                    "open": {"印": state["day"], "数え札": None, "封筒": None, "板": None}, "token_seasons": 0, "big": 0,
                    "unchecked": 0, "misremember": 0, "checked": {"数え札": 0, "封筒": 0, "板": 0},
                    "exchanges": 0, "joined": 0, "obsidian": 0, "obs_sickles": 0, "nonfood": [], "shown": None,
                    "town_seen": None, "town_low": 0, "log": [], "end": None}
    return e2["g6"]


def _g6_r(state, k):
    """集まりと 30 日のあいだの G6 の乱数 (季節の終わりに塩 41 から引いた seed から作る。前からの乱数の列には足さない)"""
    return random.Random(state["era2"]["g6"]["seed"] * 1000003 + state["day"] * 1009 + k)


def _other(state, oid):
    return next((o for o in (state["era2"].get("g6") or {}).get("others", []) if o["id"] == oid), None)


def _okey(o):
    return f"{o['name']} ({o['way']}歩いて {o['days']} 日)"


def _gw(goods):
    """{"ヤギ": 2, "土器": 18} → 「ヤギ 2 頭・土器 18 個」"""
    return "・".join(f"{k} {n} {UNIT[k]}" for k, n in goods.items() if n > 0) or "なし"


def _g6_spread(state):
    """覚えのずれ (家が多いほど、返されていない貸し借りが多いほど大きい)"""
    g = state["era2"].get("g6") or {}
    return min(SPREAD_MAX, SPREAD * (len(_homes(state)) + sum(1 for d in g.get("debts", []) if d["status"] == "まだ")))


def _g6_cover(state, what):
    """この季節の記録 (全部残せたもの) の道具。なければ None"""
    return ((state["era2"].get("g6") or {}).get("cover") or {}).get(what)


# ---- ほかの村 (地図の外。Claude は演じない。決まりで動く) ----

def _new_other(state, rng, kind, household=None, people=None, goats=0, grain=0):
    g = _g6(state)
    used = {o["dir"] for o in g["others"]}
    d = rng.choice([x for x in DIRS if x not in used] or list(DIRS))
    strangers = [o for o in g["others"] if o["kind"] == "よその村"]
    obs = USE_OBSIDIAN and kind == "よその村" and len(strangers) == 1  # 2 つ目のよその村 (歩いて 2 日) は黒曜石を持つ【仮定】
    days = 1 if kind == "分かれた家" or not strangers else 2 if obs else rng.choice([1, 2])
    name = (household[:-2] if household.endswith("の家") else household) + "の村" if kind == "分かれた家" else f"{d}の村"
    if any(o["name"] == name for o in g["others"]):
        name = f"{name}{g['next_other']}"
    n = people if people is not None else rng.randint(10, 25)
    far = kind == "よその村"
    o = {"id": f"N{g['next_other']}", "name": name, "kind": kind, "household": household, "dir": d, "way": DIRS[d][0], "days": days,
         "edge": list(DIRS[d][1]), "since": state["day"], "known": None, "people": n,
         "goats": round(n * 0.4) if far else goats, "grain": n * 100 if far else grain, "pots": n // 4 if far else 0,
         "sickles": n // 8 if far else 0, "obsidian": 20 if obs else 0, "has_obsidian": obs, "bad": None, "trust": 0.5, "contacts": []}
    g["next_other"] += 1
    g["others"].append(o)
    return o


def _g6_cap(o):
    """ほかの村が 1 季節に受けとる物の上限【仮定】(土器は 3 人に 1 個 (3 個から)、鎌は 6 人に 1 本 (1 本から)、草の種は 1 人 10 つかみ。苦しい年は 100 つかみ)"""
    return {"土器": max(3, o["people"] // 3), "鎌": max(1, o["people"] // 6), "草の種": o["people"] * (100 if o["bad"] is not None else 10)}


def _g6_wants(state, o):
    t = _g6(state)["taken"].get(o["id"], {})
    return {k: max(0, n - t.get(k, 0)) for k, n in _g6_cap(o).items()}


def _g6_supply(o):
    """ほかの村が出せる物 (ヤギは 2 頭残す。草の種は苦しい年でなく、1 人 100 つかみより多い分)"""
    return {"ヤギ": max(0, o["goats"] - 2), "黒曜石": o["obsidian"],
            "草の種": max(0, o["grain"] - o["people"] * 100) if o["bad"] is None else 0}


def _node_add(o, goods, sign):
    for k, n in goods.items():
        if NODE_KEY.get(k):
            o[NODE_KEY[k]] = max(0, o[NODE_KEY[k]] + sign * n)


def _g6_pay(o, value, want):
    """ほかの村が value (草の種のつかみ) を払う: want の物から、なければほかの物で。戻り値: 払う物、払いきれない値うち"""
    sup, pay = _g6_supply(o), {}
    for k in [want] + [x for x in ("ヤギ", "黒曜石", "草の種") if x != want]:
        n = min(sup.get(k, 0), int(value // VALUE[k]))
        if n > 0:
            pay[k] = n
            value -= n * VALUE[k]
    return pay, value


def _g6_note(state, o, took, moved=()):
    g = _g6(state)
    t = g["taken"].setdefault(o["id"], {})
    for k, n in took.items():
        t[k] = t.get(k, 0) + n
    for goods in (took,) + tuple(moved):
        for k, n in goods.items():
            g["moved"][k] = g["moved"].get(k, 0) + n


def _g6_contact(state, o):
    """交換・貸し借り・返すが 1 つ済んだ (この季節に交換した村として数える)"""
    g, sd = _g6(state), state["era2"]["step_day"]
    if sd not in o["contacts"]:
        o["contacts"].append(sd)
    g["exchanges"] += 1
    o["trust"] = min(1.0, round(o["trust"] + 0.1, 2))


# ---- 村の物・家の物 ----

def _g6_have(state, side, k):
    e2 = state["era2"]
    if side == "村":
        if k in FOOD_KCAL:
            return int(sum(f["kcal"] for f in state["store"] if f["kind"] == k) // FOOD_KCAL[k])
        if k == "ヤギ":
            return max(0, sum(1 for x in e2["goats"] if x.get("owner") is None) - 2)  # 村のヤギは 2 頭残す
        return {"土器": e2.get("pots", 0), "鎌": e2.get("sickles", 0), "黒曜石": _g6(state)["obsidian"]}.get(k, 0)
    if k in FOOD_KCAL:
        return int(sum(f["kcal"] for f in _house(state, side)["store"] if f["kind"] == k) // FOOD_KCAL[k])
    return sum(1 for x in e2["goats"] if x.get("owner") == side) if k == "ヤギ" else 0


def _g6_take(state, side, goods):
    """side (「村」か家の名前) の物を出す (足りなければある分だけ)。戻り値: 出した物"""
    e2, out = state["era2"], {}
    for k, n in goods.items():
        n = min(n, _g6_have(state, side, k))
        if n <= 0:
            continue
        if k in FOOD_KCAL:
            _move_food(state["store"] if side == "村" else _house(state, side)["store"], [], k, n * FOOD_KCAL[k])
        elif k == "ヤギ":
            mine = [x for x in e2["goats"] if x.get("owner") == (None if side == "村" else side)]
            for x in sorted(mine, key=lambda x: (x["sex"] != "オス", x["born"]))[:n]:  # オスの、年上から
                e2["goats"].remove(x)
        elif k == "黒曜石":
            _g6(state)["obsidian"] -= n
        else:
            e2["pots" if k == "土器" else "sickles"] -= n
            if k == "鎌":  # 黒曜石の刃の鎌の数は、村の鎌の数をこえない
                _g6(state)["obs_sickles"] = min(_g6(state)["obs_sickles"], e2["sickles"])
        out[k] = n
    return out


def _g6_put(state, side, goods, goats_in=()):
    """side に物を入れる (土器・鎌・黒曜石は、いつも村の物)"""
    e2, day, gi = state["era2"], state["day"], list(goats_in)
    if side != "村" and side not in _homes(state):
        side = "村"  # 家がもうない (村を出た) ときは村へ
    for k, n in goods.items():
        if n <= 0:
            continue
        if k in FOOD_KCAL:
            (state["store"] if side == "村" else _house(state, side)["store"]).append({"kind": k, "kcal": n * FOOD_KCAL[k], "day": day})
        elif k == "ヤギ":
            for i in range(n):
                x = gi[i] if i < len(gi) else {"sex": "メス", "age": 2}
                e2["goats"].append({"id": e2["next_goat"], "sex": x["sex"], "born": day - x["age"] * YEAR, "owner": None if side == "村" else side})
                e2["next_goat"] += 1
        elif k == "黒曜石":
            _g6(state)["obsidian"] += n
        else:
            key = "pots" if k == "土器" else "sickles"
            e2[key] = e2.get(key, 0) + n


# ---- 季節の終わりに、ほかの村の人が来る (申し出) ----

def _g6_offer_new(state, rng, o, first):
    g, day, s = _g6(state), state["day"], _g6_spread(state)
    head = (f"前に村を出た{o['household']}の人たちが、村に来た。いまは {_okey(o)} で暮らしているという" if first and o["kind"] == "分かれた家"
            else f"{_okey(o)} の人たちが、交換をもとめて村に来た" if first else f"{_okey(o)} の人たちが、また村に来た")
    due = next((d for d in g["debts"] if d["other"] == o["id"] and d["status"] == "まだ" and d["due"] <= day + 1), None)
    off, what = None, ""
    bring = None
    if due:
        exact = due.get("proof") in ("封筒", "板")
        bring = {k: min(n if exact else int(n * rng.uniform(1 - s, 1)), o[NODE_KEY[k]] if NODE_KEY.get(k) else n) for k, n in due["goods"].items()}
        if sum(VALUE[k] * n for k, n in bring.items()) * 2 < sum(VALUE[k] * n for k, n in due["goods"].items()):
            bring = None  # 半分も返せないときは、まだ返しに来ない
    if o["bad"] is not None and o["grain"] < o["people"] * 60:
        n = min(3000, max(100, round(o["people"] * 120, -2)))
        off = {"kind": "貸して", "give": {}, "want": {"草の種": n}}
        what = f"この年は畑が実らず苦しいので、草の種 {n} つかみ を貸してほしい、1 年のうちに同じ量を返す、と言った"
    elif bring:
        off = {"kind": "返す", "debt": due["id"], "give": bring, "want": {}}
        what = f"[{due['id']}] の分として、{_gw(bring)} を返しに来た"
    else:
        sup, wants = _g6_supply(o), _g6_wants(state, o)
        cap = sum(VALUE[k] * n for k, n in wants.items())
        # ほしい物がヤギ半頭分 (草の種 約 190 つかみ) 以上あれば、ヤギ 1 頭を出す (12 人より小さい村は、ほしい物がヤギ 1 頭分に届かないため。2026-10-09 確かめ役)
        good = "ヤギ" if sup["ヤギ"] >= 1 and cap >= VALUE["ヤギ"] / 2 else "黒曜石" if sup["黒曜石"] >= 5 and cap >= 5 * VALUE["黒曜石"] else None
        if good:
            k = max(1, min(3, sup["ヤギ"], int(cap // VALUE["ヤギ"]))) if good == "ヤギ" else min(15, sup["黒曜石"], int(cap // VALUE["黒曜石"]))
            ask, left = {}, k * VALUE[good]
            for w in ("土器", "鎌", "草の種"):
                m = min(wants.get(w, 0), int(left // VALUE[w]))
                if m > 0:
                    ask[w], left = m, left - m * VALUE[w]
            off = {"kind": "交換", "give": {good: k}, "want": ask}
            what = f"{_gw(off['give'])} を出すので、{_gw(ask)} がほしいと言った"
    if not off:
        log(state, "よその村", None, f"{head}。交換できる物がなく、帰っていった", other=o["id"])
        return
    off.update(id=f"T{g['next_offer']}", other=o["id"], day=day,
               goats_in=[{"sex": "メス" if rng.random() < 0.5 else "オス", "age": rng.randint(1, 4)} for _ in range(off["give"].get("ヤギ", 0))],
               mem={"village": round(rng.uniform(1, 1 + s), 3), "other": round(rng.uniform(1 - s, 1), 3)})
    g["next_offer"] += 1
    g["offers"].append(off)
    log(state, "よその村", None, f"{head}。{what} [{off['id']}]", other=o["id"], offer=off["id"])


# ---- 季節の集まり (G6): 答えを読む・決める ----

def _tid(k):
    m = re.search(r"\d+", str(k or ""))
    return f"T{int(m.group())}" if m else ""


def _g6_side(v):
    """申し出の答え: "村" / "家" / False (受けない) / None (読めない。お題の「...」)"""
    if v is True:
        return "村"
    if v is False:
        return False
    s = str(v or "").strip()
    if s.lower() in ("false", "no") or any(w in s for w in ("受けない", "しない", "断", "ことわ", "いらない")):
        return False
    vil, home = "村" in s, "家" in s
    return "村" if vil and not home else "家" if home and not vil else None


def _g6_good(v):
    s = str(v or "")
    return next((g for w, g in GOOD_WORDS if w in s), None)


def _g6_goods(d):
    out = {}
    for k, v in (d.items() if isinstance(d, dict) else []):
        good, n = _g6_good(k), _num(v)
        if good and n > 0:
            out[good] = out.get(good, 0) + n
    return out


def _g6_node(state, v):
    """行き先: 「N1」か、知っている村の名前 (まわりに字があってもよい)"""
    s = str(v or "")
    known = [o for o in (state["era2"].get("g6") or {}).get("others", []) if o["known"] is not None]
    m = re.search(r"[NnＮ]\s*(\d+)", s)
    if m:
        return next((o["id"] for o in known if o["id"] == f"N{int(m.group(1))}"), None)
    hit = [o for o in known if o["name"] in s]
    return max(hit, key=lambda o: len(o["name"]))["id"] if hit else None


def _g6_new_season(state):
    """季節の集まりのはじめ (G6): この季節の仕事の答えなどを空にする"""
    g = _g6(state)
    g["meets"].append(state["era2"]["step_day"])
    g["meet_first"] = state["next_event"]
    g["jobs"], g["keep_days"], g["trips"] = {}, {}, {}


def _g6_job(state, q, job, own):
    """交換に行く・記録をつける の、くわしい答え (e2["jobs"] には入れない)"""
    g = _g6(state)
    act = q["plan"]["activity"]
    if act == "交換に行く":
        then = job.get("then")
        then = then.get("activity") if isinstance(then, dict) else then
        g["jobs"][q["name"]] = {"activity": act, "to": _g6_node(state, job.get("to")), "carry": _g6_goods(job.get("carry")),
                                "want": _g6_good(job.get("want")) or "ヤギ",
                                "then": then if then in acts2(state) and then not in ACTS_G6 + [ACT_RECORD] else "休む",
                                "house": bool(own and _yes(job.get("house")))}
    elif act == ACT_RECORD:
        w = job.get("what")
        w = [w] if isinstance(w, str) else w if isinstance(w, list) else []
        what = []
        for y in w:
            what += [x for x in WHATS if x in str(y) and x not in what]
        how = next((h for h in ("板", "封筒", "数え札") if h in str(job.get("how") or "") and g["open"].get(h)), "数え札")
        g["jobs"][q["name"]] = {"activity": act, "what": what or list(WHATS), "how": how}


def _g6_collect(state, c, p, a, fam, own):
    """季節の答えから、申し出 (trade)・家の印 (seal)・村の蓄えの封 (seal_store) を集める (代表の答えは家族の大人みんなの答え)"""
    names = {q["name"] for q in fam}
    tr = a.get("trade")
    for k, v in (tr.items() if isinstance(tr, dict) else []):
        tid, side = _tid(k), _g6_side(v)
        if not tid or side is None or (side == "家" and not own):
            continue
        c["trade"].setdefault(tid, {}).setdefault(side, set()).update(names)
        c["trade_by"].setdefault(tid, {})[p["name"]] = side
        if side == "家" and p.get("household"):
            c["house"].setdefault(tid, []).append(p["household"])
    if own and p.get("household") and _yes(a.get("seal")):
        c["seal"].setdefault(p["household"], p["name"])
    if _yes(a.get("seal_store")):
        c["store"] |= names
        c["store_by"].add(p["name"])


def _g6_meeting(state, c, n):
    """季節の集まり (G6。G5 の集まりのあと、よそから来た人の受け入れの前): 家の印 → 村の蓄えの封 → 申し出"""
    e2, g = state["era2"], _g6(state)
    lead, homes = _leader(state), _homes(state)
    for h, who in sorted(c["seal"].items()):
        if h in homes and h not in g["seals"]:
            g["seals"][h] = {"day": e2["step_day"], "by": who}
            log(state, "印", who, f"{h}の代表の {who} が、家の印 (焼いた粘土に形を刻んだもの) を作った。これから{h}の倉の口は、粘土でふさいで{h}の印を押しておく",
                household=h)
    if len(c["store"]) * 2 > n or (lead and lead in c["store_by"]):
        g["store_sealed"] = e2["step_day"]
        alone = len(c["store"]) * 2 <= n
        log(state, "封", lead if alone else None, (f"まとめ役の {lead} が決めて、" if alone else "")
            + "この季節は、村の蓄えの土器の口を粘土でふさぐことになった。取るときは封を割り、取った人の家の印を押した粘土で封をし直す。割った封のかけらは取っておく")
    for off in g["offers"]:
        o = _other(state, off["other"])
        if o:
            _g6_decide(state, c, off, o, n, lead)
    g["offers"] = []


def _g6_decide(state, c, off, o, n, lead):
    g = _g6(state)
    if off["kind"] == "返す":
        _g6_repay(state, off, o)
        return
    tally = {k: len(v) for k, v in c["trade"].get(off["id"], {}).items()}
    if tally.get("村", 0) * 2 > n or (lead and c["trade_by"].get(off["id"], {}).get(lead) == "村"):
        side = "村"
    else:
        cands = [h for h in c["house"].get(off["id"], []) if all(_g6_have(state, h, k) >= m for k, m in off["want"].items())]
        side = max(sorted(cands), key=lambda h: sum(f["kcal"] for f in _house(state, h)["store"])) if cands else None
    votes = f"村 {tally.get('村', 0)}・家 {tally.get('家', 0)}・受けない {tally.get(False, 0)} / 大人 {n}"
    if side is None:
        o["trust"] = max(0.0, round(o["trust"] - 0.1, 2))
        log(state, "よその村", None, f"季節の集まりで、{o['name']} の申し出 [{off['id']}] は受けなかった ({votes})", other=o["id"], offer=off["id"])
        return
    if any(_g6_have(state, side, k) < m for k, m in off["want"].items()):
        log(state, "交換", None, f"季節の集まりで、{o['name']} の申し出 [{off['id']}] を{side}の物で受けようとしたが、{_gw(off['want'])} がなかった",
            other=o["id"], offer=off["id"])
        return
    gave = _g6_take(state, side, off["want"])
    _node_add(o, gave, 1)
    who = "村は、村の物で" if side == "村" else f"{side}が、家の物で"
    if off["kind"] == "貸して":
        d = {"id": f"D{g['next_debt']}", "other": o["id"], "lender": side, "goods": gave, "day": state["day"], "due": state["day"] + YEAR,
             "proof": None, "mem": off["mem"], "status": "まだ", "end": None}
        g["next_debt"] += 1
        g["debts"].append(d)
        _g6_note(state, o, {}, (gave,))
        _g6_contact(state, o)
        log(state, "貸し借り", None, f"季節の集まりで、{who} {o['name']} に {_gw(gave)} を貸した [{d['id']}] (1 年のうちに同じ量を返すと言った。{votes})",
            other=o["id"], debt=d["id"])
        return
    _node_add(o, off["give"], -1)
    _g6_put(state, side, off["give"], off["goats_in"])
    _g6_note(state, o, gave, (off["give"],))
    _g6_contact(state, o)
    sx = (" (" + "・".join(f"{x['sex']} {x['age']} 歳" for x in off["goats_in"]) + ")") if off["goats_in"] else ""
    log(state, "交換", None, f"季節の集まりで、{who} {o['name']} の申し出 [{off['id']}] を受け、{_gw(gave)} を {_gw(off['give'])}{sx} と取り替えた ({votes})",
        other=o["id"], offer=off["id"], **({"household": side} if side != "村" else {}))


def _g6_repay(state, off, o):
    """ほかの村が貸し借りを返しに来た (集まりで決めずに受けとる)。封筒・板の記録があれば、約束した数を両方で確かめる"""
    g, day = _g6(state), state["day"]
    d = next((x for x in g["debts"] if x["id"] == off["debt"] and x["status"] == "まだ"), None)
    if not d:
        return
    bring = {k: min(n, o[NODE_KEY[k]]) if NODE_KEY.get(k) else n for k, n in off["give"].items()}
    _node_add(o, bring, -1)
    _g6_put(state, d["lender"], bring)
    _g6_note(state, o, {}, (bring,))
    _g6_contact(state, o)
    true = d["goods"]
    short = {k: n - bring.get(k, 0) for k, n in true.items() if n - bring.get(k, 0) > 0}
    to = "村" if d["lender"] == "村" else d["lender"]
    if d.get("proof") in ("封筒", "板", "数え札"):
        g["checked"][d["proof"]] += 1
        if short:
            d["goods"] = short
        else:
            d.update(status="返した", end=day)
        how = "封筒を割って" if d["proof"] == "封筒" else f"{d['proof']}の記録を見て"
        log(state, "確かめる", None, f"{o['name']} の人が [{d['id']}] を返しに来た。{how}、貸した数 ({_gw(true)}) を確かめ、{to}は {_gw(bring)} を受けとった"
            + (f"。足りない {_gw(short)} は、あとで返すことになった" if short else ""), other=o["id"], debt=d["id"], how=d["proof"])
        return
    g["unchecked"] += 1  # 記録のない量を、覚えで決めた
    d.update(status="返した", end=day)
    mem = {k: math.ceil(n * d["mem"]["village"]) for k, n in true.items()}
    if any(mem[k] > bring.get(k, 0) * BLAME for k in mem):
        g["misremember"] += 1
        o["trust"] = max(0.0, round(o["trust"] - 0.2, 2))
        log(state, "覚え", None, f"{o['name']} の人は、[{d['id']}] の分として {_gw(bring)} を返した。{to}の覚えでは {_gw(mem)} を貸したはずだった (記録はない)",
            other=o["id"], debt=d["id"])
    else:
        log(state, "貸し借り", None, f"{o['name']} の人が、[{d['id']}] の分として {_gw(bring)} を返した ({to}が受けとった。記録はなく、量は覚えで決めた)",
            other=o["id"], debt=d["id"])


# ---- 30 日のあいだ: 交換に行く・記録をつける・封 ----

def _g6_then(p, j):
    p["plan"] = {"activity": j["then"], "place": "camp", "with": []}


def _g6_trips_day(state):
    """交換に行く (G6。毎日、仕事の計算のあと・食べる前): 出かける → 歩く → 向こうの村で交換 → 歩く → 帰る"""
    e2, g, day = state["era2"], _g6(state), state["day"]
    for p in adults(state):
        j = g["jobs"].get(p["name"])
        if not j or j["activity"] != "交換に行く":
            continue
        t = p.get("today") or {}
        tr = g["trips"].get(p["name"])
        if tr is None:
            if day != e2["step_day"]:
                continue
            tr = g["trips"][p["name"]] = _g6_depart(state, p, t, j)
        if tr["state"] != "行く":
            continue
        o, k = _other(state, tr["to"]), day - tr["start"]
        t["away"] = True
        if k != tr["days"]:
            t["spent"] = round(t.get("spent", BASE_KCAL) + world._walk_kcal(p, TRIP_WALK) * TRIP_LOAD)
        if k == tr["days"]:
            _g6_barter(state, p, t, tr, o)
        elif k == 2 * tr["days"]:
            _g6_return(state, p, t, tr, o, j)
        elif k > 0:
            t.setdefault("events", []).append(log(state, "交換に行く", p["name"], f"{p['name']} が、{o['name']} {'への' if k < tr['days'] else 'からの帰り'}道を歩いた",
                                                  other=o["id"], trip=tr["id"]))


def _g6_depart(state, p, t, j):
    g = _g6(state)
    o = _other(state, j["to"]) if j.get("to") else None
    side = p["household"] if j["house"] and p.get("household") in _homes_built(state) else "村"
    carry = {k: n for k, n in j["carry"].items() if k in LOAD}  # ほかの村が受けとる物 (_g6_cap) だけを持って行く (ヤギ・干し肉・黒曜石は受けとらないので持って行かない)
    load = sum(n / LOAD[k] for k, n in carry.items())
    if load > 1:
        carry = {k: int(n / load) for k, n in carry.items()}
    ok = o is not None and t.get("activity") == "交換に行く"
    took = _g6_take(state, side, carry) if ok else {}
    why = "行き先の村が分からず" if not o else "けがをしていて" if not ok else "持って行ける物がなく" if not took else None
    if why:
        _g6_then(p, j)
        t.setdefault("events", []).append(log(state, "交換に行く", p["name"], f"{p['name']} は、{why}、交換に行かなかった"))
        return {"state": "行かなかった"}
    tr = {"id": f"R{g['next_trip']}", "who": p["name"], "to": o["id"], "start": state["day"], "days": o["days"], "side": side,
          "took": took, "want": j["want"], "got": {}, "back": {}, "goats_in": [], "debt": None, "state": "行く"}
    g["next_trip"] += 1
    t.setdefault("events", []).append(log(state, "交換に行く", p["name"], f"{p['name']} が、{'村' if side == '村' else side}の {_gw(took)} を持って、"
                                          f"{_okey(o)} へ交換に行った", other=o["id"], trip=tr["id"]))
    return tr


def _g6_barter(state, p, t, tr, o):
    """向こうの村で: ほしい分だけ受けとり、want の物 (なければほかの物) で払う。払いきれない分は、あとで返す約束"""
    g = _g6(state)
    tr["bartered"] = True  # 季節の終わりに、まだ帰っていないときの持ち帰り方を分ける
    wants = _g6_wants(state, o)
    took = {k: min(n, wants.get(k, 0)) for k, n in tr["took"].items()}
    took = {k: n for k, n in took.items() if n > 0}
    tr["back"] = {k: n - took.get(k, 0) for k, n in tr["took"].items() if n - took.get(k, 0) > 0}
    if not took:
        t.setdefault("events", []).append(log(state, "交換", p["name"], f"{p['name']} は {o['name']} で {_gw(tr['took'])} を見せたが、"
                                              "この季節はもう足りていると言われ、交換できなかった", other=o["id"], trip=tr["id"]))
        return
    pay, left = _g6_pay(o, sum(VALUE[k] * n for k, n in took.items()), tr["want"])
    _node_add(o, took, 1)
    _node_add(o, pay, -1)
    r = _g6_r(state, 200 + int(tr["id"][1:]))
    tr["got"] = pay
    tr["goats_in"] = [{"sex": "メス" if r.random() < 0.5 else "オス", "age": r.randint(1, 4)} for _ in range(pay.get("ヤギ", 0))]
    owe = ""
    if left >= 50:
        can = tr["want"] == "ヤギ" or (tr["want"] == "黒曜石" and o["has_obsidian"])  # その村が出せる物でだけ約束する
        k = tr["want"] if can and left >= VALUE[tr["want"]] / 2 else "草の種"
        s = _g6_spread(state)
        d = {"id": f"D{g['next_debt']}", "other": o["id"], "lender": tr["side"], "goods": {k: max(1, round(left / VALUE[k]))}, "day": state["day"],
             "due": state["day"] + 2 * SEASON_DAYS, "proof": None,
             "mem": {"village": round(r.uniform(1, 1 + s), 3), "other": round(r.uniform(1 - s, 1), 3)}, "status": "まだ", "end": None}
        g["next_debt"] += 1
        g["debts"].append(d)
        tr["debt"] = d["id"]
        owe = f"。足りない分の {_gw(d['goods'])} は、あとで返すと言った [{d['id']}]"
    _g6_note(state, o, took, (pay,))
    _g6_contact(state, o)
    t.setdefault("events", []).append(log(state, "交換", p["name"], f"{p['name']} は {o['name']} で、{_gw(took)} を渡し"
                                          + (f"、{_gw(pay)} を受けとった" if pay else "た") + owe
                                          + (f" (受けとってもらえなかった {_gw(tr['back'])} は持ち帰る)" if tr["back"] else ""), other=o["id"], trip=tr["id"]))


def _g6_return(state, p, t, tr, o, j):
    r = _g6_r(state, 300 + int(tr["id"][1:]))
    got, lost, hurt = dict(tr["got"]), "", ""
    if r.random() < TRIP_LOSS:
        if got.get("ヤギ"):
            got["ヤギ"] -= 1
            lost = "。帰り道でヤギ 1 頭がはぐれていなくなった"
        elif got.get("草の種"):
            m = max(1, got["草の種"] // 10)
            got["草の種"] -= m
            lost = f"。帰り道で草の種 {m} つかみ をこぼして失った"
    if r.random() < TRIP_HURT * 2 * tr["days"]:
        p["injured"] = 2
        hurt = "。帰り道でけがをした"
    _g6_put(state, tr["side"], got, tr["goats_in"])
    _g6_put(state, tr["side"], tr["back"])
    tr.update(state="帰った", end=state["day"], got=got)
    _g6(state)["trip_log"].append(dict(tr))
    _g6_then(p, j)
    t.setdefault("events", []).append(log(state, "交換に行く", p["name"], f"{p['name']} が {o['name']} から帰った ({_gw(got)} を持ち帰った{lost}{hurt})",
                                          other=o["id"], trip=tr["id"]))


def _g6_keep_day(state, p, t):
    """記録をつける (1 日)"""
    g = _g6(state)
    j = g["jobs"].get(p["name"]) or {"what": list(WHATS), "how": "数え札"}
    g["keep_days"][p["name"]] = g["keep_days"].get(p["name"], 0) + 1
    w = "・".join(WHAT_WORDS[x] for x in j["what"])
    txt = {"数え札": f"粘土の数え札を作り、{w} を数えた", "封筒": f"粘土の数え札を作って {w} を数え、貸し借りの分は粘土の玉 (封筒) に入れて印を押した",
           "板": f"粘土の板に、物のしるしと数のしるしを分けて押し、{w} を記した"}[j["how"]]
    t.setdefault("events", []).append(log(state, "記録をつける", p["name"], f"{p['name']} がキャンプで、{txt}"))


def _g6_opened(state, p, where):
    """封のかけら: 印で封をした村の蓄え (この季節) か家の倉を、家の人が開けた (1 つの家で 1 日 1 回まで)"""
    g, h = state["era2"].get("g6"), p.get("household")
    if not g or not h:
        return
    if where == "蓄え" and g["store_sealed"] != state["era2"].get("step_day"):
        return
    if where == "倉" and h not in g["seals"]:
        return
    if g["opened"].get(f"{where}:{h}") == state["day"]:
        return
    g["opened"][f"{where}:{h}"] = state["day"]
    key = h if h in g["seals"] else "(印なし)"
    g["season_seals"][key] = g["season_seals"].get(key, 0) + 1


def _g6_obsidian_blades(state, n):
    """道具づくり (G6): 村に黒曜石があれば、鎌に黒曜石の刃をはめる (1 本に 1 個)"""
    g = state["era2"].get("g6")
    if not g or not USE_OBSIDIAN:
        return 0
    use = min(n, g["obsidian"])
    g["obsidian"] -= use
    g["obs_sickles"] += use
    return use


# ---- もめごと (G5 の仕組みに、G6 の覚えと記録を足す) ----

def _g6_claim(state, d):
    """G6 のもめごとの量: 記録 (数え札・板を全部残せた) があれば正しい量。なければ、言い出した家の覚え (多めのことがある)"""
    how = _g6_cover(state, d["kind"]) if d["kind"] in ("蓄え", "刈る") else None
    if how:
        d["record"] = how
        return f"。{how}の記録がある"
    if d["kind"] not in ("蓄え", "刈る", "倉", "覚え"):
        return ""  # ヤギに荒らされた畑は、見ればわかる
    r, s = _g6_r(state, 1000 + int(d["id"][1:])), _g6_spread(state)
    d["harm_true"], d["mem"] = d["harm"], round(r.uniform(1 - s, 1), 3)
    d["harm"] = max(1, round(d["harm"] * r.uniform(1, 1 + s)))
    return "。言い出した家の覚えで、記録はない"


def _g6_check(state, d):
    """記録のあるもめごとを、季節の集まりで確かめた (一度だけ数える)"""
    if d.get("checked"):
        return
    g = _g6(state)
    d["checked"] = state["day"]
    g["checked"][d["record"]] += 1
    log(state, "確かめる", None, f"季節の集まりで、もめごと [{d['id']}] の量を、{d['record']}の記録で確かめた (草の種にして {d['harm']} つかみ 分)",
        dispute=d["id"], how=d["record"])


def _g6_after_pay(state, d, paid):
    """覚えで払ったあと: 払った家の覚えより多く払ったと思えば、覚え違いのもめごとのもと"""
    if d.get("record") or "harm_true" not in d or paid <= 0 or d["kind"] == "覚え":
        return
    g = _g6(state)
    g["unchecked"] += 1
    mine = d["harm_true"] * d["mem"]
    if paid > mine * BLAME:
        g["misremember"] += 1
        what = (f"{d['against']}は、もめごと [{d['id']}] で{d['from']}に草の種にして 約 {paid} つかみ 分を払ったが、"
                f"{d['against']}の覚えでは 約 {round(mine)} つかみ 分だった (記録はない)")
        eid = log(state, "覚え", None, what, dispute=d["id"])
        _incident(state, "覚え", d["against"], d["from"], (paid - mine) * GRAIN, what, eid)


def _g6_credit(state, flow):
    """配給の記録 (G6): 村の蓄えの記録を全部残せた季節は、作る・記録をつける・交換に行った日を、1 日 = 大人 1 人の 1 日分として「入れた」に数える"""
    cr = (state["era2"].get("g6") or {}).get("credit") or {}
    return {h: [v[0] + cr.get(h, 0) * DAY_FOOD, v[1], v[2]] for h, v in flow.items()}


def _g6_workdays(state):
    e2, g, days = state["era2"], _g6(state), {}
    rows = list(e2.get("craft_days", {}).items()) + list(g["keep_days"].items())
    rows += [(tr["who"], 2 * tr["days"] + 1) for tr in g["trips"].values() if tr.get("start") is not None]
    for n, d in rows:
        q = next((q for q in state["people"] if q["name"] == n), None)
        if q and q.get("household"):
            days[q["household"]] = days.get(q["household"], 0) + d
    return days


# ---- 季節の終わり (G6) ----

def _g6_records(state, frac):
    """この季節の記録 (G5 のもめごとを決める前。どの量に記録があるかを決める)"""
    e2, g, g5 = state["era2"], _g6(state), state["era2"].get("g5") or {}
    g["cover"], g["credit"] = {}, {}
    keep = {n: d for n, d in sorted(g["keep_days"].items()) if d > 0}
    if not keep:
        return
    homes = _homes(state)
    flow = {h: v for h, v in g5.get("flow", {}).items() if h in homes}
    work = _g6_workdays(state)
    sd = e2["step_day"]
    need = {"蓄え": math.ceil(sum(v[0] + v[1] + v[2] for v in flow.values()) / GRAIN / TOKEN["草の種"]) + math.ceil(sum(work.values()) / TOKEN["日"]),
            "交換": sum(math.ceil(n / TOKEN.get(k, 100)) for k, n in g["moved"].items()) + sum(1 for d in g["debts"] if d["day"] >= sd - 1),
            "刈る": math.ceil(sum(n for row in g5.get("reap", {}).values() for n in row.values()) / TOKEN["草の種"])}
    done, how, env = {w: 0 for w in WHATS}, {w: None for w in WHATS}, None
    for n, days in keep.items():
        j = g["jobs"].get(n) or {"what": list(WHATS), "how": "数え札"}
        cap = days * RATE[j["how"]]
        for w in j["what"]:
            use = min(cap, need[w] - done[w])
            if use > 0:
                done[w] += use
                cap -= use
                how[w] = "板" if "板" in (j["how"], how[w]) else "数え札"
                if w == "交換" and j["how"] in ("封筒", "板"):
                    env = "板" if j["how"] == "板" or env == "板" else "封筒"
    full = [w for w in WHATS if need[w] > 0 and done[w] >= need[w]]
    g["cover"] = {w: how[w] for w in full}
    if "交換" in full:
        for d in g["debts"]:
            if d["day"] >= sd - 1 and not d.get("proof"):
                d["proof"] = env or "数え札"
    if "蓄え" in full:
        g["credit"] = work
    tokens = sum(done.values())
    if tokens:
        g["token_seasons"] += 1
        g["big"] = max(g["big"], sum(need.values()))
    g["records"] = (g["records"] + [{"day": state["day"], "keepers": {n: [d, (g["jobs"].get(n) or {}).get("how", "数え札")] for n, d in keep.items()},
                                      "need": need, "done": done, "how": how, "complete": full, "envelope": env}])[-8:]
    who = "・".join(keep)
    parts = [f"{WHAT_WORDS[w]} ({'全部残せた' if w in full else '途中まで'}。{done[w]} / {need[w]} 個分)" for w in WHATS if need[w] and done[w]]
    log(state, "記録", list(keep)[0], f"{who} が、この季節の " + ("、".join(parts) if parts else "記録をつけようとしたが、残せたものはなかった")
        + (" を残した" if parts else ""), count=tokens, how="・".join(sorted({x for x in how.values() if x})) or "数え札")


def _g6_range(rng, x, s):
    lo, hi = x * rng.uniform(1 - s, 1), x * rng.uniform(1, 1 + s)
    return [int(lo // 100 * 100), int(-(-hi // 100) * 100)]


def _g6_ladder(state):
    """記録の道具 (困りごとが起きてから使えるようになる)。使うかは人が決める"""
    g, day = _g6(state), state["day"]
    op = g["open"]
    if not op["数え札"] and g["seal_seasons"] >= 1 and g["unchecked"] >= 1:
        op["数え札"] = day
        log(state, "記録", None, "印で封をするようになり、記録のない量を覚えで決めることも起きた。これからは、粘土の数え札で量を数えて残せる (主な仕事「記録をつける」)",
            tool="数え札")
    if op["数え札"] and not op["封筒"] and any(d["status"] == "まだ" for d in g["debts"]):
        op["封筒"] = day
        log(state, "記録", None, "ほかの村との貸し借りがある。これからは、貸し借りの数え札を粘土の玉 (封筒) に入れ、外に印を押して残せる", tool="封筒")
    if op["数え札"] and not op["板"] and g["token_seasons"] >= TABLET_SEASONS and g["big"] >= TABLET_TOKENS:
        op["板"] = day
        log(state, "記録", None, f"数え札で記録した季節が {g['token_seasons']} つになり、数え札が 1 季節に {g['big']} 個も要る季節があった。"
            "これからは、粘土の板に、物のしるしと数のしるしを分けて押して記せる", tool="板")


def _town(state):
    """町の目安 (いまの季節)。届いた日は区切り F3 に残る (あとで下回っても消さない)"""
    g = state["era2"].get("g6") or {}
    last = g.get("meets", [])[-TOWN_RUN:]
    others = g.get("others", [])
    run = len(last) == TOWN_RUN and all(any(d in o["contacts"] for o in others) for d in last)
    partners = [o for o in others if any(d in last for d in o["contacts"])]
    biggest = max((o["people"] for o in partners), default=0)
    pop = sum(1 for q in state["people"] if q["alive"])
    ads, nf = len(adults(state)), len(g.get("nonfood", []))
    ok = bool(g) and pop >= TOWN_POP and run and len(partners) >= TOWN_PARTNERS and pop >= CENTRE * biggest and nf >= NONFOOD * ads - 1e-9
    return {"ok": ok, "pop": pop, "run": run, "partners": len(partners), "biggest": biggest, "nonfood": nf, "adults": ads}


def _record_ok(state):
    """記録 (文字の入口): 物のしるしと数のしるしを分けて記した粘土の板で、量を確かめた"""
    return ((state["era2"].get("g6") or {}).get("checked") or {}).get("板", 0) >= 1


def _g6_name(state):
    e2 = state["era2"]
    n = _name(e2["next_name"])
    e2["next_name"] += 1
    return n


def _g6_settled(state, v, accepted):
    """ほかの村から来た群れを、受け入れた / 受け入れなかった"""
    o = _other(state, v.get("from"))
    if not o:
        return
    if accepted:
        o["trust"] = min(1.0, round(o["trust"] + 0.1, 2))
        if v.get("seed") is not None:
            o["people"] = max(0, o["people"] - len(v["members"]))
            _g6(state)["joined"] += len(v["members"])
    else:
        o["trust"] = max(0.0, round(o["trust"] - 0.1, 2))


def _g6_season_end(state, frac):
    """季節の終わり (G6。G5 の季節の終わりのあと): ほかの村ができる → 来る (申し出) → 住みたい人 → 貸し借り → 封のかけら → 出し入れの見え方 → 記録の道具 → 町"""
    e2, g, day = state["era2"], _g6(state), state["day"]
    rng = _rng(state, G6_SALT)  # この季節の終わりの G6 の乱数は、すべてこの列から (順番を変えない)
    sd, g5 = e2["step_day"], e2.get("g5") or {}
    # 0. 途中で区切った季節: まだ帰っていない人は、持ち物を持ち帰ったことにする (向こうで交換したあとなら、受けとった物と受けとってもらえなかった物。
    #    交換の前なら、持って行った物。2026-10-09 確かめ役: 前は、向こうが受けとって何も払えなかったとき、渡した物も持ち帰っていた)
    for name, tr in g["trips"].items():
        if tr.get("state") == "行く":
            if tr.get("bartered"):
                _g6_put(state, tr["side"], tr["got"], tr["goats_in"])
                _g6_put(state, tr["side"], tr["back"])
            else:
                _g6_put(state, tr["side"], tr["took"])
            tr.update(state="帰った", end=day)
            g["trip_log"].append(dict(tr))
    # 1. 村を出た家 (G5) は、まだだれも知らない「分かれた家の村」になる (G6 の前に出た家も。来たときに初めてお題に出る)
    for f in g5.get("fissions", []):
        if not any(o["household"] == f["household"] for o in g["others"]):
            _new_other(state, rng, "分かれた家", household=f["household"], people=len(f["people"]), goats=f["goats"], grain=round(f["store"] / GRAIN))
    # 2. この季節の終わりに来たよその群れの、来たところ (G6 に入る前に来た人の来たところは書かない)
    for v in e2["visitors"]:
        if v.get("day") == day and "from" not in v:
            st = [o for o in g["others"] if o["kind"] == "よその村"]
            o = rng.choice(st) if st and (len(st) >= MAX_STRANGERS or rng.random() < 0.5) else _new_other(state, rng, "よその村")
            v["from"] = o["id"]
            o["known"] = o["known"] or day
            log(state, "よその村", None, f"よその群れの {'・'.join(m['name'] for m in v['members'])} は、{_okey(o)} から来たと言った", other=o["id"])
    # 3. 交換をもとめて、よその村の人が来る (G6 の最初の季節の終わりは必ず。【仮定】交換は村の始まりからあったので、待たない (計画 3.))
    #    最初の季節の終わりに、2. で群れの来たところの村ができていたら、その村の人が来る (新しい村は作らない。2026-10-09 確かめ役: 前は 2. で村ができると、来ないことが多かった)
    st = [o for o in g["others"] if o["kind"] == "よその村"]
    came = set()
    if not g["log"] or (len(st) < MAX_STRANGERS and rng.random() < STRANGER_P * frac):
        o = st[0] if st and not g["log"] else _new_other(state, rng, "よその村")
        o["known"] = o["known"] or day
        _g6_offer_new(state, rng, o, True)
        came.add(o["id"])
    # 4. ほかの村の 1 季節 (【仮定】人は 1 季節 0.5% ほど増える。夏のはじめに、その年が苦しい年か決まる。ヤギは春に増える。土器・鎌は少しずつ割れる)
    nxt = season(day + 1)
    for o in g["others"]:
        if rng.random() < o["people"] * 0.005 * frac:
            o["people"] += 1
        if nxt == "夏":
            o["bad"] = day if rng.random() < BAD_P else None
            o["grain"] = min(o["grain"], o["people"] * 20) if o["bad"] is not None else min(o["people"] * 300, o["grain"] + o["people"] * 100)
        if nxt == "春":
            o["goats"] = min(max(o["people"], 2), round(o["goats"] * 1.3))
        o["pots"], o["sickles"] = int(o["pots"] * 0.97), int(o["sickles"] * 0.95)
        if o["has_obsidian"]:
            o["obsidian"] = min(40, o["obsidian"] + 8)
    # 5. ほかの村の人が来る (この季節に村の人が行った村は来ない)
    went = {tr.get("to") for tr in g["trips"].values()}
    for o in g["others"]:
        if o["id"] in came or o["id"] in went:
            continue
        due = any(d["other"] == o["id"] and d["status"] == "まだ" and d["due"] <= day + 1 for d in g["debts"])
        p = min(0.8, max(0.8 if due else 0.0, CONTACT_P[o["kind"]] * o["trust"] / 0.5))
        if rng.random() < p * frac:
            first = o["known"] is None
            o["known"] = o["known"] or day
            _g6_offer_new(state, rng, o, first)
    # 6. 交換している村から、ここで暮らしたい人が来る (町に人が集まる。【文献・二次】ブラクには移り住んだ人が加わったとする調べがある【仮定】見込み)
    recent = g["meets"][-TOWN_RUN:]
    for o in g["others"]:
        if o["known"] is None or o["people"] < JOIN_MIN or not any(c in recent for c in o["contacts"]):
            continue
        if rng.random() < JOIN_P * min(1.0, store_days(state) / 120) * (2 if o["bad"] is not None else 1) * frac:
            members = []
            for i in range(rng.choice([1, 2, 2, 3])):
                age = rng.randint(16, 35) if i < 2 else rng.randint(2, 12)
                members.append({"name": _g6_name(state), "sex": "女" if rng.random() < 0.5 else "男", "age": age})
            e2["visitors"].append({"name": members[0]["name"], "members": members, "day": day, "from": o["id"], "seed": rng.getrandbits(31)})
            txt = "、".join(f"{m['name']} ({m['sex']}、{m['age']} 歳)" for m in members)
            log(state, "訪れる", None, f"{_okey(o)} から {txt} がやって来て、「ここで暮らしたい」と言った", other=o["id"])
    # 7. 返されないまま 1 年たった貸し借り
    for d in g["debts"]:
        if d["status"] == "まだ" and day - d["due"] >= YEAR:
            d.update(status="返されない", end=day)
            o = _other(state, d["other"])
            if o:
                o["trust"] = max(0.0, round(o["trust"] - 0.2, 2))
            log(state, "貸し借り", None, f"[{d['id']}] ({o['name'] if o else 'ほかの村'} が返すはずの {_gw(d['goods'])}) は、返されないまま 1 年たった", debt=d["id"])
    # 8. 封のかけら (この季節)
    ss = g["season_seals"]
    if ss:
        log(state, "封", None, "この季節、印で封をした倉や村の蓄えが開けられた (割った封のかけらは取っておいた): "
            + "、".join(f"{h}の印 {n} 回" if h != "(印なし)" else f"印のない封 {n} 回" for h, n in sorted(ss.items())), count=sum(ss.values()))
        for h, n in ss.items():
            g["sealings"][h] = g["sealings"].get(h, 0) + n
        if sum(1 for h in ss if h != "(印なし)") >= 2:
            g["seal_seasons"] += 1
    # 9. 前の季節の、家ごとの村の蓄えへの出し入れの見え方 (記録がなければ、みんなの覚えの幅。印で封をした家は幅が半分)
    s, how = _g6_spread(state), g["cover"].get("蓄え")
    rows = {}
    for h, (i, out) in sorted(g5.get("last_flow", {}).items()):
        sh = s / 2 if h in g["seals"] and g["store_sealed"] == sd else s
        rows[h] = [i, out] if how else [_g6_range(rng, i, sh), _g6_range(rng, out, sh)]
    g["shown"] = {"day": day, "how": how, "rows": rows}
    # 10. 食べ物をとらない人・記録の道具・町
    g["nonfood"] = sorted(set(e2.get("specialists", [])) | {n for n, x in g["keep_days"].items() if x >= KEEPER_DAYS * frac})
    _g6_ladder(state)
    t = _town(state)
    if t["ok"] and g["town_seen"] is None:
        g["town_seen"] = day
        log(state, "町", None, f"村の人は {t['pop']} 人で、交換した村のうちいちばん大きい村 (約 {t['biggest']} 人) の {CENTRE} 倍をこえた。この {TOWN_RUN} 季節は毎季節ほかの村と"
            f"交換し、相手の村は {t['partners']} つ。この季節、作ることや記録に 20 日以上を使った人は、大人 {t['adults']} 人のうち {t['nonfood']} 人")
    if g["town_seen"] is not None:
        g["town_low"] = 0 if t["ok"] else g["town_low"] + 1
        if g["town_low"] == 4:
            log(state, "町", None, f"町の目安を下回ったまま 1 年たった (村の人 {t['pop']} 人、この 4 季節に交換した村 {t['partners']} つ)")
    g["log"].append({"day": day, "pop": t["pop"], "adults": t["adults"], "households": len(_homes(state)), "known": sum(1 for o in g["others"] if o["known"]),
                     "partners": t["partners"], "biggest": t["biggest"], "run": t["run"], "exchanges": g["exchanges"], "joined": g["joined"],
                     "seals": len(g["seals"]), "sealings": sum(ss.values()), "tools": [k for k, v in g["open"].items() if v],
                     "tokens": sum(g["records"][-1]["done"].values()) if g["records"] and g["records"][-1]["day"] == day else 0,
                     "checked": dict(g["checked"]), "misremember": g["misremember"], "nonfood": t["nonfood"], "town": t["ok"]})
    g["season_seals"], g["opened"], g["taken"], g["moved"] = {}, {}, {}, {}
    g["seed"] = rng.getrandbits(31)  # 次の季節の集まりと 30 日の乱数のもと (この列の最後に引く)


def _g6_indicators(state):
    """G6 の目安 (G6 の前は鍵を足さない。だから G6 の前の state.json・app_data.json は前とまったく同じ。G6 に入って g6 を作る前は 0)"""
    if not era_at_least(state, "G6"):
        return {}
    base = {"g6_on": False, "g6_known": 0, "g6_partners": 0, "g6_biggest": 0, "g6_run": 0, "g6_exchanges": 0, "g6_debts_open": 0, "g6_joined": 0,
            "g6_seals": 0, "g6_sealings": 0, "g6_seal_seasons": 0, "g6_tools": "", "g6_records": 0, "g6_checked": 0, "g6_checked_tablet": 0,
            "g6_misremember": 0, "g6_nonfood": 0, "g6_town": False, "g6_town_day": None, "g6_record_day": None}
    g = state["era2"].get("g6")
    if not g:
        return base
    t = _town(state)
    sub = {x["f"]: x["day"] for x in state["era2"].get("substeps", []) if x["g"] == "G6"}
    run = 0
    for d in reversed(g["meets"]):
        if not any(d in o["contacts"] for o in g["others"]):
            break
        run += 1
    return base | {"g6_on": True, "g6_known": sum(1 for o in g["others"] if o["known"] is not None), "g6_partners": t["partners"], "g6_biggest": t["biggest"],
                   "g6_run": run, "g6_exchanges": g["exchanges"], "g6_debts_open": sum(1 for d in g["debts"] if d["status"] == "まだ"),
                   "g6_joined": g["joined"], "g6_seals": len(g["seals"]), "g6_sealings": sum(g["sealings"].values()), "g6_seal_seasons": g["seal_seasons"],
                   "g6_tools": "・".join(k for k, v in g["open"].items() if v), "g6_records": g["token_seasons"],
                   "g6_checked": sum(g["checked"].values()), "g6_checked_tablet": g["checked"]["板"], "g6_misremember": g["misremember"],
                   "g6_nonfood": t["nonfood"], "g6_town": t["ok"], "g6_town_day": sub.get("F3"), "g6_record_day": sub.get("F4")}


# ---- アプリ用 ----

def g6_places(state):
    """3D の再生で、ほかの村へ行く人が歩いて行く地図の端 (知っている村だけ。G6 の前は空)"""
    g = (state.get("era2") or {}).get("g6") or {}
    return [{"id": o["id"], "label": o["name"], "x": min(79, max(0, o["edge"][0])), "y": min(79, max(0, o["edge"][1])), "far": True}
            for o in g.get("others", []) if o["known"] is not None]


def g6_export(state):
    g = state["era2"]["g6"]
    return {"others": [{k: o[k] for k in ("id", "name", "kind", "household", "dir", "days", "edge", "known", "people", "contacts")} for o in g["others"]
                       if o["known"] is not None],
            "seals": g["seals"], "open": g["open"], "records": g["records"], "debts": g["debts"], "trips": g["trip_log"][-200:], "log": g["log"], "end": g["end"]}
```

### 5.2 Hooks in existing `era2.py` functions

Unified diff against `f8a9e46` (the two new blocks are shown as one-line placeholders; they are §5.1 and §5.4). Every changed line is either gated by `era_at_least(state, "G6")` or reads a key that only G6 code creates (`seed`, `from`, `sealed`, `record`, `harm_true`, `away`), so the arithmetic and the order of random draws before G6 are unchanged (§0 A).

```diff
--- a/sim/society/era2.py
+++ b/sim/society/era2.py
@@ -32,7 +32,8 @@
 
 
 def acts2(state):
-    return ACTS2 + (ACTS_G3 if era_at_least(state, "G3") else [])
+    return (ACTS2 + (ACTS_G3 if era_at_least(state, "G3") else []) + (ACTS_G6 if era_at_least(state, "G6") else [])
+            + ([ACT_RECORD] if era_at_least(state, "G6") and ((state["era2"].get("g6") or {}).get("open") or {}).get("数え札") else []))
 CHILD_EAT = [(3, 800), (10, 1300), (15, 1800)]  # 【仮定】子が 1 日に食べる量 (年齢まで, kcal)
 UNITS.setdefault("乳", ("杯", 150))              # 【仮定】ヤギの乳 1 杯
 world.FOOD_NAME.setdefault("乳", "ヤギの乳")
@@ -123,6 +124,10 @@
     g5 = era_at_least(state, "G5")
     reps = _reps(state) if g5 and e2.get("rep_mode") else set()
     c5 = {"judge": {}, "by": {}, "feast": set(), "feast_by": set(), "leader": {}, "call": {}}  # G5: 季節の集まりの答え
+    g6 = era_at_least(state, "G6")  # G6 の部分は、G6 の前は何もしない
+    c6 = {"trade": {}, "trade_by": {}, "house": {}, "seal": {}, "store": set(), "store_by": set()}  # G6: 季節の集まりの答え
+    if g6:
+        _g6_new_season(state)
     for name, raw in answers.items():
         p = alive.get(name)
         if not p:
@@ -160,6 +165,8 @@
             place = job.get("place") if job.get("place") in places else "camp"
             with_ = job.get("with") if isinstance(job.get("with"), list) else []
             q["plan"] = {"activity": act, "place": place, "with": [w for w in with_ if isinstance(w, str) and w in alive and w != q["name"]]}
+            if g6 and act in ACTS_G6 + [ACT_RECORD]:  # 行き先・持って行く物・残すもの (e2["jobs"] には入れない)
+                _g6_job(state, q, job, own)
             e2["jobs"][q["name"]] = {"sow": max(0, min(1000, _int(a.get("sow")))), "pick": max(0, min(40, _int(a.get("pick")))),
                                      "plant": max(0, min(5, _int(a.get("plant")))),
                                      "eat_goat": max(0, min(5, _int(a.get("eat_goat")))) if q is p and own else 0,
@@ -173,6 +180,8 @@
                 accept.setdefault(v, []).append((q["name"], ok is True or ok in ("true", "はい", "賛成")))
         if g5:
             _g5_collect(state, c5, p, a, fam)
+        if g6:
+            _g6_collect(state, c6, p, a, fam, own)
     for t in talk:  # 話は聞き手に届く
         for n, q in alive.items():
             if n != t["from"] and (t["to"] == "みんな" or t["to"] == n):
@@ -182,6 +191,8 @@
         log(state, "掟", None, msg)
     if g5:
         _g5_meeting(state, c5, len(alive))  # 掟を決めてから (この集まりで採用された罰の掟も、この集まりで使う)
+    if g6:
+        _g6_meeting(state, c6, len(alive))  # 印 → 村の蓄えの封 → 申し出 (よそから来た人の受け入れの前)
     _settle_visitors(state, accept, len(alive))
     _eat_goats(state)
 
@@ -201,6 +212,7 @@
     e2 = state["era2"]
     rng = _rng(state, 11)
     for v in e2["visitors"]:
+        vr = random.Random(v["seed"]) if v.get("seed") is not None else rng  # G6: ほかの村から来た群れは、その群れの乱数で (前からの列に足さない)
         member_names = [m["name"] for m in v["members"]]
         votes = {}  # 大人ごとの答え (群れのだれの名前で書いても同じ群れの受け入れ)
         for key, vals in accept.items():
@@ -215,17 +227,23 @@
-            plans = [q["plan"] for q in adults(state) if q["name"] in accept_answered(e2)]
+            plans = [q["plan"] for q in adults(state) if q["name"] in accept_answered(e2) and q["plan"]["activity"] not in ACTS_G6 + [ACT_RECORD]]  # G6: 行き先のない「交換に行く」をまねない
             common = max(plans, key=lambda pl: sum(1 for x in plans if x["activity"] == pl["activity"] and x["place"] == pl["place"])) if plans else {"activity": "採集", "place": "camp"}
             for m in v["members"]:
-                q = _new_person(state, rng, m["sex"], m["age"], child=m["age"] < ADULT, origin="よそから来た", name=m["name"],
+                q = _new_person(state, vr, m["sex"], m["age"], child=m["age"] < ADULT, origin="よそから来た", name=m["name"],
                                 mother=guardian if m["age"] < ADULT else None)
                 e2["joined"].append(q["name"])
                 q["household"] = member_names[0] + "の家"
+                if v.get("from"):  # G6: 来たほかの村 (家を建てる場所を、その村の方角にする)
+                    q["from_village"] = v["from"]
                 if not q.get("child"):
                     q["plan"] = {"activity": common["activity"], "place": common["place"], "with": []}
                     e2["jobs"][q["name"]] = {"sow": 0, "pick": 0, "plant": 0, "eat_goat": 0, "harvest": 0}
             names = "・".join(member_names)
-            log(state, "加わる", None, f"よそから来た {names} が、村に加わった (賛成 {yes} / {n_adults})")
+            o = _other(state, v.get("from")) if v.get("from") else None
+            log(state, "加わる", None, f"よそから来た {names} が、村に加わった ({o['name'] + 'から。' if o else ''}賛成 {yes} / {n_adults})")
         else:
-            log(state, "去る", None, f"よそから来た {v['name']} たちは、受け入れられず去っていった (賛成 {yes} / {n_adults})")
+            o = _other(state, v.get("from")) if v.get("from") else None
+            log(state, "去る", None, f"よそから来た {v['name']} たちは、受け入れられず{'、' + o['name'] + 'へ帰って' if o else '去って'}いった (賛成 {yes} / {n_adults})")
+        if v.get("from"):
+            _g6_settled(state, v, yes * 2 > n_adults)
     e2["visitors"] = []
 
 
@@ -283,15 +301,19 @@
             _catch_goat(state, p, t, rng)
         elif act == "住まいを建てる" and era_at_least(state, "G3") and state["camp"].get("dwelling_day") is not None:
             _build_house(state, p, t)
+        elif act == ACT_RECORD and era_at_least(state, "G6"):
+            _g6_keep_day(state, p, t)
         if act in CRAFTS:
             e2.setdefault("craft_days", {})[p["name"]] = e2.get("craft_days", {}).get(p["name"], 0) + 1
             if era_at_least(state, "G3"):
                 _craft(state, p, t, act)
+    if era_at_least(state, "G6"):
+        _g6_trips_day(state)  # 交換に行く (出かけている人は、夕方に木から取らず、畑も刈らない)
     # 夕方、キャンプのそばの木から取る (季節のはじめに決めた量。world.evening の「取る」を使う)
     takes = []
     for p in adults(state):
         job = e2["jobs"].get(p["name"], {})
-        if job.get("pick") and not _injured_today(p):
+        if job.get("pick") and not _injured_today(p) and not (p.get("today") or {}).get("away"):
             takes.append({"who": p["name"], "food": "木の実", "count": job["pick"], "tree": True})
         if job.get("plant") and day == e2.get("step_day"):  # この回の最初の日に、木の実を埋める
             _plant(state, p, job["plant"])
@@ -305,7 +327,7 @@
     sickles = e2.get("sickles", 0)
     for p in adults(state):
         n = e2["jobs"].get(p["name"], {}).get("harvest", 0)
-        if n and not _injured_today(p):
+        if n and not _injured_today(p) and not (p.get("today") or {}).get("away"):
             if sickles > 0 and any(f["state"] == "実った" for f in e2["fields"]):  # 鎌を使うと 2 倍刈れる (村の鎌の数の人まで)
                 sickles -= 1
                 n *= 2
@@ -360,7 +382,10 @@
             got = sum(_move_food(state["store"], p["food"], None, keep - have).values())
             _flow(state, p, 1, got)
             if have + got < keep and era_at_least(state, "G4"):  # 村の蓄えが足りないときは、家の倉から
-                got += sum(_move_food(_house(state, p.get("household"))["store"], p["food"], None, keep - have - got).values())
+                took = sum(_move_food(_house(state, p.get("household"))["store"], p["food"], None, keep - have - got).values())
+                got += took
+                if took and era_at_least(state, "G6"):  # G6: 印で封をした家の倉を開けた (封のかけら)
+                    _g6_opened(state, p, "倉")
                 if have + got < keep and p["hunger"] >= 0.6 and era_at_least(state, "G5"):  # G5: それでも足りず、ひどく空腹 (前からの 0.6) なら、よその家の倉から
                     _steal(state, p, keep - have - got)
     ate = {"total": 0, "sown": 0, "by": {}}
@@ -422,7 +447,9 @@
         p["skills"]["道具"] = round(min(1, sk + 0.02), 3)
         if n:
             e2["sickles"] = e2.get("sickles", 0) + n
-            log(state, "道具", p["name"], f"{p['name']} が石の刃を木の柄にはめた鎌を {n} 本作った (村の鎌 {e2['sickles']} 本)", count=n)
+            obs = _g6_obsidian_blades(state, n) if era_at_least(state, "G6") else 0
+            extra = f" (うち {obs} 本は黒曜石の刃)" if obs else ""
+            log(state, "道具", p["name"], f"{p['name']} が石の刃を木の柄にはめた鎌を {n} 本作った{extra} (村の鎌 {e2['sickles']} 本)", count=n)
         else:
             log(state, "道具", p["name"], f"{p['name']} がキャンプで石の刃を打ち欠き、鎌の柄を削った", count=0)
 
@@ -442,7 +469,11 @@
                 _move_food(st, [], "草の種", g / grain * lost * UNITS["草の種"][1])
         log(state, "虫", None, f"蓄えの草の種 約 {lost} つかみ が、虫やネズミに食べられた" + (f" (土器に入れていた 約 {int(safe)} つかみ は無事)" if safe else ""), amount=lost)
     for key, rate, what in (("pots", POT_BREAK, "土器"), ("sickles", SICKLE_BREAK, "鎌")):
-        broke = sum(1 for _ in range(e2.get(key, 0)) if rng.random() < rate * frac)
+        obs = min(e2.get(key, 0), (e2.get("g6") or {}).get("obs_sickles", 0)) if key == "sickles" and era_at_least(state, "G6") else 0
+        hits = [i for i in range(e2.get(key, 0)) if rng.random() < rate * frac * (OBS_BREAK if i < obs else 1)]  # 1 つに 1 回引く (G6 の前と同じ数)
+        broke = len(hits)
+        if obs:
+            e2["g6"]["obs_sickles"] -= sum(1 for i in hits if i < obs)
         if broke:
             e2[key] -= broke
             log(state, "道具", None, f"村の{what}が {broke} {'個' if key == 'pots' else '本'} 割れた (残り {e2[key]})")
@@ -461,22 +492,41 @@
     return {h for h, v in state["era2"].get("homes", {}).items() if v.get("built") is not None}
 
 
-def _house_site(state):
-    """家族の住まいを建てる場所: キャンプから 5〜9 マスの輪の上で、川でなく、南西の畑と村の住まいから離れ、ほかの家と重ならない所"""
+def _house_site(state, h=None):
+    """家族の住まいを建てる場所: キャンプから 5〜9 マスの輪の上で、川でなく、南西の畑と村の住まいから離れ、ほかの家と重ならない所
+    (G6: 11〜15 マスの輪も使う。ほかの村から来た家は、まずその村の方角の 11〜15 マスに建てる。ブラクのまわりの、来たところごとの小さな集まり)"""
     cx, cy = state["camp"]["x"], state["camp"]["y"]
     used = [(v["x"], v["y"]) for v in state["era2"].get("homes", {}).values()]
-    for r in (5, 7, 9):
+
+    def ok(x, y):
+        ix, iy = int(x), int(y)
+        if not (0 <= ix < W and 0 <= iy < H) or state["terrain"][iy][ix] == "r":
+            return False
+        if (x < cx - 1 and y > cy + 1) or math.hypot(x - (cx - 2.7), y - (cy - 1.7)) < 3:  # 南西は畑、北西は村の住まい
+            return False
+        return not any(math.hypot(x - ux, y - uy) < 2.2 for ux, uy in used)
+
+    rings = (5, 7, 9)
+    if era_at_least(state, "G6"):
+        src = next((q.get("from_village") for q in state["people"] if h and q.get("household") == h and q.get("from_village")), None)
+        o = _other(state, src) if src else None
+        if o:
+            ang = math.atan2(o["edge"][1] - cy, o["edge"][0] - cx)
+            for r in (11, 13, 15):
+                for k in sorted(range(24), key=lambda k: abs(math.remainder(math.radians(k * 15) - ang, 2 * math.pi))):
+                    a = math.radians(k * 15)
+                    if abs(math.remainder(a - ang, 2 * math.pi)) > math.radians(60):
+                        continue
+                    x, y = round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a), 1)
+                    if ok(x, y):
+                        return x, y
+        rings += (11, 13, 15)
+    for r in rings:
         for k in range(12):
-            a = math.radians(k * 30 + (15 if r == 7 else 0))
+            a = math.radians(k * 30 + (15 if r in (7, 11, 15) else 0))
             x, y = round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a), 1)
-            ix, iy = int(x), int(y)
-            if not (0 <= ix < W and 0 <= iy < H) or state["terrain"][iy][ix] == "r":
-                continue
-            if (x < cx - 1 and y > cy + 1) or math.hypot(x - (cx - 2.7), y - (cy - 1.7)) < 3:  # 南西は畑、北西は村の住まい
-                continue
-            if any(math.hypot(x - ux, y - uy) < 2.2 for ux, uy in used):
-                continue
-            return x, y
+            if ok(x, y):
+                return x, y
     return cx + 3.0, cy - 4.0
 
 
@@ -488,7 +538,7 @@
     homes = state["era2"].setdefault("homes", {})
     v = homes.get(h)
     if not v:
-        x, y = _house_site(state)
+        x, y = _house_site(state, h)
         v = homes[h] = {"x": x, "y": y, "start": state["day"], "built": None, "size": 0, "work": 0.0, "sizes": []}
     before = v["work"]
     v["work"] = round(before + t.get("work_h", 6) * (0.6 + 0.4 * p["skills"].get("道具", 0.1)), 2)
@@ -653,9 +703,11 @@
     """G5: 家ごとに、村の蓄えに入れた量 (0)・取った量 (1)・家の倉を持つ家が自分の畑にまいた村の草の種 (2) を数える (大人の分だけ。子は村の蓄えで育つ決まり)"""
     if kcal > 0 and era_at_least(state, "G5"):
         _g5(state)["flow"].setdefault(p.get("household") or "-", [0, 0, 0])[i] += kcal
+        if i == 1 and era_at_least(state, "G6"):  # G6: 印で封をした村の蓄えを開けた (封のかけら)
+            _g6_opened(state, p, "蓄え")
 
 
-def _incident(state, kind, frm, against, kcal, what, eid=None):
+def _incident(state, kind, frm, against, kcal, what, eid=None, sealed=False):
     """もめごとのもと (世界で起きたこと)。季節の終わりに、もめごとになるか決める。frm = 損をした家 (言い出す家)、against = 相手の家"""
     if not frm or not against or frm == against or kcal <= 0:
         return
@@ -666,6 +718,8 @@
         inc.append(x)
     x["kcal"] += kcal
     x["events"] += [eid] if eid is not None else []
+    if sealed:  # G6: 印で封をした倉の封が割れていた (必ずもめごとになる)
+        x["sealed"] = True
 
 
 def _steal(state, p, want):
@@ -673,14 +727,19 @@
     hs, mine, homes = state["era2"].get("house", {}), p.get("household"), _homes(state)
     if not mine:  # 家のない人 (今はいない) は取らない。取ると、もめごとのもとにならず、毎日記録が出るため (2026-10-08 確認役の指摘)
         return
-    for h in sorted([h for h in hs if h in homes and h != mine and hs[h]["store"]], key=lambda h: -sum(f["kcal"] for f in hs[h]["store"])):
+    sealed = ((state["era2"].get("g6") or {}).get("seals") or {}) if era_at_least(state, "G6") else {}  # G6: 封をした倉は、ほかの倉がからになってから
+    for h in sorted([h for h in hs if h in homes and h != mine and hs[h]["store"]], key=lambda h: (h in sealed, -sum(f["kcal"] for f in hs[h]["store"]))):
         if want <= 0:
             break
         by = _move_food(hs[h]["store"], p["food"], None, want)
         want -= sum(by.values())
         new = not any((x["kind"], x["from"], x["against"]) == ("倉", h, mine) for x in _g5(state)["incidents"])
-        eid = log(state, "倉から取る", p["name"], f"ひどく空腹の {p['name']} が、{h}の倉から {food_words(by)} を取って食べた", owner=h, home=mine) if new else None
-        _incident(state, "倉", h, mine, sum(by.values()), f"{mine}の人が、{h}の倉から食べ物を取って食べた", eid)
+        if h in sealed:
+            eid = log(state, "封", p["name"], f"{h}の倉の封が割れていた: ひどく空腹の {p['name']} ({mine}) が、封を割って食べ物を取って食べた", owner=h, home=mine) if new else None
+        else:
+            amt = "食べ物" if era_at_least(state, "G6") else food_words(by)  # G6: 量は記録にない
+            eid = log(state, "倉から取る", p["name"], f"ひどく空腹の {p['name']} が、{h}の倉から {amt} を取って食べた", owner=h, home=mine) if new else None
+        _incident(state, "倉", h, mine, sum(by.values()), f"{mine}の人が、{h}の倉から食べ物を取って食べた", eid, sealed=h in sealed)
 
 
 def _g5_reap(state, p, owner, n, to_village):
@@ -700,8 +759,9 @@
     g["next"] += 1
     g["disputes"].append(d)
     # 注意: log() の引数名 kind・who・text を、データの名前に使わない (TypeError になる)
+    claim = _g6_claim(state, d) if era_at_least(state, "G6") else ""  # G6: 記録があれば正しい量、なければ言い出した家の覚え
     d["event"] = log(state, "もめごと", None, f"もめごと [{d['id']}] ({d['kind']}): {d['from']}が、{d['against']}のことで不満を言い出した。"
-                     f"{d['what']} (草の種にして 約 {d['harm']} つかみ 分)", dispute=d["id"], about=d["kind"])
+                     f"{d['what']} (草の種にして 約 {d['harm']} つかみ 分{claim})", dispute=d["id"], about=d["kind"])
 
 
 def _g5_season_end(state, frac):
@@ -732,9 +792,14 @@
     # (4) 刈る: よその家の畑で刈った草の種が、みな畑の持ち主の家の倉に入った (刈った人の家の取り分を 1 割とみる)
     for hh, row in sorted(g["reap"].items()):
         for o, n in sorted(row.items()):
-            _incident(state, "刈る", hh, o, n * REAP_SHARE * GRAIN, f"{hh}の人が{o}の畑で刈った草の種 {n} つかみ は、みな{o}の倉に入った")
+            what = f"{hh}の人が{o}の畑で刈った草の種 {n} つかみ は、みな{o}の倉に入った"
+            if era_at_least(state, "G6") and not _g6_cover(state, "刈る"):  # G6: 記録がなければ量は分からない
+                what = f"{hh}の人が{o}の畑で刈った草の種は、みな{o}の倉に入った (量は記録になく、覚えによる)"
+            _incident(state, "刈る", hh, o, n * REAP_SHARE * GRAIN, what)
     # (3) 蓄え: 村の蓄えに入れた量にくらべて、ほかの家より多く取った家 (1 季節に 1 つの家まで。言い出すのは、いちばん多く入れた家)
-    flow = {h: v for h, v in g["flow"].items() if h in homes}
+    flow = raw = {h: v for h, v in g["flow"].items() if h in homes}
+    if era_at_least(state, "G6"):
+        flow = _g6_credit(state, raw)  # G6: 配給の記録 (村の蓄えの記録を全部残せた季節は、作る人などの働いた日を「入れた」に数える)
     tin, tout = sum(v[0] for v in flow.values()), sum(v[1] + v[2] for v in flow.values())
     if len(flow) >= 2 and tin > 0 and tin >= 0.25 * tout:  # 【仮定】ほとんど蓄えで暮らした季節 (冬・春) は、だれの出し入れも目立たない
         r = max(1.0, tout / tin)  # 村みんなで蓄えを減らした季節は、入れた量の r 倍まで取っても多くない
@@ -748,13 +813,17 @@
             h = max(sorted(cand), key=lambda x: over[x] / need[x])
             i, o, s = flow[h]
             acts = "・".join(dict.fromkeys(q["plan"]["activity"] for q in adults(state) if q.get("household") == h))
-            _incident(state, "蓄え", frm, h, over[h] / len(homes),  # 【仮定】言い出した家の損 = 取りすぎを村の家の数で割った分
-                      f"この季節、{h}の大人は、村の蓄えから草の種にして 約 {round((o + s) / GRAIN)} つかみ 分を取り"
+            what = (f"この季節、{h}の大人は、村の蓄えから草の種にして 約 {round((o + s) / GRAIN)} つかみ 分を取り"
                       + (f" (家の畑にまいた村の草の種 {round(s / GRAIN)} つかみ をふくむ)" if s else "")
                       + f"、入れたのは 約 {round(i / GRAIN)} つかみ 分だった (おもな仕事: {acts}"
                       + (f"。家の倉に {food_words(holdings({'food': hs[h]['store']}))} がある" if h in full else "")
                       + f")。{frm}は 約 {round(flow[frm][0] / GRAIN)} つかみ 分を入れた")
-    g["last_flow"] = {h: [round(v[0] / GRAIN), round((v[1] + v[2]) / GRAIN)] for h, v in sorted(flow.items())}
+            if era_at_least(state, "G6") and not _g6_cover(state, "蓄え"):  # G6: 記録がなければ量は分からない
+                what = f"この季節、{h}の大人は、村の蓄えに入れた量にくらべて多く取った (おもな仕事: {acts})。量は記録になく、{frm}の覚えによる"
+            elif flow is not raw and (flow[h][0] != raw[h][0] or flow[frm][0] != raw[frm][0]):  # G6: 入れた量に、配給の記録の働いた日を数えた (文を事実どおりに)
+                what += " (入れた量は、記録した働いた日の分をふくむ)"
+            _incident(state, "蓄え", frm, h, over[h] / len(homes), what)  # 【仮定】言い出した家の損 = 取りすぎを村の家の数で割った分
+    g["last_flow"] = {h: [round(v[0] / GRAIN), round((v[1] + v[2]) / GRAIN)] for h, v in sorted(raw.items())}
     g["flow"], g["reap"] = {}, {}
     # もめごとのもと → もめごと (家が多いほどなりやすい。罰のある掟にあたることは必ずなる。同じ家どうしの同じ中身で収まっていないものには重ねる)
     pen = {l["penalty"]["for"] for l in state["laws"] if l["status"] == "採用" and l.get("penalty")}
@@ -764,10 +833,15 @@
             continue
         old = next((d for d in g["disputes"] if d["status"] == OPEN and (d["kind"], d["from"], d["against"]) == (inc["kind"], inc["from"], inc["against"])), None)
         if old:
-            old["harm"] += max(1, round(inc["kcal"] / GRAIN))
+            add = max(1, round(inc["kcal"] / GRAIN))
+            if "harm_true" in old:  # G6: 記録のないもめごとは、言い出した家の覚えで重ねる
+                ratio = old["harm"] / max(1, old["harm_true"])
+                old["harm_true"] += add
+                add = max(1, round(add * ratio))
+            old["harm"] += add
             old["because"] += inc["events"]
             log(state, "もめごと", None, f"もめごと [{old['id']}] に、また同じことが重なった: {inc['what']}", dispute=old["id"])
-        elif new < MAX_NEW and (inc["kind"] in pen or rng.random() < p):
+        elif new < MAX_NEW and (inc["kind"] in pen or inc.get("sealed") or rng.random() < p):  # sealed は G6 だけ
             _dispute(state, inc)
             new += 1
     g["incidents"] = []
@@ -959,12 +1033,17 @@
     for d in [d for d in g["disputes"] if d["status"] == OPEN]:
         parties = (d["from"], d["against"])
         v = c["by"].get(lead, {}).get(d["id"]) if lead in ads and ads[lead].get("household") not in parties else None
+        rec = d.get("record")  # G6: 記録のあるもめごとは、記録を見て確かめる (話し合える数に数えない)
         if v:
+            if rec:
+                _g6_check(state, d)
             _verdict(state, d, v, "まとめ役", lead)
             continue
-        if talked >= TALK_MAX:
+        if talked >= TALK_MAX and not rec:
             continue
-        talked += 1
+        talked += 0 if rec else 1
+        if rec:
+            _g6_check(state, d)
         tally = {k: len(s) for k, s in c["judge"].get(d["id"], {}).items()}
         top = max(tally.values(), default=0)
         elder = max([q for q in ads.values() if q.get("household") not in parties], key=lambda q: q["age"], default=None)  # 同じ年なら人の並びで先 (家の代表の決め方と同じ。2026-10-08)
@@ -1022,6 +1101,8 @@
         paid, words = _pay(state, d["against"], d["from"], (law["penalty"]["pay"] if law else min(d["harm"], MAX_PAY)) * GRAIN)
         if round(paid / GRAIN) <= 0:  # 半つかみより少ないものは、払ったと数えない (2026-10-08 確認役の指摘)
             paid, words = 0, ""
+        if era_at_least(state, "G6") and not law:  # G6: 記録のない量を覚えで払った (払った家が多く払ったと思うと、覚え違いのもと)
+            _g6_after_pay(state, d, round(paid / GRAIN))
     d.update(status="収まった", verdict=v, by=by, judge=who, paid=round(paid / GRAIN), law=law["id"] if law else None, end=state["day"])
     if by == "まとめ役":
         g["judged"] += 1
@@ -1058,6 +1139,9 @@
     return paid, "・".join(words)
 
 
+# ... (G6 の新しい節: 5.1 のコード) ...
+
+
 def _sow(state, p, want):
     e2 = state["era2"]
     by = _move_food(state["store"], [], "草の種", want * UNITS["草の種"][1])
@@ -1262,8 +1346,12 @@
         if e2["specialists"]:
             e2.setdefault("specialist_log", []).append({"day": day, "names": e2["specialists"]})
     _sync_households(state)
+    if era_at_least(state, "G6"):
+        _g6_records(state, frac)  # この季節の記録 (G5 のもめごとを決める前に。どの量に記録があるかを決める)
     if era_at_least(state, "G5"):  # 家族を決めてから (この季節に生まれた子も母の家に入る)。村が分かれて大人が 12 人以下になれば、次の _note_mode で代表の方式が終わる
         _g5_season_end(state, frac)
+    if era_at_least(state, "G6"):  # G5 のあと (この季節に村を出た家も、ほかの村になる)
+        _g6_season_end(state, frac)
     _note_mode(state)
 
 
@@ -1432,6 +1520,7 @@
         **_g4_indicators(state),
         **_g5_indicators(state),
         **_house_indicators(state),
+        **_g6_indicators(state),
     }
 
 
@@ -1485,6 +1574,10 @@
     "G5": ("第 2 段: 家族が 6 つ以上で、まとめ役がいる。罰のある掟が 3 つ以上採用されている。まとめ役がもめごとを 2 回以上裁いた。罰を 1 回以上払わせた",
            lambda i: i["g5_stage"] >= 2 and i["households"] >= 6 and bool(i["leader"]) and i["penalty_laws"] >= 3
            and i["judged"] >= 2 and i["penalties"] >= 1),
+    # G6 (第 4 部「町と文字」): 町と記録は別々の条件で、どちらが先でもよい。それぞれ届いた日は区切り F3・F4。両方に一度でも届くと Society 2.0 の終わり
+    "G6": ("町 (村が 50 人以上で、この 4 季節は毎季節ほかの村と交換し、相手の村が 2 つ以上、村がいちばん大きい相手の村の 2 倍以上、食べ物をとらない人が大人の 1 割以上) と、"
+           "記録 (物のしるしと数のしるしを分けて記した粘土の板で、量を確かめた) の両方に、一度でも届く (どちらが先でもよい)",
+           lambda i: bool(i["g6_town_day"]) and bool(i["g6_record_day"])),
 }
 ORDER2 = ["G1", "G2", "G3", "G4", "G5", "G6"]
 NAMES2 = {"G1": "村ができる", "G2": "畑と家畜", "G3": "余りと分業", "G4": "持ち物と差", "G5": "リーダーと決まり", "G6": "交易・町・記録"}
@@ -1503,6 +1596,10 @@
     "G5": [("F1", "集まり・長老・祭りでまとまる", lambda s: bool((s["era2"].get("g5") or {}).get("stage1"))),
            ("F2", "まとめ役が選ばれる", lambda s: bool((s["era2"].get("g5") or {}).get("leaders"))),
            ("F3", "罰を払わせる", lambda s: (s["era2"].get("g5") or {}).get("penalties", 0) >= 1)],
+    "G6": [("F1", "村どうしの交換", lambda s: (s["era2"].get("g6") or {}).get("exchanges", 0) >= 1),
+           ("F2", "印で封をする", lambda s: (s["era2"].get("g6") or {}).get("seal_seasons", 0) >= 1),
+           ("F3", "町", lambda s: _town(s)["ok"]),
+           ("F4", "物と数を分けて記す", lambda s: _record_ok(s))],
 }
 # G1・G2 の F は、この仕組みを作る前に終わっていたので、記録 (出来事) から日を決めた (2026-10-08。G1_notes.md・G2_notes.md)
 RETRO_SUBSTEPS = [
@@ -1535,6 +1632,13 @@
     met = fn(ind)
     since = state["day"] - state["era_log"][-1]["day"]
     state["era_info"] = {"era": era, "name": NAMES2[era], "next": desc, "met": met, "since": since, "indicators": ind}
+    if met and era == ORDER2[-1]:  # G6: 町と記録がそろった → Society 2.0 の終わり (一度だけ。フェーズは進まない)
+        g6 = state["era2"].get("g6") or {}
+        if g6 and not g6.get("end"):
+            t, r = ind["g6_town_day"], ind["g6_record_day"]
+            g6["end"] = {"day": state["day"], "town": t, "record": r, "first": "町" if t < r else "記録" if r < t else "同じ日"}
+            return "end"
+        return False
     if met and era != ORDER2[-1]:
         nxt = ORDER2[ORDER2.index(era) + 1]
         state["era"] = nxt
@@ -1715,31 +1819,48 @@
         rows.append(f"前に祭りをしたのは {g['feast_day']} 日目 (これまで {g['feasts']} 回)")
     op = [d for d in g.get("disputes", []) if d["status"] == OPEN]
     rows.append("まだ収まっていないもめごと:" + ("" if op else " なし"))
+    j = 0  # 話し合える数に数えるもめごと (G6: 記録のあるものは数えない。G6 の前は i と同じ)
     for i, d in enumerate(op):
         age = (state["day"] - d["day"]) // SEASON_DAYS
         when = ("前の季節の終わりに起きた" if age == 0 else f"{age} 季節 収まっていない。この季節の集まりでも収まらないと、季節の終わりに、"
                 + (f"{d['from']}が村を出ていくことがある" if age + 1 < DROP_AGE else "だれも言わなくなる"))
-        talk = "" if lead else "。この季節の集まりで話し合う" if i < TALK_MAX else f"。この季節の集まりでは話し合えない (古いものから {TALK_MAX} つまで)"
+        rec = d.get("record")
+        talk = "" if lead and not rec else "。この季節の集まりで、記録を見て確かめる" if rec else "。この季節の集まりで話し合う" if j < TALK_MAX else f"。この季節の集まりでは話し合えない (古いものから {TALK_MAX} つまで)"
+        j += 0 if rec else 1
+        amt = (f"草の種にして {d['harm']} つかみ 分。{rec}の記録がある" if rec else f"言い出した家の覚えでは、草の種にして 約 {d['harm']} つかみ 分。記録はない"
+               if "harm_true" in d else f"草の種にして 約 {d['harm']} つかみ 分")
         rows.append(f"- [{d['id']}] ({d['kind']}) {d['from']}が言い出した。相手は{d['against']} ({when}{talk}): {d['what']}"
-                    f" (草の種にして 約 {d['harm']} つかみ 分) [出来事 {d['event']}]")
+                    f" ({amt}) [出来事 {d['event']}]")
     ev = [e for e in state["events"] if e["id"] >= since and e["type"] in G5_EVENTS]
     if ev:
         rows += ["この前の集まりから起きたこと:"] + [f"- [出来事 {e['id']}] {e['text']}" for e in ev[-12:]]
-    if g.get("last_flow"):
+    if g.get("last_flow") and not era_at_least(state, "G6"):  # G6 では「ほかの村・印・記録」に (記録がなければ覚えの幅で)
         rows.append("前の季節の、家ごとの村の蓄えへの出し入れ (大人の分。草の種にして): "
                     + "、".join(f"{h} 入れた 約 {i}・取った 約 {o} つかみ" for h, (i, o) in g["last_flow"].items() if h in homes))
     return "\n## 村の集まり (もめごと・祭り" + ("・まとめ役" if two else "") + ")\n" + "\n".join(rows) + "\n"
 
 
+# ... (G6 のお題のコード: 5.4 のコード) ...
+
+
 def season_prompt(state, p, first):
     e2 = state["era2"]
     g5, g = era_at_least(state, "G5"), e2.get("g5") or {}  # G5 の部分は、G5 の前はみな空の文字 (お題は前と同じ)
     lead, two = g.get("leader"), g.get("stage", 1) >= 2
     solo = bool(g5 and e2.get("rep_mode") and p["name"] not in _reps(state))  # 家族の代表でないまとめ役 (自分の分だけ答える)
+    g6 = era_at_least(state, "G6")  # G6 の部分は、G6 の前はみな空の文字
     places = "\n".join(f"- {pl['id']}: {pl['label']}" for pl in state["places"])
     names = [q["name"] for q in adults(state) if q is not p]
     vis = ""
-    if e2["visitors"]:
+    if e2["visitors"] and g6:  # G6: 群れが 2 つ以上のこともある (ほかの村から来た人)
+        rows = []
+        for v in e2["visitors"]:
+            o = _other(state, v.get("from")) if v.get("from") else None
+            rows.append("- " + "、".join(f"{m['name']} ({m['sex']}、{m['age']} 歳)" for m in v["members"]) + (f" ({o['name']} から来た)" if o else " (よその群れ)"))
+        vis = ("\n## よそから来た人\n" + "\n".join(rows) + "\nそれぞれ「ここで暮らしたい」と言っている (1 行が、いっしょに来た一つの群れ)。群れごとに、村に受け入れるか決めてください "
+               "(accept: 群れの最初の人の名前ごとに、受け入れるなら true、受け入れないなら false)。大人の半分をこえる賛成で、その群れの全員が村に加わる。"
+               "加わった大人は、この季節は村でいちばん多い仕事をし、次の季節から自分で決める\n")
+    elif e2["visitors"]:
         v = e2["visitors"][0]
         txt = "、".join(f"{m['name']} ({m['sex']}、{m['age']} 歳)" for m in v["members"])
         vis = (f"\n## よそから来た人\n{txt} が「ここで暮らしたい」と言っている (いっしょに来た一つの群れ)。村に受け入れるか決めてください "
@@ -1751,6 +1872,8 @@
     keep = '"keep": false, ' if era_at_least(state, "G4") and not solo else ""
     goat = '"eat_goat": 0, ' if e2["goats"] and not solo else ""
     acc = f'"accept": {{"{e2["visitors"][0]["name"]}": true}}, ' if e2["visitors"] else ""
+    if g6 and e2["visitors"]:
+        acc = '"accept": {' + ", ".join(f'"{v["name"]}": true' for v in e2["visitors"]) + "}, "
     pick = characters._pick_line(st)
     me = characters._me(st, p).replace("(誰でも入れたり取ったりできる)", "(日々の出し入れは自動)")
     fam_txt, fam_json = "", ""
@@ -1764,7 +1887,7 @@
                    f"あなたは {p.get('household')} の代表。\n" + ("\n".join(rows) if rows else "- (ほかの家族はいない)") +
                    "\n- 家族の大人の主な仕事も、あなたが決める (family。書かなかった人は、あなたと同じ仕事)"
                    "\n- sow・pick・plant・harvest の数は、家族の大人一人ひとりの量 (eat_goat は家族で何頭か)"
-                   f"\n- 掟の投票と、よそから来た人の受け入れ{('、もめごとの収め方・祭り' + ('・まとめ役' if two else '') + 'の答え') if g5 else ''}は、家族の大人みんなの答えとして数える\n")
+                   f"\n- 掟の投票と、よそから来た人の受け入れ{('、もめごとの収め方・祭り' + ('・まとめ役' if two else '') + ('・申し出 (trade)・村の蓄えの封' if g6 else '') + 'の答え') if g5 else ''}は、家族の大人みんなの答えとして数える\n")
         if fam:
             fam_json = '"family": {' + ", ".join(f'"{q["name"]}": {{"activity": "採集", "place": "camp"}}' for q in [q for q in fam if q["name"] != lead][:2]) + '}, '
 
@@ -1784,10 +1907,12 @@
     g5_json = ("\n " + ('"judge": {' + ", ".join(f'"{i}": "..."' for i in op) + "}, " if op else "") + '"feast": false, '
                + ('"leader": "...", ' if two else "") + ('"call": null, ' if me5 else "")) if g5 else ""
     pen = ', "penalty": null' if g5 and two else ""
+    g6_now, g6_json = _g6_now(state, p, solo), _g6_json(state, p, solo)  # G6 の前は空
+    g6_act = "   交換に行く・記録をつけるは camp と書く (行き先・持って行く物・残すものは 8. に書く)\n" if g6 else ""
 
     return f"""{RULES2}
 
-{me}{FACTS2}{(FACTS_G3 + FACTS_HOUSE) if era_at_least(state, "G3") else ""}{FACTS_G4 if era_at_least(state, "G4") else ""}{_g5_facts(state)}
+{me}{FACTS2}{(FACTS_G3 + FACTS_HOUSE) if era_at_least(state, "G3") else ""}{FACTS_G4 if era_at_least(state, "G4") else ""}{_g5_facts(state)}{_g6_facts(state)}
 ## 村のようす
 {_village(state)}
 ## 前の季節のこと
@@ -1801,28 +1926,28 @@
 
 ## 集団の掟 (季節のはじめに、みんなで集まって決める)
 {characters._laws(state, with_pending=True)}
-{_g5_text(state)}{vis}
+{_g5_text(state)}{_g6_text(state)}{vis}
 ## いま
 {state["day"] + 1} 日目、{sea}。これから {SEASON_DAYS - (state["day"] + 1) % SEASON_DAYS} 日 (この季節の終わりまで) の仕事を決める集まり (途中で村の蓄えが尽きて、ひどく空腹の人が出たら、そこで集まり直す)。
 1. 話したいことがあれば話す (0〜2 つ。相手は仲間の名前か「みんな」)。前と同じ言い回しをくり返さず、あなたらしい言葉で
 2. この季節の主な仕事を決める (job)。仕事は {' / '.join(acts2(state))} から 1 つ、場所は下の一覧の id から 1 つ、一緒に行きたい人 ({'、'.join(names) or 'なし'}) がいれば書く
    畑仕事 (草取り・刈り入れ) は camp で行う
    ヤギの世話は camp で行う。ヤギを捕まえるは、野生のヤギのいる場所で行う
-3. {(pick.strip().rstrip('。') + '。取るのはこの季節の毎夕で、1 人 40 つかみまで') if pick.strip() else 'この季節 (' + sea + ') は、キャンプのそばの木から実は取れない (実がなるのは夏と秋)'}
+{g6_act}3. {(pick.strip().rstrip('。') + '。取るのはこの季節の毎夕で、1 人 40 つかみまで') if pick.strip() else 'この季節 (' + sea + ') は、キャンプのそばの木から実は取れない (実がなるのは夏と秋)'}
 4. 持っている木の実 (なければ村の蓄えの木の実) を、この回の最初の日にキャンプのそばに埋める (plant、つかみ、5 まで) こともできる
    秋なら、季節のはじめに、蓄えの草の種をキャンプのそばの畑にまく量 (sow、つかみ、1000 まで) を書ける (主な仕事とは別にできる)
    実った畑があれば、毎夕いくつ刈るか (harvest、つかみ、60 まで) を書ける (主な仕事とは別にできる)
 {'   飼っているヤギを、この回の最初の日に何頭つぶして肉にするか (eat_goat、頭。肉は干して蓄えに入れる。2 頭は残す) を書ける' + chr(10) if e2['goats'] and not solo else ''}
 {'   家の倉を持つか (keep: 持つなら true、持たないなら false) を決める (家の代表が決める)' + chr(10) if era_at_least(state, "G4") and not solo else ''}5. 覚えていることを更新する (新しく分かったことを追加、確かさを変える、間違っていたら忘れる)
 6. 掟: みんなで守りたい決まりがあれば提案できる (なければ null)。今の掟と提案に、賛成か反対かを投票する (against に反対する理由、reason に決めた理由)
-{g5_now}{8 if g5_now else 7}. 今の気持ちを一言
+{g5_now}{g6_now}{7 + bool(g5_now) + bool(g6_now)}. 今の気持ちを一言
 
 場所の一覧:
 {places}
 
 ## 答えの形 (JSON)
 {{"say": [{{"to": "みんな", "text": "..."}}],
- "job": {{"activity": "採集", "place": "camp", "with": []}}, {sow}"pick": 0, "plant": 0, "harvest": 0, {goat}{acc}{fam_json}{keep}{g5_json}
+ "job": {{"activity": "採集", "place": "camp", "with": []}}, {sow}"pick": 0, "plant": 0, "harvest": 0, {goat}{acc}{fam_json}{keep}{g5_json}{g6_json}
  "knowledge": [{{"op": "add", "text": "...", "because": [出来事の番号], "confidence": 0.6}}],
  "proposal": {{"text": "...", "because": [出来事の番号]{pen}}},
  "votes": [{{"id": "L0", "against": "反対する理由", "agree": true, "reason": "決めた理由"}}],
```

What each hook does:
- `acts2`: 交換に行く from G6; 記録をつける only after 数え札 opens (read with `.get`, never creates state).
- `apply_answers`: `_g6_new_season` at the start (resets jobs, keep days, trips; records the meeting); `_g6_job` after a plan is set (details go to `g6.jobs`, never `e2["jobs"]`); `_g6_collect` after `_g5_collect` (respects `own`); `_g6_meeting` after `_g5_meeting`, before `_settle_visitors`.
- `_settle_visitors`: a G6 group (with `seed`) creates its members from its own `random.Random(seed)`; members get `from_village`; the 加わる text keeps 「よそから来た A・B が、」 so `_sync_households` still parses it; refusal says 「…へ帰っていった」; `_g6_settled` updates the partner. The "most common job" a newcomer copies for its first season ignores 交換に行く and 記録をつける (a newcomer has no destination or record details and would otherwise sit idle for 30 days; before G6 nobody can plan these, so the choice is unchanged).
- `_day`: 記録をつける in the work chain; `_g6_trips_day` after the chain (before the evening takes, `_feed` and `world.evening`, so a raised `spent` is eaten); travellers (`today.away`) neither pick nor harvest.
- `_feed` / `_flow`: sealing pieces when a sealed household opens its 倉 or takes from the sealed village store (1 per household per day).
- `_craft`, `_storage_season`: obsidian blades; the sickle loop still draws once per item, so the salt-31 stream is unchanged.
- `_house_site(state, h)`: identical sequence before G6 (the ring check moved into `ok()`); in G6 rings 11/13/15, and households from a partner village try the ±60° sector toward it first.
- `_steal`, `_incident`: sealed stores are robbed last; a broken seal logs 封 and the incident is `sealed` (always becomes a dispute, `_g5_season_end`); in G6 the theft text has no amount.
- `_dispute`, `_g5_season_end`: record or claim on new disputes; G6 texts without exact amounts when there is no record; merging keeps the claim ratio; ration credit only in the 蓄え comparison (`last_flow` is still the raw flow); when the credit changed what a household 「入れた」, the dispute text says so (「入れた量は、記録した働いた日の分をふくむ」), so the logged amount is not presented as grain actually put in.
- `_g5_meeting`: a recorded dispute is checked (確かめる) and does not use a talk slot.
- `_verdict`: after a つぐなう payment without a law, `_g6_after_pay` (覚え incident).
- `_season_end`: `_g6_records` before `_g5_season_end` (so new disputes know the record), `_g6_season_end` after it (so a fission in this season already becomes a dormant village), `_note_mode` last.
- `indicators`, `CRITERIA`, `SUBSTEPS`, `check`: §16. `_g5_text`, `season_prompt`: §15.

### 5.3 `world.py`

```diff
--- a/sim/society/world.py
+++ b/sim/society/world.py
@@ -289,7 +289,7 @@
 
 
 # Society 2.0 で足した仕事 (era2.py が働きを計算する。2026-10-07)
-ACTS2_EXTRA = ("畑仕事", "ヤギの世話", "ヤギを捕まえる", "土器づくり")
+ACTS2_EXTRA = ("畑仕事", "ヤギの世話", "ヤギを捕まえる", "土器づくり", "交換に行く", "記録をつける")
 ACT_EVENT = {"採集": "採集", "狩り": "狩り", "探索": "探索", "休む": "休む", "道具づくり": "道具", "火おこし": "火",
              "種まき": "種まき", "住まいを建てる": "住まい", "キャンプを移す": "移る"}
 
@@ -369,7 +369,7 @@
         if act not in ACTIVITIES and act not in ACTS2_EXTRA:
             act = "休む"
         pl = place_of(state, plan.get("place", "camp"))
-        if act == "住まいを建てる":  # 建てるのはキャンプ。材料は近くの林から運ぶ
+        if act in ("住まいを建てる", "交換に行く", "記録をつける"):  # 建てるのはキャンプ。材料は近くの林から運ぶ (G6: 交換に行く・記録をつけるも、出かける・数えるのはキャンプから)
             pl = place_of(state, "camp")
         if p["injured"] > 0:
             act, pl = "休む", place_of(state, "camp")
@@ -500,7 +500,7 @@
             res["events"].append(log(state, "ヤギの世話", p["name"], f"{p['name']} がヤギの世話をした"))
         elif act == "ヤギを捕まえる":
             res["events"].append(log(state, "ヤギを捕まえる", p["name"], f"{p['name']} が {pl['label']} でヤギを捕まえようとした"))
-        elif act == "土器づくり":  # できた数は era2.py が記録する
+        elif act in ("土器づくり", "交換に行く", "記録をつける"):  # era2.py が記録する
             pass
         else:
             res["events"].append(log(state, "休む", p["name"], f"{p['name']} はキャンプで休んだ"))
```

Before G6 these acts are never planned (`apply_answers` filters by `acts2`), so nothing changes. At camp the predator check never draws, so the per-person random sequence is the same as for 土器づくり.

### 5.4 Prompt code (place before `def season_prompt`)

```python
FACTS_G6 = ("ほかの村: 村の外 (地図の外。歩いて 1〜2 日) にも、人の暮らす村がある。知っている村は「ほかの村・印・記録」に出る。"
            "ほかの村の人は、季節の終わりに村に来て、申し出をすることがある (交換したい / 食べ物を貸してほしい / 前に借りた分を返す)。"
            "交換したい・貸してほしいの申し出は、次の季節の集まりで決める (trade: 申し出の番号ごとに、村の物で受けるなら \"村\"、"
            "自分の家の倉の食べ物と家のヤギで受けるなら \"家\"、受けないなら false)。"
            "大人の半分をこえる人が \"村\" と答えるか、まとめ役が \"村\" と答えると、村の蓄え・村の土器・村の鎌・村のヤギで受け、手に入れた物は村のものになる。"
            "そうでなければ、\"家\" と答えた家の代表のうち、払える家で、家の倉の食べ物がいちばん多い家が受け、手に入れた食べ物とヤギはその家のものになる "
            "(土器・鎌・黒曜石は、いつも村のもの)。返す申し出は、決めずに受けとる。"
            "交換している村から「ここで暮らしたい」と人が来ることもある (よそから来た人と同じく、受け入れるかを決める)\n"
            "交換に行く: 主な仕事を「交換に行く」(camp) にすると、季節のはじめの日に、知っているほかの村へ、ほかの村がほしがる物 (村の草の種・土器・鎌) を持って出かける "
            "(to: 村の番号、carry: 持って行く物と数、want: ほしい物、then: 帰ってからの仕事)。"
            f"1 人が持てるのは、草の種なら {LOAD['草の種']} つかみ、土器なら {LOAD['土器']} 個、鎌なら {LOAD['鎌']} 本ほど "
            "(2 つ持つときは、それぞれ半分ずつ)。"
            "歩いて 1 日の村なら、行く・交換する・帰るで 3 日、2 日の村なら 5 日かかる。歩く日はおなかが多くすく。帰り道で物をなくしたり、けがをしたりすることがある。"
            "向こうの村は、その季節にほしい分だけを受けとり、want の物 (なければほかの物) で払う。受けとらなかった物は持ち帰る。払いきれない分は、あとで返す約束 (貸し借り) になる。"
            "家の代表は、家の倉の草の種を持って行かせることもできる (house: true。家族の住まいのある家だけ。手に入れた食べ物とヤギは家のもの)\n"
            f"値うち: 交換では、草の種にして、ヤギ 1 頭 = {VALUE['ヤギ']} つかみ、鎌 1 本 = {VALUE['鎌']} つかみ、土器 1 個 = {VALUE['土器']} つかみ、"
            f"黒曜石 1 個 = {VALUE['黒曜石']} つかみ、干し肉 1 切れ = {VALUE['干し肉']} つかみ ほどとして釣り合わせる\n"
            "覚え: 記録のない量 (家ごとの村の蓄えへの出し入れ・もめごとの量・貸し借りの量) は、人の覚えにたよるので、はっきりしない。"
            "村の家が多いほど、ほかの村との貸し借りが多いほど、覚えはずれる。もめごとを言い出した家は、損を多めに覚えていることがある。"
            "覚えた量で払うと、払った家が「多く払った」と言い出すことがある (もめごとのもと (5) 覚え)\n"
            "印: 家の代表は、家の印 (焼いた粘土に形を刻んだもの) を作れる (seal)。印のある家の倉は、口を粘土でふさいで印を押しておく (封)。封は割らずには開けられない。"
            "よその家の人が開けると、封が割れているので分かり、必ずもめごとになる。"
            "大人の半分をこえる人か、まとめ役が望むと (seal_store)、この季節は村の蓄えの土器にも封をする。そのときは、取るたびに封を割り、取った人の家の印で封をし直す。"
            "割った封のかけらは取っておくので、どの家が何日開けたかが分かる (量は分からない)\n")

FACTS_TOKEN = ("数え札: 粘土を小さく丸めたり形をつけたりした札で、量を数えて残せる (草の種 100 つかみ分に 1 個、ヤギ 1 頭に 1 個、土器・鎌・黒曜石 10 個に 1 個、"
               "働いた日 10 日に 1 個)。主な仕事を「記録をつける」(camp) にすると、この季節の出し入れを残す (what: 残すもの。"
               "「蓄え」= 家ごとの村の蓄えへの出し入れと、作る人などの働いた日、「交換」= ほかの村との交換と貸し借り、「刈る」= よその家の畑で刈った量。"
               "書いた順に残す。how: \"数え札\")。"
               f"1 人が 1 日に作って数えられる数え札は {RATE['数え札']} 個ほどで、足りないと途中までしか残らない。"
               "全部残せた量ははっきり分かる。その量のもめごとは、季節の集まりで記録を見て確かめる (話し合える 2 つには数えない)。"
               "記録のある貸し借りは、返しに来たときに、正しい数が分かる (足りない分は、あとで返す約束のまま残る)。"
               "村の蓄えの出し入れを全部残せた季節は、作る人・記録をつける人・交換に行った人の働いた日を、1 日を大人 1 人の 1 日分として、その家が村の蓄えに入れた量に数える\n")

FACTS_ENVELOPE = ("封筒: 記録をつける人が how を \"封筒\" にして「交換」を残すと、その季節の貸し借りの数え札を粘土の玉に入れて閉じ、外に印を押しておく。"
                  "返しに来たときに玉を割ると、約束した数がどちらにも分かり、その数が返される\n")

FACTS_TABLET = (f"粘土の板: 数え札を 1 つずつ作るかわりに、平たい粘土の板に、物を表すしるし (草の種・ヤギ・土器 など) と、数を表すしるしを分けて押して記せる (how: \"板\")。"
                f"1 人が 1 日に、数え札 {RATE['板']} 個分ほどを記せる。板に記した量も、数え札と同じように確かめるのに使える。"
                "板で記した貸し借りは、封筒と同じく、どちらにも数が分かる\n")

FACTS_OBSIDIAN = ("黒曜石: 黒く光る石で、割ると鋭い刃になる。村に黒曜石があると、道具づくりで作る鎌に黒曜石の刃をはめる (鎌 1 本に 1 個)。"
                  "黒曜石の刃の鎌は、割れにくい (半分ほど)\n")


def _g6_facts(state):
    if not era_at_least(state, "G6"):
        return ""
    g = state["era2"].get("g6") or {}
    op = g.get("open") or {}
    obs = USE_OBSIDIAN and (g.get("obsidian") or any(o.get("has_obsidian") and o["known"] is not None for o in g.get("others", [])))
    return (FACTS_G6 + (FACTS_TOKEN if op.get("数え札") else "") + (FACTS_ENVELOPE if op.get("封筒") else "")
            + (FACTS_TABLET if op.get("板") else "") + (FACTS_OBSIDIAN if obs else ""))


def _g6_rw(x):
    return "ほとんどなし" if x[1] == 0 else f"約 {x[0]}〜{x[1]} つかみ"


def _g6_text(state):
    """G6 のお題の節 (見ればわかる事実だけ。状態は変えない)"""
    if not era_at_least(state, "G6"):
        return ""
    g = state["era2"].get("g6") or {}
    homes = _homes(state)
    rows = []
    known = [o for o in g.get("others", []) if o["known"] is not None]
    rows.append("知っているほかの村:" + ("" if known else " まだない"))
    for o in known:
        who = f"前に村を出た{o['household']}の人たちが暮らす" if o["kind"] == "分かれた家" else "よその村"
        has = "・".join(k for k, n in _g6_supply(o).items() if n > 0) or "目立つ物はない"
        last = max(o["contacts"]) if o["contacts"] else None
        rows.append(f"- [{o['id']}] {_okey(o)}: {who}。人 約 {max(5, 5 * round(o['people'] / 5))} 人。出せる物: {has}。ほしがる物: {'・'.join(_g6_cap(o))}。"
                    f"はじめて知った日 {o['known']} 日目。交換した季節 {len(o['contacts'])} 回" + (f" (最後は {last} 日目)" if last else "")
                    + ("。この年は畑が実らず苦しいと言っていた" if o["bad"] is not None else ""))
    offers = g.get("offers", [])
    if offers:
        rows.append("この季節の集まりで決める申し出 (trade。返す申し出は、決めずに受けとる):")
        for off in offers:
            o = _other(state, off["other"])
            rows.append(f"- [{off['id']}] {o['name']}: " + {"交換": f"{_gw(off['give'])} を出すので、{_gw(off['want'])} がほしい",
                                                          "貸して": f"{_gw(off['want'])} を貸してほしい (1 年のうちに同じ量を返す)",
                                                          "返す": f"[{off.get('debt')}] の分として {_gw(off['give'])} を返しに来た"}[off["kind"]])
    debts = [d for d in g.get("debts", []) if d["status"] == "まだ"]
    if debts:
        rows.append("まだ返されていない貸し借り:")
        for d in debts:
            o = _other(state, d["other"])
            amt = (f"{_gw(d['goods'])} ({d['proof']}の記録がある)" if d.get("proof")
                   else "覚えでは " + _gw({k: math.ceil(n * d["mem"]["village"]) for k, n in d["goods"].items()}) + " ほど (記録はない)")
            rows.append(f"- [{d['id']}] {o['name'] if o else 'ほかの村'} が{'村' if d['lender'] == '村' else d['lender']}に返す分: {amt}。{d['day']} 日目から")
    seals = g.get("seals", {})
    rows.append("家の印: " + ("、".join(f"{h} ({v['day']} 日目から)" for h, v in sorted(seals.items()) if h in homes) or "まだない")
                + ("。印のない家: " + ("、".join(h for h in homes if h not in seals) or "なし") if seals else ""))
    if g.get("store_sealed") is not None and g.get("store_sealed") == state["era2"].get("step_day"):
        rows.append("前の季節は、村の蓄えに封をした")
    rec = g.get("records", [])
    last = rec[-1] if rec and rec[-1]["day"] == state["day"] else None
    if last:
        rows.append("前の季節の記録 (" + "、".join(f"{n} {d} 日・{h}" for n, (d, h) in last["keepers"].items()) + "): "
                    + ("、".join(f"{WHAT_WORDS[w]} は{'全部残せた' if w in last['complete'] else '途中までしか残せなかった'}"
                                for w in WHATS if last["need"][w] and last["done"][w]) or "残せたものはなかった"))
    else:
        rows.append("前の季節の記録: なし")
    op = g.get("open") or {}
    rows.append("使える記録の道具: " + ("・".join(k for k in ("印", "数え札", "封筒", "板") if op.get(k)) or "印"))  # G6 の最初のお題 (g6 を作る前) も「印」
    if g.get("obsidian") or g.get("obs_sickles"):
        rows.append(f"村の黒曜石: {g['obsidian']} 個 (黒曜石の刃の鎌 {g['obs_sickles']} 本)")
    sh = g.get("shown")
    if sh and sh["rows"]:
        if sh["how"]:
            rows.append(f"前の季節の、家ごとの村の蓄えへの出し入れ ({sh['how']}の記録による。大人の分。草の種にして): "
                        + "、".join(f"{h} 入れた {i}・取った {o_} つかみ" for h, (i, o_) in sh["rows"].items() if h in homes))
        else:
            rows.append("前の季節の、家ごとの村の蓄えへの出し入れ (記録はない。みんなの覚えでは、だいたい。大人の分。草の種にして): "
                        + "、".join(f"{h} 入れた {_g6_rw(i)}・取った {_g6_rw(o_)}" for h, (i, o_) in sh["rows"].items() if h in homes))
    ev = [e for e in state["events"] if e["id"] >= (g.get("meet_first") or state["next_event"]) and e["type"] in G6_EVENTS]
    if ev:
        rows += ["この前の集まりから起きたこと (ほかの村・印・記録):"] + [f"- [出来事 {e['id']}] {e['text']}" for e in ev[-12:]]
    return "\n## ほかの村・印・記録\n" + "\n".join(rows) + "\n"


def _g6_now(state, p, solo):
    if not era_at_least(state, "G6"):
        return ""
    g = state["era2"].get("g6") or {}
    offers = [o for o in g.get("offers", []) if o["kind"] != "返す"]
    rows = ["8. ほかの村・印・記録 (上の「ほかの村・印・記録」を見て決める。どれも書かなくてもよい)"]
    if offers:
        rows.append("   申し出: 申し出の番号ごとに、村の物で受けるなら \"村\"" + ("" if solo else "、自分の家の物で受けるなら \"家\"") + "、受けないなら false (trade)")
    if not solo and p.get("household") and p["household"] not in g.get("seals", {}):
        rows.append("   印: 家の印を作るなら true (seal。家ごとに 1 回だけ)")
    rows.append("   村の蓄えの封: この季節、村の蓄えに封をするなら true、しないなら false (seal_store)")
    if any(o["known"] is not None for o in g.get("others", [])):
        rows.append('   交換に行く: 主な仕事を「交換に行く」にする人は、job か family に、to (村の番号)・carry (持って行く物と数)・want (ほしい物)・then (帰ってからの仕事) を書く。'
                    '例 {"activity": "交換に行く", "place": "camp", "to": "N1", "carry": {"土器": 4}, "want": "ヤギ", "then": "採集"}')
    op = g.get("open") or {}
    if op.get("数え札"):
        hows = " / ".join(h for h in ("数え札", "封筒", "板") if op.get(h))
        rows.append(f'   記録をつける: 主な仕事を「記録をつける」にする人は、what (残すもの: 蓄え・交換・刈る。書いた順に残す) と how ({hows}) を書く。'
                    '例 {"activity": "記録をつける", "place": "camp", "what": ["蓄え", "交換", "刈る"], "how": "数え札"}')
    return "\n".join(rows) + "\n"


def _g6_json(state, p, solo):
    if not era_at_least(state, "G6"):
        return ""
    g = state["era2"].get("g6") or {}
    offers = [o["id"] for o in g.get("offers", []) if o["kind"] != "返す"]
    return (('"trade": {' + ", ".join(f'"{i}": "..."' for i in offers) + "}, " if offers else "")
            + ('"seal": false, ' if not solo and p.get("household") and p["household"] not in g.get("seals", {}) else "")
            + '"seal_store": false, ')
```

---

## 6. Other villages

- **Dormant daughters.** At every G6 season end, each `g5.fissions` entry without a node becomes one: `kind` 分かれた家, name 「フウの村」 (household name without の家), 1 day away, people = those who left, goats and grain = what they took, `known` None. It appears in prompts only after its first contact: 「前に村を出たフウの家の人たちが、村に来た。いまは フウの村 (東へ歩いて 1 日) で暮らしているという」. Texts never name individual leavers as alive (they are `alive=False, left=day` and stay so).
- **Visitor origins.** If the base visitor roll (salt 7, unchanged) created a group at this season end, G6 tags it with a stranger village: an existing one with p 0.5 (always when 3 exist), else a new one. Logged 「よその群れの A・B は、東の村 (東へ歩いて 1 日) から来たと言った」. Groups that came before G6 keep 「よその群れから」.
- **Traders.** If fewer than 3 stranger villages exist: always at the first G6 season end (if none exists), afterwards with p 0.10 per season. 10–25 people, goats 0.4/person, grain 100/person, pots people/4, sickles people/8. The 2nd stranger village is 2 days away and has obsidian (20, +8 per season up to 40).
- **Directions** are drawn among unused 南 (39,79, river exit), 北 (49,0, river exit), 東 (79,40), 西 (0,40). Labels say only direction and days (「川にそって南へ歩いて 2 日」); the world has no river flow direction, so never 上流/川下.
- **Season dynamics** (salt-41 stream): +1 person with p = people × 0.005; at the start of summer a bad year with p 0.2 (grain falls to 20/person; otherwise +100/person up to 300/person); goats ×1.3 in spring up to the number of people; pots −3%, sickles −5% per season.
- **Contact**: each known or dormant node comes with p = min(0.8, CONTACT_P × trust / 0.5) (分かれた家 0.35, よその村 0.15), or 0.8 when a debt it owes is due; not if villagers visited it this season. trust +0.1 per completed transfer or accepted group, −0.1 per refused offer or group, −0.2 per 覚え on repayment or an unpaid debt after a year.
- **Offers** (in this order): bad year and grain < 60/person → 貸して (草の種 = people × 120, rounded to 100, ≤ 3000); a due debt it can at least half repay → 返す (brings the exact amount if the debt has an envelope or tablet proof, otherwise its own memory = true × U(1−s, 1)); otherwise 交換: up to 3 goats (keeping 2), or obsidian (5–15), for its wants of equal value in the order 土器, 鎌, 草の種. A village whose wants are worth less than one goat but at least half a goat still offers 1 goat for all of them (otherwise villages under 12 people could never offer — checked 2026-10-09: 5–11 people had wants worth 245–305 < 375). Goat sexes/ages and memory factors are drawn at the season end and stored in the offer, so the meeting is deterministic.
- **Per-season caps** (what a partner takes in one season): 土器 max(3, people/3), 鎌 max(1, people/6), 草の種 10/person (100 in a bad year).

## 7. Exchange at the meeting, loans and repayment

- Answer `"trade": {"T3": "村" | "家" | false}`; rep-weighted (`fam`), a non-rep leader counts only for themself and cannot answer "家".
- "村" by more than half of adults, **or by the leader alone**, → village goods. Otherwise the households whose reps answered "家" and can pay; the one with the most food in its 倉 takes it. Otherwise refused (trust −0.1, logged 「…の申し出 [T3] は受けなかった (村 a・家 b・受けない c / 大人 n)」).
- 交換: our goods to the partner, its goods to us (goats with the pre-drawn sexes/ages; owner None or the household). 貸して: a debt `D#` (lender 村 or household, due one year later).
- **Limit of "家" at the meeting** (checked 2026-10-09): every 交換 offer asks for 土器 and 鎌 first, and pots and sickles are always village things, so no household can pay a 交換 offer; "家" works at the meeting only for 貸して (grain). Household trade happens through trips (`house: true`, the household's grain → goats/obsidian for the household). Question 10 is worded accordingly; if the user wants households to take 交換 offers, the offer would have to ask a household for grain only (a design change, not made here).
- 返す (not voted): the goods go to the lender (to the village if the household has left). Proof 封筒 or 板 → exact, 確かめる, `checked[proof] += 1`; proof 数え札 → the village knows the exact number, the partner brings its memory, the shortfall stays as an open debt, 確かめる; no proof → the debt closes, `unchecked += 1`, and if the village's memory (true × U(1, 1+s)) exceeds what was brought by more than 25%: 覚え event, trust −0.2.
- Every completed transfer appends the season's `step_day` to the partner's `contacts`, `exchanges += 1`.

## 8. Trips (job 交換に行く)

- Job: `{"activity": "交換に行く", "place": "camp", "to": "N1", "carry": {"土器": 4}, "want": "ヤギ", "then": "採集", "house": false}` (job or family). `then` must be in `acts2` (default 休む). `house: true` only for the household's own rep answer and only for a household with a built home.
- **Departure** on the season's first day: only goods a partner takes (`_g6_cap`: 草の種, 土器, 鎌) can be carried; the load is scaled so that Σ n / LOAD ≤ 1. (An earlier draft also let travellers carry goats, meat and obsidian; partners never take them, so they always came back, and returned goats were re-created as 2-year-old females, changing the herd — removed 2026-10-09.) Goods leave the village stocks (or the household's 倉: grain only). If the target is unknown, the person is injured that day, or nothing could be taken: 「…は、…、交換に行かなかった」 and the plan switches to `then`.
- **Schedule** (D = days): walk on days 0…D−1, trade on day D, walk back D+1…2D, the plan becomes `then` after day 2D. 3 days for D = 1, 5 for D = 2. On walking days `today.spent += world._walk_kcal(p, 30000) × 1.4` (the load). `today.away` on all trip days.
- **Barter**: the partner takes only what is under its caps; pays in `want`, else ヤギ / 黒曜石 / 草の種 (keeping 2 goats; no grain in a bad year); unwanted goods come back; a remaining value ≥ 50 becomes a debt in the wanted good (if worth ≥ half a unit) or in 草の種, due two seasons later.
- **Return**: p 0.03 a goat strays or 10% of the grain is spilled; p 0.005 × 2D the traveller is hurt (`injured = 2`). Goods go to the side that carried them. Trip goods are **not** household withdrawals or deposits (the village account is the 「交換」 record).
- A season cut short by a famine break returns unfinished trips at the season end: before the barter, what was carried; after it (`bartered`), what was received plus what the partner did not take (never both — the first draft returned the carried goods even when the partner had taken them and paid nothing, duplicating them).
- Note (observed in the trial): 4 pots (160) cannot buy a goat (375); goats come mostly from offers at the meeting, trips bring grain or obsidian, or several travellers go together. This follows from the values and is left to the players.

## 9. Seals and sealings

- `"seal": true` from a household's own rep: the household seal (once). From then on its 倉 is sealed; theft from it is logged as 封 (「ナギの家の倉の封が割れていた: …」) and always becomes a dispute; sealed stores are robbed last.
- `"seal_store": true` by more than half of adults or by the leader: the village store is sealed this season. Every day a household takes from it leaves one piece with its seal, or an unstamped piece (「(印なし)」); a household opening its own sealed 倉 also leaves one.
- Season end: event 封 「この季節、印で封をした倉や村の蓄えが開けられた (割った封のかけらは取っておいた): 川辺の家の印 30 回、…」. **F2** = a season in which pieces from ≥ 2 households' seals were left (`seal_seasons ≥ 1`).
- Narration says 「家の印」「封をした」, never 「持ち主の印」 (both the communal-storage and private-property readings exist: Akkermans & Duistermaat 1996/97; Duistermaat 2012, 2013). The seal itself is still introduced in G6 as the start of records, as decided (part2.md 6.3); only the wording changes (question 12).

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
- **Ration credit**: with a complete 蓄え record, each household's craft, keeping and trip days × DAY_FOOD count as 入れた in the G5 蓄え comparison (rations in proto-cuneiform: Englund 2011; Arslantepe food distribution from mass-produced bowls: Frangipane et al. 2007, an interpretation; the credit rule is 【仮定】). Specialists' households otherwise look like over-takers (アルの家 took 1425 and put in 0 in spring 1769).
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

```text
## ほかの村・印・記録
知っているほかの村:
- [N1] 西の村 (西へ歩いて 1 日): よその村。人 約 10 人。出せる物: ヤギ・草の種。ほしがる物: 土器・鎌・草の種。はじめて知った日 1949 日目。交換した季節 7 回 (最後は 2130 日目)
- [N2] 東の村 (東へ歩いて 2 日): よその村。人 約 20 人。出せる物: ヤギ・黒曜石・草の種。ほしがる物: 土器・鎌・草の種。はじめて知った日 2099 日目。交換した季節 3 回 (最後は 2160 日目)
- [N3] 南の村 (川にそって南へ歩いて 1 日): よその村。人 約 20 人。出せる物: ヤギ・草の種。ほしがる物: 土器・鎌・草の種。はじめて知った日 2129 日目。交換した季節 2 回 (最後は 2160 日目)
まだ返されていない貸し借り:
- [D4] 西の村 が村に返す分: 黒曜石 5 個 (封筒の記録がある)。2011 日目から
家の印: アルの家 (1920 日目から)、クラの家 (1920 日目から)、ケトの家 (1920 日目から)、… (…)
前の季節は、村の蓄えに封をした
前の季節の記録 (セナ 30 日・板、ソル 30 日・板): 村の蓄えへの家ごとの出し入れ は全部残せた、ほかの村との交換と貸し借り は全部残せた、よその家の畑で刈った量 は全部残せた
使える記録の道具: 印・数え札・封筒・板
村の黒曜石: 0 個 (黒曜石の刃の鎌 20 本)
前の季節の、家ごとの村の蓄えへの出し入れ (板の記録による。大人の分。草の種にして): アルの家 入れた 6183・取った 685 つかみ、クラの家 入れた 5623・取った 0 つかみ、…
この前の集まりから起きたこと (ほかの村・印・記録):
- [出来事 44877] サエ は 南の村 で、草の種 190 つかみ・鎌 3 本 を渡し、ヤギ 1 頭・草の種 40 つかみ を受けとった (受けとってもらえなかった 草の種 410 つかみ は持ち帰る)
- [出来事 44928] ハユ は 東の村 で、土器 4 個 を渡し、黒曜石 4 個 を受けとった
- [出来事 46158] セナ・ソル が、この季節の 村の蓄えへの家ごとの出し入れ (全部残せた。389 / 389 個分)、ほかの村との交換と貸し借り (全部残せた。7 / 7 個分)、よその家の畑で刈った量 (全部残せた。51 / 51 個分) を残した
- [出来事 46164] この季節、印で封をした倉や村の蓄えが開けられた (割った封のかけらは取っておいた): アルの家の印 30 回、ケトの家の印 30 回、…

## よそから来た人
- ハユ2 (男、28 歳)、リオ2 (男、27 歳)、トワ2 (男、12 歳) (東の村 から来た)
それぞれ「ここで暮らしたい」と言っている (1 行が、いっしょに来た一つの群れ)。群れごとに、村に受け入れるか決めてください (accept: …)
…
8. ほかの村・印・記録 (上の「ほかの村・印・記録」を見て決める。どれも書かなくてもよい)
   村の蓄えの封: この季節、村の蓄えに封をするなら true、しないなら false (seal_store)
   交換に行く: 主な仕事を「交換に行く」にする人は、job か family に、to (村の番号)・carry (持って行く物と数)・want (ほしい物)・then (帰ってからの仕事) を書く。例 {…}
   記録をつける: 主な仕事を「記録をつける」にする人は、what (残すもの: 蓄え・交換・刈る。書いた順に残す) と how (数え札 / 封筒 / 板) を書く。例 {…}
9. 今の気持ちを一言
…
 "judge": {"M11": "...", "M12": "...", "M13": "..."}, "feast": false, "leader": "...", "seal_store": false,
```

The whole prompt was about 86 KB (≈ 32k characters) with 29 people and 10 households.

## 16. Indicators, CRITERIA, SUBSTEPS, end of Society 2.0

- `_g6_indicators` (§5.1) adds 20 keys, all prefixed `g6_`, from G6 on (a zero base until `g6` is created at the first G6 meeting). Before G6 it returns `{}`, so `state.json` and `app_data.json` are byte-identical to the current code (test A compares them without stripping anything).
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

```diff
--- a/sim/society/step.py
+++ b/sim/society/step.py
@@ -106,20 +106,21 @@
 
 
 ACT_BY_EVENT = {"採集": "採集", "探索": "探索", "休む": "休む", "道具": "道具づくり", "火": "火おこし", "種まき": "種まき",
-                "畑仕事": "畑仕事", "ヤギの世話": "ヤギの世話", "ヤギを捕まえる": "ヤギを捕まえる", "土器": "土器づくり", "住まい": "住まいを建てる"}  # Society 2.0 の仕事
+                "畑仕事": "畑仕事", "ヤギの世話": "ヤギの世話", "ヤギを捕まえる": "ヤギを捕まえる", "土器": "土器づくり", "住まい": "住まいを建てる",
+                "交換に行く": "交換に行く", "記録をつける": "記録をつける"}  # Society 2.0 の仕事
 
 
-def day_summaries(state):
+def day_summaries(state, extra=()):
     """3D 再生用: 日ごとに、誰がどの活動でどの場所へ行ったか (出来事の記録から組み立てる)"""
-    labels = sorted(state["places"], key=lambda p: -len(p["label"]))
+    labels = sorted(list(state["places"]) + list(extra), key=lambda p: -len(p["label"]))  # G6: ほかの村へ行く人は、地図の端へ歩く
     out = {}
     for d in range(1, state["day"] + 1):
         rows = {}
         for e in state["events"]:
             if e["day"] != d:
                 continue
             names = e.get("data", {}).get("hunters") if e["type"] == "狩り" else [e["who"]]
-            act = "狩り" if e["type"] == "狩り" else ACT_BY_EVENT.get(e["type"])
+            act = "狩り" if e["type"] == "狩り" else "交換に行く" if e["type"] == "交換" and e.get("who") else ACT_BY_EVENT.get(e["type"])  # G6: 向こうの村で交換した日も、その村にいる (集まりでの交換は who がない)
             if not act or not names:
                 continue
             pid = next((p["id"] for p in labels if p["label"] in e["text"]), "camp")
@@ -132,10 +133,11 @@
 def export(state):
     """アプリ (Web ページ) 用のデータ"""
     ev_recent = state["events"]  # すべての日 (過去の日の 3D 再生と動画のため)
+    extra = era2.g6_places(state)  # G6: 知っているほかの村の、地図の端の場所 (G6 の前は空)
     data = {
         "day": state["day"], "season": world.season(max(1, state["day"])), "phase": state["phase"],
         "map": {"w": world.W, "h": world.H, "cell": world.CELL, "terrain": state["terrain"], "legend": world.TERRAIN},
-        "camp": state["camp"], "places": state["places"],
+        "camp": state["camp"], "places": state["places"] + extra,
         "plants": [{"x": q["x"], "y": q["y"], "kind": q["kind"], "amount": round(q["amount"], 1), "sown": q.get("sown", False)}
                    for q in state["plants"]],
         "herds": state["herds"], "predators": state["predators"], "planted": state["planted"],
@@ -146,7 +148,7 @@
                       "knowledge": p.get("knowledge", [])} for p in state["people"]],
         "events": ev_recent, "laws": state.get("laws", []),
         "knowledge_log": state.get("knowledge_log", [])[-300:], "stats": state["stats"],
-        "days": day_summaries(state),
+        "days": day_summaries(state, extra),
         "era": state.get("era_info") or {"era": "F1", "name": phase.ERAS["F1"]}, "era_log": state.get("era_log", []),
         "hold": bool(state.get("hold")), "store": world.food_words(phase._store_kinds(state)),
         "resumes": resume.build(state),
@@ -155,6 +157,7 @@
         # 家族の住まい (G3 から): 3D の再生で、家族ごとの家を描く
         "houses": [{"household": h, "x": v["x"], "y": v["y"], "start": v["start"], "built": v["built"], "sizes": v["sizes"]}
                    for h, v in sorted((state.get("era2") or {}).get("homes", {}).items())],
+        **({"g6": era2.g6_export(state)} if (state.get("era2") or {}).get("g6") else {}),  # G6: ほかの村・印・記録 (G6 の前は鍵がない)
     }
     (DATA / "app_data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
     print("アプリ用のデータ:", (DATA / "app_data.json").relative_to(DATA.parent))
@@ -189,7 +192,8 @@
         era = state.get("era", "F1")
         print(f"フェーズ: {era} {phase.ERAS.get(era) or era2.NAMES2.get(era)} / 次の条件: {info.get('next', '-')}")
         if state.get("hold"):
-            print("一時停止中: フェーズが進んだので評価待ち (再開は resume)")
+            print("一時停止中: Society 2.0 が終わったので、第 4 部のまとめ待ち (再開は resume)" if ((state.get("era2") or {}).get("g6") or {}).get("end")
+                  else "一時停止中: フェーズが進んだので評価待ち (再開は resume)")
         if state["phase"] in ("evening", "night", "season"):
             print(f"お題: {pdir(state, state['phase'], 'prompts').relative_to(DATA.parent)}")
         return
@@ -216,7 +220,8 @@
         if state["phase"] != "season":
             sys.exit(f"今の段階は {state['phase']} です")
         if state.get("hold"):
-            print(f"一時停止中: フェーズ {state.get('era')} に進んだので評価待ち。進めない (再開は resume)")
+            print("一時停止中: Society 2.0 が終わったので、第 4 部のまとめ待ち。進めない (再開は resume)" if ((state.get("era2") or {}).get("g6") or {}).get("end")
+                  else f"一時停止中: フェーズ {state.get('era')} に進んだので評価待ち。進めない (再開は resume)")
             sys.exit(3)
         before = state["next_event"]  # G5: 季節の集まりで起きたこと (収める・裁き・罰・祭り・まとめ役) は、30 日を進める前の出来事
         feels = read_feelings(state)  # 代表を決める前の顔ぶれで読む (集まりで、まとめ役が変わることがあるため)
@@ -230,7 +235,13 @@
             gone = [p for p in state["people"] if p.get("left")]
             print("生きている人がいない (亡くなった人と、村を出た人" + (f" {len(gone)} 人" if gone else " 0 人") + ")")
             sys.exit(4)
-        if era2.check(state):
+        r = era2.check(state)
+        if r == "end":  # G6: 町と記録がそろった (「フェーズが…に進んだ」とは書かない)
+            state["hold"] = True
+            g = state["era2"]["g6"]["end"]
+            world.log(state, "フェーズ", None, f"Society 2.0 の終わり: 町 ({g['town']} 日目) と記録 ({g['record']} 日目) がそろった (先にそろったのは {g['first']})")
+            print(f"* Society 2.0 が終わった: 町 ({g['town']} 日目) と記録 ({g['record']} 日目) がそろった → 一時停止 (第 4 部のまとめ待ち)")
+        elif r:
             state["hold"] = True
             e = state["era_log"][-1]
             world.log(state, "フェーズ", None, f"フェーズが {e['era']} ({era2.NAMES2[e['era']]}) に進んだ")
@@ -240,7 +251,7 @@
         export(state)
         for e in state["events"]:
             if (e["id"] >= first and e["type"] in ("掟", "死", "生まれる", "加わる", "去る", "訪れる", "畑", "ヤギ", "大人になる", "フェーズ", "家族", "虫", "受けつぎ", "区切り")) \
-                    or (e["id"] >= before and e["type"] in era2.G5_EVENTS):
+                    or (e["id"] >= before and e["type"] in era2.G5_EVENTS + era2.G6_EVENTS):
                 print("*", e["text"][:120])
         harv = sum((e.get("data") or {}).get("amount", 0) for e in state["events"] if e["id"] >= first and e["type"] == "収穫")
         if harv:
@@ -251,6 +262,12 @@
             print(f"G5 第 {i['g5_stage']} 段 / 家族 {i['households']} / まとめ役 {i['leader'] or 'いない'} / もめごと 残り {i['disputes_open']} "
                   f"(まとめ役なしで収めた {i['settled']}・まとめ役の裁き {i['judged']}) / 罰のある掟 {i['penalty_laws']}・罰 {i['penalties']} / "
                   f"祭り {i['feasts']} / 分かれた家 {i['fissions']} / 共同の仕事 {i['joint']} / 第 1 段 {'済み' if i['stage1'] else 'まだ'}")
+        if i.get("g6_on"):
+            print(f"G6 / 人 {i['population']} (大人 {i['adults']}) / 知っている村 {i['g6_known']} (この 4 季節に交換した村 {i['g6_partners']}・いちばん大きい相手 {i['g6_biggest']} 人) / "
+                  f"交換の続いた季節 {i['g6_run']} / 交換 {i['g6_exchanges']}・返されていない貸し借り {i['g6_debts_open']} / G6 で加わった人 {i['g6_joined']} / "
+                  f"印 {i['g6_seals']} 家・封のかけら {i['g6_sealings']} (封をした季節 {i['g6_seal_seasons']}) / 記録の道具 {i['g6_tools']} / 記録した季節 {i['g6_records']} / "
+                  f"確かめた {i['g6_checked']} (板 {i['g6_checked_tablet']})・覚え違い {i['g6_misremember']} / 食べ物をとらない人 {i['g6_nonfood']} / "
+                  f"町 {i['g6_town_day'] or 'まだ'} / 記録 {i['g6_record_day'] or 'まだ'}")
         return
     if a.cmd == "day" and not any(p["alive"] for p in state["people"]):
         print("生きている人がいないので、進めない")
```

Notes on the step.py diff: `day_summaries` maps a 交換 event that has a `who` (the barter day of a trip) to 交換に行く, so the 3D replay keeps the traveller at the partner village on that day instead of resting at camp (meeting exchanges have no `who`; before G6 there are no 交換 events, so the export is unchanged); `season` with `hold` set prints the end-of-Society-2.0 reason too. Both were checked in test D (2026-10-09).

**sim/society/tools/society2_seasons_workflow.js**, before the phase regex (L43):
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
- Assert: prompts and feeling prompts byte-identical; `json.dumps(state, sort_keys=True)` equal **without removing anything** (no `g6_*` key exists before G6); `"g6" not in era2`; salts recorded by a monkeypatched `_rng` never include 41; `answerers`/`feelers` equal; the G6 jobs became 休む; `export()` without a `g6` key and with the same `places`/`days`; `_house_site` returns the same sites (also with 20 homes forced).

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
- **Growth may be fast.** In the trial "open" runs population went 25 → 44 in 8 seasons in one seed (all groups accepted, 3 partner villages within 3–8 seasons) and the town came at seasons 11–35. If people refuse newcomers it is much slower (projection: 0.11 within 10 years when only half the groups are accepted). Both are legitimate outcomes; consult the user after 8 seasons without growth instead of changing rules mid-run.
- **Record before town** (historically inverted: Brak's town ~900 years before writing). Report it; the tablet threshold (4 token seasons, 200 tokens) is the parameter to tune if the user wants writing to depend more on scale.
- **Information shown shrinks in G6** (ranges, claims). Haiku may be confused; FACTS explain it; ranges are deterministic.
- **覚え loop** could add disputes and fissions before records exist (stress already 0.72 at 9 households). Bounds: MAX_NEW 3, merging, DROP_AGE, feasts, the leader; 覚え does not chain.
- **Grain and pots drain.** Trading and lending can lower store days (trial: 279 → 116 days in 8 seasons while population grew). Partner caps limit it; daily_run consultation rule at `store_days < 120`.
- **Goats pile up** in long runs (trial: hundreds after 6 years, thousands after 10, also in the silent and closed runs). This is the existing G2 herd rule (tended females bear every spring, 40% twins, no pasture or feed limit), not G6; trade adds a few. Report it to the user as a separate finding; do not change it inside G6.
- **Names**: suffix names appear at once (question 15).
- **Answer load and data**: one more rep per accepted group (≈ 15–20 answers a season at 50 people); app_data.json (≈ 15 MB now) may reach 40–60 MB; the daily keeper and traveller events add ≈ 30–60 events a season.
- **Narration**: other villages are model constructs created by logged events; captions quote only those events; pre-G6 visitors get no origin; 「家の印」, not 「持ち主の印」.
- **Contested archaeology**: token meaning and token → word signs, down-the-line exchange, debt as the trigger of records, what seals meant (owner or communal store), migration into Brak — never stated as fact (§24). Several 【文献】 entries were checked only against abstracts or reviews (§23); re-check the full texts before quoting numbers in narration.
- **Live run**: the checkout is shared with the live run (and other sessions push code). Implement only after the decisions, rebase the diffs on the current HEAD, and re-run test A with the newest committed answers.

## 21. Decisions for 本人 (recommendation first)

Same 17 items as the Japanese summary. In short: (1) town 50; (2) keep the 4-season exchange in the town condition, ≥ 2 villages; (3) town pull yes; (4) villages only from logged events + a guaranteed first trader; (5) days sticky; (6) hold only at the end; (7) 覚え yes; (8) record = checked with a tablet, thresholds as given, report record-before-town; (9) trips yes; (10) household trade yes; (11) obsidian yes, no beads; (12) one seal per household, worded 「家の印」 rather than 「持ち主の印」; (13) four F; (14) no storehouse now; (15) NAMES_G6 from G6; (16) hide houses after fission and add G5 toasts; (17) fix the research docs when G6 is built.

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

## 23. Literature (【文献】 = literature basis; 【文献・二次】 = seen only in a secondary summary; 【未確認】 / (memory, unverified) = not checked this session)

Fact check (2026-10-09, web search only; full texts mostly paywalled, so most entries were checked against abstracts, publisher records or reviews). Changed after the check: Sabi Abyad date and seal count, Brak satellite distances and primacy, the Brak migration study (dental, not strontium), Hamoukar obsidian sources, village densities, Johnson 1973 → 1978/1982 for information load, interest-bearing debt, Kelley et al. 2024 (seal motifs, not a token critique), §24 items 9–11. The literature reviews in `docs/research/historical_records.md` (checked version) agree with the corrected values.

Exchange and obsidian
- Renfrew, Dixon & Cann 1968, Proc. Prehist. Soc. 34:319–331 — fall-off curves; supply zone ≤ ~300 km 【文献】
- Renfrew 1975, "Trade as action at a distance" (Sabloff & Lamberg-Karlovsky eds.) — modes of exchange 【文献】; Renfrew 1977 — monotonic decrement 【文献】
- Hodder & Orton 1976 — equifinality of fall-off curves 【文献・二次】
- Ortega, Ibáñez, Khalidi, Méndez, Campos & Teira 2014, J. Archaeol. Method Theory 21(2):461–485; Ibáñez et al. 2015, J. R. Soc. Interface 12:20150210 — agent-based models: down-the-line does not carry obsidian beyond ~300 km; a small-world network explains spread up to ~800 km 【文献】(abstracts checked; a model result, not an observation)
- Yacobi & Gopher 2023, Camb. Archaeol. J. 33(3):431–448 — kin-based trade partnership model (Wadi Rabah, Hagoshrim) 【文献】(abstract checked; the authors' model)
- Carter et al. 2006/2007/2008 — Çatalhöyük obsidian sources 【文献】
- Davidson & McKerrell 1976, Iraq 38:45–56 (Khabur headwaters); 1980, Iraq 42:155–167 (neutron activation, Arpachiyah and Gawra) — Halaf pottery moved between sites 【文献】
- Khalidi, Gratuze & Boucetta 2009, Archaeometry 51(6):879–893 — LC2 obsidian at Hamoukar and Brak mostly from the Bingöl region, minor Lake Van source (Bingöl A and Nemrut Dağ are hard to tell apart) 【文献】(abstract). The earlier note 「Hamoukar LC1–2 obsidian ~85% Nemrut Dağ, OI reports 2005–2007」 was not confirmed and conflicts with this abstract
- Hallan Çemi → Nemrut Dağ ≈ 100 km in 3 days 【文献・二次】

Seals, sealings, tokens, writing
- Duistermaat 1996; Akkermans & Duistermaat 1996/97, Paléorient 22(2):17–44; Akkermans & Duistermaat 2004, Levant 36:1–11 — Sabi Abyad: hundreds of sealings (communal storage, settled and mobile groups: the authors' reading); the 2004 finds date c. 6300–6000 BC; most sealings come from the Burnt Village (level 6, c. 6000 BC) 【文献】(abstracts). The earlier 「level 8B, ~6175–6125 cal BC」 was not confirmed
- Duistermaat 2012, OLA 219:1–16 — non-administrative origins of seals 【文献】 (text not read); Duistermaat 2013, "Private matters" (in Nieuwenhuyse et al. eds., *Interpreting the Late Neolithic of Upper Mesopotamia*, 315–322) — private-property reading 【文献】 (text not read)
- Stamp seals from the late 8th millennium BC (Ras Shamra, Byblos, Bouqras, Çatalhöyük) 【文献・二次】(Durham repository paper)
- Frangipane et al. 2007, *Arslantepe Cretulae* (Arslantepe V) — >2,200 sealings with impressions from the Period VI A palace (c. 3400–3000 BC); storeroom A340: 30 seals on 175 cretulae, read by the authors as the seals of many people withdrawing goods (a reviewer finds this possible but not compelling: Weingarten 2009, AJA 113.2); Temple C bowls 【文献】
- McMahon 2009, Iraq 71 — Late Chalcolithic seal iconography at Brak 【文献】
- Schmandt-Besserat 1992, *Before Writing* — tokens → envelopes → tablets (her interpretation) 【文献】
- Bennison-Chapman 2018, Levant 50(3):305– ("Clay objects as 'tokens'?", Tell Sabi Abyad: some contexts suggest counting/administration); 2019, Camb. Archaeol. J. 29(2):233– ("Reconsidering 'tokens'": tokens from the 10th millennium cal BC, mostly multifunctional) 【文献】
- Englund 1993, Science 260:1670–1671 (review of *Before Writing*); Englund 1998, OBO 160/1; Englund 2011, "Accounting in proto-cuneiform"; Damerow & Englund 1987 — numerical tablets (Uruk V, c. 3500–3350 BC), number and kind signs (Uruk IV, c. 3350–3200 BC), ~85% administrative 【文献】; envelopes (bullae) with tokens from the mid-4th millennium (Uruk VI/V, c. 3500 BC) 【文献・二次】
- Zimansky 1993, J. Field Archaeol. 20(4):513–517; Michalowski 1993, "Tokenism", Am. Anthropol. 95(4):996–999; Friberg 1994 — critiques of token → word signs 【文献】; Kelley, Cartolano & Ferrara 2024, "Seals and signs", Antiquity (doi 10.15184/aqy.2024.165) — some proto-cuneiform signs derive from seal motifs of c. 4400–3400 BC (another source of kind signs) 【文献】

Towns and information
- Childe 1950, Town Planning Review 21:3–17 — urban revolution criteria 【文献】
- Johnson 1973, *Local Exchange and Early State Development in Southwestern Iran*, Anthropol. Pap. 51 (Univ. Michigan) — Uruk settlement and exchange on the Susiana plain 【文献】; Johnson 1978 (in Redman et al. eds., *Social Archeology*, 87–112) — information sources and decision-making organizations 【文献】(bibliographic record only); Johnson 1982 — scalar stress (used in G5) 【文献】
- Wright & Johnson 1975, "Population, exchange, and early state formation in southwestern Iran", Am. Anthropol. 77(2):267–289 — administrative hierarchy and settlement tiers 【文献】
- Shin, Price, Wolpert, Shimao, Tracey & Kohler 2020, Nat. Commun. 11:2394 — scale threshold before information threshold (Seshat) 【文献】
- Ur, Karsgaard & Oates 2007, Science 317:1188; Ur, Karsgaard & Oates 2011, Iraq 73:1–19; Oates et al. 2007, Antiquity 81:585–600 — Tell Brak LC: LC2 (c. 4200–3900/3800 BC) ≈ 55 ha, LC3–4 ≈ 130 ha (figures from Ur's Brak project page; Science text not read) 【文献】
- McMahon, Sołtysiak & Weber 2011, J. Field Archaeol. 36:201–220 — Tell Majnuna 【文献】
- Brak migration: a dental-morphology (not strontium) study of Late Chalcolithic Brak, J. Anthropol. Archaeol. (c. 2022; Sołtysiak and colleagues) — growth partly by migration, neighbourhoods by origin 【文献・二次】(press summary only). The earlier 「isotope study 2020, Archaeol. Anthropol. Sci., doi 10.1007/s12520-020-01104-3」 could not be found
- Lawrence & Wilkinson 2015, "Hubs and upstarts: pathways to urbanism in the northern Fertile Crescent", Antiquity 89 【文献】(abstract; the 10–20 ha small-centre figure not re-checked)
- Ur 2010, *Urbanism and Cultural Landscapes in Northeastern Syria: The Tell Hamoukar Survey* (OIP 137) — Hamoukar LC1–2 southern extension ≈ 280–300 ha dispersed 【文献・二次】
- McMahon 2020 (online 2019), J. Archaeol. Res. 28 — low-density zones in early northern cities 【文献】(abstract; no density figure)
- Ur 2014, Camb. Archaeol. J. 24(2):249–268 — households and the emergence of cities 【文献】
- Village densities ≈ 100–200 persons/ha (Kramer's ≈ 120/ha, cited via Hassan 1981) 【文献・二次】; Kramer 1982 and Watson 1979 themselves not read; Nissen 2003 — Uruk ≈ 40,000 【文献・二次】
- Bandy 2004, Am. Anthropol. 106 — fission size (G5) 【文献】; Stein 1994; Fried; Flannery 2002 (G5) 【文献】
- Halstead & O'Shea 1982 — social storage (memory, unverified); Hudson 2018, *…and forgive them their debts* — interest-bearing grain loans and debt cancellations from c. 2400 BC (Enmetena of Lagash); Hudson's reading 【文献・二次】

## 24. Corrections to the research docs (fix when G6 is built; question 17)

1. society2_research.md L262 「村から村へ手渡しで運ばれた」: contested; down-the-line cannot reach far unless villages are ~100 km apart or pass on ~90% (Ortega et al. 2014; Ibáñez et al. 2015); small-world/kin networks fit better.
2. L262 「それより遠いと急に減る」: the decline is smooth (log-linear); the 300 km / 80% zone thresholds lack an ethnographic basis.
3. L260 「約 200 km」: usually ~190 km (unverified); Çatalhöyük also received eastern Anatolian obsidian >600 km away (Carter et al. 2008).
4. L263, L275 「前8000年頃から…形ごとに穀物1かご・ヒツジ1頭」: Schmandt-Besserat's interpretation and dating; in calibrated terms tokens appear from the 10th millennium cal BC and were mostly multifunctional, with possible counting use in some contexts (Bennison-Chapman 2018, 2019).
5. L264–265 「数の記号と物の記号に分かれ、文字」: accepted for number signs; weak for word signs from complex tokens (Zimansky 1993; Michalowski 1993; Englund 1993; Kelley et al. 2024); tokens continued after writing.
6. L266 「約9割は役所の帳簿」: ~85% overall; Uruk IV almost all administrative, Uruk III ~80% (Englund 2011).
7. L267, L278 「最初の町の人口」 for Uruk: Brak (LC2) and Hamoukar are earlier towns; 40–50k is an estimate (Nissen 2003 ~40,000).
8. L277 「トークン → 文字 約5000年」: ~4,800–6,500 years depending on the start date.
9. periodization.md L56 「約 300 ha は根拠がなく、近くのハムーカルとまざった可能性が高い」: **no change** (this item was withdrawn after checking). No source gives Brak ~300 ha; Hamoukar's LC1–2 southern extension is ≈ 280–300 ha (Ur 2010), so the periodization note stands.
10. periodization.md L19, L56 「LC2 (前 4,200〜3,800)・約 55 ha」: **matches** Ur's Brak project page (LC2 4200–3800 BC, 55 ha). Optional: add that other sources (Oates et al. 2007; Wikipedia's Period E) end LC2 ~3900 BC.
11. periodization.md L40 「トークン 前 8,000/7,500 年ごろ〜」「サビ・アビヤドの印章 前 6,200」: tokens from the 10th millennium cal BC (Bennison-Chapman 2019); stamp seals already from the late 8th millennium BC (Ras Shamra, Byblos, Bouqras, Çatalhöyük); Sabi Abyad stands out for its hundreds of sealings, c. 6300–6000 BC, most from the Burnt Village c. 6000 BC (Akkermans & Duistermaat 2004; historical_records.md uses 前 6000 年ごろ).
12. society2_phase_plan.md L21 G6 町: exchange predates towns by millennia; 100 people is unreachable for decades (§3) — update after question 1 and 2.
13. part2.md L61 and plan L41 「持ち主の印」: both communal-storage (Akkermans & Duistermaat 1996/97) and private-property (Duistermaat 2010, 2013) readings exist; narration says 「家の印」「封をした」. part2.md records the user's decision, so do not rewrite it; add a note there only if the user approves question 12.
14. research §7(c), §9 「記録なしの貸し借りの覚え違い」: 【仮定】; stores, withdrawals, rations and transfers are better attested triggers (§2, §11).
