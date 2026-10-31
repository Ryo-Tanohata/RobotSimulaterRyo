# 修士論文のインタビューから出たものを使っている所 (本人に確かめてもらう)

作ったのは Claude (2026-10-31)。本人の決まり (2026-10-30): インタビューの言葉や、インタビューから出た分析の結果を使うときは、使う前に本人が目で確かめる。
ここには、いま文書と論文 2 の下書きに書いてある文を、そのまま写した。英語の所には Claude の日本語訳をつけた。
インタビューの記録そのもの (話した人の言葉) は、どこにも使っていない。使っているのは、修士論文に書かれた分析の結果 (2026-10-29 に本人がチャットで貼った論文の本文から)。

見てほしいこと: (1) 修士論文の書き方と合っているか、(2) インタビューの結果として出してよいか、(3) 直す・外す所はあるか。

---

## 0. 論文 2 のはじめ (1 節): 修士論文のまとめ (1 と 3 を両方ふくむ)

`paper/paper2/main.tex` 43 行目:

> The model combined Maslow's theory of motivation \citep{maslow1943theory} with Freud's structural theory \citep{freud1923ego}. Humans have unconscious basic needs (physiological, safety, belonging and love, esteem, self-actualisation, and the need to know); this layer---the \emph{id}---contains both good and bad impulses. The needs become socially acceptable behaviour only after censorship by the \emph{superego} and adjustment by the \emph{ego}; which form the satisfaction takes is shaped by environment, culture and custom. The survey (84 Japanese adults, 54 items on everyday rights violations) and interviews (13 participants) found five kinds of awareness (rights, ownership, information, privacy, self-responsibility) and, crucially, that people do not apply rules mechanically. In gray zones they adjust situationally, using seven ways of thinking: \emph{if there is a legitimate reason, one may use it freely}; \emph{take responsibility for one's own actions}; \emph{act if the damage is tolerable}; \emph{an act without malice is forgivable}; \emph{follow the majority}; \emph{where conditions are clear, take them into account and act so that no one is harmed}; \emph{where conditions are unclear, interpret them in one's own favour}. Rule-bending was more likely when ``everyone around me does it'', when one ``has never heard of anyone being caught'', when one is ``in a weak position'', and when it is ``technically easy''; it was less likely when creators would lose income, when a clear system existed, and out of respect for creators. The thesis concluded that law decides by rules, while people decide as subjects who weigh conditions---and that this situational adjustment is the human nature at stake.

訳: 修士論文は、マズローの動機づけの理論とフロイトの心の構造を組み合わせた。人には無意識の基本的な欲求 (生理・安全・所属と愛・承認・自己実現・知る欲求) があり、この層 (エス) はよい衝動もわるい衝動もふくむ。欲求は、超自我の検閲と自我の調整を経て、はじめて社会に受け入れられる行いになる。どんな形で満たすかは、環境・文化・慣習で決まる。アンケート (日本の大人 84 人、54 問) と**インタビュー (13 人)** から、5 つの意識 (権利・所有・情報・プライバシー・自己責任) が見つかった。そして大事なこととして、人は決まりを機械的には当てはめない。グレーゾーンでは、**7 つの考え方**で、場面に合わせて調整する: 正当な理由があれば自由に扱ってよい / 自分の行動に責任を持つ / 被害が許容できるものであれば行為する / 悪意がない行為は許される / 多数派を支持する / 条件が明らかなものは考慮して損害の無いように行為する / 条件が不明なものは自分にとって都合よく解釈する。**はみ出しやすいのは**「まわりがみんなやっている」「捕まった人を聞いたことがない」「弱い立場にいる」「技術的に簡単」なとき。**はみ出しにくいのは**、作り手の収入がなくなるとき・しっかりしたシステムがあるとき・作り手への敬意があるとき。修士論文の結論: 法は決まりで決めるが、人は条件を考える主体として決める。この場面ごとの調整こそが、ここで問う人間性である。

---

## 1. 7 つの考え方 (わけを分ける物差しに使った)

**論文 2・4 節の前の「この論文でしたこと」** (54 行目):

>   \item A transparent, LLM-free dictionary coding of 1{,}150 one-phrase reasons against the thesis's seven ways of thinking (exploratory).

訳: LLM を使わない、透明な辞書で、1,150 件の一言のわけを、修士論文の 7 つの考え方で分けた (探索)。

**論文 2・4.3 節** (197 行目・201 行目):

