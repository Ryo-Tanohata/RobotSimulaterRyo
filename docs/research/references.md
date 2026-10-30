# 参考にした研究と出典

このプロジェクトが外から持ってきたもの (本人の修士論文・人の論文や本・ゲーム・道具・声・AI) の一覧です。このファイルは `python3.13 sim/society/tools/build_references.py` が作ります (手で直すのは `sim/society/tools/references.json` の entries だけ)。まとめた日: 2026-10-30。

## 読み方

- **✓ 確かめた**: 書誌 (だれが・いつ・題・どこに出たか) を、本や雑誌の記録・DOI・図書館の目録と照らした。いつ、どこで照らしたかを書いた。
- **✗ 確かめていない**: まだ照らしていない。名前や中身は、Claude の記憶 (【記憶】) か、研究ノートを書いたときの調べ (要旨・紹介) のまま。
- **⚠ 食い違い**: 照らしたら、書いてあることと合わなかった。
- 書誌が分からないものは、作らずに「分かることだけ」を書いた。研究ノートの文献の行は、文のまま写した。
- ダッシュボード (`sim/society/app/research.html`) では、外から持ってきた研究に〔 〕の印をつけ、この一覧につないでいる。

## 数

| | 件数 | ✓ | ✗ | ⚠ |
|---|---|---|---|---|
| 本人の研究 | 1 | 1 | 0 | 0 |
| 論文・本 | 44 | 43 | 0 | 1 |
| ゲーム・道具・声 | 10 | 10 | 0 | 0 |
| 使った AI | 2 | 0 | 2 | 0 |
| **手で書いた一覧の合計** | **57** | **54** | **2** | **1** |
| 研究ノートの文献 (機械で集めた) | 480 | 0 | 480 | 0 |

研究ノートの文献 480 件のうち、【未確認】の印 15・【記憶】の印 17・名前と年だけ (書誌の行がない) 56。これらは、ノートを書いたときに要旨や紹介で読んだものが多いが、この一覧を作るときには確かめなおしていない (✗)。

## 本人の研究

### ✓ 確かめた 〔田之畑 2017 (修士論文)〕

- **書誌**: 田之畑 諒 (2017)「他人の権利を侵害する事についての意識とその背景」放送大学大学院 文化科学研究科 情報学プログラム 修士論文 (公開されていない)。refs.bib の英語: Tanohata, R. (2017). Master's thesis, Graduate School of Arts and Sciences (Information Studies Program), The Open University of Japan.
- **種類**: 修士論文 (本人の研究)
- **どんなものか**: ふだんの「他人の権利をおかすこと」を、人がどれくらい問題と感じるかを 54 問のアンケートとインタビューで調べた研究。
- **何に使ったか**: 論文 2 の実験 1〜3 の土台: アンケート 54 問の文・論文にある「常識的な回答の予想」・印刷された主成分の表 (表 3、第 1 主成分 0.268 など)・7 つの考え方・意識のモデル。
- **使っていないもの**: 答えた人ひとりひとりの元のデータ (持っていない)・インタビューの言葉 (2016 年の約束で、この研究だけに使い、終わったら捨てると約束したため)。
- **2016 年の約束**: 2016 年のアンケートの説明文「データは統計的に処理して利用しますので、個人が特定されることはありません」→ 使うのは論文に印刷された集計の値だけ。インタビューの説明文「本研究にのみ、匿名で使われます … 本研究終了後、速やかにかつ適切に廃棄します」→ インタビューの言葉は使わない。集計の値を論文に出してよいかは、本人が確かめる (論文 2 の TODO 5)。
- **どう入ったか**: 本人がつくった研究。2026-10-29 に本人がチャットで論文を渡した
- **確かめ**: ✓ 確かめた — 本人が渡した論文そのもの (表紙と付録 9.1) で、題・学校・年を確かめた。ウェブには公開されていない (2026-10-30 のウェブ検索でも出てこない)。英語の題と学校の英語名は Claude の訳で、まだ確かめていない (論文 2 の本人の TODO 3)
- **使った所**: `docs/research/humanity/thesis2017_questionnaire.md`・`docs/research/humanity/paper2_exp1_prereg.md`・`docs/research/humanity/paper2_exp1_results.md`・`docs/research/humanity/paper2_exp2_prereg.md`・`docs/research/humanity/paper2_exp3_prereg.md`・`paper/paper2/refs.bib`・`paper/paper2/main.tex`・`sim/society/tools/survey/`・`sim/society/tools/research_dashboard_content.json`

## 論文・本

### ⚠ 食い違い 〔Sacks の言葉とされる文〕

- **書誌**: “We must humanize technology before it dehumanizes us.” 修士論文 (田之畑 2017) の始めに、神経科医 Oliver Sacks の言葉として引かれていた文。Sacks の本・話の中の出どころは見つかっていない。
- **種類**: 言葉 (引用)
- **どんなものか**: 「テクノロジーが人を人でなくする前に、テクノロジーを人らしくしなければならない」という文。
- **何に使ったか**: 論文 2 の始めの言葉。いまは「修士論文での引用のまま」とし、脚注で出どころが分からないと書いている。
- **どう入ったか**: 本人の修士論文から (2026-10-29 に本人が渡した)
- **確かめ**: ⚠ 食い違い — 2026-10-29 (論文 2 を書くとき) と 2026-10-30 に Claude がウェブ検索。Sacks の文章・話には見つからず、ほぼ同じ文が Rana el Kaliouby (Affectiva) の言葉として広く出てくる (2018 年ごろの講演、2020 年の本、Boston Globe 2023-12-14 の記事)。https://www.bostonglobe.com/2023/12/14/business/ai-rana-el-kaliouby-smart-eye-driving/
- **注**: 出どころが食い違う (⚠)。修士論文がどこから引いたかを本人が確かめる (論文 2 の TODO 2)。本当の出どころに直すか、名前を外すかを決める。
- **使った所**: `paper/paper2/main.tex`・`paper/paper2/README.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔el Kaliouby 2020〕

- **書誌**: el Kaliouby, R. (2020). Girl Decoded: A Scientist's Quest to Reclaim Our Humanity by Bringing Emotional Intelligence to Technology. (ISBN 9781984824769 ほか)
- **種類**: 本
- **どんなものか**: 感情を読む AI の研究者の自伝。「テクノロジーが人を人でなくする前に人らしくする」を自分の目標として語る。
- **何に使ったか**: Sacks の言葉とされる文の、本当の出どころの候補。
- **どう入ったか**: 2026-10-29 に論文 2 の手伝いの Claude がウェブ検索で見つけた (Sacks の言葉を調べたとき)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。図書館の目録 (例: https://concordia.catalog.ckls.org/Record/703704) と書評。本の中に「humanize technology before it dehumanizes us」の言い方があるとする紹介がある (本文は開いていない)
- **使った所**: `paper/paper2/README.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Park ほか 2023〕

- **書誌**: Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. Proceedings of UIST '23. ACM.
- **DOI**: https://doi.org/10.1145/3586183.3606763
- **種類**: 論文
- **どんなものか**: LLM の村人 25 人が町で暮らすシミュレーション。
- **何に使ったか**: LLM の村の先行研究としてくらべた。
- **どう入ったか**: 論文 1 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/society_phase/G7_design.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Altera.AL ほか 2024〕

- **書誌**: Altera.AL, Ahn, A., Becker, N., ほか (2024). Project Sid: Many-agent simulations toward AI civilization. arXiv:2411.00114.
- **URL**: https://arxiv.org/abs/2411.00114
- **種類**: 論文 (プレプリント)
- **どんなものか**: 1,000 ほどの LLM エージェントの社会 (Minecraft の中)。
- **何に使ったか**: LLM の文明シミュレーションの先行研究。
- **どう入ったか**: 論文 1 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`

### ✓ 確かめた 〔Piatti ほか 2024〕

- **書誌**: Piatti, G., Jin, Z., Kleiman-Weiner, M., Schölkopf, B., Sachan, M., & Mihalcea, R. (2024). Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM Agents. NeurIPS 2024.
- **DOI**: https://doi.org/10.52202/079017-3548
- **種類**: 論文
- **どんなものか**: LLM の群れが、共有の資源を使いつくさずにいられるかを見た。
- **何に使ったか**: 共有の資源と協力の先行研究。
- **どう入ったか**: 論文 1 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Horton 2023〕

- **書誌**: Horton, J. J. (2023). Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus? NBER Working Paper 31122.
- **URL**: https://www.nber.org/papers/w31122
- **種類**: ワーキングペーパー
- **どんなものか**: LLM を経済の実験の「人」の代わりにする考え。
- **何に使ったか**: LLM を人の代わりにする研究として (論文 1・2)。
- **どう入ったか**: 論文 1・2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper2/refs.bib`・`paper/paper1/main.tex`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Aher ほか 2023〕

- **書誌**: Aher, G., Arriaga, R. I., & Kalai, A. T. (2023). Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies. ICML 2023 (PMLR 202). arXiv:2208.10264.
- **URL**: https://arxiv.org/abs/2208.10264
- **種類**: 論文
- **どんなものか**: LLM で心理学などの有名な実験をなぞれるかを見た。
- **何に使ったか**: LLM を人の代わりにする研究として (論文 1・2)。
- **どう入ったか**: 論文 1・2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper2/refs.bib`・`paper/paper1/main.tex`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Argyle ほか 2023〕

- **書誌**: Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J. R., Rytting, C., & Wingate, D. (2023). Out of One, Many: Using Language Models to Simulate Human Samples. Political Analysis 31(3): 337–351.
- **DOI**: https://doi.org/10.1017/pan.2023.2
- **種類**: 論文
- **どんなものか**: 人の背景を書いて LLM に答えさせると、世論調査の答えに近づく。
- **何に使ったか**: 論文 2 の「暮らしを持たせる」考えのもと。
- **どう入ったか**: 論文 1・2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper2/refs.bib`・`paper/paper1/main.tex`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Mei ほか 2024〕

- **書誌**: Mei, Q., Xie, Y., Yuan, W., & Jackson, M. O. (2024). A Turing test of whether AI chatbots are behaviorally similar to humans. PNAS 121(9): e2313925121.
- **DOI**: https://doi.org/10.1073/pnas.2313925121
- **種類**: 論文
- **どんなものか**: AI の行いが人と似ているかを、経済ゲームと性格テストでくらべた。
- **何に使ったか**: AI は人より協力的、という先行の結果として。
- **どう入ったか**: 論文 1・2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper2/refs.bib`・`paper/paper1/main.tex`・`paper/paper2/main.tex`・`docs/research/state_emergence_plan.md`

### ✓ 確かめた 〔Akata ほか 2025〕

- **書誌**: Akata, E., Schulz, L., Coda-Forno, J., Oh, S. J., Bethge, M., & Schulz, E. (2025). Playing repeated games with large language models. Nature Human Behaviour 9(7): 1380–1390.
- **DOI**: https://doi.org/10.1038/s41562-025-02172-y
- **種類**: 論文
- **どんなものか**: LLM どうしでくり返しのゲームをすると、ゆるさない・協力の仕方にくせがある。
- **何に使ったか**: LLM のくせの先行研究。
- **どう入ったか**: 論文 1 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`

### ✓ 確かめた 〔Sharma ほか 2024〕

- **書誌**: Sharma, M., Tong, M., Korbak, T., ほか (2024). Towards Understanding Sycophancy in Language Models. ICLR 2024. arXiv:2310.13548.
- **URL**: https://arxiv.org/abs/2310.13548
- **種類**: 論文
- **どんなものか**: LLM が相手に合わせすぎる (おべっか) くせ。
- **何に使ったか**: LLM の村人が「すぐ払う」「逆らわない」ことの読みの一つとして。
- **どう入ったか**: 論文 1 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`

### ✓ 確かめた 〔Dillion ほか 2023〕

- **書誌**: Dillion, D., Tandon, N., Gu, Y., & Gray, K. (2023). Can AI language models replace human participants? Trends in Cognitive Sciences 27(7): 597–600.
- **DOI**: https://doi.org/10.1016/j.tics.2023.04.008
- **種類**: 論文
- **どんなものか**: AI は実験の参加者の代わりになるか、という問いの整理。
- **何に使ったか**: 論文 2 の問いのもと。
- **どう入ったか**: 論文 2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Santurkar ほか 2023〕

- **書誌**: Santurkar, S., Durmus, E., Ladhak, F., Lee, C., Liang, P., & Hashimoto, T. (2023). Whose Opinions Do Language Models Reflect? ICML 2023 (PMLR 202): 29971–30004.
- **種類**: 論文
- **どんなものか**: LLM の意見が、どの人びとの意見に近いか。
- **何に使ったか**: LLM の答えのかたよりの先行研究。
- **どう入ったか**: 論文 2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Bisbee ほか 2024〕

- **書誌**: Bisbee, J., Clinton, J. D., Dorff, C., Kenkel, B., & Larson, J. M. (2024). Synthetic Replacements for Human Survey Data? The Perils of Large Language Models. Political Analysis 32(4): 401–416.
- **DOI**: https://doi.org/10.1017/pan.2024.5
- **種類**: 論文
- **どんなものか**: LLM の答えはばらつきが小さすぎる、という注意。
- **何に使ったか**: 実験 1 の「答えがそろいすぎる」の先行研究。
- **どう入ったか**: 論文 2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Wang ほか 2024〕

- **書誌**: Wang, A., Morgenstern, J., & Dickerson, J. P. (2024). Large language models that replace human participants can harmfully misportray and flatten identity groups. arXiv:2402.01908.
- **URL**: https://arxiv.org/abs/2402.01908
- **種類**: 論文 (プレプリント)
- **どんなものか**: LLM に人の立場を演じさせると、集団を平たく描いてしまう。
- **何に使ったか**: 論文 2 の注意点として。雑誌の版があるかは確かめていない。
- **どう入ったか**: 論文 2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Serapio-García ほか 2023〕

- **書誌**: Serapio-García, G., Safdari, M., Crepy, C., ほか (2023). Personality Traits in Large Language Models. arXiv:2307.00184.
- **URL**: https://arxiv.org/abs/2307.00184
- **種類**: 論文 (プレプリント)
- **どんなものか**: LLM の性格を、性格テストで測って変えられるか。
- **何に使ったか**: 実験 1 の「人格の言葉」の先行研究。雑誌の版と著者の順は確かめていない。
- **どう入ったか**: 論文 2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Jiang ほか 2024〕

- **書誌**: Jiang, H., Zhang, X., Cao, X., Breazeal, C., Roy, D., & Kabbara, J. (2024). PersonaLLM: Investigating the Ability of Large Language Models to Express Personality Traits. Findings of NAACL 2024: 3605–3627.
- **DOI**: https://doi.org/10.18653/v1/2024.findings-naacl.229
- **種類**: 論文
- **どんなものか**: LLM に性格を与えると、文章に性格が出るか。
- **何に使ったか**: 実験 1 の「人格の言葉」の先行研究。
- **どう入ったか**: 論文 2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Hu & Collier 2024〕

- **書誌**: Hu, T., & Collier, N. (2024). Quantifying the Persona Effect in LLM Simulations. ACL 2024 (Long Papers): 10289–10307.
- **DOI**: https://doi.org/10.18653/v1/2024.acl-long.554
- **種類**: 論文
- **どんなものか**: 人の属性を与えても、LLM の答えはあまり説明できない。
- **何に使ったか**: 実験 2 の「暮らしを持たせる」の先行研究。
- **どう入ったか**: 論文 2 を書くとき、手伝いの Claude が先行研究としてウェブ検索で集めた (2026-10-29)
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`

### ✓ 確かめた 〔Maslow 1943〕

- **書誌**: Maslow, A. H. (1943). A theory of human motivation. Psychological Review 50(4): 370–396.
- **DOI**: https://doi.org/10.1037/h0054346
- **種類**: 論文
- **どんなものか**: 人の欲求には段がある (食べ物・安全 → 仲間 → 認められる → 自分らしく)。
- **何に使ったか**: 修士論文のモデル (欲求の段と、心の 3 つの部分) を論文 2 で説明するため。
- **どう入ったか**: 本人の修士論文のモデルが使っていた考え。論文 2 を書くとき (2026-10-29/30) に書誌をウェブ検索で確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Freud 1923〕

- **書誌**: Freud, S. (1923/1961). The Ego and the Id. In J. Strachey (Ed.), The Standard Edition of the Complete Psychological Works of Sigmund Freud, Vol. XIX. London: Hogarth Press. (もとはドイツ語 Das Ich und das Es, 1923)
- **種類**: 本の章
- **どんなものか**: 心を「それ (欲)・自分・上の自分 (きまり)」に分ける考え。
- **何に使ったか**: 修士論文のモデル (欲求の段と、心の 3 つの部分) を論文 2 で説明するため。
- **どう入ったか**: 本人の修士論文のモデルが使っていた考え。論文 2 を書くとき (2026-10-29/30) に書誌をウェブ検索で確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29/30 に論文 2 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌と照らした (paper/paper2/README.md の記録)
- **使った所**: `paper/paper2/refs.bib`・`paper/paper2/main.tex`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Carneiro 1970〕

- **書誌**: Carneiro, R. L. (1970). A Theory of the Origin of the State. Science 169(3947): 733–738.
- **DOI**: https://doi.org/10.1126/science.169.3947.733
- **種類**: 論文
- **どんなものか**: 逃げ場のない土地で争いが起きると、負けた側は従い、国ができる (囲みの説)。
- **何に使ったか**: 国の研究の仮説 H1・村の「出ていく」の読み。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/state_emergence_plan.md`・`docs/research/humanity/part1_same_and_different.md`・`docs/society_phase/G7_design.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Scott 2017〕

