#!/usr/bin/env node
/* Render a kinetic-intro HTML composition to MP4.
 *
 *   node render.mjs --html path/intro.html --out intro.mp4 \
 *        [--w 1920 --h 1080] [--fps 30] [--dur 15] [--audio track.wav] [--crf 16]
 *
 * Frames are seeked with window.__seek(t) and piped straight into ffmpeg,
 * so nothing touches disk and every frame is exact. ?w=&h= are passed to
 * the page so one composition can lay itself out for 16:9 or 9:16.
 */
import { createRequire } from 'module';
import { spawn } from 'child_process';
import path from 'path';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => {
  if (v.startsWith('--')) a.push([v.slice(2), arr[i + 1]]); return a;
}, []));
const W = +(args.w || 1920), H = +(args.h || 1080), FPS = +(args.fps || 30);
const html = path.resolve(args.html), out = path.resolve(args.out || 'intro.mp4');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('console', m => m.type() === 'error' && console.error('[page]', m.text()));
await page.goto(`file://${html}?render=1&w=${W}&h=${H}`);
await page.evaluate(() => window.__ready);
const meta = await page.evaluate(() => window.__meta);
const DUR = +(args.dur || meta.duration);
const N = Math.round(DUR * FPS);

const ff = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-'];
if (args.audio) ff.push('-i', path.resolve(args.audio));
ff.push('-c:v', 'libx264', '-preset', 'slow', '-crf', String(args.crf || 16), '-pix_fmt', 'yuv420p',
  '-movflags', '+faststart', '-r', String(FPS));
if (args.audio) ff.push('-c:a', 'aac', '-b:a', '256k', '-shortest');
ff.push(out);
const enc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });

const t0 = Date.now();
for (let i = 0; i < N; i++) {
  await page.evaluate(t => window.__seek(t), i / FPS);
  const buf = await page.screenshot({ type: 'png' });
  if (!enc.stdin.write(buf)) await new Promise(r => enc.stdin.once('drain', r));
  if (i % FPS === 0) process.stdout.write(`\rframe ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
enc.stdin.end();
await new Promise((res, rej) => enc.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg exit ' + c))));
await browser.close();
console.log(`\nwrote ${out} (${W}x${H} @${FPS}fps, ${DUR}s)`);