> This analysis was \emph{not} pre-registered as a hypothesis (the pre-registration only promised to store the reasons). We coded the 1{,}150 one-phrase reasons (5 items $\times$ 230 respondents) with a deterministic dictionary of Japanese regular expressions written after reading the reasons; no LLM was used. Codes are the thesis's seven ways of thinking (\emph{bending} side) and four rule-following reasons (illegal/rules; paying or respecting creators; relationship and courtesy; personal information). A reason can carry several codes; ``mixed'' reasons carry both a bending and a rule-following code (e.g., ``illegal, but everyone does it, so I can't say much'').

> \paragraph{Findings.} Reasons containing at least one rule-bending rationale made up 57\% (D1), 53\% (D2) and 31\% (D3, Opus) of reasons (same 30 people, Opus $-$ Sonnet $= -23$ points [$-35$, $-11$]); they accompanied more lenient numbers (mean answer 2.66 for bending-only, 2.96 mixed, 3.54 rule-only reasons). The most frequent bending rationales were ``where conditions are clear, act so no one is harmed'' (17--22\%; e.g., ``a friend would understand if we talk later''), ``act if the damage is tolerable'' (6--19\%), and ``follow the majority'' (5--20\%). ``An act without malice is forgivable'' appeared mainly for the unreturned clothes (18\% of B11 reasons); ``take responsibility oneself'', ``use freely if justified'' and ``interpret unclear conditions in one's favour'' were rare ($\le 4\%$). Within D2, the ``everyone does it'' line raised the share of reasons with a bending rationale from 39\% to 67\% ($+28$ points [$+18$, $+38$]) and of ``follow the majority'' by $+17$ points [$+10$, $+24$]; ``never caught'' raised them by $+11$ [$0$, $+22$] and $+9$ [$+2$, $+16$]; ``weak position'' and ``technically easy'' changed neither ($|\Delta| \le 4$ points)---the same ordering as the numeric H8 results (Figure~\ref{fig:reasons}). Overall, D2 replaced other bending rationales by ``follow the majority'' (+8 points [$+3$, $+13$]) rather than adding bending rationales ($-4$ points [$-12$, $+3$]). A caution: ``a friend would understand if we talk later'' occurred only for respondents whose description contained ``even if something happens, we can talk it over later and understand each other'' (110 of 110 cases); 83\% of A23 reasons from these respondents but 14\% from others were coded ``conditions clear''. Much of this category is the model paraphrasing its prompt.

訳 (要点): この分け方は、仮説として前もって決めていない。230 人 × 5 問 = 1,150 件の一言のわけを、わけを読んだあとで作った日本語の正規表現の辞書で分けた (LLM は使っていない)。分類は、修士論文の 7 つの考え方 (はみ出す側) と、決まりに従う 4 つのわけ (違法・規則 / 作り手への対価や敬意 / 関係と礼儀 / 個人情報)。— はみ出す側の考え方を 1 つ以上ふくむわけは D1 57%・D2 53%・D3 (opus) 31%。多いのは「条件が明らかなら損害のないように」(17〜22%)・「被害が許せる程度なら」(6〜19%)・「多数派を支持する」(5〜20%)。「みんながやっている」を読んだ人では、はみ出す側が 39% → 67%。ただし「条件が明らか」の多くは、お題の暮らしの文 (「何かあっても後で話せば分かり合える」) の言いかえだった。

**分類の名前の表** (`sim/society/tools/survey/out_exp2/reasons_summary.md`): 修士論文の 7 つの考え方の言葉を、そのまま分類の名前にした。

> JUST 正当な理由があれば自由に扱ってよい / RESP 自分の行動に責任を持つ / HARM 被害が許容できるものであれば行為する / NOMAL 悪意がない行為は許される / MAJ 多数派を支持する / CLEAR 条件が明らかなものは考慮して損害の無いように行為する / UNCL 条件が不明なものは自分にとって都合よく解釈する

**実験 2 の前もって固めた文書** (`paper2_exp2_prereg.md` 140 行目):

> - わけは、修士論文の 7 つの考え方 (正当な理由があれば自由に / 被害が許せる程度なら / 多数派を支持 など) にあたるものが出るかを、あとで見るため (探索。分け方は答えを見る前に別に決める)。

---

## 2. 「学生はお金のわけで、違法と知りつつダウンロードする」(仮説 H9 のもと)

**論文 2・5 節** (172 行目):

