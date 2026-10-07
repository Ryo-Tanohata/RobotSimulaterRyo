# 調査メモ: 「シヴィライゼーション」シリーズの技術ツリー

> 目的: あとで社会シミュレーション（小さな群れ → 村と畑 → 初期国家…）を作るときの「ヒント置き場」。
> コードは変えていません。これは読むだけの資料です。
>
> 作成日: 2026-10-07

## 0. はじめに（権利についての注意）

- 「Sid Meier's Civilization（シヴィライゼーション）」は Take-Two Interactive / Firaxis Games の商標・著作物です。
- このメモでは、ゲームの文章・名言・アイコン・長い説明文は**写していません**。
- 技術の名前と「どれがどれの前に必要か」という関係は、ゲームの仕組みの事実として、自分の言葉と表の形でまとめています。
- 私たちのシミュレーションは「考え方をまねる（インスピレーション）」だけにします。名前・絵・文章などの素材は使いません。
  技術名も、使うときは自分たちの言葉（例: 「土器」「水路」）にします。

### 調べ方と確かさについて

- 今回の作業環境では、Fandom wiki・CivFanatics・Wikipedia などのページを直接開くことができませんでした（ネットワーク制限）。
  そのため、**検索結果のまとめ文**と、筆者がもともと知っている知識を組み合わせて書いています。
- 確かめられた内容と、記憶にたよった内容を分けるため、表の中で **(要確認)** と書いた所があります。
  実際に使う前に、ゲーム内の百科事典（Civilopedia）や wiki で確認してください。
- ゲームは追加パック（Rise and Fall / Gathering Storm など）やパッチで数字や条件が変わります。

---

## 1. 概要

### 1.1 技術ツリーとは

- 「技術ツリー（tech tree）」は、技術どうしのつながりを**木（グラフ）**の形で表したものです。
- 「Aを知らないとBを研究できない」という**前提条件（prerequisite）**でつながっています。
- 技術を手に入れると、新しい建物・ユニット・土地の改良（畑・鉱山など）・不思議（遺産）などが**使えるようになる（アンロック）**。
- 正確には木ではなく、複数の親を持つ技術もあるので「有向非巡回グラフ（DAG）」です。

### 1.2 研究のしくみ（ざっくり）

1. 都市や建物が毎ターン「科学ポイント（ビーカー）」を生む。
2. プレイヤーは、前提を満たした技術から1つを選んで研究する。
3. その技術のコスト分のポイントがたまると完成し、新しいものが使えるようになる。
4. 技術は「時代（エラ）」にまとめられている（古代・古典・中世・ルネサンス・産業・近代…）。
   多くの作品では、技術を進めると自分の時代が進む。

### 1.3 シリーズごとのちがい

| 作品 | 年 | 技術ツリーの特徴（短く） |
|---|---|---|
| Civ I | 1991 | 「文明の進歩（advances）」と呼ぶ。多くの技術に前提が2つある。1980年のボードゲーム『Civilization』（Francis Tresham）の「進歩カード」の考えを受け継いだと言われる。 |
| Civ II | 1996 | Iと似た形で技術数が増える。「未来技術」をくり返し研究できる。 |
| Civ III | 2001 | 技術を「時代」ごとの画面に分け、時代が切りかわる感じが強まる。 |
| Civ IV | 2005 | 前提に「AND（全部必要）」と「OR（どれか1つでよい）」の2種類がある。たとえば「Xと、YかZのどちらか」という形。技術の交換（外交で売り買い）が大きな役割。宗教が技術に結びつく。 |
| Civ V | 2010 | 横に流れる1本の大きなツリー。最初の根は「農業」。都市が多いほど技術コストが上がる（広がりすぎをおさえる）。 |
| Civ VI | 2016 | ツリーが**2本に分かれる**: 科学で進む「技術ツリー」と、文化で進む「社会制度（Civics）ツリー」。さらに、**ある行動をすると研究が速くなる「ブースト」**（技術は「ひらめき（Eureka）」、社会制度は「着想（Inspiration）」）が入った。ブーストをとると必要量の約50%（追加パック Rise and Fall 以降は40%）がすぐ手に入る。 |
| Civ VII | 2025 | ゲームを3つの「時代（Age）」— 古代（Antiquity）・大航海（Exploration）・近代（Modern）— に分け、**時代ごとに別の技術ツリー・社会制度ツリー**がある。時代が終わると文明そのものを乗りかえる。技術の多くに「熟達（Mastery）」というもう一段の研究があり、追加の効果がもらえる（例: 数学の熟達で「写本（Codex）」が増える、など）。古代の技術として、農業・航海・土器・畜産・文字・灌漑・石工・通貨・青銅器・車輪・航法・工学・軍事訓練・数学・鉄器などが挙げられている。**ただし Civ VII の細かい仕組みは、今回見つけた情報が少なく、確かではありません。** |

