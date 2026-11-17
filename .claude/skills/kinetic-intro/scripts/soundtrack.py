#!/usr/bin/env python3
"""Synthesise a beat-locked soundtrack for a kinetic intro from a cue sheet.

    python3 soundtrack.py cues.json out.wav

The point is not great music; it is a bed whose hits land exactly on the
picture's cuts, with the tension gap (silence before the answer) built in.
Swap in a licensed track later and keep the same cue times.

Cue sheet (all times in seconds, bars counted from 0):
{
  "bpm": 128, "duration": 15,
  "chords": [[50,"m"],[46,""],[53,""],[48,""]],   # MIDI root + quality, one per bar, loops
  "bars": [ {"kick":1,"hats":1,"clap":1,"bass":1,"pad":1,"arp":1}, ... ],  # {} = silent bar; hats:2 = 16ths
  "mute": [[t0,t1]],          # hard-mute the music bed (the tension gap)
  "impacts": [t], "whooshes": [t_end], "risers": [[t0,t1]],
  "ticks": [[t0,t1]], "chimes": [t], "fade_out": 0.6
}
"""
import json, sys
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def onepole_lp(x, a):
    """One-pole low-pass; a may be scalar or per-sample array in (0,1]."""
    y = np.empty_like(x); acc = 0.0
    a = np.broadcast_to(a, x.shape)
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc); y[i] = acc
    return y


def env(n, attack, decay):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / decay)
    return e


def place(buf, sig, t, gain=1.0):
    i = int(round(t * SR))
    if i >= len(buf): return
    if i < 0: sig, i = sig[-i:], 0
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n] * gain


def kick():
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7)
    s[:120] += rng.standard_normal(120) * 0.3 * np.linspace(1, 0, 120)
    return np.tanh(s * 1.6)


def hat():
    n = int(0.06 * SR); x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # crude high-pass
    return x * env(n, 0.001, 0.015) * 0.5


def clap():
    n = int(0.25 * SR); x = rng.standard_normal(n)
    x = x - onepole_lp(x, 0.08)
    e = env(n, 0.002, 0.07)
    for d in (0.010, 0.021):  # the three-flam clap shape
        k = int(d * SR); e[k:] += env(n - k, 0.001, 0.05)[: n - k] * 0.6
    t = np.arange(n) / SR
    return (x * e * 0.6 + np.sin(2 * np.pi * 190 * t) * env(n, 0.001, 0.05) * 0.3)


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f * (1 + detune)) % 1) - 1


def midi(m): return 440 * 2 ** ((m - 69) / 12)


def chord_notes(root, q):
    third = 3 if q == "m" else 4
    return [root, root + third, root + 7, root + 12]


def impact():
    n = int(1.8 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (38 + 40 * np.exp(-t * 9)) * t) * np.exp(-t * 2.2)
    noise = rng.standard_normal(n); noise = onepole_lp(noise, 0.25) * env(n, 0.001, 0.18)
    return np.tanh((boom * 1.2 + noise * 0.8) * 1.4)


def whoosh(length=0.55):
    n = int(length * SR); x = rng.standard_normal(n)
    p = np.linspace(0, 1, n)
    a = 0.02 + 0.5 * p ** 2
    y = onepole_lp(x, a)
    e = p ** 2.2 * (1 - np.clip((p - 0.93) / 0.07, 0, 1))
    return y * e * 1.2


def riser(length):
    n = int(length * SR); p = np.linspace(0, 1, n); t = np.arange(n) / SR
    f = 200 * 2 ** (p * 3)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    noise = onepole_lp(rng.standard_normal(n), 0.03 + 0.4 * p) * 0.6
    return (tone + noise) * p ** 2


def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 300) * 0.35


