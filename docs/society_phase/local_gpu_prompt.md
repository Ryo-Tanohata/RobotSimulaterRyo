# ローカル (自分の PC・GPU) で動画を撮るための指示 (Claude Code に渡す)

2026-11-26。本人「GPU の作業はローカルでしたいです。その為のプロンプトを考えて下さい」。
下の「--- ここから ---」から「--- ここまで ---」までを、自分の PC で開いた Claude Code に、そのまま貼って渡す。

役わけ: **クラウド** = 村を回す・見せ方のコードを直す・絵コンテ。**ローカル** = GPU を使う作業 (人のモデルを作る・本番の動画を撮る)。
同じブランチを使うので、どちらも作業の前に `git pull` する。

--- ここから ---

あなたは、私の PC (Windows・Git Bash・GPU つき) で、村のシミュレーション「川辺の村」の動画を撮る係です。
クラウドの Claude Code は CPU しかなく遅いので、GPU を使う作業をこの PC に移します。

## 守ること
- 返事はいつも日本語で、やさしく短く。質問しないで、おすすめで進めて、選んだことと理由を書く。大きな分かれ目だけ聞く。
- リポジトリ: `Ryo-Tanohata/RobotSimulaterRyo`、ブランチ `claude/physics-engine-robot-simulator-xmyxdn`。ほかのブランチには push しない。PR は作らない。
- 作業の前に `git pull`。push の前に `git fetch origin claude/physics-engine-robot-simulator-xmyxdn && git merge --no-edit FETCH_HEAD`。rebase や force-push はしない。
- コミットの名前: `git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit`
- **mp4・画像・人のモデル (.glb)・VRoid のサンプル・CMU の動きのファイルは、コミットしない** (公開リポジトリ)。絵コンテの json (`sim/society/video/storyboards/`) はコミットする。
- 村のデータ (`sim/society/data/state.json` や記録) は変えない。直すのは見せ方だけ。
- まず読む: `CLAUDE.md`、`docs/society_phase/video_review_loop.md` (見直しの流れ・気になる所 K1〜K17・終わらせ方)、`docs/society_phase/fashion.md` (時代ごとの服)、`sim/society/tools/human/README.md`。

## 1. 準備 (一度だけ)
1. 入れるもの: Git for Windows (Git Bash)、Node.js 20 以上、Google Chrome、ffmpeg (PATH に)、Python 3.11 (`py -3.11`。Blender の bpy 用) と Python 3.12 以上 (`py`。ほかの道具用)。足りないものは、入れ方を私に短く伝えてから入れる。
2. `cd sim/society/video && npm install` (puppeteer-core など)。
3. 作業用のフォルダを 1 つ決める (例 `C:/kawabe_work`。以下 `W`)。クラウドでは `/dev/shm` と `/root` に置いていたものを、ここに置く。
4. 素材を `W` に取る (どれも CC0 か公開のもの)。中身は `sim/society/tools/human/cloud/env_setup.sh` のとおり:
   - CMU の動き: `https://github.com/una-dinosauria/cmu-mocap` のコミット `09a07f54f3bbb58797325f009282d0b2048a2871` から、`env_setup.sh` にある 14 個の `.bvh` だけ (`W/cmu/una/data/...`)。
   - VRoid のサンプル: `https://github.com/madjin/vrm-samples` の `vroid/beta/` から 5 つの `.vrm` (`W/vrmsamples/vroid/beta/`)。
   - bpy: `py -3.11 -m pip install --target W/bpy "bpy==4.5.*"`。