**ポイント**: シリーズは「ポイントをためて1つずつアンロック」から始まり、VI で「プレイヤーの行動が発見を速める」形（ブースト）に、VII で「時代ごとにリセットされ、文明を乗りかえる」形に変わってきた。
シミュレーションにとって一番役に立つのは VI のブーストの考え方です（3章）。

---

## 2. 古代〜古典の技術（村・畑 → 初期国家に関係する部分）

ここでは「Society 2.0（農耕 → 初期国家）」に関係する、最初の2つの時代だけを見ます。

### 2.1 Civ VI の技術（古代 Ancient）

「前提」が「—」のものは最初から研究できます。

| 技術（英語） | 日本語の意味 | 前提 | ゲーム内でできるようになること（短く） |
|---|---|---|---|
| Pottery | 土器 | — | 穀物庫（Granary）の建物 |
| Animal Husbandry | 畜産（家畜を飼う） | — | 牧草地（Pasture）の改良、馬の資源が見える、（狩り場 Camp も (要確認)） |
| Mining | 採掘 | — | 鉱山（Mine）・石切り場（Quarry）の改良、森を切ってすぐに資材を得る |
| Sailing | 帆走・航海 | — | 小型の船（ガレー）、漁船（漁場の改良） |
| Astrology | 占星術 | — | 聖地（Holy Site）の地区、ストーンヘンジ |
| Irrigation | 灌漑 | 土器 | 農園（Plantation）の改良、空中庭園 |
| Writing | 文字 | 土器 | 学問の地区（Campus）、図書館 |
| Archery | 弓術 | 畜産 | 弓兵 |
| Masonry | 石工 | 採掘 | 古代の城壁、ピラミッド |
| Bronze Working | 青銅器 | 採掘 | 槍兵、鉄の資源が見える |
| The Wheel | 車輪 | 採掘 | 戦車（チャリオット）、水車小屋（Water Mill） |

### 2.2 Civ VI の技術（古典 Classical）

| 技術（英語） | 日本語の意味 | 前提 | できるようになること（短く） |
|---|---|---|---|
| Currency | 通貨 | 文字 | 商業の地区（Commercial Hub）、市場 |
| Horseback Riding | 乗馬 | 畜産 | 騎兵（ホースマン） |
| Celestial Navigation | 天体航法 | 帆走・占星術 | 港（Harbor）の地区 |
| Shipbuilding | 造船 | 帆走 | より大きな軍船 (要確認) |
| Iron Working | 鉄器 | 青銅器 | 剣士、鉄の鉱山 |
| Mathematics | 数学 | 通貨 | （効果の詳細は要確認） |
| Construction | 建設 | 石工・乗馬 | 娯楽の地区（闘技場）、製材所 (要確認) |
| Engineering | 工学 | 車輪 | 水道橋（Aqueduct）、投石機 (要確認) |

**流れのイメージ（Civ VI）**

```
土器 ─┬─ 灌漑
      └─ 文字 ── 通貨 ── 数学
畜産 ─┬─ 弓術
      └─ 乗馬 ──┐
採掘 ─┬─ 石工 ──┴─ 建設
      ├─ 青銅器 ── 鉄器
      └─ 車輪 ── 工学
帆走 ─┬─ 造船
占星術┴─ 天体航法（帆走＋占星術）
```

### 2.3 くらべるために: Civ V の古代の技術

Civ V では「農業（Agriculture）」が**すべての根**になっています。VI では農業という技術はなく、最初から畑が作れます。

