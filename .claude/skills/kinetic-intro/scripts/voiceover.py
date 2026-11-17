#!/usr/bin/env python3
"""Voice-over for a kinetic intro: synthesise timed lines offline with Kokoro,
fit each line into its slot, and mix over the music with ducking.

    python voiceover.py vo.json --model-dir DIR --music soundtrack.wav --out mix.wav [--voice hm_omega]

Setup, once per session (GitHub release downloads; nothing leaves the machine):
    python3 -m venv venv && venv/bin/pip install kokoro-onnx soundfile
    curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
    curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
Run this script with venv/bin/python -I.

vo.json: {"voice": "hm_omega", "lang": "hi", "speed": 1.0,
          "lines": [{"t": 0.7, "text": "...", "speed": 1.05?}, ...]}
Hindi voices: hm_omega, hm_psi (male) · hf_alpha, hf_beta (female).
Write English words in Devanagari (वोकल फ़ॉर सनातन) so the Hindi voice says them naturally.
A line that runs into the next one's start is sped up (max 1.25x), and the report flags it.
"""
import argparse, json, os, subprocess, tempfile
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ap = argparse.ArgumentParser()
ap.add_argument("vo"); ap.add_argument("--model-dir", required=True)
ap.add_argument("--music"); ap.add_argument("--out", required=True)
ap.add_argument("--voice"); ap.add_argument("--duration", type=float)
ap.add_argument("--vo-db", type=float, default=0.0, help="voice gain in dB")
a = ap.parse_args()

cfg = json.load(open(a.vo))
voice = a.voice or cfg.get("voice", "hm_omega")
lang = cfg.get("lang", "hi")
k = Kokoro(os.path.join(a.model_dir, "kokoro-v1.0.onnx") if os.path.exists(os.path.join(a.model_dir, "kokoro-v1.0.onnx"))
           else os.path.join(a.model_dir, "kokoro.onnx"),
           os.path.join(a.model_dir, "voices-v1.0.bin") if os.path.exists(os.path.join(a.model_dir, "voices-v1.0.bin"))
           else os.path.join(a.model_dir, "voices.bin"))

def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(0, idx[0] - 240): idx[-1] + 2400] if len(idx) else x

lines = cfg["lines"]
clips, sr = [], 24000
for i, ln in enumerate(lines):
    slot = (lines[i + 1]["t"] - ln["t"] - 0.08) if i + 1 < len(lines) else 99
    sp = ln.get("speed", cfg.get("speed", 1.0))
    x, sr = k.create(ln["text"], voice=voice, speed=sp, lang=lang); x = trim(x)
    d = len(x) / sr
    if d > slot and sp < 1.25:
        sp = min(1.25, sp * d / slot)
        x, sr = k.create(ln["text"], voice=voice, speed=sp, lang=lang); x = trim(x); d = len(x) / sr
    flag = "  << OVERLAPS next line" if d > slot else ""
    print(f"{ln['t']:6.2f}s  {d:4.2f}s / slot {min(slot, 99):5.2f}s  x{sp:.2f}  {ln['text']}{flag}")
    clips.append((ln["t"], x))

end = a.duration or (max(t + len(x) / sr for t, x in clips) + 1)
vo = np.zeros(int(end * sr) + sr)
for t, x in clips:
    i = int(t * sr); vo[i:i + len(x)] += x[: len(vo) - i]
vo = vo[: int(end * sr)]
vo /= max(1e-9, np.max(np.abs(vo))) / 0.89

tmp = tempfile.mkdtemp()
vpath = os.path.join(tmp, "vo.wav"); sf.write(vpath, vo, sr)
# voice chain: high-pass rumble, presence lift, gentle compression, short room
vchain = (f"highpass=f=90,equalizer=f=3200:t=q:w=1.2:g=3,equalizer=f=250:t=q:w=1:g=-2,"
          f"acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=3,"
          f"aecho=0.8:0.5:28:0.12,volume={a.vo_db}dB,aresample=48000,aformat=channel_layouts=stereo")
if a.music:
    fc = (f"[1:a]{vchain},asplit=2[v][sc];"
          f"[0:a]aresample=48000,volume=-3dB[m];"
          f"[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350:makeup=1[duck];"
          f"[duck][v]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[out]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", a.music, "-i", vpath, "-filter_complex", fc, "-map", "[out]", a.out]
else:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", vpath, "-af", vchain, a.out]
subprocess.run(cmd, check=True)
print("wrote", a.out)
