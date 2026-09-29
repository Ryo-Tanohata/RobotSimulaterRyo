"""動画の音声を作る: ナレーション (VOICEVOX の wav) + 効果音 + BGM を 1 本の wav にまとめる。

  python mix.py film.timeline.json voice_dir out.wav

- film.timeline.json は web/test/record-film.mjs が書き出す (ナレーションの開始時刻と、足音・ゴール・転倒の時刻)
- 効果音と BGM はすべてこのスクリプトの中で数式から作る (外部の音源は使わない)
- 使うのは Python 標準の wave と numpy だけ
"""
import json
import os
import sys
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(1)


def read_wav(path):
    with wave.open(path, 'rb') as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    if sr != SR:  # 線形補間で 48 kHz に
        t = np.arange(int(len(x) * SR / sr)) * sr / SR
        x = np.interp(t, np.arange(len(x)), x).astype(np.float32)
    return x


def env(n, attack, release):
    """立ち上がり attack 秒、指数で減衰 (時定数 release 秒) の包絡線"""
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / release)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


# ---- 効果音 ----
def footstep():
    n = int(0.06 * SR)
    noise = lowpass(rng.standard_normal(n).astype(np.float32), 900)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 110 * t)
    return (noise * 3 + body * 0.5) * env(n, 0.002, 0.012)


def chime():
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k, (f, d) in enumerate([(1046.5, 0.0), (1568.0, 0.12)]):  # ド → ソ
        s = int(d * SR)
        tt = t[: n - s]
        tone = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)
        out[s:] += tone * env(n - s, 0.004, 0.35)
    return out * 0.5


def thud():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 90 * np.exp(-t * 4) + 40  # 下がっていく低音
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    noise = lowpass(rng.standard_normal(n).astype(np.float32), 400) * 2
    return (body + noise) * env(n, 0.003, 0.12)


# ---- BGM: ゆっくりしたコード進行 (C - Am - F - G) のパッドと、軽いアルペジオ ----
def bgm(duration, n):
    out = np.zeros(n, np.float32)
    bar = 4.0  # 1 コード 4 秒 (BPM 60 の 4 拍)
    chords = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    nb = int(bar * SR)
    t = np.arange(nb) / SR
    fade = np.minimum(1, np.minimum(t / 0.8, (bar - t) / 0.8))
    for b in range(int(np.ceil(duration / bar))):
        s = b * nb
        seg = np.zeros(nb, np.float32)
        ch = chords[b % 4]
        for m in ch + [ch[0] - 12]:
            f = hz(m)
            seg += (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 1.003 * t + 1)) * 0.12
        seg *= fade
        # アルペジオ (8 分音符、ベルのような短い音)
        for k in range(8):
            m = ch[[0, 1, 2, 1][k % 4]] + 12
            p = int(k * 0.5 * SR)
            ln = min(int(0.45 * SR), nb - p)
            tt = np.arange(ln) / SR
            seg[p:p + ln] += np.sin(2 * np.pi * hz(m) * tt) * env(ln, 0.005, 0.18) * 0.10
        e = min(n, s + nb)
        out[s:e] += seg[: e - s]
    fin = int(3 * SR)  # 最後の 3 秒でフェードアウト
    out[-fin:] *= np.linspace(1, 0, fin)
    out[: int(1.5 * SR)] *= np.linspace(0, 1, int(1.5 * SR))
    return out


def place(track, clip, t, gain=1.0):
    s = int(t * SR)
    if s >= len(track):
        return
    e = min(len(track), s + len(clip))
    track[s:e] += clip[: e - s] * gain


def main():
    tl_path, voice_dir, out_path = sys.argv[1:4]
    tl = json.load(open(tl_path))
    dur = tl['duration']
    n = int(dur * SR) + 1
    voice = np.zeros(n, np.float32)
    left = np.zeros(n, np.float32)
    right = np.zeros(n, np.float32)

    speaking = np.zeros(n, np.float32)
    for it in tl['narration']:
        clip = read_wav(os.path.join(voice_dir, it['id'] + '.wav'))
        place(voice, clip, it['start'])
        place(speaking, np.ones(len(clip), np.float32), it['start'])

    steps = [footstep() for _ in range(6)]
    ch, th = chime(), thud()
    last = {}
    for k, e in enumerate(tl['events']):
        pan = 0.3 if e['lane'] == 0 else 0.7  # 左のロボット = 左寄り
        if e['type'] == 'step':
            # 同じロボットの足音が 60 ms 以内に重なったら 1 つにまとめる
            if e['t'] - last.get(e['lane'], -1) < 0.06:
                continue
            last[e['lane']] = e['t']
            clip, g = steps[k % len(steps)], 0.09
        elif e['type'] == 'goal':
            clip, g = ch, 0.35
        else:
            clip, g = th, 0.45
        place(left, clip, e['t'], g * (1 - pan) * 2 * 0.7)
        place(right, clip, e['t'], g * pan * 2 * 0.7)

    # BGM は話している間は小さく (ダッキング)。切り替えは 0.3 秒かけてなめらかに
    k = int(0.3 * SR)
    duck = np.convolve(speaking, np.ones(k) / k, mode='same')
    music = bgm(dur, n) * (0.16 - 0.10 * np.clip(duck, 0, 1))

    L = voice * 0.9 + left + music
    R = voice * 0.9 + right + music
    peak = max(np.abs(L).max(), np.abs(R).max())
    if peak > 0.95:
        L, R = L * 0.95 / peak, R * 0.95 / peak
    data = (np.stack([L, R], axis=1) * 32767).astype(np.int16)
    with wave.open(out_path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f'{dur:.1f}s, narration {len(tl["narration"])}, events {len(tl["events"])}, peak {peak:.2f} → {out_path}')


if __name__ == '__main__':
    main()