| 技術（英語） | 日本語 | 前提 | できること（短く） |
|---|---|---|---|
| Agriculture | 農業 | — | 畑（Farm） |
| Pottery | 土器 | 農業 | 穀物庫、ほこら (要確認) |
| Animal Husbandry | 畜産 | 農業 | 牧草地、馬が見える |
| Archery | 弓術 | 農業 | 弓兵 |
| Mining | 採掘 | 農業 | 鉱山、森を切る |
| Sailing | 帆走 | 土器 | 漁船、船 |
| Calendar | 暦 | 土器 | 農園（Plantation）、ストーンヘンジ |
| Writing | 文字 | 土器 | 図書館 |
| Trapping | わな猟 | 畜産 | 狩り場（Camp） |
| The Wheel | 車輪 | 畜産 | 戦車弓兵、水車小屋、道 (要確認) |
| Masonry | 石工 | 採掘 | 石切り場、城壁、ピラミッド |
| Bronze Working | 青銅器 | 採掘 | 槍兵、兵舎 (要確認) |

古典時代の例（Civ V）: 数学（弓術＋車輪）、乗馬（車輪）、鉄器（青銅器）、建設（石工など）、哲学（文字など）。(前提の細部は要確認)

**VI と V のちがい**
- V は「農業 → 土器 → 文字」のように**農業が出発点**。VI は農業を「最初から持っている」扱いにして、土器・畜産・採掘の3本から始まる。
- V では「暦」が農園を開くが、VI では「灌漑」が農園を開く。
- V の「わな猟」は VI ではなくなり、狩り場は畜産にまとめられた (要確認)。
- Civ IV では前提に OR があり、「同じ技術に別の道から行ける」。これは「歴史には色々な道がある」ことを少し表せる。

### 2.4 Civ VI の初期の社会制度（Civics、文化ポイントで進む）

| 社会制度（英語） | 日本語の意味 | 前提 | できること（短く） |
|---|---|---|---|
| Code of Laws | 法典 | — | 最初の政体（族長制）、基本の政策 |
| Craftsmanship | 職人の技 | 法典 | 土地改良を助ける政策など |
| Foreign Trade | 外国との交易 | 法典 | 交易路・交易商ユニット |
| Early Empire | 初期の帝国 | 外国との交易 | 開拓者を作りやすくする政策、国境を開く外交 |
| Mysticism | 神秘主義 | 外国との交易 | 宗教まわりの政策 (要確認) |
| Military Tradition | 軍事の伝統 | 職人の技 | 軍事の政策 |
| State Workforce | 国の労働力 | 職人の技 | 地区づくりを助ける政策 |
| Political Philosophy | 政治哲学 | 国の労働力・初期の帝国 | 3つの政体（古典共和制・寡頭制・専制） |
| Games and Recreation | 遊びと娯楽 | 国の労働力 | 娯楽の地区 (要確認) |
| Drama and Poetry | 劇と詩 | 初期の帝国 | 文化の政策 (要確認) |
| Recorded History | 記録された歴史 | 政治哲学・劇と詩 | 学問の政策 (要確認) |
| Theology | 神学 | 神秘主義・劇と詩 | 宗教の政策 |

**大事な考え方**: VI では「技術（モノの知恵）」と「制度（人のまとまり方の知恵）」が**別々に進む**。
私たちの G5（リーダーと決まり）や G6（交易と記録）は、この「制度ツリー」の考え方に近い。

---

## 3. ブースト（行動が発見を速める）— Civ VI

### 3.1 しくみ

- 技術ごとに「ある行動をする」という条件がある。条件を満たすと、その技術の研究が一気に進む（約50%、追加パック以降は40%）。
- その技術を**研究中でなくても**、条件を満たした時点でブーストがつく。あとで研究すると早く終わる。
- 最初の3つの技術（土器・畜産・採掘）と最初の制度（法典）にはブーストがない。
- 部族の村を見つけたときなど、ランダムにブーストがもらえることもある。

### 3.2 古代〜古典の技術のブースト（「この行動 → この技術が速くなる」）

