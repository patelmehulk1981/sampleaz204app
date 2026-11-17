---
name: kinetic-intro
description: Make short, beat-locked kinetic-typography intros and promo openers (5–30 s) as MP4, in a brand's colours and fonts, landscape and vertical from one source. Use when asked for a channel intro, logo sting, reel opener, ad hook or "make it feel like this reference video". Builds an HTML composition driven by a deterministic draw(t), renders it frame-exact with Playwright + ffmpeg, and synthesises a soundtrack whose hits land on the cuts.
---

# Kinetic intro

You make the intro as a **pure function of time**. `draw(t)` sets every style from `t`,
`render.mjs` seeks to each frame and pipes PNGs into ffmpeg, and `soundtrack.py` builds
audio from the same beat grid. Because picture and sound share one clock, every hit lands.

## 1. Read the reference first, if there is one

Pull out the numbers before you design anything:

```bash
ffmpeg -i ref.mp4 -vf "fps=8,scale=180:-1,tile=8x5" -frames:v 1 sheet.png              # motion, 8 fps
ffmpeg -i ref.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep pts_time  # cut times
ffmpeg -i ref.mp4 -af "asetnsamples=3000,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level" -f null - 2>&1 | grep RMS  # silences and hits
```

Note the shot length, where the audio drops out and what lands on the return, the type
weights and colours, and how elements enter (masked rise, blur trail, push).
`reference/analysis.md` has a worked breakdown.

## 2. The rules that make it feel good

1. **Put everything on a grid.** Choose a BPM where `bars × 4 × 60 / bpm` equals the
   duration (128 BPM gives 32 beats in 15.0 s). Every entrance starts on a beat or a half-beat.
2. **One idea per beat, one scene per bar.** Change something about every 0.5 s; never
   hold an unchanged frame longer than about 1.5 s.
3. **Silence before the payoff.** Drop the music for 2–3 beats under the question, then
   bring the answer in on an impact, a shake and a scale overshoot. That gap creates more
   energy than any amount of motion.
4. **Question, answer, proof, brand.** Pose a problem in the cool colour, answer it in the
   hot brand colour, show it rapid-fire, then resolve to the logo and a call to action.
5. **Type:** one heavy geometric sans (Poppins 700–800) paired with a matching Devanagari or
   other script (Hind 700, from the same foundry). Use two colours only: dark navy-type for
   the setup and the brand colour for the payoff. Set headlines at 12–17% of the short side,
   left-aligned stacks for statements and centred for single words. A tiny tracked label
   (`FOR`, `02 / 05`) adds rhythm against the huge words.
6. **Entrances:** masked line rise (`outExpo`, 0.35–0.5 s) with motion blur scaled by
   speed. Hits use the `spring` ease, which overshoots and settles. Exits use `inExpo`, and
   the next scene enters in the same direction so the cut reads as one continuous whip.
7. **Keep the background alive:** a slowly drifting glow, rotating hairline arcs and a
   twinkling sparkle mark. This keeps holds from looking frozen.
8. **Use hard colour cuts for lists.** Swapping the full-frame background on every beat
   produces the most energy for the least effort.
9. **End on a tap.** Show the subscribe/CTA press (cursor, ripple, state change, bell
   wobble), then hold the logo for about 1 s and fade the audio.

## 3. Build

```
project/
  intro.html     composition (copy templates/starter.html)
  engine.js      copy of scripts/engine.js
  cues.json      soundtrack cue sheet (same beat grid)
  assets/        logo.png (transparent), fonts/*.woff2 (npm pack @fontsource/<font>)
```

- Engine API (`KI`): `kf(t, [[t0,v0],[t1,v1,'outExpo']])`, `ease.*` (including `spring`),
  `motionBlur(fn,t)`, `shake(t, at)`, `grid(bpm)`, `css(el, props)`,
  `compose({duration, fps, draw})`.
- **Do not use CSS animations or transitions**, and do not read `Date`/`performance` in `draw`.
- Lay out from `?w=&h=`: `U = min(W,H)/100`, `P = H > W`. One file renders 16:9 and 9:16.
- Put brand colours in `:root` tokens. If no brand kit exists, sample the colours from the
  logo (median of the saturated pixels) and tell the user what you sampled.
- Fonts: get them with `npm pack @fontsource/<name>`, copy the `files/*-latin|devanagari-<wt>-normal.woff2` you need, and declare `@font-face` locally (rendering works offline).

## 4. Review, render, deliver

```bash
S=.claude/skills/kinetic-intro/scripts
node $S/stills.mjs --html intro.html --out sheet.png --times 0.5,2,4,6,8,10,12,14   # check this first
node $S/stills.mjs --html intro.html --w 1080 --h 1920 --out sheet_v.png --times ...
python3 $S/soundtrack.py cues.json soundtrack.wav
node $S/render.mjs --html intro.html --out out/intro-16x9.mp4 --w 1920 --h 1080 --audio soundtrack.wav
node $S/render.mjs --html intro.html --out out/intro-9x16.mp4 --w 1080 --h 1920 --audio soundtrack.wav
```

Look at the sheets before rendering. These faults are common:
- masked text peeking before its beat (`rise` hides it until t0)
- `display` toggles wiping out flex layouts (use `el.dataset.d`)
- words overflowing in 9:16
- a filter on an element replacing its drop-shadow (use `el.dataset.f`)

Rendering takes about 2 minutes per 15 s at 1080p30. Opening `intro.html` in a browser
gives a looping preview with a scrubber.

The synthesised bed is a placeholder whose timing is exact. If the user has a licensed
track, keep the cue times and replace the WAV.
