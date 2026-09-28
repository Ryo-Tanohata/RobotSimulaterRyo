# 四足ロボット 強化学習シミュレータ (Unity + ML-Agents)

千葉工業大学 fuRo の古田先生がデモした「絶望ロボット」
([動画](https://www.youtube.com/watch?v=g8abhEHcFA4)) のように、
**物理エンジンの仮想空間で多数のロボットを並列に動かし、強化学習で歩き方を身につけさせる**
ためのシミュレータです。まずはシンプル版です。

- 四足ロボット: 胴体 + 脚 4 本 × 3 関節 = 12 関節 (PhysX の ArticulationBody で PD 制御)
- 「目の見えない」ロボット: 観測は IMU (傾き・角速度) と関節角・関節速度だけ。カメラ・LiDAR なし
- 地形: でこぼこ / 坂 (上り・下り) / 階段 (上り・下り) / 段差ブロック × 難易度 6 段階
- 難易度カリキュラム: 遠くまで歩けたロボットは難しい地形へ、歩けなかったら易しい地形へ
- 外乱: ときどきランダムに押される (蹴られても倒れないように学習)
- 並列台数は設定で変更可能 (既定 16 体。fuRo のデモは 4096 体)
- 学習前でも **プログラムされたトロット歩容** で歩くので、開いてすぐ動作を確認できる

## 動かし方

### 1. プロジェクトを開く

1. Unity Hub で **Unity 6 (6000.0 LTS)** をインストール
2. Unity Hub →「Add」→ このリポジトリの `RobotSimulator` フォルダを選ぶ
3. 初回はパッケージ (ML-Agents 4.0.3 など) の読み込みに数分かかります

### 2. Play する

どのシーンでも **Play を押すだけ** でシミュレーションが自動生成されます
(`SimulationBootstrap`)。シーンとして保存したい場合はメニュー
`RobotSim > Create Main Scene` を実行すると `Assets/RobotSim/Scenes/Main.unity` が作られます。
並列台数などは Hierarchy の `RobotSimulation` オブジェクト (SimulationManager) の Inspector で変更します。

| キー | 操作 |
|---|---|
| W / S | 前進 / 後退 |
| A / D | 左 / 右へ横歩き |
| Q / E | 左 / 右へ旋回 |
| M | 選択中ロボットのキーボード操作 ON/OFF (OFF だとランダムな速度指令) |
| Space | 選択中ロボットを蹴る |
| R | 選択中ロボットをリセット |
| Tab / B | 次 / 前のロボットを選択 |
| 1〜5 | 地形を変更 (でこぼこ / 上り坂 / 上り階段 / 下り階段 / 段差) |
| + / - | 難易度を上げる / 下げる |
| F | 全体表示 / 追従表示 |
| P | ランダムな外乱 ON/OFF |
| T | 4 倍速 |
| 右ドラッグ / ホイール | カメラ回転 / ズーム |

### 3. 強化学習する

```bash
# Python 3.10.12 の環境を作る (ML-Agents の要件)
conda create -n mlagents python=3.10.12 && conda activate mlagents
python -m pip install mlagents==1.1.0

# リポジトリのルートで
mlagents-learn config/quadruped_ppo.yaml --run-id=quadruped01
# 「Start training by pressing the Play button in the Unity Editor」と出たら Unity で Play
```

- 学習中は画面左上に `TRAINING` と表示されます。進み具合は `tensorboard --logdir results` で確認
- 並列台数を増やすと学習が速くなります (PC の性能次第。まずは 16〜64 体程度から)
- さらに速くしたい場合: `RobotSim > Build Training Executable` でビルドし、
  `mlagents-learn config/quadruped_ppo.yaml --run-id=q02 --env=Builds/Quadruped/Quadruped --num-envs=4 --no-graphics`
- 学習が終わると `results/quadruped01/Quadruped.onnx` ができます。これを Unity の `Assets` に入れ、
  SimulationManager の **Policy Model** に設定して Play すると、学習した方策で歩きます

## 構成

```
RobotSimulator/                     Unity プロジェクト
  Assets/RobotSim/Scripts/Core/     Unity に依存しない計算 (運動学・歩容・報酬・観測・地形生成)
  Assets/RobotSim/Scripts/Runtime/  ロボット生成、ML-Agents エージェント、地形メッシュ、カメラ、HUD
  Assets/RobotSim/Scripts/Editor/   メニュー (シーン作成・学習用ビルド)
  Assets/RobotSim/Tests/EditMode/   Core のテスト (Unity の Test Runner で実行可)
config/quadruped_ppo.yaml           PPO の学習設定
tools/verify/                       Unity なしでの検証用 .NET プロジェクト
```

### 報酬 (legged_gym を参考)

速度指令への追従 (前後・左右・旋回) を報酬とし、上下動・胴体の揺れ・傾き・トルク・関節加速度・
行動の急変・太ももやすねの接地にペナルティ、足の滞空時間 (大きな歩幅) にボーナス、転倒で終了。

## 検証 (Unity なし)

```bash
cd tools/verify
dotnet test CoreTests                 # Core のテスト (IK・歩容・地形・報酬・観測・カリキュラム)
dotnet build UnityCompileCheck        # Runtime スクリプトが UnityEngine API でコンパイルできるか
```

`UnityCompileCheck` は UnityEngine 2021.3 の参照アセンブリと ML-Agents のスタブを使った確認なので、
Unity 6 固有の分岐 (`#if UNITY_2023_3_OR_NEWER`) と Editor スクリプトは Unity 上で確認が必要です。