> On the five download/copy items (A08, A09, A10, A17, A34), respondents who were students or financially strained ($n=30$) averaged 3.44 versus 3.81 for employed, non-strained respondents ($n=61$): difference $-0.37$ [$-0.53$, $-0.21$], in the direction of the thesis interviews (students cited money when downloading illegally). The difference was smaller in D2 ($-0.18$ [$-0.36$, $0.01$]) and similar for Opus D3 ($-0.31$, but with $n<15$ in one group, so not judged).

訳: ダウンロード・コピーの 5 問で、学生かお金が苦しい答え手 (30 人) の平均は 3.44、働いていてゆとりのある答え手 (61 人) は 3.81。差 −0.37。**修士論文のインタビューと同じ向き (学生は、違法にダウンロードするわけとしてお金を挙げた)**。

**前もって固めた文書** (`paper2_exp2_prereg.md`):

> 4. **立場とお金:** 学生や暮らしが苦しい人は、ダウンロードの問いを、働いていて暮らしが苦しくない人より、ゆるく見るか。

> | H9 を支持 | 修士論文のインタビュー (学生はお金のわけでダウンロードする) と同じ向きの違いが、LLM の答えにも出る |

> - **人間の側は、表 3 の数だけ** (実験 1 と同じ)。H9 の「学生はダウンロードをゆるく見る」は、修士論文のインタビュー (13 人) の見立てで、アンケートの数ではない。

**結果の文書** (`paper2_exp2_results.md` 3 節の 3):

> 3. **学生や暮らしが苦しい人は、ダウンロードをゆるく見た。** 修士論文のインタビューで見えた「学生は経済的な理由で、違法と知りつつダウンロードする」と同じ向き。

---

## 3. 「弱い立場」「簡単にできる」が、人がはみ出すわけだったこと

**論文 2・6 節** (219 行目):

> ``I am in a weak position'' and ``it is technically easy'' had no detectable effect on gray-zone items. In the thesis, weakness (students' lack of money) and ease were reasons people gave for bending rules; the models did not convert their own disadvantage into leniency. This is consistent with the companion village study \citep{tanohata2026village}, where LLM agents rarely gave themselves self-serving excuses, and with LLMs' known lean toward prosocial answers \citep{mei2024turing}. Moreover, the human component structure---which items move together---was not reproduced in either experiment (1 of 5 components). The LLM population now has the right \emph{amount} of one-dimensionality, but not the human \emph{content} of the dimensions.

訳: 「自分は弱い立場にいる」「技術的に簡単」は、グレーゾーンの問いに目立った効き目がなかった。**修士論文では、弱さ (学生のお金のなさ) と簡単さは、人がはみ出すわけとして挙げていた**。モデルは、自分の不利をゆるさに変えなかった。…

**前もって固めた文書** (`paper2_exp2_prereg.md`。LLM に渡した文と、その考え):

> | はみ出しやすい時 | はみ出す側の文 | 逆の側の文 |
> |---|---|---|
> | 自分が弱い立場にいる | このところ、自分は弱い立場にいると感じることが多い。急な出費で手元のお金が足りず、まわりにも言いたいことが言いにくい。 | このところ、お金にも人間関係にも余裕があり、自分が弱い立場だとは感じない。 |

> 「自分が弱い立場」は、修士論文の言葉そのものに、お金 (学生の答え) と人間関係の両方の例をつけた【仮定】。暮らし向き (いつもの) とは別に、「このところ」の様子としてくじで与える (D1 の暮らし向きとは独立)。

> 2. 「自分が弱い立場にいる」を、お金と人間関係の両方で書いた (4.)。修士論文での意味 (インタビューで出た例) に合っているか。

**結果の文書** (`paper2_exp2_results.md` 3 節の 2):

> 2. **修士論文の「はみ出しやすい時」のうち、2 つは LLM でも同じ向きに効いた。** 「みんながやっている」と「捕まった人を聞いたことがない」で、グレーゾーンとダウンロードの答えがゆるくなった。修士論文のインタビューで、人が理由にしていたことと同じ。一方、「弱い立場」と「簡単にできる」は、ほとんど効かなかった。

---

## 4. LLM のわけが、インタビューの言葉に「近い」と書いた所

**結果の文書** (`paper2_exp2_results.md` 2 節の探索):

> - ひとことの理由には、修士論文のインタビューに近い言葉が多く出た (「違法かもだが皆やっていて軽め」「仲が良いので後で話せば済む」「作り手に対価が入らないので問題」)。分け方は、あとで決める。

かぎかっこの中は、LLM の答え手が書いたわけ。「近い」と言ったくらべの相手は、修士論文に載ったインタビューの分析 (7 つの考え方など)。
