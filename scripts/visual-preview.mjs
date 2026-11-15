// Capture the built site on a GitHub-hosted runner, without publishing it.
// The resulting gallery embeds screenshots and works without a web server.
import { spawn } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

if (process.env.GITHUB_ACTIONS !== 'true') {
  throw new Error('Visual previews must run in GitHub Actions.');
}

const { chromium } = await import(pathToFileURL(join(
  process.env.RUNNER_TEMP,
  'opsmith-visual-preview/node_modules/playwright/index.mjs',
)).href);

const origin = 'http://127.0.0.1:4321';
const output = 'artifacts/visual-preview';
const runUrl = `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`;
const commit = process.env.GITHUB_SHA;
const escape = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[char]));

await mkdir(output, { recursive: true });

const server = spawn(process.execPath, [
  'node_modules/astro/astro.js', 'preview', '--host', '127.0.0.1', '--port', '4321',
], { stdio: 'inherit' });
let serverError;
server.on('error', (error) => { serverError = error; });

async function waitForServer() {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (serverError) throw serverError;
    if (server.exitCode !== null) throw new Error(`Preview server exited: ${server.exitCode}`);
    try {
      const response = await fetch(origin, { signal: AbortSignal.timeout(1000) });
      await response.body?.cancel();
      if (response.ok) return;
    } catch {}
    await delay(250);
  }
  throw new Error('Preview server did not start on the GitHub runner.');
}

const variants = [];
const viewports = [
  { id: 'desktop', label: 'Компьютер', width: 1440, height: 1000 },
  { id: 'mobile', label: 'Телефон', width: 390, height: 844 },
];
const themes = [
  { id: 'dark', label: 'Тёмная тема', hour: 22 },
  { id: 'light', label: 'Светлая тема', hour: 12 },
];
let browser;

try {
  await waitForServer();
  browser = await chromium.launch();

  for (const viewport of viewports) {
    for (const theme of themes) {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
        deviceScaleFactor: 1,
        isMobile: viewport.id === 'mobile',
        hasTouch: viewport.id === 'mobile',
        locale: 'ru-RU',
        timezoneId: 'UTC',
        reducedMotion: 'reduce',
      });
      // Screenshots need only the built assets; do not send preview visits to analytics.
      await context.route('**/*', (route) =>
        new URL(route.request().url()).origin === origin ? route.continue() : route.abort()
      );
      const page = await context.newPage();
      const clock = new Date();
      clock.setUTCHours(theme.hour, 0, 0, 0);
      // The site's real day/night switch uses the visitor's clock.
      await page.clock.setFixedTime(clock);

      const variant = {
        id: `${viewport.id}-${theme.id}`,
        label: `${viewport.label} · ${theme.label}`,
        width: viewport.width,
        height: viewport.height,
        shots: [],
      };

      async function visit(path) {
        const response = await page.goto(`${origin}${path}`, { waitUntil: 'load' });
        if (!response?.ok()) throw new Error(`Cannot render ${path}: ${response?.status()}`);
        await page.evaluate(() => document.fonts.ready);
      }

      async function capture(id, label, locator) {
        const filename = `${variant.id}-${id}.jpg`;
        await (locator ?? page).screenshot({
          path: join(output, filename),
          type: 'jpeg',
          quality: 88,
          animations: 'disabled',
          caret: 'hide',
          // A sticky header would otherwise cover content in tall section crops.
          style: locator ? 'header { visibility: hidden !important; }' : undefined,
        });
        variant.shots.push({ filename, label });
        console.log(`Captured ${filename}`);
      }

      await visit('/');
      await capture('home-hero', 'Главная — первый экран');
      await capture('home-services', 'Главная — направления DevOps', page.locator('.section').first());

      await visit('/services/');
      await capture('services-hero', 'Услуги — первый экран и переходы к заказу');
      await capture('services-details', 'Услуги — новые описания', page.locator('#directions'));

      await visit('/work/');
      await capture('work-faq', 'Процесс — вопросы перед заказом', page.locator('.faq-sec'));

      variants.push(variant);
      await context.close();
    }
  }

  const sections = [];
  for (const [index, variant] of variants.entries()) {
    const figures = [];
    for (const shot of variant.shots) {
      const image = await readFile(join(output, shot.filename));
      figures.push(`<figure>
        <figcaption>${escape(shot.label)}</figcaption>
        <img src="data:image/jpeg;base64,${image.toString('base64')}" alt="${escape(shot.label)}" />
      </figure>`);
    }
    sections.push(`<details class="${variant.id.startsWith('mobile') ? 'mobile' : ''}" ${index === 0 ? 'open' : ''}>
      <summary>${escape(variant.label)} <small>${variant.width} × ${variant.height}</small></summary>
      <div class="shots">${figures.join('\n')}</div>
    </details>`);
  }

  await writeFile(join(output, 'preview.html'), `<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OPSMITH — визуальное превью из GitHub Actions</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; padding: 32px 20px 64px; background: #111216; color: #ededee; font: 16px/1.6 system-ui, sans-serif; }
    main { max-width: 1440px; margin: auto; }
    h1 { font-size: clamp(24px, 4vw, 38px); line-height: 1.2; }
    p { color: #bfc1c9; }
    a { color: #b3e58d; }
    code { font-size: 0.9em; }
    details { margin-top: 20px; border: 1px solid #383a42; border-radius: 12px; overflow: hidden; }
    summary { padding: 18px 24px; cursor: pointer; font-size: 20px; font-weight: 600; background: #1c1e24; }
    summary small { display: inline-block; margin-left: 12px; font-size: 14px; color: #bfc1c9; }
    .shots { display: grid; gap: 24px; padding: 24px; }
    figure { margin: 0; min-width: 0; }
    figcaption { margin-bottom: 10px; font-weight: 600; }
    img { display: block; max-width: 100%; height: auto; border: 1px solid #383a42; border-radius: 8px; }
    .mobile img { width: 390px; }
    @media (max-width: 600px) { .shots { padding: 12px; } summary { padding: 14px; } }
  </style>
</head>
<body>
  <main>
    <h1>OPSMITH · визуальное превью</h1>
    <p>Скриншоты собраны в Chromium на GitHub Actions. Компьютер и телефон, светлая и тёмная темы.
      Раскройте нужный вариант ниже. В отдельных снимках блоков закреплённая шапка скрыта, чтобы не перекрывать текст.</p>
    <p>Коммит <code>${escape(commit.slice(0, 7))}</code> · <a href="${escape(runUrl)}">Сборка и исходные изображения</a>.
      Это галерея снимков, а не опубликованная версия сайта.</p>
    ${sections.join('\n')}
  </main>
</body>
</html>`);

  await writeFile(join(output, 'manifest.json'), JSON.stringify({
    commit, runUrl, capturedAt: new Date().toISOString(), variants,
  }, null, 2));
} finally {
  await browser?.close();
  server.kill('SIGTERM');
}
