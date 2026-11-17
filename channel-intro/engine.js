/* kinetic-intro engine — deterministic, frame-accurate motion for HTML compositions.
 *
 * A composition is a pure function draw(t) that sets every style from the time t
 * (seconds). No CSS animations or transitions: that is what makes the render
 * frame-exact and lets render.mjs seek to any frame.
 *
 * Page contract (read by render.mjs):
 *   window.__ready  Promise that resolves once fonts and images are loaded
 *   window.__seek(t) draws the frame at t seconds
 *   window.__meta   { duration, fps }
 */
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;

  const ease = {
    linear: x => x,
    inCubic: x => x * x * x,
    outCubic: x => 1 - Math.pow(1 - x, 3),
    outQuint: x => 1 - Math.pow(1 - x, 5),
    outExpo: x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)),
    inExpo: x => (x <= 0 ? 0 : Math.pow(2, 10 * x - 10)),
    inOutCubic: x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    inOutExpo: x => x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2,
    outBack: x => { const s = 1.9; return 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2); },
    // damped spring that settles by x=1: the "slam and settle" used for hits
    spring: x => (x >= 1 ? 1 : 1 - Math.exp(-6.5 * x) * Math.cos(11 * x)),
  };

  /* kf(t, [[t0, v0], [t1, v1, 'outExpo'], ...])
   * Keyframes; the ease named on a key shapes the segment arriving at it.
   * Values may be numbers or arrays of numbers. */
  function kf(t, keys) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [t1, v1, e] = keys[i];
      if (t <= t1) {
        const [t0, v0] = keys[i - 1];
        const p = (ease[e || 'outCubic'])(clamp((t - t0) / (t1 - t0 || 1e-9)));
        return Array.isArray(v0) ? v0.map((a, j) => lerp(a, v1[j], p)) : lerp(v0, v1, p);
      }
    }
    return keys[keys.length - 1][1];
  }

  /* Directional motion blur from velocity. fn(t) -> [x, y] in px.
   * Returns a CSS filter string: a blur scaled by speed, which is how the
   * reference intro sells its slides (the ghost trail on every entrance). */
  function motionBlur(fn, t, k = 0.035, max = 28) {
    const dt = 1 / 60;
    const a = fn(t), b = fn(t - dt);
    const v = Math.hypot(a[0] - b[0], a[1] - b[1]) / dt; // px/s
    const r = Math.min(max, v * k * dt * 2);
    return r > 0.35 ? `blur(${r.toFixed(2)}px)` : 'none';
  }

  /* Camera shake that decays after an impact time. */
  function shake(t, at, amp = 14, dur = 0.35) {
    const d = t - at;
    if (d < 0 || d > dur) return [0, 0];
    const fall = Math.pow(1 - d / dur, 2);
    return [Math.sin(d * 97) * amp * fall, Math.cos(d * 131) * amp * 0.7 * fall];
  }

  /* Beat grid helper: beat(n) -> seconds. */
  function grid(bpm, offset = 0) { const b = 60 / bpm; return n => offset + n * b; }

  /* Set many styles at once; skips unchanged values. */
  function css(el, props) {
    for (const k in props) {
      const v = String(props[k]);
      if (el.style[k] !== v) el.style[k] = v;
    }
  }

  /* Wire up a composition. draw(t) does the work. */
  function compose({ duration, fps = 30, draw }) {
    window.__meta = { duration, fps };
    const imgs = [...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; }));
    window.__ready = Promise.all([document.fonts.ready, ...imgs]).then(() => draw(0));
    window.__seek = t => draw(t);

    // Live preview when opened in a browser (render.mjs adds ?render=1).
    if (!new URLSearchParams(location.search).has('render')) {
      window.__ready.then(() => {
        const bar = document.createElement('input');
        Object.assign(bar, { type: 'range', min: 0, max: duration, step: 1 / fps, value: 0 });
        Object.assign(bar.style, { position: 'fixed', left: '2%', right: '2%', bottom: '8px', width: '96%', zIndex: 9999 });
        document.body.appendChild(bar);
        let start = performance.now(), scrubbing = false;
        bar.addEventListener('input', () => { scrubbing = true; draw(+bar.value); });
        bar.addEventListener('change', () => { scrubbing = false; start = performance.now() - bar.value * 1000; });
        const loop = now => {
          if (!scrubbing) { const t = ((now - start) / 1000) % duration; bar.value = t; draw(t); }
          requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
      });
    }
  }

  window.KI = { clamp, lerp, ease, kf, motionBlur, shake, grid, css, compose };
})();