- **書誌**: Scott, J. C. (2017). Against the Grain: A Deep History of the Earliest States. New Haven: Yale University Press. (日本語訳: ジェームズ・C・スコット『反穀物の人類史 国家誕生のディープヒストリー』立木勝 訳、みすず書房、2019)
- **URL**: https://ci.nii.ac.jp/ncid/BB29407099
- **種類**: 本
- **どんなものか**: 最初の国は、見えて量れてためられる穀物から税を取って生まれた。人はよく国から逃げた。
- **何に使ったか**: 国の研究の仮説 H5・「この村は穀物も倉もそろったのに税がなかった」の読み。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **注**: 日本語訳の書誌は 2026-10-30 に CiNii (https://ci.nii.ac.jp/ncid/BB29407099) で確かめた。part3 の「Scott の『生きるための倫理』」は、この本ではなく Scott 1976 の考え。
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/state_emergence_plan.md`・`docs/research/humanity/part2_technology.md`・`docs/research/humanity/part3_humanness.md`・`docs/research/humanity/part1_same_and_different.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Scott 1976〕

- **書誌**: Scott, J. C. (1976). The Moral Economy of the Peasant: Rebellion and Subsistence in Southeast Asia. New Haven: Yale University Press.
- **種類**: 本
- **どんなものか**: 農民は「暮らしていけること」を何より大事にし、それをおびやかす取り立てに怒る (生きるための倫理)。
- **何に使ったか**: part3 で「飢えた人の取りを罪としない考え」の出どころ。
- **どう入ったか**: Claude の下地の知識 (part3 で年を書かずに「Scott の『生きるための倫理』」と書いた)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。図書館の目録と紹介 (例: https://ebooks.jgu.edu.in/Record/ebsco_acadsubs_ocn826657988/TOC)。副題の順や本のページ数は版で違う
- **注**: part3 には年がなく、Scott 2017 と取りちがえやすい。この本だと分かるように登録した。
- **使った所**: `docs/research/humanity/part3_humanness.md`

### ✓ 確かめた 〔Graeber & Wengrow 2021〕

- **書誌**: Graeber, D., & Wengrow, D. (2021). The Dawn of Everything: A New History of Humanity. New York: Farrar, Straus and Giroux.
- **種類**: 本
- **どんなものか**: 人は昔から、わざと王を作らない・季節で仕組みを変えるなど、社会の形を選んできた。
- **何に使ったか**: 国の研究の仮説 H6 (余りがあっても王を作らない)。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/state_emergence_plan.md`・`docs/tech_tree_design_draft.md`・`docs/research/humanity/part1_same_and_different.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G5.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Boehm 1999〕

- **書誌**: Boehm, C. (1999). Hierarchy in the Forest: The Evolution of Egalitarian Behavior. Cambridge, MA: Harvard University Press.
- **種類**: 本
- **どんなものか**: 狩りの群れは、いばる人を下からみんなでおさえて平等を保つ。
- **何に使ったか**: 国の研究の仮説 H6・村人が上に立とうとしないことの読み。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/state_emergence_plan.md`・`docs/research/humanity/part1_same_and_different.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Johnson 1982〕

- **書誌**: Johnson, G. A. (1982). Organizational structure and scalar stress. In C. Renfrew, M. J. Rowlands & B. A. Segraves (Eds.), Theory and Explanation in Archaeology (pp. 389–421). New York: Academic Press.
- **種類**: 本の章
- **どんなものか**: 話し合いで決める組が 6 ほどをこえると決めにくくなり、上の段ができる (規模のストレス)。
- **何に使ったか**: 国の研究の仮説 H3・世界のコードの ORG_GROUPS=6・G5 の設計。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **注**: state_emergence_plan.md・G7_design.md では【記憶】の印のままだが、論文 1 の refs.bib で確かめ済み。
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/state_emergence_plan.md`・`docs/society_phase/G5_design.md`・`docs/society_phase/G7_design.md`・`docs/research/humanity/part1_same_and_different.md`・`docs/research/humanity/part3_humanness.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G5.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/part2.md`・`docs/society_phase/part3.md`・`docs/tech_tree_design_draft.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Turchin ほか 2013〕

- **書誌**: Turchin, P., Currie, T. E., Turner, E. A. L., & Gavrilets, S. (2013). War, space, and the evolution of Old World complex societies. PNAS 110(41): 16384–16389.
- **DOI**: https://doi.org/10.1073/pnas.1308825110
- **種類**: 論文
- **どんなものか**: 戦の技術が広まった所で、大きな国ができた (模型と史実のくらべ)。
- **何に使ったか**: 国の研究の仮説 H2。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/state_emergence_plan.md`・`docs/society_phase/G7_design.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Hirschman 1970〕

- **書誌**: Hirschman, A. O. (1970). Exit, Voice, and Loyalty: Responses to Decline in Firms, Organizations, and States. Cambridge, MA: Harvard University Press.
- **種類**: 本
- **どんなものか**: 不満があるとき、人は「出ていく」か「声を上げる」か「残る」。
- **何に使ったか**: 国の研究の仮説 H7・村のききんでの「出ていく」の読み。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/state_emergence_plan.md`・`docs/research/humanity/part1_same_and_different.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Kohler ほか 2017〕

- **書誌**: Kohler, T. A., Smith, M. E., Bogaard, A., ほか (2017). Greater post-Neolithic wealth disparities in Eurasia than in North America and Mesoamerica. Nature 551: 619–622.
- **DOI**: https://doi.org/10.1038/nature24646
- **種類**: 論文
- **どんなものか**: 家の大きさから昔の差 (ジニ) を測った。旧大陸では、大きな家畜と犂のある社会で差が大きくなった。
- **何に使ったか**: 村の持ち物の差を、昔の差とくらべるところ。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **注**: part2_technology.md では【記憶】の印のままだが、書誌は論文 1 の refs.bib で確かめ済み。「大きな家畜と犂」という中身は、この調べでは本文で確かめなおしていない。
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part2_technology.md`・`docs/research/archaeological_evidence.md`・`docs/research/historical_records.md`・`docs/society_phase/G7_design.md`・`docs/society_phase/part3.md`・`docs/research/society2_periodization.md`・`sim/society/tools/research_dashboard_content.json`・`docs/research/humanity/README.md`・`docs/research/humanity/part1_same_and_different.md`・`docs/research/humanity/part3_humanness.md`

### ✓ 確かめた 〔Bogaard ほか 2019〕

- **書誌**: Bogaard, A., Fochesato, M., & Bowles, S. (2019). The farming-inequality nexus: new insights from ancient Western Eurasia. Antiquity 93(371): 1129–1143.
- **DOI**: https://doi.org/10.15184/aqy.2019.105
- **種類**: 論文
- **どんなものか**: 西ユーラシアでは、大きく長く続く差は前 4000 年ごろ (犂・牛のころ) から。
- **何に使ったか**: 「持ち物の差」の時期をくらべるところ。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part1_same_and_different.md`・`docs/society_phase/G7_design.md`・`docs/research/society2_periodization.md`・`docs/society_phase/part2.md`・`docs/society_phase/part3.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Flannery 2002〕

- **書誌**: Flannery, K. V. (2002). The Origins of the Village Revisited: From Nuclear to Extended Households. American Antiquity 67(3): 417–433.
- **DOI**: https://doi.org/10.2307/1593820
- **種類**: 論文
- **どんなものか**: みんなで分ける村から、家ごとに倉を持つ村へ変わった。
- **何に使ったか**: 家の倉・分け合いの読み (G4・part3)。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part3_humanness.md`・`docs/research/archaeological_evidence.md`・`docs/society_phase/G5_design.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G4.md`・`docs/society_phase/G6_design.md`・`sim/society/techtree/plan.json`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Englund 2011〕

- **書誌**: Englund, R. K. (2011). Accounting in Proto-Cuneiform. In K. Radner & E. Robson (Eds.), The Oxford Handbook of Cuneiform Culture (pp. 32–50). Oxford: Oxford University Press.
- **URL**: https://cdli.earth/files-up/publications/englund2011a.pdf
- **種類**: 本の章
- **どんなものか**: いちばん古い粘土板の文字は、ほとんどが帳簿だった (約 85%)。
- **何に使ったか**: 「記録は帳簿として生まれた」のくらべ (G6・part2)。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part2_technology.md`・`docs/research/historical_records.md`・`docs/research/economic_lenses.md`・`docs/society_phase/G6_design.md`・`docs/research/humanity/part1_same_and_different.md`・`docs/society_phase/G6.md`・`docs/society_phase/part4.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Schmandt-Besserat 1992〕

- **書誌**: Schmandt-Besserat, D. (1992). Before Writing, Vol. I: From Counting to Cuneiform. Austin: University of Texas Press.
- **種類**: 本
- **どんなものか**: 粘土の小さな数え札 (トークン) から、文字が生まれたという説。
- **何に使ったか**: G6 の「印・封・板」の設計とくらべ。この説には反論もある (Zimansky 1993 など、研究ノートの欄)。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/historical_records.md`・`docs/research/economic_lenses.md`・`docs/society_phase/G6_design.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json`

### ✓ 確かめた 〔Henrich ほか 2005〕

- **書誌**: Henrich, J., Boyd, R., Bowles, S., Camerer, C., Fehr, E., Gintis, H., McElreath, R., ほか (2005). “Economic man” in cross-cultural perspective: Behavioral experiments in 15 small-scale societies. Behavioral and Brain Sciences 28(6): 795–855.
- **種類**: 論文
- **どんなものか**: 15 の小さな社会で経済ゲーム (最後通牒など) をすると、答えは社会ごとに大きく違う。
- **何に使ったか**: 人とくらべる物差しの候補 (humanity README の 6.)。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **注**: humanity/README.md では【記憶】の印のままだが、論文 1 の refs.bib で確かめ済み。ページは 795–855 (795–815 ではない)。
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/README.md`・`docs/research/humanity/paper2_design_draft.md`・`sim/society/tools/research_dashboard_content.json`・`docs/research/humanity/part1_same_and_different.md`・`docs/research/humanity/part2_technology.md`・`docs/research/humanity/part3_humanness.md`

### ✓ 確かめた 〔Henrich ほか 2006〕

- **書誌**: Henrich, J., McElreath, R., Barr, A., ほか (2006). Costly Punishment Across Human Societies. Science 312(5781): 1767–1770.
- **種類**: 論文
- **どんなものか**: 15 の社会で、自分が損をしても不公平な人を罰する人は、どの社会にもいた (罰の強さは社会で違う)。
- **何に使ったか**: part3 で「人は損をしても罰する。村は 50 年から罰しない」のくらべ。
- **どう入ったか**: Claude の下地の知識 (part3 で【記憶】として書いた)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。Harvard の Henrich の研究室のページ (https://henrich.fas.harvard.edu/publications/costly-punishment-across-human-societies-0)・HRAF の記録
- **注**: part3_humanness.md では【記憶】の印のまま。論文 1 では引いていない。
- **使った所**: `docs/research/humanity/part3_humanness.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Bowles 2011〕

- **書誌**: Bowles, S. (2011). Cultivation of cereals by the first farmers was not more productive than foraging. PNAS 108(12): 4760–4765.
- **DOI**: https://doi.org/10.1073/pnas.1010733108
- **種類**: 論文
- **どんなものか**: 最初の麦作りは、採集より得ではなかった。
- **何に使ったか**: 村の食べ物が木の実ばかりだったことのくらべ。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part1_same_and_different.md`・`docs/research/economic_lenses.md`・`docs/society_phase/fidelity_checklist.md`

### ✓ 確かめた 〔Bocquet-Appel 2002〕

- **書誌**: Bocquet-Appel, J.-P. (2002). Paleoanthropological Traces of a Neolithic Demographic Transition. Current Anthropology 43(4): 637–650.
- **DOI**: https://doi.org/10.1086/342429
- **種類**: 論文
- **どんなものか**: 農耕が始まると、生まれる子が増えて人が増えた (墓の骨の年齢から)。
- **何に使ったか**: 村で人が増えたわけ (よそから来た人) とのくらべ。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part1_same_and_different.md`・`docs/research/archaeological_evidence.md`・`docs/research/historical_records.md`・`sim/society/techtree/plan.json`

### ✓ 確かめた 〔Boserup 1965〕

- **書誌**: Boserup, E. (1965). The Conditions of Agricultural Growth: The Economics of Agrarian Change under Population Pressure. London: Allen & Unwin.
- **種類**: 本
- **どんなものか**: 人が増えると、人はより手間のかかる作り方を始めて、食べ物を増やす。
- **何に使ったか**: 「村の人の増え方は、ボズラップでもマルサスでもない」の読み (part2・economic_lenses)。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part2_technology.md`・`docs/research/economic_lenses.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Malthus 1798〕

- **書誌**: [Malthus, T. R.] (1798). An Essay on the Principle of Population, as it affects the Future Improvement of Society, with remarks on the Speculations of Mr. Godwin, M. Condorcet, and Other Writers. London: J. Johnson. (はじめは名前なしで出た)
- **種類**: 本
- **どんなものか**: 人は食べ物より速く増えようとするので、ききんなどでおさえられる。
- **何に使ったか**: part2 で「村の人が減ったのは、人の多さで食べ物が足りなくなったから (マルサス) ではない」の読み。
- **どう入ったか**: Claude の下地の知識 (part2 で年を書かずに「マルサス」と書いた)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。Library of Economics and Liberty の 1798 年版 (https://www.econlib.org/library/Malthus/malPop.html)・図書館の目録
- **使った所**: `docs/research/humanity/part2_technology.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Ogburn & Thomas 1922〕

- **書誌**: Ogburn, W. F., & Thomas, D. (1922). Are Inventions Inevitable? A Note on Social Evolution. Political Science Quarterly 37(1): 83–98.
- **DOI**: https://doi.org/10.2307/2142320
- **種類**: 論文
- **どんなものか**: 同じ発明が、別々の人にほぼ同時に起きた例がたくさんある (前提がそろうと発明は起きる)。
- **何に使ったか**: 「前提がそろっても、この村では起きなかった」の読み (part2)。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part2_technology.md`・`docs/tech_tree_design_draft.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Keeley 1996〕

- **書誌**: Keeley, L. H. (1996). War Before Civilization: The Myth of the Peaceful Savage. New York: Oxford University Press.
- **種類**: 本
- **どんなものか**: 国より前の社会でも、争いで亡くなる人は多かった (議論あり)。
- **何に使ったか**: 「村では殺し・戦が 0」のくらべ (part3)。
- **どう入ったか**: Claude の研究ノートの調べ (ウェブ検索 2026-10-09〜10-23、または Claude の下地の知識) で入り、2026-10-29 に論文 1 の書誌として確かめた
- **確かめ**: ✓ 確かめた — 2026-10-29 に論文 1 の refs.bib を作るとき、手伝いの Claude がウェブ検索で書誌 (DOI・出版社・目録) と照らした (paper/paper1/README.md の記録)
- **使った所**: `paper/paper1/refs.bib`・`paper/paper1/main.tex`・`docs/research/humanity/part3_humanness.md`・`docs/society_phase/G7_design.md`・`sim/society/tools/research_dashboard_content.json`

### ✓ 確かめた 〔Renfrew ほか 1968〕

- **書誌**: Renfrew, C., Dixon, J. E., & Cann, J. R. (1968). Further analysis of Near Eastern obsidians. Proceedings of the Prehistoric Society 34: 319–331.
- **種類**: 論文
- **どんなものか**: 黒曜石は、産地から遠いほど少なくなりながら、町より前から遠くまで運ばれた。
- **何に使ったか**: part1 で「村が黒曜石だけを遠くに求めた」のくらべ・G6 の交換の設計。
- **どう入ったか**: Claude の調べ (G6 の設計、2026-10-09 のウェブ検索で要旨を確かめた)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。Cambridge Core のページ (https://www.cambridge.org/core/journals/proceedings-of-the-prehistoric-society/article/further-analysis-of-near-eastern-obsidians/D71852F4CB8471295062D6ECBB9CD018) と DAI の目録
- **注**: Cambridge Core では著作権の年が 1969 と出る (巻 34 はふつう 1968 年)。論文 1 では引いていない。
- **使った所**: `docs/research/humanity/part1_same_and_different.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/G6.md`・`docs/society_phase/part4.md`・`sim/society/techtree/plan.json`

### ✓ 確かめた 〔Goody 1977〕

- **書誌**: Goody, J. (1977). The Domestication of the Savage Mind. Cambridge: Cambridge University Press.
- **種類**: 本
- **どんなものか**: 文字 (とくに表やリスト) が、人の考え方を変えた。
- **何に使ったか**: part2 で、記録と考え方を考えるところ。
- **どう入ったか**: Claude の下地の知識 (part2 で【記憶】として書いた)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。Cambridge University Press のページ (https://www.cambridge.org/9780521292429) と書評の記録
- **注**: part2_technology.md では【記憶】の印のまま。
- **使った所**: `docs/research/humanity/part2_technology.md`

### ✓ 確かめた 〔Borgerhoff Mulder ほか 2009〕

- **書誌**: Borgerhoff Mulder, M., Bowles, S., Hertz, T., ほか (2009). Intergenerational wealth transmission and the dynamics of inequality in small-scale societies. Science 326: 682–688.
- **DOI**: https://doi.org/10.1126/science.1178336
- **種類**: 論文
- **どんなものか**: 牧畜・農耕の小さな社会は、家畜や土地が親から子へ渡るので、差が大きく続く。採集の社会は小さい。
- **何に使ったか**: 「本物の持ち物の差 (ジニ 0.4〜0.5 ほど)」のくらべ。
- **どう入ったか**: Claude の調べ (economic_lenses.md、2026-10-14 のウェブ検索)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。目録 (https://pure.psu.edu/en/publications/intergenerational-wealth-transmission-and-the-dynamics-of-inequal/)。書誌は合う
- **注**: ジニの平均「0.4〜0.5」の数は、本文が開けず確かめていない (【未確認】・【記憶】のまま)。
- **使った所**: `docs/research/economic_lenses.md`・`docs/research/humanity/part1_same_and_different.md`・`docs/research/humanity/README.md`・`docs/society_phase/fidelity_checklist.md`・`sim/society/tools/research_dashboard_content.json`

## ゲーム・道具・声

### ✓ 確かめた 〔Civilization (ゲーム)〕

- **書誌**: Sid Meier's Civilization シリーズ (1991〜。Civilization VI は 2016 年、Firaxis Games 作・2K 発売)。「Sid Meier's Civilization」「Civilization」「Civ」は Take-Two Interactive の商標。
- **URL**: https://2k.com/games/civilization/
- **種類**: ゲーム
- **どんなものか**: 国を育てる戦略ゲーム。研究を進めると、前提の矢印でつながった「技術の木」が開いていく。
- **何に使ったか**: テクノロジーツリーのページの考え方 (「テクノロジー」と「社会制度」の 2 本の木・前提の矢印) だけを借りた。ゲームの絵・アイコン・文・データは写していない (アイコンは make_tech_icons.py で自分で描いた)。
- **どう入ったか**: 本人の希望 (テクノロジーツリーを Civ VI のように 2 本の木にしたい、2026-10-28) と、Claude の調べ (docs/research/civilization_tech_tree.md、2026-10-07。ファンの wiki などの検索結果の要約を使った)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。持ち主は Wikipedia の記事 (https://en.wikipedia.org/wiki/Civilization_(series)) と 2K のページ
- **注**: 商標は持ち主のもの。このプロジェクトはゲームの会社とは関係がない。
- **使った所**: `docs/research/civilization_tech_tree.md`・`docs/tech_tree.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json`・`sim/society/app/tech_tree.html`

### ✓ 確かめた 〔VOICEVOX:ずんだもん〕

- **書誌**: VOICEVOX (無料の読み上げソフト、https://voicevox.hiroshiba.jp/) の声「ずんだもん」。クレジット: VOICEVOX:ずんだもん
- **URL**: https://zunko.jp/con_ongen_kiyaku.html
- **種類**: 声 (読み上げソフト)
- **どんなものか**: 文を声にするソフトと、そのキャラクターの声。
- **何に使ったか**: 村の動画・ロボットの動画のナレーション。
- **どう入ったか**: 本人の決め (動画のナレーション)。tools/voicevox/setup.sh が公式の配布元から取ってくる (リポジトリには入れていない)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。ずんだもんの音源利用ガイドライン (https://zunko.jp/con_ongen_kiyaku.html): 商用・非商用とも使える、クレジット「VOICEVOX:ずんだもん」が要る
- **注**: 作った声と、声の入った動画は MIT ライセンスの外 (README の「音声」)。
- **使った所**: `README.md`・`docs/compliance_check.md`・`tools/voicevox/`

### ✓ 確かめた 〔three.js〕

- **書誌**: three.js (JavaScript の 3D の道具)。MIT License。Copyright © 2010-2026 three.js authors
- **URL**: https://threejs.org/
- **種類**: ソフト
- **どんなものか**: ブラウザで 3D を描く道具。
- **何に使ったか**: 村のアプリ (sim/society/app/index.html は CDN の r128)・ロボットのシミュレータ (web/dist に同梱)。
- **どう入ったか**: プロジェクトで選んだ道具 (ロボットのシミュレータ・村のアプリの 3D)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。ライセンスの文 (https://github.com/mrdoob/three.js/blob/dev/LICENSE)
- **使った所**: `sim/society/app/index.html`・`web/package.json`・`web/THIRD_PARTY_LICENSES.txt`

### ✓ 確かめた 〔Rapier〕

- **書誌**: Rapier (@dimforge/rapier3d-compat、物理エンジン)。Apache License 2.0
- **URL**: https://rapier.rs/
- **種類**: ソフト
- **どんなものか**: 物がぶつかる・倒れるなどを計算する道具。
- **何に使ったか**: ロボットのシミュレータ (web/dist に同梱)。研究ダッシュボードでは使っていない。
- **どう入ったか**: プロジェクトで選んだ道具 (ロボットのシミュレータ)
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。ライセンスの文 (https://github.com/dimforge/rapier.js/blob/master/LICENSE)
- **使った所**: `web/package.json`・`web/THIRD_PARTY_LICENSES.txt`

### ✓ 確かめた 〔Zen Kaku Gothic New〕

- **書誌**: Zen Kaku Gothic New (デザイン: Yoshimichi Ohira)。SIL Open Font License 1.1。Google Fonts から読み込む (リポジトリには入れていない)
- **URL**: https://fonts.google.com/specimen/Zen+Kaku+Gothic+New
- **種類**: フォント
- **どんなものか**: 日本語の字の形。
- **何に使ったか**: 研究ダッシュボード (research.html)・村の跡のダッシュボード・村のアプリの字。
- **どう入ったか**: ページを作るとき Claude が選んだ
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。Google Fonts の記録 (https://github.com/google/fonts/tree/main/ofl/zenkakugothicnew の METADATA.pb: license OFL)
- **使った所**: `sim/society/app/research.html`・`sim/society/tools/build_research_dashboard.py`

### ✓ 確かめた 〔Dela Gothic One〕

- **書誌**: Dela Gothic One (デザイン: artakana)。SIL Open Font License 1.1。Google Fonts から読み込む (リポジトリには入れていない)
- **URL**: https://fonts.google.com/specimen/Dela+Gothic+One
- **種類**: フォント
- **どんなものか**: 日本語の字の形。
- **何に使ったか**: 見出しの太い字 (docs/humanity・村のアプリ)。
- **どう入ったか**: ページを作るとき Claude が選んだ
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。Google Fonts の記録 (https://github.com/google/fonts/tree/main/ofl/delagothicone の METADATA.pb: license OFL)
- **使った所**: `docs/humanity/index.html`・`sim/society/app/index.html`

### ✓ 確かめた 〔Shippori Mincho〕

- **書誌**: Shippori Mincho (デザイン: FONTDASU)。SIL Open Font License 1.1。Google Fonts から読み込む (リポジトリには入れていない)
- **URL**: https://fonts.google.com/specimen/Shippori+Mincho
- **種類**: フォント
- **どんなものか**: 日本語の字の形。
- **何に使ったか**: 明朝の字 (docs/humanity・村のアプリ)。
- **どう入ったか**: ページを作るとき Claude が選んだ
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。Google Fonts の記録 (https://github.com/google/fonts/tree/main/ofl/shipporimincho の METADATA.pb: license OFL)
- **使った所**: `docs/humanity/index.html`・`sim/society/app/index.html`

### ✓ 確かめた 〔Playwright〕

- **書誌**: Playwright (playwright-core、ブラウザを動かす道具。Microsoft)。Apache License 2.0
- **URL**: https://playwright.dev/
- **種類**: ソフト
- **どんなものか**: ブラウザを自動で動かして、画面の写真をとる。
- **何に使ったか**: ページのスクリーンショット (docs/media/research_dashboard*.png など)・アイコンの確かめ。リポジトリには入れていない。
- **どう入ったか**: プロジェクトで選んだ開発の道具
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。ライセンスの文 (https://github.com/microsoft/playwright/blob/main/LICENSE)
- **使った所**: `web/package.json`・`docs/tech_tree.md`・`docs/media/`

### ✓ 確かめた 〔matplotlib〕

- **書誌**: matplotlib (Python の図の道具)。matplotlib License (PSF 型)
- **URL**: https://matplotlib.org/
- **種類**: ソフト
- **どんなものか**: 数から図を描く。
- **何に使ったか**: 論文 1・2 の図・part2 の図 4 枚・実験 2 の図。
- **どう入ったか**: プロジェクトで選んだ道具
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。ライセンスの文 (https://github.com/matplotlib/matplotlib/blob/main/LICENSE/LICENSE)
- **使った所**: `paper/paper1/figures/make_figures.py`・`paper/paper2/figures/make_figures.py`・`sim/society/tools/survey/analyze.py`

### ✓ 確かめた 〔NumPy〕

- **書誌**: NumPy (Python の数の計算の道具)。BSD 3-Clause License。Copyright (c) 2005-2025, NumPy Developers
- **URL**: https://numpy.org/
- **種類**: ソフト
- **どんなものか**: 表の数の計算 (主成分・区間など)。
- **何に使ったか**: 論文 2 の実験の分析 (主成分・ブートストラップ)。
- **どう入ったか**: プロジェクトで選んだ道具
- **確かめ**: ✓ 確かめた — 2026-10-30 に Claude がウェブ検索で確かめた。ライセンスの文 (https://github.com/numpy/numpy/blob/main/LICENSE.txt)
- **使った所**: `sim/society/tools/survey/analyze.py`

## 使った AI

### ✗ 確かめていない 〔Claude (村人と答え手)〕

- **書誌**: Anthropic の Claude のモデル (Claude Haiku・Claude Sonnet・Claude Opus)。呼び名 (haiku・sonnet・opus) で呼んだ。その日の版は、1 回ごとには記録していない。
- **種類**: AI モデル
- **どんなものか**: 文を読んで答えを書く AI。
- **何に使ったか**: 村の大人の答え (初めは Haiku。62 年から代表は Sonnet、8 人に 1 人ほど Opus、気持ちは Haiku)・論文 2 の答え手 520 人・国の研究 B・C。
- **どう入ったか**: プロジェクトの作り (Claude Code のワークフローから呼んだ)
- **確かめ**: ✗ 確かめていない — どの版だったかは記録がない (論文 1 の TODO 3・論文 2 の TODO 4)。62 年からの答えは models.json に呼び名を残した
- **使った所**: `paper/paper1/main.tex`・`paper/paper2/main.tex`・`docs/research/humanity/paper2_exp1_prereg.md`・`sim/society/HANDOFF.md`

### ✗ 確かめていない 〔Claude (書く手伝い)〕

- **書誌**: Anthropic の Claude (Claude Code の中で動く)。研究ノート・設計書・コード・論文の下書き・訳・このページを書いた。
- **種類**: AI モデル (書く手伝い)
- **どんなものか**: 文を書く AI。
- **何に使ったか**: 研究ノート・論文の下書き・英訳 (54 問の英訳は確かめていない)・このページ。【記憶】と書いたものは Claude の記憶だけで、確かめていないもの。
- **どう入ったか**: プロジェクトの作り。文書の始めに「書いたのは Claude (日付)」と書いてある
- **確かめ**: ✗ 確かめていない — モデルの版は文書ごとには記録していない。書いた中身の確かさは、それぞれの文書の印 (【文献】【記憶】【未確認】など) とこの一覧で示す
- **使った所**: `docs/research/`・`docs/society_phase/`・`paper/`・`sim/society/tools/`

## 研究ノートの文献 (機械で集めた。みな ✗ 確かめていない)

研究ノート (`docs/research/`・`docs/society_phase/`・`docs/tech_tree*.md`・`sim/society/techtree/plan.json`) が文献の欄に書いた行と、本文に名前と年だけが出てくるものです。文はノートのまま写しました。上の手で書いた一覧と同じものは、上にまとめました。

どう入ったか (文献の欄ごと):

- `docs/research/archaeological_evidence.md` の「8. 出典」: Claude がウェブ検索で調べた (2026-10-09。同じ日に別の目で確かめなおした)。論文の多くは開けず、要旨・目録・大学の発表・報道で読んだ
- `docs/research/historical_records.md` の「7. 出典」: Claude がウェブ検索で調べた (2026-10-09)。元の本や論文の多くは開けず、紹介文・目録・まとめから書いた
- `docs/research/economic_lenses.md` の「8. 参考文献」: Claude がウェブ検索で調べた (2026-10-14)。多くは要旨か紹介で読んだ
- `docs/research/modern_records.md` の「8.2 出典一覧」: Claude がウェブ検索で調べた (2026-10-09)。「(一般知識)」とあるものは確かめなおしていない
- `docs/research/society2_periodization.md` の「6. 主な出典」: Claude がウェブ検索で調べた (2026-10-08)。検索の上限のため、いくつかは記憶だけ
- `docs/research/civilization_tech_tree.md` の「6. 参考」: Claude がウェブ検索で調べた (2026-10-07)。ページは開けず、検索結果の要約を使った
- `docs/society_phase/G6_design.md` の「23. Literature」: Claude がウェブ検索で調べた (2026-10-09)。全文の多くは開けず、要旨・出版社の記録・書評で照らした
- `docs/society_phase/G7_design.md` の「9. 参考文献」: Claude の調べ (2026-10-16)。計画書 docs/society2_extension_plan.md の文献から。紹介だけ読んだものは【記憶】
- `docs/tech_tree_design_draft.md` の「出典 (主なもの)」: Claude がウェブ検索で調べた (2026-10-09)
- 名前と年だけのもの: 研究ノートの本文 (Claude の下地の知識か、その文書の調べ)。書誌の行がないので、書誌は書いていない

| # | 名前 | 書誌 (ノートのまま) | 印 | 使った所 |
|---|---|---|---|---|
| 1 | [10] York 大学 Gregory King | [10] York 大学 Gregory King: https://www.york.ac.uk/depts/maths/histstat/king.htm | ✗  | `docs/research/modern_records.md` |
| 2 | [11] Britannica "baojia" | [11] Britannica "baojia": https://www.britannica.com/topic/baojia | ✗  | `docs/research/modern_records.md` |
| 3 | [12] ウメオ大学 TABVERK | [12] ウメオ大学 TABVERK: https://www.umu.se/en/centre-for-demographic-and-ageing-research/databases/tabverk / スウェーデン統計局の歴史: https://scb.se/en/About-us/main-activity/history-of-statistics-sweden | ✗  | `docs/research/modern_records.md` |
| 4 | [13] アメリカ国勢調査局 1790 年の質問 | [13] アメリカ国勢調査局 1790 年の質問: https://www.census.gov/programs-surveys/decennial-census/technical-documentation/questionnaires/1790.html | ✗  | `docs/research/modern_records.md` |
| 5 | [14] INED「民事婚の 200 年」 | [14] INED「民事婚の 200 年」: https://www.ined.fr/fr/publications/editions/population-et-societes/le-bicentenaire-du-mariage-civil/ | ✗  | `docs/research/modern_records.md` |
| 6 | [15] The Gazette | [15] The Gazette (1800 年の人口法): https://www.thegazette.co.uk/all-notices/content/162 | ✗  | `docs/research/modern_records.md` |
| 7 | [16] Britannica | [16] Britannica (Quetelet): https://britannica.com/print/article/487148 / Encyclopedia of Mathematics: https://encyclopediaofmath.org/wiki/Quetelet,_Adolphe | ✗  | `docs/research/modern_records.md` |
| 8 | [17] グロスターシャー公文書館 GRO 索引 | [17] グロスターシャー公文書館 GRO 索引: https://www.gloucestershire.gov.uk/archives/researching/search-by-theme/using-the-archive/general-register-office-index / 国連 IIVRS paper 55: https://unstats.un.org/unsd/demographic-social/crvs/documents/IIVRS_papers/IIVRS_paper55.pdf | ✗  | `docs/research/modern_records.md` |
| 9 | [18] ケンブリッジ大学 Campop | [18] ケンブリッジ大学 Campop: https://www.campop.geog.cam.ac.uk/research/projects/gendertimeuse/ / Wikipedia "Engel's law": https://en.wikipedia.org/wiki/Engel%27s_law / ボン大学: https://www.wiwi.uni-bonn.de/bgsepapers/old%20series/bonedp/bgse22_2009.pdf | ✗  | `docs/research/modern_records.md` |
| 10 | [19] リーハイ大学 Nightingale | [19] リーハイ大学 Nightingale: https://exhibits.lib.lehigh.edu/exhibits/show/data_visualization/science/nightingale | ✗  | `docs/research/modern_records.md` |
| 11 | [1] 英国国立公文書館 Domesday Book | [1] 英国国立公文書館 Domesday Book: https://www.nationalarchives.gov.uk/help-with-your-research/research-guides/domesday-book/ | ✗  | `docs/research/modern_records.md` |
| 12 | [20] 総務省統計局『統計 150 年のあゆみ』 | [20] 総務省統計局『統計 150 年のあゆみ』: https://www.stat.go.jp/museum/toukei150/ayumi/pdf/ayumi_all.pdf | ✗  | `docs/research/modern_records.md` |
| 13 | [21] コトバンク「壬申戸籍」 | [21] コトバンク「壬申戸籍」: https://kotobank.jp/word/%E5%A3%AC%E7%94%B3%E6%88%B8%E7%B1%8D-82002 / 参議院 第 219 回国会 答弁書 75 号 | ✗  | `docs/research/modern_records.md` |
| 14 | [22] 一橋大学附属図書館 | [22] 一橋大学附属図書館: https://www.lib.hit-u.ac.jp/images/2020/01/kikaku2003_pamphlet.pdf | ✗  | `docs/research/modern_records.md` |
| 15 | [23] エディンバラ大学 SW100 | [23] エディンバラ大学 SW100: https://sw100.ed.ac.uk/node/155 | ✗  | `docs/research/modern_records.md` |
| 16 | [24] アメリカ国勢調査局 Hollerith | [24] アメリカ国勢調査局 Hollerith: https://www.census.gov/about/history/bureau-history/census-innovations/technology/hollerith-machine.html / 集計の歴史: https://www.census.gov/about/history/bureau-history/census-innovations/technology/tabulation-and-processing.html | ✗  | `docs/research/modern_records.md` |
| 17 | [25] 厚生労働省 人口動態統計 | [25] 厚生労働省 人口動態統計: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/houkoku24/dl/all.pdf | ✗  | `docs/research/modern_records.md` |
| 18 | [26] プレジデント | [26] プレジデント (羽仁もと子の家計簿): https://president.jp/articles/-/20873 | ✗  | `docs/research/modern_records.md` |
| 19 | [27] 国立国会図書館 農家経済調査 | [27] 国立国会図書館 農家経済調査: https://ndlsearch.ndl.go.jp/en/books/R100000039-I976139 | ✗  | `docs/research/modern_records.md` |
| 20 | [28] アメリカ労働統計局 CPI の歴史 | [28] アメリカ労働統計局 CPI の歴史: https://www.bls.gov/opub/hom/cpi/history.htm | ✗  | `docs/research/modern_records.md` |
| 21 | [29] 総務省統計局 国勢調査の解説 | [29] 総務省統計局 国勢調査の解説: https://www.stat.go.jp/data/kokusei/pdf/kaisetu1.pdf / https://www.stat.go.jp/english/data/kokusei/2005/nihon/pdf/r02.pdf | ✗  | `docs/research/modern_records.md` |
| 22 | [2] カンザス大学図書館 Pacioli | [2] カンザス大学図書館 Pacioli: https://exhibits.lib.ku.edu/exhibits/show/keeping-the-books--the-rubinst/under-the-tuscan-sum---the-ita | ✗  | `docs/research/modern_records.md` |
| 23 | [30] 労働政策研究・研修機構 家計調査 | [30] 労働政策研究・研修機構 家計調査: https://www.jil.go.jp/kokunai/statistics/shozai/html/k02.html / 総務省統計局 家計調査: https://www.stat.go.jp/data/kakei/1.html | ✗  | `docs/research/modern_records.md` |
| 24 | [31] FRASER "National Income, 1929-1932" | [31] FRASER "National Income, 1929-1932": https://fraser.stlouisfed.org/title/national-income-1929-1932-971 / BEA: https://apps.bea.gov/scb/issues/2020/08-august/0820-influencer-kuznets.htm | ✗  | `docs/research/modern_records.md` |
| 25 | [32] アメリカ社会保障局 SSN の年表 | [32] アメリカ社会保障局 SSN の年表: https://www.ssa.gov/history/ssn/ssnchron.html | ✗  | `docs/research/modern_records.md` |
| 26 | [33] アメリカ国勢調査局 CPS の歴史 | [33] アメリカ国勢調査局 CPS の歴史: https://www.census.gov/programs-surveys/cps/about/history-of-the-cps.html / BLS: https://www.bls.gov/opub/hom/cps/history.htm | ✗  | `docs/research/modern_records.md` |
| 27 | [34] Meade と Stone の表 | [34] Meade と Stone の表: https://copsmodels.com/webhelp/viewhar/hc_stone1.htm / ノーベル賞 Stone: https://www.nobelprize.org/prizes/economic-sciences/1984/stone/biographical/ | ✗  | `docs/research/modern_records.md` |
| 28 | [35] 総務省統計局 FAQ | [35] 総務省統計局 FAQ (生活時間): https://www.stat.go.jp/library/faq/faq23/faq23e02.html | ✗  | `docs/research/modern_records.md` |
| 29 | [37] 労働政策研究・研修機構 労働力調査 | [37] 労働政策研究・研修機構 労働力調査: https://www.jil.go.jp/kokunai/statistics/shozai/html/r25.html / 総務省統計局 消費者物価指数の解説: https://www.stat.go.jp/data/cpi/2025/kaisetsu/pdf/6.pdf / 国立国会図書館 (日銀の東京小売物価): https://ndlsearch.ndl.go.jp/rnavi/business/post_102809 | ✗  | `docs/research/modern_records.md` |
| 30 | [38] スウェーデン税務庁 人口登録の歴史 | [38] スウェーデン税務庁 人口登録の歴史: https://www.skatteverket.se/privat/folkbokforing/attvarafolkbokford/folkbokforingenshistoria.4.18e1b10334ebe8bc80003006.html / スウェーデン統計局 "Personal identity number" (2016:1) | ✗  | `docs/research/modern_records.md` |
| 31 | [39] 名古屋大学 JAHIS 戸籍法 | [39] 名古屋大学 JAHIS 戸籍法: https://jahis.law.nagoya-u.ac.jp/lawdb/l/322a0224/compare/322a0224en | ✗  | `docs/research/modern_records.md` |
| 32 | [3] Wikipedia "Parish register" | [3] Wikipedia "Parish register": https://en.wikipedia.org/wiki/Parish_register | ✗  | `docs/research/modern_records.md` |
| 33 | [40] アメリカ国勢調査局 UNIVAC I | [40] アメリカ国勢調査局 UNIVAC I: https://www.census.gov/about/history/bureau-history/census-innovations/technology/univac-i.html | ✗  | `docs/research/modern_records.md` |
| 34 | [42] 総務省統計局 統計 150 年の年表 | [42] 総務省統計局 統計 150 年の年表 (昭和): https://www.stat.go.jp/museum/toukei150/img/nenpyo/pdf/nenpyo_showa.pdf | ✗  | `docs/research/modern_records.md` |
| 35 | [43] 九州大学 衛生・公衆衛生学 | [43] 九州大学 衛生・公衆衛生学: https://eph.med.kyushu-u.ac.jp/ | ✗  | `docs/research/modern_records.md` |
| 36 | [44] デンマーク統計局 CPR 50 年 | [44] デンマーク統計局 CPR 50 年: https://www.dst.dk/da/presse/rigsstat-klumme/2018/2018-03-27-det-lille-nummer-gor-en-stor-forskel / デンマーク統計局の歴史: https://www.dst.dk/pubfile/3854/history / 国連 CRVS (ノルウェー・フィンランド) | ✗  | `docs/research/modern_records.md` |
| 37 | [45] Encyclopedia.com "Social Indicators" | [45] Encyclopedia.com "Social Indicators": https://www.encyclopedia.com/social-sciences/encyclopedias-almanacs-transcripts-and-maps/social-indicators / ニッセイ基礎研究所: https://www.nli-research.co.jp/files/topics/38839_ext_18_0.pdf?site=nli | ✗  | `docs/research/modern_records.md` |
| 38 | [46] 盛岡市 | [46] 盛岡市: https://www.city.morioka.iwate.jp/_res/projects/default_project/_page_/001/011/132/0202.pdf / 総務省 住民基本台帳事務処理要領: https://www.soumu.go.jp/main_content/001077702.pdf | ✗  | `docs/research/modern_records.md` |
| 39 | [47] ICPSR 37142 | [47] ICPSR 37142 (PSID): https://www.icpsr.umich.edu/web/ICPSR/studies/37142 | ✗  | `docs/research/modern_records.md` |
| 40 | [49] 総務省統計局 社会生活基本調査 | [49] 総務省統計局 社会生活基本調査: https://www.stat.go.jp/data/shakai/2016/kekka.html / https://www.stat.go.jp/data/shakai/2021/gaiyou.html / e-Stat: https://www.e-stat.go.jp/surveyitems/items/367010239 | ✗  | `docs/research/modern_records.md` |
| 41 | [4] PGSA "History of Polish church records" | [4] PGSA "History of Polish church records": https://pgsa.org/history-of-polish-church-records/ | ✗  | `docs/research/modern_records.md` |
| 42 | [50] 大阪府 SNA への対応 | [50] 大阪府 SNA への対応: https://www.pref.osaka.lg.jp/o040090/toukei/gdp/taiou.html / 内閣府 経済社会総合研究所: https://www.esri.cao.go.jp/jp/sna/data/data_list/kakuhou/files/rekishi/sna_top.html | ✗  | `docs/research/modern_records.md` |
| 43 | [51] ノルウェー統計局 | [51] ノルウェー統計局: https://www.ssb.no/en/befolkning/artikler-og-publikasjoner/different-methods-comparable-results / Statistical Journal of the IAOS: https://content.iospress.com/articles/statistical-journal-of-the-iaos/sji00798 / スウェーデン 2011 年 (ASA 2012): https://ww2.amstat.org/meetings/proceedings/2012/data/assets/pdf/303749_77679.pdf | ✗  | `docs/research/modern_records.md` |
| 44 | [52] ILOSTAT "Forms of work" | [52] ILOSTAT "Forms of work": https://ilostat.ilo.org/methods/concepts-and-definitions/forms-of-work/ | ✗  | `docs/research/modern_records.md` |
| 45 | [53] Wikipedia "Human Development Report" | [53] Wikipedia "Human Development Report": https://en.wikipedia.org/wiki/Human_Development_Report | ✗  | `docs/research/modern_records.md` |
| 46 | [54] 慶應義塾大学 パネルデータ設計・解析センター | [54] 慶應義塾大学 パネルデータ設計・解析センター: https://www.pdrc.keio.ac.jp/en/?p=5028 / https://www.pdrc.keio.ac.jp/en/?p=205 | ✗  | `docs/research/modern_records.md` |
| 47 | [55] 国連統計部 公的統計の基本原則 | [55] 国連統計部 公的統計の基本原則: https://unstats.un.org/unsd/dnss/hb/E-fundamental%20principles_A4-WEB.pdf | ✗  | `docs/research/modern_records.md` |
| 48 | [56] 法務省 | [56] 法務省: https://www.moj.go.jp/content/001271597.pdf | ✗  | `docs/research/modern_records.md` |
| 49 | [57] 厚生労働省 | [57] 厚生労働省: https://www.mhlw.go.jp/shingi/2004/07/s0729-6a.html | ✗  | `docs/research/modern_records.md` |
| 50 | [58] UN SDG | [58] UN SDG:Learn: https://www.unsdglearn.org/blog/navigating-progress-towards-sustainable-development-the-crucial-role-of-the-iaeg-sdgs-and-the-global-indicator-framework/ / 国連 SDG 指標一覧: https://unstats.un.org/sdgs/indicators/indicators-list/ | ✗  | `docs/research/modern_records.md` |
| 51 | [59] Data Privacy Lab | [59] Data Privacy Lab: https://dataprivacylab.org/projects/identifiability/ | ✗  | `docs/research/modern_records.md` |
| 52 | [5] Britannica "John Graunt" | [5] Britannica "John Graunt": https://www.britannica.com/biography/John-Graunt / Encyclopedia of Mathematics: https://encyclopediaofmath.org/wiki/Graunt,_John | ✗  | `docs/research/modern_records.md` |
| 53 | [60] 文部科学省 21 世紀出生児縦断調査 | [60] 文部科学省 21 世紀出生児縦断調査: https://www.mext.go.jp/b_menu/toukei/chousa08/21seiki/ | ✗  | `docs/research/modern_records.md` |
| 54 | [61] 栃木県 住基ネット | [61] 栃木県 住基ネット: https://www.pref.tochigi.lg.jp/a02/pref/shichouson/jinjigyousei/juki-net.html / 箕面市: https://www.city.minoh.lg.jp/simin/juuki/juuki_net/juukicode.html | ✗  | `docs/research/modern_records.md` |
| 55 | [62] 個人情報保護委員会 | [62] 個人情報保護委員会: https://www.ppc.go.jp/ / 日本法令外国語訳: https://www.japaneselawtranslation.go.jp/ja/laws/view/4241 | ✗  | `docs/research/modern_records.md` |
| 56 | [63] NCI Cohort Consortium | [63] NCI Cohort Consortium (UK Biobank): https://epi.grants.cancer.gov/cohort-consortium/members/ukb.html | ✗  | `docs/research/modern_records.md` |
| 57 | [64] 総務省 統計法 | [64] 総務省 統計法: https://www.soumu.go.jp/main_content/000339382.pdf | ✗  | `docs/research/modern_records.md` |
| 58 | [65] MIT Press "Hacking Life" | [65] MIT Press "Hacking Life": https://hackinglife.mitpress.mit.edu/pub/razodglh | ✗  | `docs/research/modern_records.md` |
| 59 | [66] e-Stat ヘルプ | [66] e-Stat ヘルプ: https://www.e-stat.go.jp/help/e-Stat-1-2 | ✗  | `docs/research/modern_records.md` |
| 60 | [67] ESDN | [67] ESDN (スティグリッツ・セン・フィトゥシの勧め): https://www.esdn.eu/fileadmin/pdf/Workshops/6th_Workshop_2010/Presentations/12_Stiglitz-Sen-Fitoussi_Commission_Recommendations.pdf | ✗  | `docs/research/modern_records.md` |
| 61 | [68] Wikipedia "OECD Better Life Index" | [68] Wikipedia "OECD Better Life Index": https://en.wikipedia.org/wiki/OECD_Better_Life_Index / OECD "How's Life? 2013" 1 章 | ✗  | `docs/research/modern_records.md` |
| 62 | [69] TechCrunch・Engadget の 2014 年 6 月 2 日 WWDC の記事 | [69] TechCrunch・Engadget の 2014 年 6 月 2 日 WWDC の記事 | ✗  | `docs/research/modern_records.md` |
| 63 | [6] Korea Journal 47-2 | [6] Korea Journal 47-2: https://accesson.kr/kj/assets/pdf/8149/journal-47-2-99.pdf | ✗  | `docs/research/modern_records.md` |
| 64 | [70] KPMG | [70] KPMG (マイナンバー制度): https://assets.kpmg.com/content/dam/kpmg/pdf/2016/03/jp-my-number-system.pdf / 目黒区: https://www.city.meguro.tokyo.jp/koseki/kurashi/mynumber/mynumber_nagare.html | ✗  | `docs/research/modern_records.md` |
| 65 | [71] EUR-Lex GDPR | [71] EUR-Lex GDPR: https://eur-lex.europa.eu/eli/reg/2016/679/oj | ✗  | `docs/research/modern_records.md` |
| 66 | [72] 総務省 報道資料 | [72] 総務省 報道資料 (統計ダッシュボード): https://www.soumu.go.jp/menu_news/s-news/01toukei09_01000024.html | ✗  | `docs/research/modern_records.md` |
| 67 | [73] 内閣府 満足度・生活の質に関する調査 | [73] 内閣府 満足度・生活の質に関する調査: https://www5.cao.go.jp/keizai2/wellbeing/manzoku/ | ✗  | `docs/research/modern_records.md` |
| 68 | [75] 総務省資料 | [75] 総務省資料 (東京都の新型コロナ対策サイト): https://www.soumu.go.jp/main_content/000680542.pdf | ✗  | `docs/research/modern_records.md` |
| 69 | [77] 国連 2025 SNA | [77] 国連 2025 SNA: https://unstats.un.org/unsd/nationalaccount/sna2025.asp / 32 章 (草案): https://unstats.un.org/unsd/nationalaccount/SNAUpdate/2025/2025SNA_CH32_V5.pdf | ✗  | `docs/research/modern_records.md` |
| 70 | [79] MTUS の歴史 | [79] MTUS の歴史 (Szalai の調べ): https://www.timeuse.org/sites/default/files/9727/chapter-2-historical-development-of-the-mtus.pdf | ✗  | `docs/research/modern_records.md` |
| 71 | [7] 福井県文書館 | [7] 福井県文書館: https://www.library-archives.pref.fukui.lg.jp/bunsho/file/615718.pdf / コトバンク「宗門改」 | ✗  | `docs/research/modern_records.md` |
| 72 | [80] Open Government Directive | [80] Open Government Directive: https://obamawhitehouse.archives.gov/open/documents/open-government-directive | ✗  | `docs/research/modern_records.md` |
| 73 | [81] ONC Data Brief 2016 | [81] ONC Data Brief 2016: https://www.healthit.gov/sites/default/files/briefs/2015_hospital_adoption_db_v17.pdf | ✗  | `docs/research/modern_records.md` |
| 74 | [82] 内閣府 次世代医療基盤法 | [82] 内閣府 次世代医療基盤法: https://www8.cao.go.jp/iryou/ | ✗  | `docs/research/modern_records.md` |
| 75 | [83] 総務省 オープンデータ | [83] 総務省 オープンデータ: https://www.soumu.go.jp/menu_seisaku/ictseisaku/ictriyou/opendata/ / デジタル庁: https://www.digital.go.jp/resources/open_data | ✗  | `docs/research/modern_records.md` |
| 76 | [84] 総務省統計局 国勢調査の研究資料 | [84] 総務省統計局 国勢調査の研究資料: https://www.stat.go.jp/info/kenkyu/kokusei/ | ✗  | `docs/research/modern_records.md` |
| 77 | [85] SDG Transformation Center | [85] SDG Transformation Center (SDG Index 2016): https://www.sdgtransformationcenter.org/reports/sdg-index-2016 | ✗  | `docs/research/modern_records.md` |
| 78 | [86] Oxford Martin School | [86] Oxford Martin School (SDG Tracker): https://www.oxfordmartin.ox.ac.uk/news/sdg-tracker | ✗  | `docs/research/modern_records.md` |
| 79 | [87] パネル調査の追いかけの決まり | [87] パネル調査の追いかけの決まり: Survey Research Methods (2011) の論文、LISS パネルの説明書 | ✗  | `docs/research/modern_records.md` |
| 80 | [88] 見なおしの調べ | [88] 見なおしの調べ (2026-10-09) で使った資料: クズネッツ報告の原本 https://fraser.stlouisfed.org/title/national-income-1929-1932-971 と BEA の紹介 (200 以上の表) / ラウントリー https://en.wikipedia.org/wiki/Seebohm_Rowntree / トリエント公会議 第 24 総会 https://www.ewtn.com/catholicism/library/twentyfourth-session-of-the-council-of-trent-1491 / アメリカ 1850 年国勢調査 https://www.familysearch.org/en/blog/1850-united-states-census / イギリス 1851 年国勢調査 https://www.nationalarchives.gov.uk/education/resources/census-detective/source-1/ / ICD の歴史 (CDC) https://stacks.cdc.gov/view/cdc/65417/cdc_65417_DS1.pdf / ファー https://epsilon.ac.uk/view/dcp-data/nameregs/nameregs_1595 / 1837 年の 619 区 https://en.wikipedia.org/wiki/General_Register_Office_for_England_and_Wales / 1920 年国勢調査の世帯数 https://www.stat.go.jp/data/kokusei/2015/kouhou/ayumi.html / 東京小売物価指数 https://ndlsearch.ndl.go.jp/rnavi/business/post_102809 / 個人情報保護法の 2021 年改正の施行 https://www.ppc.go.jp/personalinfo/minaoshi / 2025 SNA 34 章 (草案) https://unstats.un.org/unsd/nationalaccount/snaupdate/2025/2025SNA_CH34_V11.pdf / スウェーデンの教区の帳簿からの国勢調査 (IPUMS) https://international.ipums.org/international-action/source_documents/enum_form_se1900a_tag.xml / 内閣府 Well-being ダッシュボード https://www5.cao.go.jp/keizai2/wellbeing/manzoku/index.html | ✗  | `docs/research/modern_records.md` |
| 81 | [8] Encyclopedia.com "William Petty" | [8] Encyclopedia.com "William Petty": https://www.encyclopedia.com/people/history/british-and-irish-history-biographies/william-petty | ✗  | `docs/research/modern_records.md` |
| 82 | [9] Lokalhistoriewiki "Husförhörslängd" | [9] Lokalhistoriewiki "Husförhörslängd": https://lokalhistoriewiki.no/wiki/Husförhörslängd / [38] の Skatteverket | ✗  | `docs/research/modern_records.md` |
| 83 | A New Classification of Technologies | A New Classification of Technologies（arXiv）: https://arxiv.org/pdf/1712.07711 | ✗  | `docs/research/civilization_tech_tree.md` |
| 84 | Abell 2019 | Abell, J. ほか 2019. Urine salts elucidate Early Neolithic animal management at Aşıklı Höyük, Turkey. *Science Advances*. | ✗  | `docs/research/archaeological_evidence.md` |
| 85 | Adams 1965 | Adams, R.McC. 1965. *Land Behind Baghdad*. / Adams & Nissen 1972. *The Uruk Countryside*. / Adams 1981. *Heartland of Cities*. | ✗  | `docs/research/historical_records.md` |
| 86 | Akkermans 1996 | Akkermans, P.M.M.G. & Duistermaat, K. 1996/97. Of storage and nomads. *Paléorient* 22(2). Duistermaat, K. 1996. The seals and sealings. In Akkermans (ed.) *Tell Sabi Abyad*. (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/historical_records.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/part2.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 87 | Aldeias 2016 | Aldeias, V. ほか 2016. How heat alters underlying deposits. *Journal of Archaeological Science*. | ✗  | `docs/research/archaeological_evidence.md` |
| 88 | AlQahtani 2010 | AlQahtani, S., Hector, M. & Liversidge, H. 2010. Brief communication: The London atlas of human tooth development and eruption. *American Journal of Physical Anthropology* 142. AlQahtani ほか 2014. *AJPA* 154 (1,506 人での確かめ). | ✗  | `docs/research/archaeological_evidence.md` |
| 89 | Alter 2014 | Alter, G. & Mandemakers, K. 2014. The Intermediate Data Structure (IDS) for longitudinal historical microdata, version 4. *Historical Life Course Studies* 1: 1–26. | ✗  | `docs/research/historical_records.md` |
| 90 | Andersson 2014 | Andersson, J. 2014. (ファラの売り買いの証文). *CDLB* 2014:1. https://cdli.earth/articles/cdlb/2014-1 | ✗  | `docs/research/historical_records.md` |
| 91 | Arnold 2025 | [78] EUR-Lex 32025R0327 / Arnold & Porter (2025 年 3 月): https://www.arnoldporter.com/en/perspectives/advisories/2025/03/european-health-data-space-regulation-published | ✗  | `docs/research/modern_records.md` |
| 92 | Arranz-Otaegui 2016 | 畑とヤギ: Arranz-Otaegui ほか 2016 (PNAS 113); Tanno & Willcox 2006 (Science); Zeder & Hesse 2000 (Science 287); Stiner ほか 2014・2022 (PNAS。アシュクル・ホユックのヒツジとヤギ) | ✗  | `docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 93 | Arranz-Otaegui 2018 | Arranz-Otaegui, A. ほか 2018. 'Founder crops' v. wild plants. *Quaternary Science Reviews*. https://joeroe.io/papers/2018/founder_crops_vs_wild_plants.html | ✗  | `docs/research/archaeological_evidence.md` |
| 94 | Arthur 2006 | Arthur, W. B. & Polak, W. (2006). The evolution of technology within a simple computer model. *Complexity* 11(5): 23–31. https://doi.org/10.1002/cplx.20130 | ✗  | `docs/research/civilization_tech_tree.md` |
| 95 | Asouti 2001 | Asouti, E. & Hather, J. 2001. Charcoal analysis in the Konya Basin. https://www.wikis.uni-kiel.de/archbotlit/doku.php/2001_asouti_hather_charcoal_analysis_and_the_reconstruction | ✗  | `docs/research/archaeological_evidence.md` |
| 96 | ASPRO chronology | ASPRO chronology: https://en.wikipedia.org/wiki/ASPRO_chronology | ✗  | `docs/research/society2_periodization.md` |
| 97 | Axelrod の貢ぎのモデル | Axelrod の貢ぎのモデル (SFI Working Paper 93-11-068) https://ideas.repec.org/p/wop/safiwp/93-11-068.html | ✗  | `docs/society_phase/G7_design.md` |
| 98 | Axelrod, Building New Political Actors | Axelrod, Building New Political Actors: https://public.websites.umich.edu/~axe/research/Building.pdf (批評でも開けなかった) | ✗  | `docs/society_phase/G7_design.md` |
| 99 | Balasse 2017 | Balasse, M. ほか 2017. Investigating seasonality and season of birth in past herds. *Animal*. https://discovery.ucl.ac.uk/id/eprint/10082380/ | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/historical_records.md` |
| 100 | Baldi 2016 | 回る台: Roux、Baldi & Roux 2016・2021【二次】 (ほかの書き方 1) | ✗  | `docs/society_phase/G7_design.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 101 | Balossi Restelli, F. | Balossi Restelli, F. (アルスランテペ神殿 C・D の鉢の紹介文、Sapienza): https://research.uniroma1.it/node/33887 | ✗  | `docs/research/historical_records.md` |
| 102 | Bandy 2004 | Bandy 2004, Am. Anthropol. 106 — fission size (G5) 【文献】; Stein 1994; Fried; Flannery 2002 (G5) 【文献】 (ほかの書き方 1) | ✗  | `docs/society_phase/G5_design.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/G7_design.md`・`docs/society_phase/part3.md` |
| 103 | Banning 1987 | Banning, E.B. & Byrd, B.F. 1987. Houses and the changing residential unit: domestic architecture at PPNB 'Ain Ghazal, Jordan. *Proceedings of the Prehistoric Society* 53. | ✗  | `docs/research/archaeological_evidence.md` |
| 104 | Bar-Yosef 1998 | Bar-Yosef, O. 1998. The Natufian culture in the Levant, threshold to the origins of agriculture. Evolutionary Anthropology 6:159-177 | ✗  | `docs/research/society2_periodization.md` |
| 105 | Bartash 2018 | Bartash, V. 2018. Age, gender and labor: recording human resources in 3350–2500 BC Mesopotamia. In *What's in a Name?* (AOAT 440), 45–80 (ページは【未確認】). / Bartash, V. 2015. Children in institutional households of Late Uruk period Mesopotamia. *ZA* 105: 131–138. | ✗ 【未確認】 | `docs/research/historical_records.md` |
| 106 | Baud 1995 | Baud, M. & Dobrev, V. 1995. *BIFAO* 95. | ✗  | `docs/research/historical_records.md` |
| 107 | Bayliss 2007 | Bayliss, A., Bronk Ramsey, C., van der Plicht, J. & Whittle, A. 2007. Bradshaw and Bayes: towards a timetable for the Neolithic. *Cambridge Archaeological Journal* 17(S1). | ✗  | `docs/research/archaeological_evidence.md` |
| 108 | Bayliss 2015 | Bayliss, A. ほか 2015. Getting to the bottom of it all: a Bayesian approach to dating the start of Çatalhöyük. *Journal of World Prehistory* 28. | ✗  | `docs/research/archaeological_evidence.md` |
| 109 | Belovsky 1987 | Belovsky 1987, Hunter-gatherer foraging: A linear programming approach (J. Anthropological Archaeology 6): https://doi.org/10.1016/0278-4165(87)90016-X | ✗  | `docs/research/economic_lenses.md` |
| 110 | Bennison-Chapman 2018 | Bennison-Chapman 2018, Levant 50(3):305– ("Clay objects as 'tokens'?", Tell Sabi Abyad: some contexts suggest counting/administration); 2019, Camb. Archaeol. J. 29(2):233– ("Reconsidering 'tokens'": tokens from the 10th millennium cal BC, mostly multifunctional) 【文献】 | ✗  | `docs/society_phase/G6_design.md` |
| 111 | Bennison-Chapman 2019 | Bennison-Chapman, L. 2019 (ネット公開 2018). Reconsidering 'tokens': the Neolithic origins of accounting or multifunctional, utilitarian tools? *Cambridge Archaeological Journal* 29(2): 233–. https://www.cambridge.org/core/product/7E6C04CB040AD8AA0EA84B94D4D275C4 (ほかの書き方 1) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G6_design.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 112 | Beyond Depression? 動物考古学と植物考古学の最適採餌理論の文献のまとめ | Beyond Depression? 動物考古学と植物考古学の最適採餌理論の文献のまとめ: https://ojs.ethnobiology.org/index.php/ebl/article/view/786 | ✗  | `docs/research/economic_lenses.md` |
| 113 | Bocquentin 2001 | Bocquentin, F., Sellier, P. & Murail, P. 2001. La population natoufienne de Mallaha (Eynan, Israël): dénombrement, âge au décès et recrutement funéraire. *Paléorient* 27(1): 89–106. | ✗  | `docs/research/archaeological_evidence.md` |
| 114 | Bocquentin 2020 | Bocquentin, F. ほか 2020. (ベイサムーンの火葬). *PLOS ONE* 15(8): e0235386. | ✗  | `docs/research/archaeological_evidence.md` |
| 115 | Bocquet-Appel 1982 | Bocquet-Appel, J.-P. & Masset, C. 1982. Farewell to paleodemography. *Journal of Human Evolution* 11: 321–333. | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/economic_lenses.md` |
| 116 | Bocquet-Appel 2006 | Bocquet-Appel & Naji 2006, Testing the hypothesis of a worldwide Neolithic demographic transition (Current Anthropology 47): https://www.journals.uchicago.edu/doi/reader/10.1086/497665 | ✗  | `docs/research/economic_lenses.md` |
| 117 | Bocquet-Appel 2011 | Bocquet-Appel 2011, The Agricultural Demographic Transition (Current Anthropology 52 S4)。「約 2 人」は【未確認】: https://www.journals.uchicago.edu/doi/10.1086/659243 (ほかの書き方 2) | ✗ 【未確認】 | `docs/research/archaeological_evidence.md`・`docs/research/economic_lenses.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G6_measures.md` |
| 118 | Bogaard 2009 | 家と道具で【未確認】のもの: テル・マドゥフルの家の広さ、ドゥラーの倉の数、DeBoer のシピボ・コニボの土器の寿命の数、チャタルヒュユクの居間の広さと家の倉 約 1,000 リットル (Bogaard ほか 2009 の 661 ページの値として、ほかの論文が引いている) (ほかの書き方 3) | ✗ 【未確認】 | `docs/research/archaeological_evidence.md`・`docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/research/society2_periodization.md` |
| 119 | Boldsen 2002 | Boldsen, J., Milner, G., Konigsberg, L. & Wood, J. 2002. Transition analysis. In Hoppa & Vaupel (eds) *Paleodemography*: 73–106. | ✗  | `docs/research/archaeological_evidence.md` |
| 120 | Boost | Boost (Civ6)（Fandom）: https://civilization.fandom.com/wiki/Boost_(Civ6) | ✗  | `docs/research/civilization_tech_tree.md` |
| 121 | Boserup, The Conditions of Agricultural Growth | Boserup, The Conditions of Agricultural Growth (Routledge): https://www.routledge.com/Conditions-of-Agricultural-Growth/Boserup/p/book/9781138878600 | ✗  | `docs/research/economic_lenses.md` |
| 122 | Brack-Bernsen 2007 | Brack-Bernsen, L. 2007. The 360-day year in Mesopotamia. In J.M. Steele (ed.), *Calendars and Years*, 83–100. Oxbow. https://epub.uni-regensburg.de/58013/1/31.the%20360%20day%20year.pdf | ✗  | `docs/research/historical_records.md` |
| 123 | Brak migration | Brak migration: a dental-morphology (not strontium) study of Late Chalcolithic Brak, J. Anthropol. Archaeol. (c. 2022; Sołtysiak and colleagues) — growth partly by migration, neighbourhoods by origin 【文献・二次】(press summary only). The earlier 「isotope study 2020, Archaeol. Anthropol. Sci., doi 10.1007/s12520-020-01104-3」 could not be found | ✗  | `docs/society_phase/G6_design.md` |
| 124 | Breu 2024 | Özbal, H., Breu, A., Thissen, L. ほか 2024. From bowls to pots: the dairying revolution in Northwest Turkey, a view from Barcın Höyük, 6600 to 6000 BCE. *PLOS ONE* 19(5): e0302788. | ✗  | `docs/research/archaeological_evidence.md` |
| 125 | Buikstra 1994 | Buikstra, J. & Ubelaker, D. 1994. *Standards for Data Collection from Human Skeletal Remains*. | ✗  | `docs/research/archaeological_evidence.md` |
| 126 | Byrd 1994 | Byrd, B.F. 1994. Public and private, domestic and corporate. *American Antiquity* 59(4): 639–666. | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/society2_periodization.md` |
| 127 | CADTM, メソポタミアとエジプトの借りの帳消し | CADTM, メソポタミアとエジプトの借りの帳消し (Hudson への注釈): https://www.cadtm.org/The-Long-Tradition-of-Debt | ✗  | `docs/research/economic_lenses.md` |
| 128 | Carter 2003 | Carter, E., Campbell, S. ほか 2003. Elusive complexity: new data from late Halaf Domuztepe in south central Turkey. *Paléorient* 29(2): 117–133. (ドムズテペの「死の穴」) | ✗  | `docs/research/archaeological_evidence.md` |
| 129 | Carter 2006 | Carter et al. 2006/2007/2008 — Çatalhöyük obsidian sources 【文献】 | ✗  | `docs/society_phase/G6_design.md` |
| 130 | Cederman 1997 | Cederman 1997 https://press.princeton.edu/node/25923 | ✗  | `docs/society_phase/G7_design.md` |
| 131 | Childe 1950 | Childe 1950, Town Planning Review 21:3–17 — urban revolution criteria 【文献】 | ✗  | `docs/society_phase/G6_design.md` |
| 132 | Chopra 2024 | Chopra ほか 2024 (原型) https://arxiv.org/abs/2409.10568 ([6]) | ✗  | `docs/society_phase/G7_design.md` |
| 133 | Chyleński, M. ほか 2019. *Genes* 10 | Chyleński, M. ほか 2019. *Genes* 10(3): 207. | ✗  | `docs/research/archaeological_evidence.md` |
| 134 | Civ 6 Tech Tree | Civ 6 Tech Tree（ファンのツール）: https://civilization6planner.com/en/tools/tech-tree | ✗  | `docs/research/civilization_tech_tree.md` |
| 135 | Civ IV の AND/OR 前提 | Civ IV の AND/OR 前提（CivFanatics フォーラム）: https://forums.civfanatics.com/threads/civ-iv-tech-tree-question.150010 | ✗  | `docs/research/civilization_tech_tree.md` |
| 136 | Civ V Technologies | Civ V Technologies（StrategyWiki）: https://strategywiki.org/wiki/Sid_Meier%27s_Civilization_V/Technologies | ✗  | `docs/research/civilization_tech_tree.md` |
| 137 | Civ VI Base Game Technology Tree | Civ VI Base Game Technology Tree（BBG）: https://civ6bbg.github.io/en_US/tech_tree_base_game.html | ✗  | `docs/research/civilization_tech_tree.md` |
| 138 | Civilisation Video game Review | Civilisation Video game Review: A Cultural Artefact of Eurocentrism?（Curieux）: https://www.curieux.com.au/opinion/civilisation-video-game-review-a-cultural-artefact-of-eurocentrism | ✗  | `docs/research/civilization_tech_tree.md` |
| 139 | Civilization | Civilization (1980 board game)（Wikipedia）: https://en.wikipedia.org/wiki/Civilization_(1980_board_game) | ✗  | `docs/research/civilization_tech_tree.md` |
| 140 | Civilization 6 Ancient Era | Civilization 6 Ancient Era（gamepressure）: https://www.gamepressure.com/sidmeierscivilization6/ancient-era/z092c2 | ✗  | `docs/research/civilization_tech_tree.md` |
| 141 | Civilization 7 technology tree | Civilization 7 technology tree（Dot Esports）: https://dotesports.com/civilization/news/civilization-7-technology-tree-all-techs-how-to-unlock-them | ✗  | `docs/research/civilization_tech_tree.md` |
| 142 | Civilization VI | Civilization VI: Technologies（CivFanatics）: https://civfanatics.com/civ6/info/technology/ | ✗  | `docs/research/civilization_tech_tree.md` |
| 143 | Civilization VI | Civilization VI: Civics（CivFanatics）: https://civfanatics.com/civ6/info/civic/ | ✗  | `docs/research/civilization_tech_tree.md` |
| 144 | Civilization VI Analyst | Civilization VI Analyst: Technology / Civics: https://www.well-of-souls.com/civ/civ6_technology.html , https://well-of-souls.com/civ/civ6_civics.html | ✗  | `docs/research/civilization_tech_tree.md` |
| 145 | Civilization VII Ages | Civilization VII Ages（CivFanatics）: https://civfanatics.com/civ7/civ-vii-gameplay-mechanics/civilization-vii-ages/ | ✗  | `docs/research/civilization_tech_tree.md` |
| 146 | Codd 1970 | [48] Codd 1970, CACM 13(6):377-387: https://web.eecs.umich.edu/~michjc/eecs584/Papers/codd_1970.pdf | ✗  | `docs/research/modern_records.md` |
| 147 | Colledge 2014 | Colledge, S. & Conolly, J. 2014. Wild plant use in European Neolithic subsistence economies: a formal assessment of preservation bias in archaeobotanical assemblages. *Quaternary Science Reviews* 101: 193–206. | ✗  | `docs/research/archaeological_evidence.md` |
| 148 | Cooper 1983 | Cooper, J. 1983. *Reconstructing History from Ancient Inscriptions*. (確かめていない) | ✗  | `docs/research/historical_records.md` |
| 149 | Craig 2012 | Craig, O. ほか 2012. Distinguishing wild ruminant lipids by GC-C-IRMS. *Rapid Communications in Mass Spectrometry*. | ✗  | `docs/research/archaeological_evidence.md` |
| 150 | Croucher 2012 | Croucher, K. 2012. *Death and Dying in the Neolithic Near East*. Oxford University Press. | ✗  | `docs/research/archaeological_evidence.md` |
| 151 | Cumulative culture | Cumulative culture（Open Encyclopedia of Cognitive Science, MIT）: https://oecs.mit.edu/pub/6bvu7f8m/release/1 | ✗  | `docs/research/civilization_tech_tree.md` |
| 152 | Currie 2010 | Currie ほか 2010 https://hraf.yale.edu/documents/1300 | ✗  | `docs/society_phase/G7_design.md` |
| 153 | Daly 2021 | Daly, K. ほか 2021. Herded and hunted goat genomes from the dawn of domestication in the Zagros Mountains. *PNAS* 118: e2100901118. コペンハーゲン大学の紹介 (ひづめの跡): https://humanities.ku.dk/news/2021/10000-year-old-bones-reveal-earliest-goat-herders-practices/ | ✗  | `docs/research/archaeological_evidence.md` |
| 154 | Damerow 2012 | Damerow, P. 2012. Sumerian beer. *CDLJ* 2012:2. | ✗  | `docs/research/historical_records.md` |
| 155 | Davidson 1976 | Davidson & McKerrell 1976, Iraq 38:45–56 (Khabur headwaters); 1980, Iraq 42:155–167 (neutron activation, Arpachiyah and Gawra) — Halaf pottery moved between sites 【文献】 | ✗  | `docs/society_phase/G6_design.md` |
| 156 | Davis 1978 | Davis, S. & Valla, F. 1978. Evidence for domestication of the dog 12,000 years ago in the Natufian of Israel. *Nature* 276: 608–610. | ✗  | `docs/research/archaeological_evidence.md` |
| 157 | DCCLT | DCCLT (古い言葉の表): https://oracc.museum.upenn.edu/dcclt/lexicallistsperiods/archaic/index.html | ✗  | `docs/research/historical_records.md` |
| 158 | de Ayala 1615 | Guaman Poma de Ayala, F. 1615. *Nueva corónica*. / Cieza de León, P. 1550. | ✗  | `docs/research/historical_records.md` |
| 159 | Demographic Research 49 巻 29 | Demographic Research 49 巻 29 (狩猟採集民と農耕民の TFR。二次の引用)【未確認】: https://www.demographic-research.org/articles/volume/49/29/letters | ✗ 【未確認】 | `docs/research/economic_lenses.md` |
| 160 | Dietrich 2012 | Dietrich, O. ほか 2012. The role of cult and feasting in the emergence of Neolithic communities. *Antiquity* 86: 674–695. 石の道具が 1 万以上という数は、のちの数え (Nature の 2021 年の記事、発掘隊のブログ)。L. Dietrich の本 (*Plant Food Processing Tools at Early Neolithic Göbekli Tepe*) は 7,000 以上の道具をあつかう | ✗  | `docs/research/archaeological_evidence.md` |
| 161 | Do the same mechanisms that create complex life also create  | Do the same mechanisms that create complex life also create complex technology?（New Things Under the Sun）: https://www.newthingsunderthesun.com/pub/bm44y48u | ✗  | `docs/research/civilization_tech_tree.md` |
| 162 | Domesday Book | Domesday Book (The National Archives); Open Domesday (https://opendomesday.org). | ✗  | `docs/research/historical_records.md` |
| 163 | Dong 2020 | [74] Dong, Du, Gardner, Lancet Infectious Diseases 2020;20(5):533-534: https://pmc.ncbi.nlm.nih.gov/articles/PMC7159018/ | ✗  | `docs/research/modern_records.md` |
| 164 | Downey 2014 | Downey ほか 2014, ヨーロッパの新石器時代の人口転換と若い人の割合 (PLoS ONE): https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4143272/ | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md` |
| 165 | Duistermaat 1996 | Duistermaat, K. 1996. The seals and sealings. In P.M.M.G. Akkermans (ed.), *Tell Sabi Abyad: The Late Neolithic Settlement*, 339–401. (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/historical_records.md`・`docs/society_phase/G6.md`・`docs/society_phase/G6_design.md`・`sim/society/techtree/plan.json` |
| 166 | Duistermaat 2012 | Duistermaat 2012, OLA 219:1–16 — non-administrative origins of seals 【文献】 (text not read); Duistermaat 2013, "Private matters" (in Nieuwenhuyse et al. eds., *Interpreting the Late Neolithic of Upper Mesopotamia*, 315–322) — private-property reading 【文献】 (text not read) | ✗  | `docs/society_phase/G6_design.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 167 | Englund 1988 | Englund, R.K. 1988. Administrative timekeeping in ancient Mesopotamia. *JESHO* 31(2): 121–185. (「1 年 = 12 (うるう年は 13) か月 = 360 (390) 日」) | ✗  | `docs/research/historical_records.md` |
| 168 | Englund 1991 | Englund, R.K., Grégoire, J.-P. & Matthews, R. 1991. *The Proto-Cuneiform Texts from Jemdet Nasr I* (MSVO 1。ジェムデト・ナスルの畑の測量)。「EN の畑」の粘土板: CDLI P005069、https://cdli.ox.ac.uk/wiki/complex_calculations_jemdetnasr (ほかの書き方 3) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/society_phase/G6_measures.md` |
| 169 | Englund 1993 | Englund, R.K. & Nissen, H.J. 1993. *ATU 3* (言葉の表). (ほかの書き方 1) | ✗  | `docs/research/historical_records.md`・`docs/society_phase/G6.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/part4.md` |
| 170 | Englund 1995 | Englund, R.K. 1995a. Late Uruk period cattle and dairy products: evidence from proto-cuneiform sources. *BSA* 8: 33–48. (ほかの書き方 2) | ✗  | `docs/research/historical_records.md` |
| 171 | Englund 1998 | Englund, R.K. 1998. Texts from the Late Uruk Period. *OBO* 160/1. | ✗  | `docs/research/historical_records.md`・`docs/society_phase/G6_design.md` |
| 172 | Englund 2001 | Englund, R.K. 2001. Grain accounting practices in archaic Mesopotamia. https://cdli.earth/files-up/publications/englund2001b.pdf (ほかの書き方 1) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/society_phase/fidelity_checklist.md` |
| 173 | Englund 2004 | Englund, R.K. 2004. Proto-cuneiform account-books and journals. In Hudson & Wunsch (eds.), *Creating Economic Order*. | ✗  | `docs/research/historical_records.md` |
| 174 | Englund 2009 | Englund, R.K. 2009. The smell of the cage. *CDLJ* 2009:4. https://cdli.earth/articles/cdlj/2009-4 | ✗  | `docs/research/historical_records.md` |
| 175 | Englund, ウル第 3 王朝の働いた日の帳簿 | Englund, ウル第 3 王朝の働いた日の帳簿 (CDLJ): https://cdli.earth/articles/cdlj/327 | ✗  | `docs/research/economic_lenses.md` |
| 176 | Eshed 2004 | Eshed, V., Gopher, A., Galili, E. & Hershkovitz, I. 2004. *AJPA* 123. Eshed, V., Gopher, A. & Hershkovitz, I. 2006. *AJPA* 130. | ✗  | `docs/research/archaeological_evidence.md` |
| 177 | Esin 1994 | Esin, U. 1994. The functional evidence of seals and sealings of Değirmentepe. In *Archives Before Writing*, 59–81. | ✗  | `docs/research/historical_records.md` |
| 178 | Eurocentrism | Eurocentrism（Wikipedia）: https://en.wikipedia.org/wiki/Eurocentrism | ✗  | `docs/research/civilization_tech_tree.md` |
| 179 | Evans-Pritchard 1940 | Evans-Pritchard, E.E. 1940. *The Nuer*. / Roberts, M.N. & Roberts, A. 1996 (ルバの記憶の板). | ✗  | `docs/research/historical_records.md` |
| 180 | Evershed 2008 | Evershed, R. ほか 2008. Earliest date for milk use in the Near East and southeastern Europe linked to cattle herding. *Nature* 455: 528–531. | ✗  | `docs/research/archaeological_evidence.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 181 | Falkenstein, A. 1956–57. *Die neusumerischen Gerichtsurkunde | Falkenstein, A. 1956–57. *Die neusumerischen Gerichtsurkunden*. | ✗  | `docs/research/historical_records.md` |
| 182 | FAO, 収穫のあとの損 | FAO, 収穫のあとの損 (村の倉の調べ。熱帯のトウモロコシが中心で、壺の大麦には目安だけ): https://www.fao.org/4/w1544e/W1544E05.htm | ✗  | `docs/research/economic_lenses.md` |
| 183 | FAO, 食料と農業の経済の勘定 3 章 | FAO, 食料と農業の経済の勘定 3 章: https://www.fao.org/4/W0010E/W0010E05.htm | ✗  | `docs/research/economic_lenses.md` |
| 184 | Fay 2019 | Increasing population size can inhibit cumulative cultural evolution（Fay ほか 2019）: https://researchgate.net/profile/Nicolas-Fay/publication/331759071_Increasing_population_size_can_inhibit_cumulative_cultural_evolution/links/5c8afc6d92851c1df941a76f/Increasing-population-size-can-inhibit-cumulative-cultural-evolution.pdf | ✗  | `docs/research/civilization_tech_tree.md` |
| 185 | Flannery 1972 | Flannery, K. 1972. / Flannery, K. 2002. The origins of the village revisited. *American Antiquity* 67(3). | ✗  | `docs/research/historical_records.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 186 | Frangipane 1994 | Frangipane, M. 1994. The record function of clay sealings. | ✗  | `docs/research/historical_records.md` |
| 187 | Frangipane 2007 | Frangipane, M. et al. 2007. *Arslantepe Cretulae: An Early Centralised Administrative System Before Writing* (Arslantepe V。宮殿の封泥 2,200 個以上). (書評: https://ajaonline.org/book-review/605/) (ほかの書き方 1) | ✗  | `docs/research/historical_records.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G6.md`・`docs/society_phase/G6_design.md` |
| 188 | Frenez 1997 | Frenez, D. & Tosi, M. (ロータルの封泥); Kenoyer, J.M.; Meadow, R. & Kenoyer, J.M. 1997 (ハラッパー); Rao, R. 2018. arXiv:1812.00049. | ✗  | `docs/research/historical_records.md` |
| 189 | Friberg 1994 | Friberg, J. 1994. (同じ本の書評). *Orientalistische Literaturzeitung* 89.【未確認】 | ✗ 【未確認】 | `docs/research/historical_records.md`・`docs/society_phase/G6_design.md` |
| 190 | Fuller 2006 | Fuller, B. ほか 2006. *AJPA* 129. Beaumont, J. ほか 2013. *Archaeometry*. Beaumont, J. & Montgomery, J. 2015. *Annals of Human Biology*. | ✗  | `docs/research/archaeological_evidence.md` |
| 191 | Gage 1986 | Gage & Dyke 1986, Siler の式 (Human Biology 58): https://digitalcommons.wayne.edu/humbiol/vol58/iss2/12 | ✗  | `docs/research/economic_lenses.md` |
| 192 | Gardiner, A.H. 1941–48. *The Wilbour Papyrus*. | Gardiner, A.H. 1941–48. *The Wilbour Papyrus*. | ✗  | `docs/research/historical_records.md` |
| 193 | Gelb 1965 | Gelb, I.J. 1965. The ancient Mesopotamian ration system. *JNES* 24: 230–243. (ほかの書き方 3) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/society_phase/G7_design.md`・`sim/society/techtree/plan.json` |
| 194 | Gelb 1991 | Gelb, I.J., Steinkeller, P. & Whiting, R. 1991. *Earliest Land Tenure Systems in the Near East*. OIP 104. | ✗  | `docs/research/historical_records.md` |
| 195 | Gmür 1917 | Historisches Lexikon der Schweiz「Hauszeichen」. / Gmür 1917. / Stebler 1907. | ✗  | `docs/research/historical_records.md` |
| 196 | Godley 2007 | Godley & Lavoie 2007 の、出し入れのつり合うモデル (Wikipedia): https://en.wikipedia.org/wiki/Stock-flow_consistent_model | ✗  | `docs/research/economic_lenses.md` |
| 197 | Goodman 1990 | Goodman, A. & Rose, J. 1990. *Yearbook of Physical Anthropology* 33. Ritzman, T., Baker, B. & Schwartz, G. 2008. *AJPA* 135. | ✗  | `docs/research/archaeological_evidence.md` |
| 198 | Goody 1963 | Goody, J. & Watt, I. 1963. The consequences of literacy. / Vansina, J. 1985. *Oral Tradition as History*. | ✗  | `docs/research/historical_records.md` |
| 199 | Goren 2001 | Goren, Y., Goring-Morris, N. & Segal, I. 2001. The technology of skull modelling in the Pre-Pottery Neolithic B. *Journal of Archaeological Science* 28. | ✗  | `docs/research/archaeological_evidence.md` |
| 200 | Goren-Inbar 2004 | 火: Goren-Inbar ほか 2004 (Science 304); Karkanas ほか 2007; Shahack-Gross ほか 2014 | ✗  | `docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 201 | Goring-Morris 2007 | Goring-Morris, N. & Horwitz, L.K. 2007. Funerals and feasts during the Pre-Pottery Neolithic B of the Near East. *Antiquity* 81: 902–919. | ✗  | `docs/research/archaeological_evidence.md` |
| 202 | Goulder 2010 | Goulder, J. 2010. Administrators' bread. *Antiquity* (斜めの縁の鉢の使いみち). (ほかの書き方 1) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md` |
| 203 | Graeber 2011 | Graeber 2011, Debt: The First 5,000 Years の受けとめられ方 (Wikipedia): https://en.wikipedia.org/wiki/Debt:_The_First_5,000_Years | ✗  | `docs/research/economic_lenses.md` |
| 204 | Green 1980 | Green, M.W. 1980. Animal husbandry at Uruk in the archaic period. *JNES* 39: 1–35. | ✗  | `docs/research/historical_records.md` |
| 205 | Greene 2007 | Smithsonian NAA, Lakota Winter Counts. / Greene, C. & Thornton, R. 2007. *The Year the Stars Fell*. / Library of Congress (Battiste Good の冬の数え). | ✗  | `docs/research/historical_records.md` |
| 206 | Griffin と Stanish | Griffin と Stanish (ティティカカの国のでき方のモデル【記憶】) https://escholarship.org/uc/item/2zd1t887 | ✗ 【記憶】 | `docs/society_phase/G7_design.md` |
| 207 | Griffith 1898 | Griffith, F.Ll. 1898. *Hieratic Papyri from Kahun and Gurob*. / Kóthay, K. 2001. *Bulletin du Musée Hongrois des Beaux-Arts* suppl. | ✗  | `docs/research/historical_records.md` |
| 208 | Groman-Yaroslavski 2016 | Groman-Yaroslavski, I., Weiss, E. & Nadel, D. 2016. Composite sickles and cereal harvesting methods at 23,000-years-old Ohalo II, Israel. *PLOS ONE*. (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 209 | Grosman 2008 | Grosman, L., Munro, N. & Belfer-Cohen, A. 2008. A 12,000-year-old Shaman burial from the southern Levant (Israel). *PNAS* 105. | ✗  | `docs/research/archaeological_evidence.md` |
| 210 | Guerrero 2009 | Guerrero, E., Molist, M., Kuijt, I. & Anfruns, J. 2009. Seated memory: new insights into Near Eastern Neolithic mortuary variability from Tell Halula, Syria. *Current Anthropology* 50(3): 379–391. | ✗  | `docs/research/archaeological_evidence.md` |
| 211 | Gurven 2007 | Gurven & Kaplan 2007, Longevity among hunter-gatherers (Population and Development Review 33)【未確認】: https://hraf.yale.edu/ehc/documents/1294 | ✗ 【未確認】 | `docs/research/economic_lenses.md`・`docs/society_phase/G6_measures.md` |
| 212 | Guérin 2026 | Guérin ほか 2026. (OxCal・Chronomodel・BayLum をチャタルヒュユクで比べ、始まりはもっと早いだろうとした). *Geochronology*. | ✗  | `docs/research/archaeological_evidence.md` |
| 213 | Haklay 2015 | Haklay, G. & Gopher, A. 2015. A new look at Shelter 131/51 in the Natufian site of Eynan (Ain-Mallaha), Israel. *PLOS ONE*. | ✗  | `docs/research/archaeological_evidence.md` |
| 214 | Halstead & O'Shea | Halstead & O'Shea (編) 1989, Bad Year Economics (Cambridge): https://resolve.cambridge.org/core/books/bad-year-economics/2249365CCA983DAC9E902E08D7990E48 | ✗  | `docs/research/economic_lenses.md` |
| 215 | Halstead 1982 | Halstead & O'Shea 1982 — social storage (memory, unverified); Hudson 2018, *…and forgive them their debts* — interest-bearing grain loans and debt cancellations from c. 2400 BC (Enmetena of Lagash); Hudson's reading 【文献・二次】 | ✗ 【記憶】 | `docs/society_phase/G6_design.md` |
| 216 | Halstead 1989 | Halstead, P. 1989. The economy has a normal surplus. In Halstead & O'Shea (eds.), *Bad Year Economics*, 68–80. (ほかの書き方 1) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/research/society2_periodization.md`・`docs/society_phase/fidelity_checklist.md` |
| 217 | Hassan 1981 | Village densities ≈ 100–200 persons/ha (Kramer's ≈ 120/ha, cited via Hassan 1981) 【文献・二次】; Kramer 1982 and Watson 1979 themselves not read; Nissen 2003 — Uruk ≈ 40,000 【文献・二次】 | ✗  | `docs/research/archaeological_evidence.md`・`docs/society_phase/G6_design.md` |
| 218 | Hastorf 1988 | Hastorf, C. & Popper, V. (eds) 1988. *Current Paleoethnobotany*. University of Chicago Press. | ✗  | `docs/research/archaeological_evidence.md` |
| 219 | Hather 1993 | Hather, J. 1993. *An Archaeobotanical Guide to Root and Tuber Identification*. Hather 2000. *Archaeological Parenchyma*. | ✗  | `docs/research/archaeological_evidence.md` |
| 220 | Henrich 2004 | Henrich, J. (2004). Demography and cultural evolution: How adaptive cultural processes can produce maladaptive losses — the Tasmanian case. *American Antiquity* 69(2). PDF（著者サイト）: https://www2.psych.ubc.ca/~henrich/Website/Papers/HenrichTasmania.pdf | ✗  | `docs/research/civilization_tech_tree.md`・`docs/tech_tree_design_draft.md` |
| 221 | Henton 2012 | Henton, E. 2012. Using gazelle dental cementum studies to explore seasonality and mobility at the Epipalaeolithic mega-sites of Kharaneh IV and Wadi Jilat 6, Azraq Basin, Jordan. *Quaternary International* 252: 195–201. | ✗  | `docs/research/archaeological_evidence.md` |
| 222 | Henton 2019 | Henton, E., Roe, J., Martin, L. ほか 2019. Epipalaeolithic and Neolithic gazelle hunting in the Badia of north-east Jordan: reconstruction of seasonal movements of herds by stable isotope and dental microwear analyses. *Levant* 50(2): 127–172. https://joeroe.io/pdf/Henton_et_al_2019.pdf | ✗  | `docs/research/archaeological_evidence.md` |
| 223 | Hershkovitz 2008 | Hershkovitz, I. ほか 2008. Detection and molecular characterization of 9000-year-old *Mycobacterium tuberculosis* from a Neolithic settlement in the Eastern Mediterranean. *PLOS ONE* 3(10): e3426. Hershkovitz, I. ほか 2015. Tuberculosis origin: the Neolithic scenario. *Tuberculosis* (9250〜8160 年前という年代はここから). | ✗  | `docs/research/archaeological_evidence.md` |
| 224 | Hesse, Slaughter Patterns and Domestication | Hesse, Slaughter Patterns and Domestication: The Beginnings of Pastoralism in Western Iran: https://keibi.uni-tuebingen.de/Record/KEI00059118 | ✗  | `docs/research/economic_lenses.md` |
| 225 | Hodder 1976 | Hodder & Orton 1976 — equifinality of fall-off curves 【文献・二次】 | ✗  | `docs/society_phase/G6_design.md` |
| 226 | Hodder 1996 | チャタルヒュユクの塗りなおしの数と間かく: 40〜50 回 (Hodder 1996)、厚さ 20 cm に 450 回まで (のちの紹介)。1 年に 1 回か、壁は月に 1 回ほどか (2011 年の報告の紹介) | ✗  | `docs/research/archaeological_evidence.md` |
| 227 | Hodder 2010 | Hodder, I. & Pels, P. 2010. History houses. In Hodder (ed.) *Religion in the Emergence of Civilization*. チャタルヒュユクの報告 (1996): https://catalhoyuk.com/archive_reports/1996/last.html | ✗  | `docs/research/archaeological_evidence.md` |
| 228 | Hole 1989 | Hole, F. 1989. Patterns of burial in the fifth millennium. In Henrickson & Thuesen (eds) *Upon This Foundation*. | ✗  | `docs/research/archaeological_evidence.md` |
| 229 | How do Ages work in Civilization VII | How do Ages work in Civilization VII（Siliconera）: https://www.siliconera.com/how-do-ages-work-in-civilization-vii/ | ✗  | `docs/research/civilization_tech_tree.md` |
| 230 | Hudson 2000 | Hudson 2000, How interest rates were set, 2500 BC – 1000 AD: https://michael-hudson.com/2000/03/how-interest-rates-were-set-2500-bc-1000-ad/ | ✗  | `docs/research/economic_lenses.md` |
| 231 | Hudson 2010 | Hudson, M. The lost tradition of biblical debt cancellations. https://michael-hudson.com/wp-content/uploads/2010/03/HudsonLostTradition.pdf | ✗  | `docs/research/historical_records.md` |
| 232 | Hudson 2018 | Hudson 2018 (利子と帳消し。`docs/research/economic_lenses.md`・`historical_records.md`)・Wu & Lu (ニップルの利子【二次】)・Cripps (ウル第 3 王朝の値【二次】) | ✗  | `docs/society_phase/G6_design.md`・`docs/society_phase/G7_design.md` |
| 233 | Hudson, Modern | Hudson, Modern (Mis)interpretations of Clean Slates: https://rozenbergquarterly.com/?p=38454 | ✗  | `docs/research/economic_lenses.md` |
| 234 | Hulsewé 1985 | Hulsewé, A.F.P. 1985. *Remnants of Ch'in Law*. / 『睡虎地秦墓竹簡』. | ✗  | `docs/research/historical_records.md` |
| 235 | Hummel 2012 | Hummel, Graeber への批判 (EconLog): https://www.econlib.org/archives/2012/07/hummel_on_graeb.html | ✗  | `docs/research/economic_lenses.md` |
| 236 | Humphrey 1985 | Humphrey 1985, Barter and Economic Disintegration (引用で読んだ)【未確認】: https://era.org.au/money-and-the-myth-of-barter/ | ✗ 【未確認】 | `docs/research/economic_lenses.md` |
| 237 | i3.MesopOil | i3.MesopOil (乳製品の資料): https://www.i3-mesop-oil.gwi.uni-muenchen.de/dossier/a-2-1-06/ 、 https://www.i3-mesop-oil.gwi.uni-muenchen.de/?p=2898 | ✗  | `docs/research/historical_records.md` |
| 238 | Ibáñez 2016 | 確かめなおしで直したこと (2026-10-09): ジャアデの刃 48 枚は Ibáñez ほか 2016 でなく Pichon ほか 2021。アイン・マラハの狩りの季節は Henton ほか 2019 でなく Rivals ほか 2020 (Henton ほか 2019 はガゼルが季節で遠くへ動かなかったという研究、セメント質は Henton 2012)。シャラーラはナトゥーフ期でなく PPNA。バルジン・ホユクの乳は Evershed ほか 2008 でなく Özbal ほか 2024。ギョベクリ・テペの石の道具の数 (7,000 → 1 万以上)。熟れた穀物を刈る刃の年代は Ibáñez-Estévez ほか 2021 で確かめた。ドムズテペの論文の筆頭は Carter (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md` |
| 239 | Ibáñez-Estévez 2021 | Ibáñez-Estévez, J.J. ほか 2021. Sickle gloss texture analysis elucidates long-term change in plant harvesting during the transition to agriculture. *Journal of Archaeological Science* (105502). | ✗  | `docs/research/archaeological_evidence.md` |
| 240 | IUSSP, Coale–Demeny のモデル生命表 | IUSSP, Coale–Demeny のモデル生命表 (いちばん低い段は e0 = 20): https://papp.iussp.org/sessions/papp103_s01/PAPP103_s01_070_020.html | ✗  | `docs/research/economic_lenses.md` |
| 241 | Jacobsen 1958 | Jacobsen & Adams 1958, Salt and Silt in Ancient Mesopotamian Agriculture: https://ocb.uni-tuebingen.de/Record/KEI00092253?lng=en | ✗  | `docs/research/economic_lenses.md` |
| 242 | Jasim 1986 | Jasim, S.A. & Oates, J. 1986. Early tokens and tablets in Mesopotamia. *World Archaeology* 17(3): 348–362. | ✗  | `docs/research/historical_records.md` |
| 243 | Jasim 1988 | Jasim, S.A. 1988. (テル・アバダ). | ✗  | `docs/research/historical_records.md` |
| 244 | Jasim 2021 | Jasim, S.A. 2021. *Tell Abada: An Ubaid Village in Central Mesopotamia*. OIP 147. (テル・アバダの年とトークン) | ✗  | `docs/research/historical_records.md` |
| 245 | Johnson 1973 | Johnson, G. 1973, 1987. / Wright, H. & Johnson, G. 1975. Population, exchange, and early state formation in southwestern Iran. *American Anthropologist* 77(2): 267–289. (ほかの書き方 1) | ✗  | `docs/research/historical_records.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G6_design.md` |
| 246 | Julien 1988 | Julien, C. 1988. How Inca decimal administration worked. *Ethnohistory* 35(3): 257–279. / Escudero, A. (インカの年齢の区分と、植民地時代にそろえた数の年齢。書名は【未確認】) | ✗ 【未確認】 | `docs/research/historical_records.md` |
| 247 | Jędrzejowski ほか 2025. How precise can the calibration of a s | Jędrzejowski ほか 2025. How precise can the calibration of a single radiocarbon measurement be? *Radiocarbon*. | ✗  | `docs/research/archaeological_evidence.md` |
| 248 | Karasik 2000 | Karasik, D., Arensburg, B. & Pavlovsky, O. 2000. Age assessment of Natufian remains from the land of Israel. *American Journal of Physical Anthropology*. | ✗  | `docs/research/archaeological_evidence.md` |
| 249 | Keene, 線形計画による後期アルカイック期の暮らし | Keene, 線形計画による後期アルカイック期の暮らし (博士論文の記録): https://deepblue.lib.umich.edu/handle/2027.42/181028?show=full | ✗  | `docs/research/economic_lenses.md` |
| 250 | Keightley 1978 | Keightley, D. 1978. *Sources of Shang History*. / 2000. *The Ancestral Landscape*. / 2012. *Working for His Majesty*. | ✗  | `docs/research/historical_records.md` |
| 251 | Kelley 2018 | Kelley, K. 2018. Gender, age, and labour organization in the earliest texts from Mesopotamia and Iran (c. 3300–2900 BC). Oxford DPhil. https://ora.ox.ac.uk/objects/uuid:afa3362e-1182-43aa-a2b9-d675bd8c585a | ✗  | `docs/research/historical_records.md` |
| 252 | Kelley 2024 | Kelley, K., Cartolano, M. & Ferrara, S. 2024. Seals and signs: tracing the origins of writing in ancient South-west Asia. *Antiquity* (ネット公開 2024-11-05). https://www.cambridge.org/core/journals/antiquity/article/seals-and-signs-tracing-the-origins-of-writing-in-ancient-southwest-asia/B3C2D400F3F80A7A0162D9035C9C2804 (ほかの書き方 1) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/society_phase/G6_design.md`・`docs/tech_tree_design_draft.md` |
| 253 | Khalidi 2009 | Khalidi, Gratuze & Boucetta 2009, Archaeometry 51(6):879–893 — LC2 obsidian at Hamoukar and Brak mostly from the Bingöl region, minor Lake Van source (Bingöl A and Nemrut Dağ are hard to tell apart) 【文献】(abstract). The earlier note 「Hamoukar LC1–2 obsidian ~85% Nemrut Dağ, OI reports 2005–2007」 was not confirmed and conflicts with this abstract | ✗  | `docs/society_phase/G6_design.md`・`docs/society_phase/part4.md` |
| 254 | Kislev 2006 | Kislev, M., Hartmann, A. & Bar-Yosef, O. 2006. Early domesticated fig in the Jordan Valley. *Science* 312. | ✗  | `docs/research/archaeological_evidence.md` |
| 255 | Kjeldsen 2000 | Kjeldsen 2000, A Contextualized Historical Analysis of the Kuhn-Tucker Theorem (Historia Mathematica 27): https://doi.org/10.1006/hmat.2000.2289 | ✗  | `docs/research/economic_lenses.md` |
| 256 | Koca Özer, B., Sağır, M. & Özer, İ. 2011. Secular changes in | Koca Özer, B., Sağır, M. & Özer, İ. 2011. Secular changes in the height of the inhabitants of Anatolia. *Economics & Human Biology* 9(2): 211–219. | ✗  | `docs/research/archaeological_evidence.md` |
| 257 | Kohler 1996 | Kohler & Van West 1996, The calculus of self-interest: https://rex.libraries.wsu.edu/esploro/outputs/bookChapter/The-Calculus-of-Self-interest-in-the/99900590461601842 | ✗  | `docs/research/economic_lenses.md` |
| 258 | Kramer 1982 | Kramer, C. 1982. *Village Ethnoarchaeology*. Hassan, F. 1981. *Demographic Archaeology*. (どちらも引用から) | ✗  | `docs/research/archaeological_evidence.md`・`docs/society_phase/G6_design.md` |
| 259 | Kraus 1966 | Kraus, F.R. 1966. / Postgate, J.N. 1975. Some Old Babylonian shepherds and their flocks. | ✗  | `docs/research/historical_records.md` |
| 260 | Kuijt 2009 | Kuijt, I. & Finlayson, B. 2009. Evidence for food storage and predomestication granaries 11,000 years ago in the Jordan Valley. *PNAS* 106: 10966–10970. (ほかの書き方 4) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/research/society2_periodization.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 261 | Kuijt 2024 | チャタルヒュユクの家の寿命: 50〜100 年 (紹介) と、1 世代 20〜45 年 (Kuijt & Marciniak 2024) (ほかの書き方 2) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/historical_records.md` |
| 262 | Kuznets 1934 | Kuznets 1934, National Income, 1929–1932 (NBER): https://www.nber.org/system/files/chapters/c12278/c12278.pdf | ✗  | `docs/research/economic_lenses.md` |
| 263 | Larsen 2019 | Larsen, C.S. ほか 2019. Bioarchaeology of Neolithic Çatalhöyük reveals fundamental transitions in health, mobility, and lifestyle in early farmers. *PNAS* 116(26): 12615–12623. (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/economic_lenses.md` |
| 264 | Lawrence 2015 | Lawrence & Wilkinson 2015, "Hubs and upstarts: pathways to urbanism in the northern Fertile Crescent", Antiquity 89 【文献】(abstract; the 10–20 ha small-centre figure not re-checked) | ✗  | `docs/society_phase/G6_design.md` |
| 265 | Le Brun 1978 | Le Brun, A. & Vallat, F. 1978. L'origine de l'écriture à Suse. *Cahiers de la DAFI* 8: 11–70 (目録によっては 7–59。ページは【未確認】). | ✗ 【未確認】 | `docs/research/historical_records.md` |
| 266 | Leach 1999 | Leach 1999, Intensification in the Pacific: a critique (Current Anthropology): https://www.journals.uchicago.edu/doi/10.1086/200021 | ✗  | `docs/research/economic_lenses.md` |
| 267 | Leontief 1936 | Leontief 1936 とケネーの経済表 (BLS Monthly Labor Review 2001): https://www.bls.gov/opub/mlr/2001/06/art3full.pdf | ✗  | `docs/research/economic_lenses.md` |
| 268 | List of boosts in Civ6 | List of boosts in Civ6（Fandom）: https://civilization.fandom.com/wiki/List_of_boosts_in_Civ6 | ✗  | `docs/research/civilization_tech_tree.md` |
| 269 | List of civics in Civ6 | List of civics in Civ6（Fandom）: https://civilization.fandom.com/wiki/List_of_civics_in_Civ6 | ✗  | `docs/research/civilization_tech_tree.md` |
| 270 | List of technologies in Civ6 | List of technologies in Civ6（Civilization Wiki / Fandom）: https://civilization.fandom.com/wiki/List_of_technologies_in_Civ6 | ✗  | `docs/research/civilization_tech_tree.md` |
| 271 | Lyman 2008 | Lyman, R.L. 2008. *Quantitative Paleozoology*. Cambridge University Press. Grayson, D.K. 1984. *Quantitative Zooarchaeology*. Academic Press. | ✗  | `docs/research/archaeological_evidence.md` |
| 272 | Mankiw 2020 | Mankiw 2020, A Skeptic's Guide to Modern Monetary Theory: https://www.aeaweb.org/doi/10.1257/pandp.20201102 | ✗  | `docs/research/economic_lenses.md` |
| 273 | Marciniak 2015 | Marciniak, A. ほか 2015. Fragmenting times. *Antiquity* 89. | ✗  | `docs/research/archaeological_evidence.md` |
| 274 | Masonry | Masonry (Civ6)（Fandom）: https://civilization.fandom.com/wiki/Masonry_(Civ6) | ✗  | `docs/research/civilization_tech_tree.md` |
| 275 | Matthews 2005 | Matthews, W. 2005. Micromorphological and microstratigraphic traces of uses and concepts of space. In Hodder (ed.) *Inhabiting Çatalhöyük*. | ✗  | `docs/research/archaeological_evidence.md` |
| 276 | McMahon 2009 | McMahon 2009, Iraq 71 — Late Chalcolithic seal iconography at Brak 【文献】 | ✗  | `docs/society_phase/G6_design.md` |
| 277 | McMahon 2011 | McMahon, Sołtysiak & Weber 2011, J. Field Archaeol. 36:201–220 — Tell Majnuna 【文献】 | ✗  | `docs/society_phase/G6_design.md` |
| 278 | McMahon 2020 | McMahon 2020 (online 2019), J. Archaeol. Res. 28 — low-density zones in early northern cities 【文献】(abstract; no density figure) | ✗  | `docs/society_phase/G6_design.md` |
| 279 | Mesoudi, A. ABM tutorial, Model 9 | Mesoudi, A. ABM tutorial, Model 9: Demography and cultural gain/loss: https://amesoudi-abmtutorial.share.connect.posit.cloud/model9.html | ✗  | `docs/research/civilization_tech_tree.md` |
| 280 | Michalowski 1993 | Michalowski, P. 1993. (Schmandt-Besserat 1992 の書評). *American Anthropologist* 95. | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/society_phase/G6_design.md` |
| 281 | Molina 2010 | Molina, M. 2010. (ウンマの裁きの記録). https://bdtns.cesga.es/PDFs/Molina_2010_FS_Owen.pdf | ✗  | `docs/research/historical_records.md` |
| 282 | Molleson 1994 | Molleson, T. 1994. The eloquent bones of Abu Hureyra. *Scientific American* 271(2). Molleson 2000. In Moore, Hillman & Legge, *Village on the Euphrates*. | ✗  | `docs/research/archaeological_evidence.md` |
| 283 | MSVO 3, 29 | MSVO 3, 29 (クシムの帳簿。シェーエン・コレクション MS 1717), CDLI P005340. https://cdli.ucla.edu/P005340 | ✗  | `docs/research/historical_records.md` |
| 284 | Munro 2010 | ヒラゾン・タクティトのカメの数: 宴のくぼみで 71 匹以上 (Munro & Grosman 2010)、女の墓の甲は 50 (Grosman ほか 2008) と 86 (のちの研究・報道) (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/society_phase/G5_design.md`・`sim/society/techtree/plan.json` |
| 285 | Naroll 1962 | Naroll, R. 1962. Floor area and settlement population. *American Antiquity* 27. Brown, B. 1987. Population estimation from floor area. *Behavior Science Research* 21. (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/historical_records.md` |
| 286 | Navitainuck 2022 | 確かめられたので【未確認】を外したもの: チャタルヒュユクの頭のけが (93 のうち 25、12 人は何度も、女 13・男 10。大学の発表から)、エリドゥの墓地の約 1,000 基 (試し掘りからの見積もり)。ほかに、テル・タウィーラ (2 ha まで、50〜100 人、丸い家の内のり 3〜7 m)・アイン・マラハの家の大きさ・オハロ II の刃 5 枚・ガンジ・ダレの年代とひづめの跡・ヒラゾン・タクティトとクファル・ハホレシュの数・Tanno & Willcox の 804 個・家ネズミ・アシュクル・ホユクの DNA (60 のうち 22)・アメロゲニン (7,300 年前・乳歯)・Skoglund の 2 人と約 10 万の読み・アナトリアの男の背・チャタルヒュユクの乳離れと母方のつながり・ベイサムーンの火葬・アトリット・ヤムの結核・テル・ハルラの座った墓・年齢の方法で平均が 15 年以上ずれる例 (Navitainuck ほか 2022) は、要旨や大学の発表で確かめた (ほかの書き方 1) | ✗ 【未確認】 | `docs/research/archaeological_evidence.md` |
| 287 | Nieuwenhuyse 2010 | Nieuwenhuyse, O., Akkermans, P. & van der Plicht, J. 2010. Not so coarse, nor always plain: the earliest pottery of Syria. *Antiquity* 84. Nishiaki, Y. & Le Mière, M. 2005. The oldest Pottery Neolithic of Upper Mesopotamia: new evidence from Tell Seker al-Aheimar, the Khabur, northeast Syria. *Paléorient* 31(2). Nishiaki, Y. & Le Mière, M. 2017. The oldest Neolithic pottery from Tell Seker al-Aheimar, Upper Khabur, northeastern Syria. In Tsuneki, Nieuwenhuyse & Campbell (eds) *The Emergence of Pottery in West Asia*. Oxbow. | ✗  | `docs/research/archaeological_evidence.md` |
| 288 | Nishiaki 2005 | 土器: Nishiaki & Le Mière 2005 (Paléorient); Wu ほか 2012 (Science 336); 大平山元 I (縄文遺跡群と外ヶ浜町の資料。約 1.65 万年前と約 1.5 万年前の 2 つの書き方がある) | ✗  | `docs/research/archaeological_evidence.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 289 | Nissen 1993 | Nissen, H.J., Damerow, P. & Englund, R.K. 1993. *Archaic Bookkeeping*. University of Chicago Press. | ✗  | `docs/research/historical_records.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 290 | Oates 2007 | Oates, J., McMahon, A., Karsgaard, P., Al Quntar, S. & Ur, J. 2007. Early Mesopotamian urbanism: a new view from the north. *Antiquity* 81: 585–600. https://jasonur.scholars.harvard.edu/publications/early-mesopotamian-urbanism-new-view-north | ✗  | `docs/research/historical_records.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G6_design.md` |
| 291 | Ortega 2014 | Ortega, Ibáñez, Khalidi, Méndez, Campos & Teira 2014, J. Archaeol. Method Theory 21(2):461–485; Ibáñez et al. 2015, J. R. Soc. Interface 12:20150210 — agent-based models: down-the-line does not carry obsidian beyond ~300 km; a small-world network explains spread up to ~800 km 【文献】(abstracts checked; a model result, not an observation) | ✗  | `docs/society_phase/G6_design.md` |
| 292 | Orton 1993 | Orton, C., Tyers, P. & Vince, A. 1993. *Pottery in Archaeology*. Cambridge University Press. | ✗  | `docs/research/archaeological_evidence.md` |
| 293 | Palley 2013 | Palley 2013/2015, MMT への批判 (IMK WP 109): https://www.imk-boeckler.de/fpdf/HBS-005445/p_imk_wp_109_2013.pdf | ✗  | `docs/research/economic_lenses.md` |
| 294 | Parker 1950 | Parker, R.A. 1950. *The Calendars of Ancient Egypt*. | ✗  | `docs/research/historical_records.md` |
| 295 | Payne 1973 | Payne, S. 1973. *Anatolian Studies* 23: 281–303. / Blaise & Balasse 2011. / Balasse et al. 2017. | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/society_phase/fidelity_checklist.md` |
| 296 | Pearson 2015 | Pearson, J., Haddow, S., Hillson, S., Knüsel, C., Larsen, C.S. & Sadvari, J. 2015. Stable carbon and nitrogen isotope analysis and dietary reconstruction through the life course at Neolithic Çatalhöyük, Turkey. *Journal of Social Archaeology* 15(2): 210–232. (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/historical_records.md` |
| 297 | Petti 2020 | [76] Petti & Flaxman 2020: https://pmc.ncbi.nlm.nih.gov/articles/PMC7216402/ | ✗  | `docs/research/modern_records.md` |
| 298 | Phenice 1969 | Phenice, T. 1969. *AJPA* 30. Walker, P. 2008. Sexing skulls using discriminant function analysis of visually assessed traits. *AJPA* 136. | ✗  | `docs/research/archaeological_evidence.md` |
| 299 | Pichon 2021 | Pichon, F. ほか 2021. (ジャアデ・エル・ムガラの前期 PPNB の鎌の刃 48 枚のつや). *Journal of Archaeological Science: Reports* 36: 102807. | ✗  | `docs/research/archaeological_evidence.md` |
| 300 | Popli 2023 | Monroy Kuhn, J., Jakobsson, M. & Günther, T. 2018. Estimating genetic kin relationships in prehistoric populations (READ). *PLOS ONE*. Popli, D. ほか 2023. KIN. *Genome Biology*. | ✗  | `docs/research/archaeological_evidence.md` |
| 301 | Posener-Kriéger 1976 | Posener-Kriéger, P. 1976. *Les archives du temple funéraire de Néferirkarê-Kakaï*.【未確認】 | ✗ 【未確認】 | `docs/research/historical_records.md` |
| 302 | Posener-Kriéger 2004 | Posener-Kriéger, P. 2004. *I papiri di Gebelein* (トリノのエジプト博物館。Demichelis が関わったかは【未確認】). | ✗ 【未確認】 | `docs/research/historical_records.md` |
| 303 | Powell 1985 | Powell 1985, Salt, Seed, and Yields in Sumerian Agriculture (ZA 75): https://keibi.uni-tuebingen.de/Record/KEI00062118 | ✗  | `docs/research/economic_lenses.md` |
| 304 | Prentice 2010 | Prentice, R. 2010. *The Exchange of Goods and Services in Pre-Sargonic Lagash*. AOAT 368. https://www.academia.edu/68918828/ | ✗  | `docs/research/historical_records.md` |
| 305 | Prime Economics, GDP | Prime Economics, GDP: origin, uses and abuses (クズネッツの注意。二次): https://primeeconomics.org/articles/gdp-origin-uses-and-abuses/ | ✗  | `docs/research/economic_lenses.md` |
| 306 | Proto-cuneiform | Proto-cuneiform (Unicode proposal): https://www.unicode.org/L2/L2019/19284-proto-cuneiform.pdf | ✗  | `docs/research/society2_periodization.md` |
| 307 | Pöllath 2021 | Pöllath, N., García-González, R., Kevork, S. ほか 2021. A non-linear prediction model for ageing foetal and neonatal sheep reveals basic issues in early Neolithic husbandry. *Journal of Archaeological Science* (105344). 紹介: https://spm.snsb.de/den-problemen-neolithischer-schafhalter-auf-der-spur/?lang=en | ✗  | `docs/research/archaeological_evidence.md` |
| 308 | Renfrew 1975 | Renfrew 1975, "Trade as action at a distance" (Sabloff & Lamberg-Karlovsky eds.) — modes of exchange 【文献】; Renfrew 1977 — monotonic decrement 【文献】 | ✗  | `docs/society_phase/G6_design.md` |
| 309 | Rivals 2020 | Rivals, F. ほか 2020. (アイン・マラハのナトゥーフ期の終わりの狩りの季節。歯の生え方・すり減り・細かい傷). *Archaeological and Anthropological Sciences*. doi:10.1007/s12520-020-01190-3【筆頭より後の著者は未確認】 | ✗  | `docs/research/archaeological_evidence.md` |
| 310 | Roaf 1989 | Roaf, M. 1989. (テル・マドゥフルのウバイドの家). In Henrickson & Thuesen (eds) *Upon This Foundation: The 'Ubaid Reconsidered*: 91–146. | ✗  | `docs/research/archaeological_evidence.md` |
| 311 | Rogers 2003 | Rogers 2003 (広まりやすさの 5 つ【記憶】)・Bass のモデル (Sultan ほか 1990) https://en.wikipedia.org/wiki/Bass_diffusion_model | ✗ 【記憶】 | `docs/society_phase/G7_design.md` |
| 312 | Roth 1995 | Roth 1995 (ウル・ナンムの法【二次】) | ✗ 【記憶】 | `docs/society_phase/G7_design.md`・`sim/society/techtree/plan.json` |
| 313 | Roth 1997 | Roth, M. 1997. *Law Collections from Mesopotamia and Asia Minor* (2nd ed.). Scholars Press. (ほかの書き方 1) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md` |
| 314 | Rothman 1994 | Rothman, M. 1994. Seal and sealing findspot, design, audience and function: monitoring changes in administrative oversight and structure at Tepe Gawra during the fourth millennium B.C. In *Archives Before Writing*, 97–119. (テペ・ガウラの印: https://journals.openedition.org/syria/237?lang=en。層ごとの年はペン博物館の目録) | ✗  | `docs/research/historical_records.md` |
| 315 | Santana 2021 | Santana, J. ほか 2021. Multi-isotope evidence of population aggregation in the Natufian and scant migration during the early Neolithic of the Southern Levant. *Scientific Reports* 11: 11857. | ✗  | `docs/research/archaeological_evidence.md` |
| 316 | Sattenspiel 1983 | Sattenspiel & Harpending 1983, Stable populations and skeletal age (American Antiquity): https://resolve.cambridge.org/core/journals/american-antiquity/article/abs/stable-populations-and-skeletal-age/D89BE08A7E6483DB316412D0B51C47E4 | ✗  | `docs/research/economic_lenses.md` |
| 317 | Scheidel 2009 | Scheidel & Friesen 2009, The Size of the Economy and the Distribution of Income in the Roman Empire (JRS 99): https://onwork.edu.au/bibitem/2009-Scheidel,Walter-Friesen,Steven+J-The+Size+of+the+Economy+and+the+Distribution+of+Income+in+the+Roman+Empire | ✗  | `docs/research/economic_lenses.md` |
| 318 | Schmandt-Besserat 2018 | Schmandt-Besserat 2018, Prehistoric administrative technologies and the ancient Near Eastern redistribution economy: https://sites.utexas.edu/dsb/tokens/prehistoric-administrative-technologies-and-the-ancient-near-eastern-redistribution-economy-the-case-of-greater-susiana/ | ✗  | `docs/research/economic_lenses.md` |
| 319 | Schmandt-Besserat, D. | Schmandt-Besserat, D. (ムレイベト・ジャルモのトークンの年と数): https://sites.utexas.edu/dsb/tokens/the-invention-of-tokens/ | ✗  | `docs/research/historical_records.md` |
| 320 | Schmandt-Besserat, Tokens and Writing | Schmandt-Besserat, Tokens and Writing: the Cognitive Development: https://sites.utexas.edu/dsb/tokens/tokens-and-writing-the-cognitive-development/ | ✗  | `docs/research/economic_lenses.md` |
| 321 | Semenova, The Origin of Money | Semenova, The Origin of Money (CFEPS WP 55): https://tools.bard.edu/wwwmedia/resources/files/1267/WP%2055%20-%20The%20Origin%20of%20Money%20-%20Semenova.pdf | ✗  | `docs/research/economic_lenses.md` |
| 322 | Sherratt 1981 | 乳: Sherratt 1981; Evershed ほか 2008 (Nature 455); Helmer & Vigne 2007; Greenfield 2014 | ✗  | `docs/research/society2_periodization.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 323 | Shin 2020 | Shin, J. ほか 2020. Scale and information-processing thresholds in Holocene social evolution. Nature Communications 11. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7224170/ (ほかの書き方 1) | ✗  | `docs/research/society2_periodization.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/G7_design.md` |
| 324 | Shott 1996 | Shott, M. 1996. Mortal pots. *American Antiquity* 61: 463–482. DeBoer, W. 1974. Ceramic longevity and archaeological interpretation. *American Antiquity* 39. Varien, M. & Mills, B. 1997. Accumulations research. *Journal of Archaeological Method and Theory* 4. | ✗  | `docs/research/archaeological_evidence.md` |
| 325 | Sigrist 2001 | Sigrist, M. & Damerow, P. 2001. *Mesopotamian Year Names* (CDLI の年の名前の一覧。2,000 以上)。年の名前のまとめ: https://www.encyclopedia.com/history/news-wires-white-papers-and-books/reckoning-time | ✗  | `docs/research/historical_records.md` |
| 326 | Siler 1983 | Siler 1983, Parameters of mortality in human populations: https://u.demog.berkeley.edu/~jrw/Biblio/Eprints/%20P-S/siler.1983.pdf | ✗  | `docs/research/economic_lenses.md` |
| 327 | Sinha 2019 | Sinha ほか 2019, 新アッシリアの盛衰と気候 (「定まらない地帯」)。40〜60% は【未確認】: https://pmc.ncbi.nlm.nih.gov/articles/PMC6853769 | ✗ 【未確認】 | `docs/research/economic_lenses.md`・`docs/society_phase/fidelity_checklist.md` |
| 328 | Skoglund 2013 | Skoglund, P. ほか 2013. Accurate sex identification of ancient human remains using DNA shotgun sequencing. *Journal of Archaeological Science* 40: 4477–4482. | ✗  | `docs/research/archaeological_evidence.md` |
| 329 | Smith 1952 | Smith, W.S. 1952. *JNES* 11. / Schaeffer 1902 (パレルモ石の写し). | ✗  | `docs/research/historical_records.md` |
| 330 | Smith 1983 | E. A. Smith 1983, 最適採餌理論の人類学への使い方の批評 (業績一覧): https://faculty.washington.edu/easmith/easpubs.htm | ✗  | `docs/research/economic_lenses.md` |
| 331 | Smith 2014 | B. D. Smith 2014, 最適採餌理論が農耕の始まりの研究者に受け入れられなかったこと (PNAS 111): https://repository.si.edu/items/925d2f29-634c-4485-9a68-3d25f5c122ca | ✗  | `docs/research/economic_lenses.md` |
| 332 | Souvatzi 2008 | Souvatzi, S. 2008. *A Social Archaeology of Households in Neolithic Greece*. | ✗  | `docs/research/historical_records.md` |
| 333 | Spencer 2010 | Spencer 2010 (最初の国) https://pmc.ncbi.nlm.nih.gov/articles/PMC2867764 | ✗  | `docs/research/society2_periodization.md`・`docs/society_phase/G7_design.md` |
| 334 | Stein 1994 | Stein 1994, Economy, ritual and power in 'Ubaid Mesopotamia (要旨): https://ehrafarchaeology.yale.edu/traditions/mh55/documents/004 | ✗  | `docs/research/economic_lenses.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G5.md`・`docs/society_phase/G5_design.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/part3.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 335 | Steinkeller 1987 | Steinkeller 1987 (gun mada【二次】)・Olson 1993 (取り立てる側の言い分【記憶】) (ほかの書き方 1) | ✗ 【記憶】 | `docs/society_phase/G7_design.md`・`sim/society/techtree/plan.json` |
| 336 | Stewart 2017 | Stewart, N. ほか 2017. Sex determination of human remains from peptides in tooth enamel. *PNAS* 114(52): 13649–13654. Parker, G. ほか 2019. Sex estimation using sexually dimorphic amelogenin protein fragments in human enamel. *Journal of Archaeological Science* 101: 169–180. | ✗  | `docs/research/archaeological_evidence.md` |
| 337 | Stiner 2014 | Stiner, M. ほか 2014・2022 (アシュクル・ホユクのヒツジとヤギ). *PNAS*. | ✗  | `docs/research/archaeological_evidence.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 338 | Stodder 2012 | Stodder, A. & Palkovich, A. (eds.) 2012. *The Bioarchaeology of Individuals*. | ✗  | `docs/research/historical_records.md` |
| 339 | Stordeur 2000 | Stordeur, D. et al. 2000. *Paléorient* 26(1): 29–44. | ✗  | `docs/research/historical_records.md` |
| 340 | Szarzyńska, K. 1993. Offerings for the goddess Inana in arch | Szarzyńska, K. 1993. Offerings for the goddess Inana in archaic Uruk. *RA* 87: 7–28. | ✗  | `docs/research/historical_records.md` |
| 341 | Tanno 2006 | Tanno, K. & Willcox, G. 2006. How fast was wild wheat domesticated? *Science* 311: 1886. | ✗  | `docs/research/archaeological_evidence.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 342 | Technology tree | Technology tree（Wikipedia）: https://en.wikipedia.org/wiki/Technology_tree | ✗  | `docs/research/civilization_tech_tree.md` |
| 343 | Tell Sabi Abyad | Tell Sabi Abyad (封泥の数・印の数・図柄 27 の型・焼けた村の年): https://en.wikipedia.org/wiki/Tell_Sabi_Abyad | ✗  | `docs/research/historical_records.md` |
| 344 | Tell Sabi Abyad | Tell Sabi Abyad: https://en.wikipedia.org/wiki/Tell_Sabi_Abyad | ✗  | `docs/research/society2_periodization.md` |
| 345 | The Civilization V Technology Tree | The Civilization V Technology Tree（USC Scalar, Empire of the Earth）: https://scalar.usc.edu/works/empire-of-the-earth-piece-done-in-the-hexagonal-style-of-sid-meier/media/the-civilization-v-technology-tree | ✗  | `docs/research/civilization_tech_tree.md` |
| 346 | The paradoxical evolution of agriculture | The paradoxical evolution of agriculture (Bowles の紹介。「0.6 倍」は紹介記事の数で【未確認】): https://www.sciencedirect.com/science/article/pii/S0960982213009779 | ✗ 【未確認】 | `docs/research/economic_lenses.md` |
| 347 | The Ubaid Period | The Ubaid Period (Met Museum): https://www.metmuseum.org/essays/the-ubaid-period-5500-4000-b-c | ✗  | `docs/research/society2_periodization.md` |
| 348 | The Universal Tech Tree | The Universal Tech Tree（Asterisk Magazine）: https://asteriskmag.substack.com/p/the-universal-tech-tree | ✗  | `docs/research/civilization_tech_tree.md` |
| 349 | Thuesen 2023 | Thuesen ほか 2023. (シュバイカ 6 のビーズづくり) PLOS ONE 18(12). https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10707568/ | ✗  | `docs/research/society2_periodization.md` |
| 350 | Topoi A-4-4 | Topoi A-4-4 (古いヒツジの飼い方): https://static.topoi.org/project/a-4-4/ | ✗  | `docs/research/historical_records.md` |
| 351 | Trotter 1958 | Trotter, M. & Gleser, G. 1958. *AJPA* 16: 79–123. Ruff, C. ほか 2012. *AJPA* 148: 601–617. | ✗  | `docs/research/archaeological_evidence.md` |
| 352 | Tsuneki 2022 | Tsuneki, A., Hironaga, N. & Jammo, S. 2022. *The Neolithic Cemetery at Tell el-Kerkh*. (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/economic_lenses.md` |
| 353 | Tsuya 2004 | 速水融 1973. 『近世農村の歴史人口学的研究』. / Tsuya, N. & Kurosu, S. (EurAsia Project, *Life Under Pressure* 2004, *Prudence and Pressure* 2010). / コトバンク「宗門改」. | ✗  | `docs/research/historical_records.md` |
| 354 | Turchin 2018 | Seshat Global History Databank (https://seshat-db.com). / Turchin, P. et al. 2018. (ほかの書き方 1) | ✗  | `docs/research/historical_records.md`・`docs/society_phase/G7_design.md` |
| 355 | Twiss 2008 | Twiss, K. 2008. Transformations in an early agricultural society: feasting in the southern Levantine Pre-Pottery Neolithic. *Journal of Anthropological Archaeology* 27: 418–442. | ✗  | `docs/research/archaeological_evidence.md` |
| 356 | Tymoigne 2005 | Tymoigne & Wray 2005, Money: An Alternative Story (CFEPS WP 45): https://tools.bard.edu/wwwmedia/resources/files/1257/WP%2045%20-%20Money%20-%20An%20Alternative%20Story%20-%20Tymoigne%20_%20Wray.pdf | ✗  | `docs/research/economic_lenses.md` |
| 357 | Unger-Hamilton 1984 | Unger-Hamilton, R. 1984. The formation of use-wear polish on flint. *Journal of Archaeological Science* 11: 91–98. | ✗  | `docs/research/archaeological_evidence.md` |
| 358 | Ur 2007 | Ur, J., Karsgaard, P. & Oates, J. 2007. Early urban development in the Near East. Science. / Tell Brak: https://jasonur.scholars.harvard.edu/pages/tell-brak (ほかの書き方 1) | ✗  | `docs/research/society2_periodization.md`・`docs/society_phase/G6_design.md` |
| 359 | Ur 2010 | Ur 2010, *Urbanism and Cultural Landscapes in Northeastern Syria: The Tell Hamoukar Survey* (OIP 137) — Hamoukar LC1–2 southern extension ≈ 280–300 ha dispersed 【文献・二次】 | ✗  | `docs/research/society2_periodization.md`・`docs/society_phase/G6_design.md` |
| 360 | Ur 2014 | Ur 2014, Camb. Archaeol. J. 24(2):249–268 — households and the emergence of cities 【文献】 | ✗  | `docs/society_phase/G6_design.md` |
| 361 | URL のないもの | URL のないもの (一般知識。この調べでは開いていない): パチョーリ 1494 (Summa de arithmetica。複式簿記を本にした)、マーコウィッツ 1952 (Portfolio Selection, Journal of Finance 7。分散投資)、コース 1937 (取引の費用) | ✗  | `docs/research/economic_lenses.md` |
| 362 | Urton 2005 | Urton, G. & Brezine, C. 2005. Khipu accounting in ancient Peru. *Science* 309. / Urton, G. & Chu, A. 2015. Accounting in the King's Storehouse: the Inkawasi khipu archive. *Latin American Antiquity* 26(4): 512–529. (中身は【未確認】) | ✗ 【未確認】 | `docs/research/historical_records.md` |
| 363 | Vaesen 2012 | Vaesen, K. (2012) ほか、Henrich モデルへの批判（PMC）: https://pmc.ncbi.nlm.nih.gov/articles/PMC3404092 | ✗  | `docs/research/civilization_tech_tree.md` |
| 364 | Vaiman 1974 | Vaiman, A.A. 1974. (働く人の記号). | ✗  | `docs/research/historical_records.md` |
| 365 | Valla 2017 | Valla, F. ほか 2017. Eynan (Ain Mallaha). In *Quaternary of the Levant*. https://halshs.archives-ouvertes.fr/halshs-01852519v1 | ✗  | `docs/research/archaeological_evidence.md` |
| 366 | Veenker 2009 | Veenker, R. & Johnson, J.C. 2009. The appellate process in a legal record (di til-la) from Ur III Umma. *AoF* 36(2): 349–364. https://research.birmingham.ac.uk/en/publications/the-appellate-process-in-a-legal-record-di-til-la-from-ur-iii-umm/ | ✗  | `docs/research/historical_records.md` |
| 367 | Ventris 1956 | Ventris, M. & Chadwick, J. 1956/1973. *Documents in Mycenaean Greek*. / Killen, J. 1964. *BSA*. / Palaima, T. 1982/1984. / Nosch, M.-L. (Od 粘土板). / Montecchi (ta-ra-si-ja). / Koropeckyj. / Bartoněk、Stavrianopoulou、Carpenter (ピュロスの土地). | ✗  | `docs/research/historical_records.md` |
| 368 | Vita-Finzi 1970 | Vita-Finzi, C. & Higgs, E. 1970. Prehistoric economy in the Mount Carmel area of Palestine: site catchment analysis. *Proceedings of the Prehistoric Society* 36. | ✗  | `docs/research/archaeological_evidence.md` |
| 369 | Wadsworth 2006 | [36] CLOSER NSHD: https://closer.ac.uk/study/mrc-national-survey-health-development / Wadsworth ほか 2006, International Journal of Epidemiology | ✗  | `docs/research/modern_records.md` |
| 370 | Walker 2009 | Walker, P. ほか 2009. The causes of porotic hyperostosis and cribra orbitalia. *AJPA* 139: 109–125. Brickley, M. 2018. *AJPA*. | ✗  | `docs/research/archaeological_evidence.md` |
| 371 | Webb 1985 | Webb, P. & Suchey, J. 1985. *AJPA* 68. Scheuer, L. & Black, S. 2000. *Developmental Juvenile Osteology*. | ✗  | `docs/research/archaeological_evidence.md` |
| 372 | Weissbrod 2017 | Weissbrod, L. ほか 2017. Origins of house mice in ecological niches created by settled hunter-gatherers in the Levant 15,000 y ago. *PNAS* 114(16): 4099–4104. | ✗  | `docs/research/archaeological_evidence.md` |
| 373 | Whitlam 2023 | Whitlam, J., Finlayson, B., Bogaard, A., Charles, M. & Makarewicz, C. 2023. Processing and storage of tree fruits, cereals and pulses at PPNA Sharara, southern Jordan. *Vegetation History and Archaeobotany*. doi:10.1007/s00334-023-00938-w | ✗  | `docs/research/archaeological_evidence.md` |
| 374 | Whittle 2018 | Whittle, A. 2018. *The Times of Their Lives*. Oxbow. | ✗  | `docs/research/archaeological_evidence.md` |
| 375 | Wilk 1982 | Wilk, R. & Rathje, W. 1982. Household archaeology. *American Behavioral Scientist* 25(6): 617–639. | ✗  | `docs/research/historical_records.md` |
| 376 | Wilk 1984 | Wilk, R. & Netting, R. 1984. Households: changing forms and functions. In Netting, Wilk & Arnould (eds.), *Households*. University of California Press. (家の働き 5 つ) | ✗  | `docs/research/historical_records.md` |
| 377 | Wilkinson 1994 | Wilkinson 1994 の雨だけの麦作のモデル (振り返り。Harvard DASH): https://dash.harvard.edu/server/api/core/bitstreams/7312037d-f06b-6bd4-e053-0100007fdf3b/content | ✗  | `docs/research/economic_lenses.md`・`docs/society_phase/fidelity_checklist.md` |
| 378 | Wilkinson 2000 | Wilkinson, T. 2000. *Royal Annals of Ancient Egypt*. | ✗  | `docs/research/historical_records.md` |
| 379 | Will Civilization VII Finally Get the Tech Tree Right? | Will Civilization VII Finally Get the Tech Tree Right?（SUPERJUMP）: https://www.superjumpmagazine.com/will-civilization-vii-finally-get-the-tech-tree-right/ | ✗  | `docs/research/civilization_tech_tree.md` |
| 380 | Willcox 2008 | Willcox, G., Fornite, S. & Herveux, L. 2008. Early Holocene cultivation before domestication in northern Syria. *Vegetation History and Archaeobotany* 17. Willcox, G. 2024. (見なおし). *Vegetation History and Archaeobotany*. | ✗  | `docs/research/archaeological_evidence.md` |
| 381 | Wilson 2014 | Wilson 2014, 麦にそろえた GDP の見積もりへの批判: https://www.ancientportsantiques.com/wp-content/uploads/Documents/AUTHORS/Wilson2014-DataBases.pdf | ✗  | `docs/research/economic_lenses.md` |
| 382 | Wood 1992 | Wood, J., Milner, G., Harpending, H. & Weiss, K. 1992. The osteological paradox. *Current Anthropology* 33: 343–370. (ほかの書き方 1) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/historical_records.md` |
| 383 | Woods 2010 | CDLI wiki「The Late Uruk Period」、Woods, C. 2010 (見つかった場所)。 | ✗  | `docs/research/historical_records.md` |
| 384 | Wray | Wray (編) 2004, Credit and State Theories of Money (イネスの論文): https://www.e-elgar.com/shop/gbp/credit-and-state-theories-of-money-9781843765134.html | ✗  | `docs/research/economic_lenses.md` |
| 385 | Wray 1998 | Wray 1998, Modern Money (Levy WP 252): https://levyinstitute.org/wp-content/uploads/2024/02/wp252.pdf | ✗  | `docs/research/economic_lenses.md` |
| 386 | Wright 1975 | Wright, H. & Johnson, G. 1975. Population, Exchange, and Early State Formation in Southwestern Iran. American Anthropologist 77:267-289 (ほかの書き方 3) | ✗ 【記憶】 | `docs/research/historical_records.md`・`docs/research/society2_periodization.md`・`docs/society_phase/G6.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/G7_design.md`・`docs/society_phase/part4.md`・`sim/society/techtree/plan.json` |
| 387 | Wrigley 1981 | Wrigley, E.A. & Schofield, R. 1981. *The Population History of England 1541–1871*. / Wrigley, Davies, Oeppen & Schofield 1997. *English Population History from Family Reconstitution 1580–1837*. / Alter, Newton & Oeppen 2020. *HLCS*. | ✗  | `docs/research/historical_records.md` |
| 388 | Yacobi 2023 | Yacobi & Gopher 2023, Camb. Archaeol. J. 33(3):431–448 — kin-based trade partnership model (Wadi Rabah, Hagoshrim) 【文献】(abstract checked; the authors' model) | ✗  | `docs/society_phase/G6_design.md` |
| 389 | Yaka 2021 | Yaka, R. ほか 2021. Variable kinship patterns in Neolithic Anatolia revealed by ancient genomes. *Current Biology* 31(11). doi:10.1016/j.cub.2021.03.050 | ✗  | `docs/research/archaeological_evidence.md` |
| 390 | Yüncü 2025 | Yüncü, E. ほか 2025. (チャタルヒュユクの母方のつながりと血縁). *Science* 388(6754). doi:10.1126/science.adr2915 | ✗  | `docs/research/archaeological_evidence.md` |
| 391 | Zahid 2016 | Zahid, Robinson & Kelly 2016, Agriculture, population growth, and the radiocarbon record (PNAS。1 年 0.041% を確かめた): https://pmc.ncbi.nlm.nih.gov/articles/PMC4743830 | ✗  | `docs/research/economic_lenses.md`・`docs/society_phase/G6_measures.md`・`docs/society_phase/fidelity_checklist.md` |
| 392 | Zeder 2000 | ガンジ・ダレのオスを殺した年齢: 「大人の盛りの前」(Zeder & Hesse 2000) と「大人の大きさになってから」(Daly ほか 2021 の報道) (ほかの書き方 2) | ✗  | `docs/research/archaeological_evidence.md`・`docs/research/economic_lenses.md`・`docs/society_phase/fidelity_checklist.md`・`docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 393 | Zeder 2011 | Zeder, M. 2011. The Origins of Agriculture in the Near East. Current Anthropology 52(S4). https://www.journals.uchicago.edu/doi/10.1086/659307 | ✗  | `docs/research/society2_periodization.md` |
| 394 | Zimansky 1993 | Zimansky, P. 1993. (同じ本の書評). *Journal of Field Archaeology* 20: 513–517. (ほかの書き方 2) | ✗  | `docs/research/economic_lenses.md`・`docs/research/historical_records.md`・`docs/society_phase/G6.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/part4.md`・`docs/tech_tree_design_draft.md` |
| 395 | 『里耶発掘報告』2006. / 王子今、邢義田 | 『里耶発掘報告』2006. / 王子今、邢義田 (里耶の戸籍). / Yates, R. *Early China* 35–36. | ✗  | `docs/research/historical_records.md` |
| 396 | くらべる資料 | くらべる資料 (4.I.3): Seshat https://www.seshat-db.com (計画 [13]) / HYDE 3.2 https://essd.copernicus.org/articles/9/927/2017/ (計画 [12]。今は 3.3 が新しい版) | ✗  | `docs/society_phase/G7_design.md` |
| 397 | ウルナンムの法 | ウルナンムの法: https://en.wikipedia.org/wiki/Code_of_Ur-Nammu | ✗  | `docs/research/historical_records.md` |
| 398 | ウル・ナンムの法 | ウル・ナンムの法: https://en.wikipedia.org/wiki/Code_of_Ur-Nammu ・ https://www.worldhistory.org/Code_of_Ur-Nammu/ | ✗  | `docs/society_phase/G7_design.md` |
| 399 | オーストラリア統計局, 家の中の世話のサテライト勘定 | オーストラリア統計局, 家の中の世話のサテライト勘定: https://www.abs.gov.au/statistics/detailed-methodology-information/concepts-sources-methods/australian-system-national-accounts-concepts-sources-and-methods/2020-21/chapter-23-satellite-accounts/household-satellite-account-and-unpaid-work | ✗  | `docs/research/economic_lenses.md` |
| 400 | シュメールの複利の最古の例 | シュメールの複利の最古の例 (大麦 33⅓%): https://arxiv.org/pdf/1510.00330 | ✗  | `docs/research/economic_lenses.md` |
| 401 | チャヤーノフの考え | チャヤーノフの考え (働く人と食べる人のつり合い): https://era.anthropology.ac.uk/Era_Resources/Era/Peasants/theory07.html | ✗  | `docs/research/economic_lenses.md` |
| 402 | テル・タウィーラの発掘の成果 | テル・タウィーラの発掘の成果 (ハレ大学): https://www.orientarch.uni-halle.de/digs/tawila/tawila_results_eng.pdf | ✗  | `docs/research/archaeological_evidence.md` |
| 403 | ニップルの銀の貸し借り | ニップルの銀の貸し借り: https://yzwmyjy.nenu.edu.cn/info/1334/2171.htm | ✗  | `docs/society_phase/G7_design.md` |
| 404 | ハンムラビ法典の抜き書き | ハンムラビ法典の抜き書き (§48): https://history.hanover.edu/courses/excerpts/165hammurabi.html | ✗  | `docs/research/economic_lenses.md` |
| 405 | ルンドベリの上限 | ルンドベリの上限 (破産の確率): https://arxiv.org/pdf/2107.02537 | ✗  | `docs/research/economic_lenses.md` |
| 406 | 人口と累積的文化のレビュー | 人口と累積的文化のレビュー（Stirling）: https://www.stir.ac.uk/research/hub/file/1249333 | ✗  | `docs/research/civilization_tech_tree.md` |
| 407 | 刺激による伝播【二次】https | 刺激による伝播【二次】https://textsavvy.substack.com/p/stimulus-diffusion | ✗  | `docs/society_phase/G7_design.md` |
| 408 | 北東イベリアの地下の倉の研究 | 北東イベリアの地下の倉の研究 (チャタルヒュユクの倉の値もここから). *Antiquity* 2020.【著者は未確認】 https://www.cambridge.org/core/product/9B3BB34552AF141E2776EB0F43158F47 | ✗  | `docs/research/archaeological_evidence.md` |
| 409 | 印の中の犂 | 印の中の犂 (テル・スレイマの時期): https://jarch.journals.ekb.eg/article_90925_8a25d0477cc24b8cc0de6a2f37f5be6f.pdf | ✗  | `docs/society_phase/G7_design.md` |
| 410 | 国連 2025 SNA | 国連 2025 SNA: https://unstats.un.org/unsd/nationalaccount/sna2025.asp | ✗  | `docs/research/economic_lenses.md` |
| 411 | 国連 SNA 1993 の説明 | 国連 SNA 1993 の説明 (自分で使う物の値うち): https://unstats.un.org/unsd/sna1993/clarDescription.asp?ID=17 | ✗  | `docs/research/economic_lenses.md` |
| 412 | 外の知識のもれ | 外の知識のもれ: arXiv 2601.13717 (Simulated Ignorance Fails, 2026); arXiv 2505.00030 (中身をまだ確かめていない) | ✗  | `docs/tech_tree_design_draft.md` |
| 413 | 大英博物館 大麦の配給の粘土板 | 大英博物館 大麦の配給の粘土板: https://www.bmimages.com/preview.asp?image=00273611001 | ✗  | `docs/research/historical_records.md` |
| 414 | 張家山漢簡『二年律令』 | 張家山漢簡『二年律令』(前 186 年). / 天長紀荘 19 号墓の報告 2006. / 尹龍九 (楽浪の戸口簿). / 『尹湾漢墓簡牘』1997. / 李暁林ほか 2004. | ✗  | `docs/research/historical_records.md` |
| 415 | 批評 | 批評 (2026-10-16) が確かめた出典 (直しで足した) | ✗  | `docs/society_phase/G7_design.md` |
| 416 | 日本の田んぼ | 日本の田んぼ: 国立歴史民俗博物館の年代 (春成ほか 2003。前 10 世紀)。前 5 世紀ごろとする説もある | ✗  | `docs/tech_tree_design_draft.md` |
| 417 | 日本アクチュアリー会, 資格試験の案内 | 日本アクチュアリー会, 資格試験の案内 (1 次試験の 5 科目の 1 つが「会計・経済・投資理論」。検索の要約で読んだ): https://www.actuaries.jp/examin/info.html | ✗  | `docs/research/economic_lenses.md` |
| 418 | 日本アクチュアリー会, 資格試験要領 別紙 | 日本アクチュアリー会, 資格試験要領 別紙(1) 試験科目・内容 (会計・経済・投資理論の出題の範囲。検索の要約で読んだ): https://www.actuaries.jp/examin/2025exam/2025-B1.html | ✗  | `docs/research/economic_lenses.md` |
| 419 | 旧世界の果樹の始まり | 旧世界の果樹の始まり (2015): https://cris.biu.ac.il/en/publications/beginnings-of-fruit-growing-in-the-old-world-two-generations-late-3/ | ✗  | `docs/research/economic_lenses.md` |
| 420 | 狩猟採集民の危険の分けあい | 狩猟採集民の危険の分けあい (Wiessner の hxaro。まとめ): https://www.hgcosmos.org/assets/topics/Risk.pdf | ✗  | `docs/research/economic_lenses.md` |
| 421 | 現実の例 | 現実の例: アッカド (Met) https://www.metmuseum.org/essays/the-akkadian-period-ca-2350-2150-b-c / ウル第 3 王朝の帳簿 https://cdli.earth/P105944 / テル・ブラク https://www.tellbrak.mcdonald.cam.ac.uk/occupation.html ([3]) | ✗  | `docs/society_phase/G7_design.md` |
| 422 | 琉球大学附属図書館のコラム | 琉球大学附属図書館のコラム (藁算)。『月刊みんぱく』2012。八重山蔵元の規則。『八重山算法書』1826. | ✗  | `docs/research/historical_records.md` |
| 423 | 職業の表 | 職業の表 (キシュのかけら): https://cdli.earth/articles/cdln/2014-15 | ✗  | `docs/research/historical_records.md` |
| 424 | 語の一覧と Lu A | 語の一覧と Lu A: https://en.wikipedia.org/wiki/Lexical_lists ・ CDLI https://cdli.earth/articles/cdlj/2003-3 | ✗  | `docs/society_phase/G7_design.md` |
| 425 | Adams 1966 | Adams 1966 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/research/state_emergence_plan.md` |
| 426 | Akkermans 2004 | Akkermans 2004 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md`・`docs/society_phase/G6_design.md` |
| 427 | Algaze 1993 | Algaze 1993 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/society_phase/G6.md`・`docs/society_phase/part4.md` |
| 428 | Anderson 1952 | Anderson 1952 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/society_phase/F4_notes.md` |
| 429 | Birch 2017 | Birch 2017 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/historical_records.md` |
| 430 | Blanton 1996 | Blanton 1996 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md` |
| 431 | Bollongino 2012 | Bollongino 2012 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/society_phase/G7_design.md` |
| 432 | Boyd 1985 | Boyd 1985 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |
| 433 | Bulliet 1975 | Bulliet 1975 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |
| 434 | Carneiro 1981 | Carneiro 1981 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md` |
| 435 | Carter 2008 | Carter 2008 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/society_phase/G6_design.md` |
| 436 | Carter 2010 | Carter 2010 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md` |
| 437 | Clastres 1974 | Clastres 1974 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/state_emergence_plan.md` |
| 438 | Damerow 1987 | Damerow 1987 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/society_phase/G6_design.md` |
| 439 | Derex 2016 | Derex 2016 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |
| 440 | Duistermaat 2010 | Duistermaat 2010 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/society_phase/G6_design.md`・`docs/society_phase/part2.md` |
| 441 | Feinman 1984 | Feinman 1984 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md`・`docs/society_phase/G5.md` |
| 442 | Friesem 2019 | Friesem 2019 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `sim/society/techtree/plan.json` |
| 443 | Hayden 2001 | Hayden 2001 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/research/humanity/part3_humanness.md` |
| 444 | Helbaek 1972 | Helbaek 1972 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `sim/society/techtree/plan.json` |
| 445 | Henrich 2001 | Henrich 2001 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |
| 446 | Hodder 2022 | Hodder 2022 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md` |
| 447 | Johnson 1978 | Johnson 1978 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/economic_lenses.md`・`docs/society_phase/G6.md`・`docs/society_phase/G6_design.md`・`docs/society_phase/part4.md` |
| 448 | Kadowaki 2012 | Kadowaki 2012 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md` |
| 449 | Kingery 1988 | Kingery 1988 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `sim/society/techtree/plan.json` |
| 450 | Kohler 2025 | Kohler 2025 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md` |
| 451 | Kuijt 2000 | Kuijt 2000 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/historical_records.md`・`docs/research/society2_periodization.md` |
| 452 | Lansing 1991 | Lansing 1991 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/research/state_emergence_plan.md` |
| 453 | Larsen 2015 | Larsen 2015 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/society_phase/G9_design.md`・`docs/society_phase/G9_design_draft.md`・`sim/society/techtree/plan.json` |
| 454 | Lewis 2012 | Lewis 2012 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |
| 455 | Lopez 1971 | Lopez 1971 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `sim/society/techtree/plan.json` |
| 456 | Mayshar 2022 | Mayshar 2022 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/research/state_emergence_plan.md` |
| 457 | McCrae 1989 | McCrae 1989 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/research/humanity/paper2_exp1_prereg.md` |
| 458 | McMahon 2019 | McMahon 2019 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/society_phase/G6_design.md` |
| 459 | Meade 1941 | Meade 1941 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/economic_lenses.md` |
| 460 | Meadow 1997 | Meadow 1997 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/historical_records.md` |
| 461 | Mendels 1972 | Mendels 1972 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `sim/society/techtree/plan.json` |
| 462 | Moran 1992 | Moran 1992 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/society_phase/G9_design.md`・`sim/society/techtree/plan.json` |
| 463 | Mullins 2018 | Mullins 2018 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `sim/society/techtree/plan.json` |
| 464 | Nadel 2012 | Nadel 2012 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 465 | Nijenhuis 2010 | Nijenhuis 2010 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/humanity/paper2_exp1_prereg.md` |
| 466 | Palley 2015 | Palley 2015 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/economic_lenses.md` |
| 467 | Piperno 2004 | Piperno 2004 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 468 | Rivers 1912 | Rivers 1912 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |
| 469 | Roux 2009 | Roux 2009 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md`・`sim/society/techtree/plan.json` |
| 470 | Snir 2015 | Snir 2015 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |
| 471 | Sorokin 1942 | Sorokin 1942 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/research/humanity/part3_humanness.md` |
| 472 | Ur 2011 | Ur 2011 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/society_phase/G6_design.md` |
| 473 | Vaesen 2016 | Vaesen 2016 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |
| 474 | Watson 1974 | Watson 1974 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `sim/society/techtree/plan.json` |
| 475 | Weingarten 2009 | Weingarten 2009 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/society_phase/G6_design.md` |
| 476 | Weiss 2004 | Weiss 2004 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `sim/society/techtree/plan.json` |
| 477 | Wittfogel 1957 | Wittfogel 1957 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ 【記憶】 | `docs/research/state_emergence_plan.md` |
| 478 | Wright 1977 | Wright 1977 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md` |
| 479 | Yoffee 2005 | Yoffee 2005 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/research/society2_periodization.md`・`docs/society_phase/G5.md` |
| 480 | Zielhofer 2012 | Zielhofer 2012 (研究ノートの本文に名前と年だけが出てくる。書誌の行はない) | ✗ 名前と年だけ | `docs/tech_tree_design_draft.md` |

