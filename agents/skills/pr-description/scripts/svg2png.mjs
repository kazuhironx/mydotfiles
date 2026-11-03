#!/usr/bin/env node
// Render an SVG figure to a PNG at 2x for a PR attachment.
// Run with the tool directory from setup.sh as cwd, so playwright resolves:
//   (cd "$TOOLS" && node <skill>/scripts/svg2png.mjs in.svg out.png [width])
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const [src, out, width = '1040'] = process.argv.slice(2);
if (!src || !out) { console.error('usage: svg2png.mjs <in.svg> <out.png> [width]'); process.exit(2); }
const { chromium } = createRequire(join(process.cwd(), 'package.json'))('playwright');
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: Number(width), height: 800 }, deviceScaleFactor: 2, colorScheme: 'light' });
await p.setContent(`<html><body style="margin:0;background:#fff">${readFileSync(src, 'utf8')}</body></html>`);
await p.locator('svg').first().screenshot({ path: out });
await b.close();
console.log(out);
