"""ずんだもんの声で文章を読み上げて wav に保存する (VOICEVOX CORE)。
   python synth.py <セリフの一覧.json> <出力フォルダ> [保存先 (setup.sh と同じ)]
   セリフの一覧: [{"id": "s01", "text": "...", "say": "(読み上げだけ変えたいとき)"}, ...]
   1 文ごとに声を変えるとき: "style" (スタイル ID) と "vvm" (その声の入った音声モデルのファイル名、例 "21.vvm")、
   "speed"・"pitch"・"intonation" (なければ前と同じ。声はずんだもん)。音声モデルは setup.sh の保存先の vvms/ に置く
   → 出力フォルダ/s01.wav、durations.json (各セリフの秒数)、readings.md (読み仮名の一覧表。本人に確認してもらう)
   読みを直したい言葉は tools/voicevox/user_dict.json (ユーザー辞書) に登録する。
生成した音声には「VOICEVOX:ずんだもん」(ほかの声ならその名前) のクレジット表記が必要。"""
import io
import json
import os
import sys
import wave
from pathlib import Path

from voicevox_core import UserDictWord
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, UserDict, VoiceModelFile

ZUNDAMON_NORMAL = 3  # 話者: ずんだもん (ノーマル)

lines = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
base = Path(sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser("~/.cache/robotsim-voicevox"))
ort = Onnxruntime.load_once(filename=str(next(base.glob("voicevox_onnxruntime-linux-x64-*/lib/libvoicevox_onnxruntime.so.*.*.*"))))
ojt = OpenJtalk(str(base / "open_jtalk_dic_utf_8-1.11"))
dict_path = Path(__file__).with_name("user_dict.json")
if dict_path.exists():  # この世界の言葉の読みとアクセント
    ud = UserDict()
    for w in json.loads(dict_path.read_text(encoding="utf-8")):
        ud.add_word(UserDictWord(surface=w["surface"], pronunciation=w["pronunciation"], accent_type=w["accent_type"],
                                 word_type=w.get("word_type", "COMMON_NOUN"), priority=w.get("priority", 8)))
    ojt.use_user_dict(ud)
syn = Synthesizer(ort, ojt)
for vvm in sorted({ln.get("vvm", "0.vvm") for ln in lines}):  # 使う音声モデルだけ読む
    with VoiceModelFile.open(str(base / "vvms" / vvm)) as m:
        syn.load_voice_model(m)
durations, readings = {}, ["# 読み仮名の一覧 (確認用)", "", "| id | 字幕の文 | 読み (カタカナ、' はアクセント) |", "|---|---|---|"]
for line in lines:
    say = line.get("say", line["text"])
    sid = line.get("style", ZUNDAMON_NORMAL)
    q = syn.create_audio_query(say, sid)
    q.speed_scale = line.get("speed", 1.1)
    if "pitch" in line:
        q.pitch_scale = line["pitch"]
    if "intonation" in line:
        q.intonation_scale = line["intonation"]
    wav = syn.synthesis(q, sid)
    (out / f"{line['id']}.wav").write_bytes(wav)
    with wave.open(io.BytesIO(wav)) as w:
        durations[line["id"]] = w.getnframes() / w.getframerate()
    readings.append(f"| {line['id']} | {line['text']} | {q.kana} |")
    print(f"{line['id']}: {durations[line['id']]:.2f}s  {say}")
(out / "durations.json").write_text(json.dumps(durations, ensure_ascii=False, indent=1), encoding="utf-8")
(out / "readings.md").write_text("\n".join(readings) + "\n", encoding="utf-8")