## 2. 人のモデルを作る (時代・組ごと。CPU でもよいが時間がかかる)
クラウドでの作り方は `sim/society/tools/human/cloud/build_set.sh`。その中の `/dev/shm/...`・`/root/...`・`/home/user/RobotSimulaterRyo` を、`W` の下とこの PC のリポジトリの場所に読みかえて動かす。
- 環境の変数: `PEOPLE_ERA` (服の時代 `hide` か `leather`)、`HUMAN_GLB_DIR` と `VROID_WORK` (作業の置き場)、`VROID_DIR` (VRoid のサンプルの場所)、`BLENDER_USER_RESOURCES`、`PYTHONPATH=W/bpy`。動かすのは `py -3.11 -u tools/human/run.py tools/human/build_person_vroid.py -- --person <名前> ...`。
- 記録から自動で決めた人の設定は `sim/society/tools/human/sets/auto_<組>_hide.json` (クラウドで作ったもの。新しい組は `auto_people.py --days <撮る日> --out ...` で作る)。
- 組と使う動画:
  | 組 | 服 | 設定 | 置き場 (render_all.sh の変数) | 動画 |
  |---|---|---|---|---|
  | hide | hide | `sets/auto_g1_hide.json` | `PEOPLE_DIR_HIDE` | S1V・G1F1V・G1F2V・G1F3V・G1V |
  | g2 | hide | `sets/auto_g2_hide.json` | `PEOPLE_DIR_G2` | G2V・G2F1V・G2F2V・G2F3V・G3V・G3F3V |
  | g4 | leather | `sets/auto_g4_leather.json` | `PEOPLE_DIR_G4` | G4V・G4F1V・G4F2V (家族の家を建てる動き。2026-11-27) |
- 最後に `retarget_cmu.py --bvh W/cmu/una/data --src <作業の置き場> --out W/people_glb_<組> --config <設定>` で動きをつける。

## 3. 動画を撮る
- `sim/society/video/render_all.sh` は、この PC 用の決まりがすでにある (`GPU=1`・`PY=py`・Chrome の場所が既定)。`LIBS` はいらない。
- 撮る: `PEOPLE_DIR_HIDE=W/people_glb_hide PEOPLE_DIR_G2=W/people_glb_g2 bash sim/society/video/render_all.sh <名前>` (例 `G1V`)。できた動画は `sim/society/app/society_<名前>.mp4`。
- 新しい動画は、先に絵コンテ (`--storyboard <名前>`) → `video_review_loop.md` の見直し → 本番、の順。
- 撮ったら、長さ (秒) がナレーションと合うか確かめて、私に「どの動画ができたか・長さ・気になった所」を日本語で短く伝える。

## 4. 今やること (2026-11-26 の時点)
1. 準備と、hide と g2 の組のモデル作り。
2. まず 1 本 (G1F1V、約 2 分) を撮って、GPU で描けているか・クラウドで撮ったものと同じ見た目かを確かめる。
3. つぎに、まだの動画 (クラウドで撮れなかったもの。`out/ordered.log` と `sim/society/app/` を見て判断) を撮る。
4. そのあとは、G4 からの動画を同じしかけで (ヤギが増えたら服は leather。家族の小屋は 1590 日目から)。見せ方のコードを直したら、コミットして push する。

## 5. 追加 (2026-11-27): G4 の 3 本 (家を建てる動き)
本人「家を建てるモーションが入っている動画がなく…そこの動画があればすぐ見たい」。クラウドで見せ方を直した (`houseBuild`)。
1. `git pull`。G4 の人のモデルは作らなくてよい (2026-11-28 から、非公開の素材のリポジトリ `Ryo-Tanohata/kawabe-assets` に置いてある)。`render_all.sh` が札 `sim/society/assets.json` を読み、`sim/society/tools/fetch_assets.sh g4` で `.kawabe_work/assets/` に自動で取ってくる (本人の GitHub のログインで読める)。
2. 絵コンテ: `bash sim/society/video/render_all.sh --storyboard G4V` → `video_review_loop.md` の見直し。とくに K6 (建てる様子)・K1/K16 (家にめり込む・すり抜け)・家が柱 → 壁 → 屋根とできていくか (1591 日目 フウの家 1 割、1625 日目 フウの家ができる、1636 日目 ナギの家ができる、1680 日目 トワの家を建てはじめ)。
3. 本番: `bash sim/society/video/render_all.sh G4F1V G4F2V` (G4V は 2026-11-28 にクラウドで撮った)。

--- ここまで ---