| この行動をすると | この技術が速くなる | メモ |
|---|---|---|
| 資源のある土地に畑を作る | 灌漑 | 農業の経験 → 水の管理 |
| 他の文明と出会う | 文字 | 出会い・伝えたい → 記録 |
| 海ぞいに都市をつくる | 帆走 | 別の情報では「漁船を2つ持つ」(版による違い) |
| 投石兵で敵を倒す | 弓術 | 飛び道具の経験 → 弓 |
| 石切り場を作る | 石工 | 石をあつかう経験 |
| 蛮族を3体倒す | 青銅器 | 戦い → 武器 |
| 資源を掘る鉱山を作る | 車輪 | (版によって条件がちがうという情報あり) |
| 自然の驚異を見つける | 占星術 | ふしぎな物を見る → 天への関心 |
| 交易路をつくる | 通貨 | 交換 → お金 |
| 牧草地を作る | 乗馬 | 家畜の経験 → 馬に乗る |
| 海の資源を2つ改良する | 天体航法 | 海での経験 |
| ガレー船を2隻持つ (要確認) | 造船 | 船の経験 |
| 鉄の資源に鉱山を作る | 鉄器 | 鉄に出会う |
| 3種類の専門の地区を作る | 数学 | 複雑な都市 → 計算が必要 |
| 水車小屋を作る | 建設 | |
| 古代の城壁を作る | 工学 | |

### 3.3 初期の社会制度の着想（Inspiration）

| この行動をすると | この制度が速くなる |
|---|---|
| 土地を3か所改良する | 職人の技 |
| 2つ目の大陸を見つける | 外国との交易 |
| 人口を6まで増やす | 初期の帝国 |
| 万神殿（最初の信仰）をつくる | 神秘主義 |
| 蛮族の野営地をつぶす | 軍事の伝統 |
| 地区を1つ作る | 国の労働力 |
| 都市国家3つと出会う | 政治哲学 |
| 「建設」の技術を研究する | 遊びと娯楽 |
| 不思議（遺産）を1つ作る | 劇と詩 |
| 学問の地区を2つ持つ (要確認) | 記録された歴史 |
| (今回は確認できず) | 神学 |

### 3.4 シミュレーションにとっての意味

- ブーストは「**その技術に関係する経験をすると、発見が近づく**」というモデル。
  これは考古学や人類学での「試行錯誤や、となりの技術からの発見」という見方にわりと近い。
- 私たちのエージェントは、すでに畑を耕す・家畜を世話する・物を運ぶ…などの行動をしている。
  その**行動の回数・経験**を「ひらめきのもと」にできる（5章の案A）。

---

## 4. 歴史とのくらべ

### 4.1 考古学と合っているところ

| ゲームの関係 | 考古学・歴史では | 合っている度 |
|---|---|---|
| 土器 → 穀物庫 | 土器は食べ物の保存・煮炊きに使われ、定住や穀物の保管と強く結びつく。ただし日本の縄文土器のように、**農耕より前に土器がある**例も多い。 | だいたい合う（順番は地域による） |
| 畜産 → 乗馬 | 馬はまず食用・乳用として家畜化され、そのあと乗るようになったと考えられている。 | 合う |
| 土器・農業 → 灌漑 | メソポタミアなどで、農耕のあとに水路が発達した。 | 合う |
| 文字 → 通貨 | メソポタミアでは記録（数を数える粘土の印 → 文字）が、取引や税の管理と一緒に発達。ただし「お金」の形はさまざまで、硬貨は文字よりずっと後。 | 一部合う |
| 採掘 → 青銅器 → 鉄器 | 銅 → 青銅 → 鉄 という「三時代区分」に近い。ただしアフリカの一部では青銅器時代をとばして鉄に進んだ地域もある。 | だいたい合う（例外あり） |
| 他の文明と出会う → 文字 | 交易や行政の必要が文字を生んだ、という見方とは少し合う。 | 雰囲気として合う |

### 4.2 よく言われる批判

1. **一本道の進歩（線形・目的論）**
   すべての文明が同じ順番で同じ技術を得て、同じゴール（宇宙・現代）へ向かう。
   本当の歴史では、地域ごとに全く違う道があり、「戻る」こともある。
2. **ヨーロッパ中心（ユーロセントリズム）**
   時代の分け方（古典・中世・ルネサンス…）や技術の並びが、西ヨーロッパの歴史を「ふつう」としている、という批判。
   エッセイ「Civilisation Video game Review: A Cultural Artefact of Eurocentrism?」や、Civ V の技術ツリーを分析した学術寄りの作品（USC Scalar）がこの点を論じている。
