# Vocal for Sanatan: 15 s channel intro

- `out/intro-16x9.mp4` (1920×1080, YouTube intro) · `out/intro-9x16.mp4` (1080×1920, Shorts/Reels)
- Built with the `kinetic-intro` skill (`.claude/skills/kinetic-intro`). 128 BPM, so the 32 beats run exactly 15 s.

| beats | time | scene |
|---|---|---|
| 0–8 | 0–3.75 | saffron wipe → logo slam (impact) → VOCAL / FOR / SANATAN, one word per beat → pillars tagline |
| 8–16 | 3.75–7.5 | "Shop नहीं है?" → **music cuts out** → "कोई समस्या नहीं!" lands on the drop |
| 16–21 | 7.5–9.8 | धर्म · संस्कृति · सेवा · स्वदेशी · समृद्धि, one per beat, hard colour cuts |
| 21–24 | 9.8–11.25 | "Shop नहीं… फिर भी Business है!" under a riser |
| 24–32 | 11.25–15 | iris → logo resolve + chime → Subscribe tap → hold |

Re-render: see `.claude/skills/kinetic-intro/SKILL.md` §4. Preview: open `intro.html` in a browser.
The soundtrack is synthesised (`cues.json`). To use a licensed track, keep these cue times.
The logo was cut from a frame of the promo video, so a high-res PNG dropped into `assets/logo.png` will sharpen it.

---

# 90 s app introduction (`intro-90.html`)

- `out/intro-90s-16x9.mp4` · `out/intro-90s-9x16.mp4`. 128 BPM, so 48 bars run exactly 90.0 s. Soundtrack: `cues-90.json` → `soundtrack-90.wav`.

| time | act | on screen |
|---|---|---|
| 0–3.75 | Hook | logo slam → VOCAL / FOR / SANATAN → pillars |
| 3.75–7.5 | | "Shop नहीं है?" → silence → "दुकान हो या न हो, भरोसा पूरा है।" |
| 7.5–15 | Problem | navy: "हुनर है… पर पहचान नहीं।" · paper: "ज़रूरत है… पर भरोसेमंद कौन?" |
| 15–18.75 | Gap | split: ग्राहक "अच्छा कारीगर कहाँ मिले?" / Service Provider "काम आता है, ग्राहक कहाँ मिलें?" (music drops out) |
| 18.75–26.25 | Answer | iris → logo: "पेश है — एक App, जो अपनों को अपनों से जोड़े।" |
| 26.25–30 | | "आपके पास, आपके अपने।" + Find your people. Grow together. |
| 30–41.25 | How it works | ग्राहक के लिए: खोजें → देखें → जुड़ें |
| 41.25–52.5 | | Business और Service Provider के लिए: Register करें → Profile बनाइए → ग्राहक पाइए |
| 52.5–60 | Everyone | 16 trades, one per beat (Electrician … और भी बहुत कुछ…) |
| 60–67.5 | Values | धर्म · संस्कृति · सेवा · स्वदेशी · समृद्धि → "हर हुनर को पहचान, हर ज़रूरत को अपना साथ।" |
| 67.5–75 | Heart | "दुकान हो या न हो, पहचान है, हुनर है, और भरोसा पूरा है।" |
| 75–82.5 | | "अपनों से खरीदें, अपनों को आगे बढ़ाएँ।" |
| 82.5–90 | CTA | logo + "आपके पास, आपके अपने।" + "आज ही जुड़ें" tap → "जुड़ गए ✓" |

Every scene is one line in the SCRIPT block of `intro-90.html` (beat numbers + text). Edit the copy there and re-render.

## Voice-over

- Script with timings and English meaning: `voiceover-script.md` (sources: `vo-90.json`, `vo-15.json`).
- 15 s intro: `out/intro-{16x9,9x16}-vo-{male,female}.mp4`.
- `out/intro-90s-{16x9,9x16}-vo-male.mp4` (Kokoro `hm_omega`) · `out/intro-90s-{16x9,9x16}-vo-female.mp4` (`hf_alpha`).
- Regenerate: see `.claude/skills/kinetic-intro/scripts/voiceover.py` (offline Kokoro TTS + ducking mix), then re-mux. No video re-render needed.
