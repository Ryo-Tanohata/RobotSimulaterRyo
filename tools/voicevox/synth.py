"""ずんだもんの声で文章を読み上げて wav に保存する (VOICEVOX CORE)。
   python synth.py <セリフの一覧.json> <出力フォルダ> [保存先 (setup.sh と同じ)]
   セリフの一覧: [{"id": "s01", "text": "..."}, ...] → 出力フォルダ/s01.wav と durations.json (各セリフの秒数)
生成した音声には「VOICEVOX:ずんだもん」のクレジット表記が必要。"""
import json, sys, wave, io, os
from pathlib import Path
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

ZUNDAMON_NORMAL = 3  # 話者: ずんだもん (ノーマル)

lines = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
base = Path(sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser("~/.cache/robotsim-voicevox"))
ort = Onnxruntime.load_once(filename=str(next(base.glob("voicevox_onnxruntime-linux-x64-*/lib/libvoicevox_onnxruntime.so.*.*.*"))))
syn = Synthesizer(ort, OpenJtalk(str(base / "open_jtalk_dic_utf_8-1.11")))
with VoiceModelFile.open(str(base / "vvms" / "0.vvm")) as m:
    syn.load_voice_model(m)
durations = {}
for line in lines:
    q = syn.create_audio_query(line["text"], ZUNDAMON_NORMAL)
    q.speed_scale = line.get("speed", 1.1)
    wav = syn.synthesis(q, ZUNDAMON_NORMAL)
    (out / f"{line['id']}.wav").write_bytes(wav)
    with wave.open(io.BytesIO(wav)) as w:
        durations[line["id"]] = w.getnframes() / w.getframerate()
    print(f"{line['id']}: {durations[line['id']]:.2f}s  {line['text']}")
(out / "durations.json").write_text(json.dumps(durations, ensure_ascii=False, indent=1), encoding="utf-8")