3. **決定論（地理・技術で全部決まる）**
   技術さえあれば社会が自動的に変わる、という見方になりやすい。実際には、制度・信仰・偶然・人口が大きく効く。
4. **技術が「ON/OFF のスイッチ」**
   ゲームでは、技術は一瞬で「手に入った／まだ」の二択。
   本当は、少しずつ上手になる（改良）、広がるのに時間がかかる（普及）、一部の人だけが知っている、などがある。
   Asterisk Magazine の「The Universal Tech Tree」も、ツリーは「最初の発明」しか示さず、**普及や小さな改良がうまく表せない**と指摘している。
5. **技術は失われない**
   ゲームでは一度得た技術は消えない。でも実際には、知っている人がいなくなると技術は失われることがある（下の4.3）。

なお、「ゲームは単純化であって歴史の主張ではない」という反論もある。
また、Civ VI のブーストや Civ VII の「時代ごとのツリー」「文明の乗りかえ」は、こうした批判への一部の答えとも読める。

### 4.3 研究の世界での「技術の進化」モデル

- **累積的文化（cumulative culture）**: 人間は、前の世代の知恵の上に少しずつ積み上げる。
- **Henrich（2004）タスマニアの議論**: タスマニアが本土から切りはなされ、**一緒に学び合う人の数が減った**ため、
  複雑な技術（骨の道具・釣り針・寒さ用の衣服など）がだんだん失われた、という数理モデル。
  理由は「人が劣っていたから」ではなく、「上手な人が少ないと、まねる時の失敗で技術がくずれていく」から。
  - ただし、このモデルの仮定（技能の分布や、一番上手な人をまねるという前提）や、考古学データの解釈には反論がある（Vaesen ら 2012 など）。
  - 実験では「人数が多いほうが積み上げやすい」をある程度支持する結果もあれば、「人数が多すぎるとかえって進みにくい」という結果もある。
- **組み合わせによる進化（Arthur & Polak 2006）**: 単純な論理回路から始めて、既存の回路をランダムに組み合わせていくと、
  だんだん複雑な回路（8ビット加算器など）が生まれるという計算モデル。
  「新しい技術は、古い技術の**組み合わせ**から生まれる」という考え（W. Brian Arthur『テクノロジーとイノベーション（The Nature of Technology）』）。
- **Mesoudi の ABM チュートリアル**: 「人口と文化の獲得・喪失」を R でまねできるモデルが公開されている（参考を見る）。

---

## 5. シミュレーションへの入れ方の案（アイデアのみ）

前提: エージェントは小さな群れから始まり、村・畑・家畜・余り・分業…へ進む（G1〜G6）。

### 案A: 「経験 → ひらめき」型の技術グラフ（ブーストを主役にする）

- 技術ごとに「関係する行動」と「必要な経験量」を決める。
  例: 「畑で働いた回数」がたまる → 「水路」の発見チャンスが上がる。
- 科学ポイントは使わず、**毎ステップ、確率で発見**する（経験が多いほど確率が上がる、前提の技術があるときだけ）。
- 発見したのは**そのエージェント本人**（だれが見つけたかが物語になる）。

| 良い点 | 悪い点 |
|---|---|
| 行動と発見が直接つながり、説明しやすい | 確率の調整がむずかしい（早すぎ／永遠に来ない） |
| ナレーションに「○○さんが気づいた」と書ける | どの行動がどの技術につながるか、人が決める必要がある |

### 案B: 話す・教えることで知識が広がる

- 技術は「群れ全体」ではなく**エージェント一人ひとりの持ち物**。
- 会話・一緒に作業・親子・師弟で、一定の確率で伝わる。伝わるときに「少し下手になる」ことも入れられる。

| 良い点 | 悪い点 |
|---|---|
| 普及の速さ・地域差・身分差が自然に出る | 人数×技術数のデータが増える |
| G4（持ち物と差）とつながる: 知識も「持ち物」になる | 「村として使える」条件（何人知っていれば良い？）を決める必要 |

### 案C: 技術が世界のルールを少しずつ変える（アンロック＋効果）

