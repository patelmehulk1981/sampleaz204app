#!/usr/bin/env node
/* Contact sheet of a composition at chosen times — the fast review loop.
 *   node stills.mjs --html intro.html --out sheet.png [--w 1920 --h 1080] [--times 0.5,1,2] [--cols 6] [--thumb 320]
 * With no --times it samples every 0.25 s across the duration.
 */
import { createRequire } from 'module';
import { execFileSync } from 'child_process';
import fs from 'fs'; import os from 'os'; import path from 'path';
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const a = Object.fromEntries(process.argv.slice(2).reduce((r, v, i, arr) => { if (v.startsWith('--')) r.push([v.slice(2), arr[i + 1]]); return r; }, []));
const W = +(a.w || 1920), H = +(a.h || 1080), cols = +(a.cols || 6), thumb = +(a.thumb || 320);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('console', m => m.type() === 'error' && console.error('[page]', m.text()));
page.on('pageerror', e => console.error('[pageerror]', e.message));
await page.goto(`file://${path.resolve(a.html)}?render=1&w=${W}&h=${H}`);
await page.evaluate(() => window.__ready);
const { duration } = await page.evaluate(() => window.__meta);
const times = a.times ? a.times.split(',').map(Number) : Array.from({ length: Math.floor(duration / 0.25) }, (_, i) => i * 0.25);
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ki-'));
for (const [i, t] of times.entries()) {
  await page.evaluate(t => window.__seek(t), t);
  await page.screenshot({ path: path.join(dir, `f${String(i).padStart(4, '0')}.png`) });
}
await browser.close();
const rows = Math.ceil(times.length / cols);
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '1', '-i', path.join(dir, 'f%04d.png'), '-vf',
  `scale=${thumb}:-1,drawtext=text='%{eif\\:n\\:d}':x=6:y=6:fontsize=14:fontcolor=white:box=1:boxcolor=black@0.6,tile=${cols}x${rows}:padding=4`,
  '-frames:v', '1', path.resolve(a.out)]);
console.log('times:', times.map((t, i) => `${i}=${t}`).join(' '));
console.log('wrote', a.out);