def chime(root=74):
    n = int(2.2 * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for i, m in enumerate([root, root + 7, root + 12, root + 16]):
        d = int(i * 0.045 * SR)
        s[d:] += np.sin(2 * np.pi * midi(m) * t[: n - d]) * np.exp(-t[: n - d] * 2.4) * (0.5 - i * 0.07)
    return s


def build(c):
    dur, bpm = c["duration"], c["bpm"]
    beat = 60 / bpm; bar = beat * 4
    N = int((dur + 2) * SR)
    drums, bassb, padb, fx = (np.zeros(N) for _ in range(4))
    side = np.ones(N)  # sidechain gain from kick
    chords = c.get("chords", [[50, "m"], [46, ""], [53, ""], [48, ""]])
    K, H, C = kick(), hat(), clap()
    for bi, b in enumerate(c["bars"]):
        t0 = bi * bar
        root, q = chords[bi % len(chords)]
        if b.get("pad"):
            n = int(bar * SR); s = np.zeros(n)
            for m in chord_notes(root + 12, q):
                for d in (-0.006, 0.006):
                    s += saw(midi(m), n, d)
            s = onepole_lp(s / 8, 0.06) * 0.35
            place(padb, s, t0)
        for k in range(4):
            tb = t0 + k * beat
            if b.get("kick"):
                place(drums, K, tb, 0.9)
                i = int(tb * SR); m = min(int(0.22 * SR), N - i)
                side[i:i + m] = np.minimum(side[i:i + m], 0.25 + 0.75 * np.linspace(0, 1, m) ** 1.5)
            if b.get("clap") and k in (1, 3): place(drums, C, tb, 0.55)
            if b.get("hats"):
                place(drums, H, tb + beat / 2, 0.5)
                if b.get("hats") == 2: place(drums, H, tb + beat / 4, 0.25); place(drums, H, tb + 3 * beat / 4, 0.25)
            if b.get("arp"):  # eighth-note pluck arpeggio: gives long pieces a melody line
                pat = [0, 1, 2, 3, 2, 1, 0, 2]
                notes = chord_notes(root + 24, q)
                for h in range(2):
                    m = notes[pat[(k * 2 + h) % 8]]
                    n = int(0.3 * SR); f = midi(m)
                    s = (np.sin(2 * np.pi * f * np.arange(n) / SR) + 0.15 * saw(f, n)) * env(n, 0.002, 0.12)
                    place(padb, s, tb + h * beat / 2, 0.16)
            if b.get("bass"):
                n = int(beat * SR * 0.9); f = midi(root - 12)
                s = np.sin(2 * np.pi * f * np.arange(n) / SR) + 0.3 * saw(f, n)
                s = onepole_lp(s, 0.12) * env(n, 0.005, 0.25) * 0.55
                place(bassb, s, tb + beat / 2)  # off-beat bass = drive
    music = drums + (bassb + padb) * side
    for t0, t1 in c.get("mute", []):
        i0, i1 = int(t0 * SR), int(t1 * SR); r = int(0.012 * SR)
        g = np.ones(N); g[i0:i1] = 0
        g[max(0, i0 - r):i0] = np.linspace(1, 0, min(r, i0)); music *= g
    for t in c.get("impacts", []): place(fx, impact(), t, 0.9)
    for t in c.get("whooshes", []): w = whoosh(); place(fx, w, t - len(w) / SR, 0.5)
    for t0, t1 in c.get("risers", []): place(fx, riser(t1 - t0), t0, 0.45)
    for t0, t1 in c.get("ticks", []):
        t = t0
        while t < t1 - 1e-6: place(fx, tick(), t); t += beat
    for t in c.get("chimes", []): place(fx, chime(), t, 0.5)
    mix = np.tanh((music * 0.8 + fx) * 1.1)[: int(dur * SR)]
    fo = int(c.get("fade_out", 0.6) * SR)
    mix[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    mix /= np.max(np.abs(mix)) / 0.89  # -1 dBFS peak
    return mix


def write_wav(path, x):
    import wave
    st = np.stack([x, x], 1)
    data = (np.clip(st, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data)


if __name__ == "__main__":
    cues = json.load(open(sys.argv[1]))
    write_wav(sys.argv[2], build(cues))
    print("wrote", sys.argv[2])