- 技術は「新しい行動ができる」か「数字が良くなる」のどちらか。
  - 土器 → 食べ物の保存ロス（くさる量）が減る
  - 灌漑 → 畑の収穫が増える／日照りに強くなる
  - 畜産 → 家畜を飼える、乳・毛が取れる
  - 石工 → 丈夫な家・倉、壁
  - 文字 → 記録（貸し借り・取り決めを忘れない）
  - 通貨 → 物々交換より取引が楽になる
- ゲームのような「ON/OFF」ではなく、**上手さ（0〜1）**で効果を少しずつ上げることもできる。

| 良い点 | 悪い点 |
|---|---|
| 効果が目に見える（グラフ・映像に出やすい） | 効果の数字の調整が必要、バランスがくずれやすい |
| 段階的にすれば「改良」も表せる | 効果を入れすぎると「技術で全部決まる」決定論になる |

### 案D: 知っている人が死ぬと技術が消える（累積的文化）

- 案Bと組み合わせる。技術を知っている人が全員いなくなると、その技術は失われる。
- 複雑な技術ほど「教えるときに失敗しやすい」とすると、小さな群れでは高度な技術が保てない（Henrich のタスマニアの考え）。
- 病気・飢え・争いで人口が減ると、技術も後戻りする。

| 良い点 | 悪い点 |
|---|---|
| 「進歩は一本道ではない」を自然に表せる（批判への答えになる） | 見ている人には「なぜ消えたか」が分かりにくい → ナレーションで説明が必要 |
| 人口・交流の大切さがドラマになる | モデルの仮定には学問上の反論もある（そのまま事実として語らない） |

### 案E: 私たちの段階 G1〜G6 に対応させる

| 段階 | 内容 | 対応しそうな技術・制度（ゲームから借りる「考え方」） | 発見のきっかけ（ブースト的な行動の例） |
|---|---|---|---|
| G1 | 村 | 土器（保存）、石工（家・倉） | 食べ物がくさって困った回数、同じ場所に長くいる |
| G2 | 畑と家畜 | 農耕、畜産、灌漑 | 種をまく・収穫する回数、動物に近づく・えさをやる回数、水場の近くの畑 |
| G3 | 余りと分業 | 土器の上達、穀物庫、採掘、職人の技 | 余りが続く、同じ仕事を長く続ける人が出る |
| G4 | 持ち物と差 | 青銅器（価値の高い道具）、牧畜の財産 | 道具を作る、だれのものかでもめる |
| G5 | リーダーと決まり | 法典、政治哲学、神秘主義（儀式） | もめごとの回数、話し合いの回数、人口が一定をこえる |
| G6 | 交易と記録 | 文字、通貨、帆走・車輪（運ぶ） | 他の村と出会う、交換の回数、貸し借りを忘れてもめる |

| 良い点 | 悪い点 |
|---|---|
| 今の計画（段階）にそのまま乗せられる | 段階を固定すると、また「一本道」になりやすい |
| 段階ごとに見どころを作りやすい | どの技術が「段階を進める条件」かを決める必要 |

**おすすめの組み合わせ（ひとこと）**: A（経験→ひらめき）＋ B（伝える）＋ D（失われる）を土台にし、効果は C の小さな数値変化から始める。E は「物語の章立て」として使い、段階の切りかえは技術だけでなく人口・余り・争いなどの組み合わせで決めると、一本道になりにくい。
Civ IV の「OR 前提」のように、**同じ発見に複数の道**を用意するのも良い（例: 記録は交易からも、宗教の儀式からも生まれうる）。

---

## 6. 参考

ゲームの情報（技術名・前提・ブースト条件）。※今回はページ本文を直接開けず、検索結果の要約を使いました。
- List of technologies in Civ6（Civilization Wiki / Fandom）: https://civilization.fandom.com/wiki/List_of_technologies_in_Civ6
- List of civics in Civ6（Fandom）: https://civilization.fandom.com/wiki/List_of_civics_in_Civ6
- List of boosts in Civ6（Fandom）: https://civilization.fandom.com/wiki/List_of_boosts_in_Civ6
- Boost (Civ6)（Fandom）: https://civilization.fandom.com/wiki/Boost_(Civ6)
- Masonry (Civ6)（Fandom）: https://civilization.fandom.com/wiki/Masonry_(Civ6)
- Civilization VI: Technologies（CivFanatics）: https://civfanatics.com/civ6/info/technology/
- Civilization VI: Civics（CivFanatics）: https://civfanatics.com/civ6/info/civic/
- Civilization VI Analyst: Technology / Civics: https://www.well-of-souls.com/civ/civ6_technology.html , https://well-of-souls.com/civ/civ6_civics.html
- Civ 6 Tech Tree（ファンのツール）: https://civilization6planner.com/en/tools/tech-tree
- Civ VI Base Game Technology Tree（BBG）: https://civ6bbg.github.io/en_US/tech_tree_base_game.html
- Civilization 6 Ancient Era（gamepressure）: https://www.gamepressure.com/sidmeierscivilization6/ancient-era/z092c2
- Civ V Technologies（StrategyWiki）: https://strategywiki.org/wiki/Sid_Meier%27s_Civilization_V/Technologies
- Civ IV の AND/OR 前提（CivFanatics フォーラム）: https://forums.civfanatics.com/threads/civ-iv-tech-tree-question.150010
- Civilization VII Ages（CivFanatics）: https://civfanatics.com/civ7/civ-vii-gameplay-mechanics/civilization-vii-ages/
- How do Ages work in Civilization VII（Siliconera）: https://www.siliconera.com/how-do-ages-work-in-civilization-vii/
- Civilization 7 technology tree（Dot Esports）: https://dotesports.com/civilization/news/civilization-7-technology-tree-all-techs-how-to-unlock-them
- Technology tree（Wikipedia）: https://en.wikipedia.org/wiki/Technology_tree
- Civilization (1980 board game)（Wikipedia）: https://en.wikipedia.org/wiki/Civilization_(1980_board_game)

批判・分析
- The Universal Tech Tree（Asterisk Magazine）: https://asteriskmag.substack.com/p/the-universal-tech-tree
- Civilisation Video game Review: A Cultural Artefact of Eurocentrism?（Curieux）: https://www.curieux.com.au/opinion/civilisation-video-game-review-a-cultural-artefact-of-eurocentrism
- The Civilization V Technology Tree（USC Scalar, Empire of the Earth）: https://scalar.usc.edu/works/empire-of-the-earth-piece-done-in-the-hexagonal-style-of-sid-meier/media/the-civilization-v-technology-tree
- Will Civilization VII Finally Get the Tech Tree Right?（SUPERJUMP）: https://www.superjumpmagazine.com/will-civilization-vii-finally-get-the-tech-tree-right/
- Eurocentrism（Wikipedia）: https://en.wikipedia.org/wiki/Eurocentrism

技術の進化・累積的文化の研究
- Henrich, J. (2004). Demography and cultural evolution: How adaptive cultural processes can produce maladaptive losses — the Tasmanian case. *American Antiquity* 69(2). PDF（著者サイト）: https://www2.psych.ubc.ca/~henrich/Website/Papers/HenrichTasmania.pdf
- Vaesen, K. (2012) ほか、Henrich モデルへの批判（PMC）: https://pmc.ncbi.nlm.nih.gov/articles/PMC3404092
- 人口と累積的文化のレビュー（Stirling）: https://www.stir.ac.uk/research/hub/file/1249333
- Cumulative culture（Open Encyclopedia of Cognitive Science, MIT）: https://oecs.mit.edu/pub/6bvu7f8m/release/1
- Increasing population size can inhibit cumulative cultural evolution（Fay ほか 2019）: https://researchgate.net/profile/Nicolas-Fay/publication/331759071_Increasing_population_size_can_inhibit_cumulative_cultural_evolution/links/5c8afc6d92851c1df941a76f/Increasing-population-size-can-inhibit-cumulative-cultural-evolution.pdf
- Mesoudi, A. ABM tutorial, Model 9: Demography and cultural gain/loss: https://amesoudi-abmtutorial.share.connect.posit.cloud/model9.html
- Arthur, W. B. & Polak, W. (2006). The evolution of technology within a simple computer model. *Complexity* 11(5): 23–31. https://doi.org/10.1002/cplx.20130
- Do the same mechanisms that create complex life also create complex technology?（New Things Under the Sun）: https://www.newthingsunderthesun.com/pub/bm44y48u
- A New Classification of Technologies（arXiv）: https://arxiv.org/pdf/1712.07711
