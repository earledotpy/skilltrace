// Automated axe-core scan for T-ValidationExecution #344 (wayfinder map #327).
// Decision aid; agent-executed tooling — recorded as such in the observation report.
// Emulation note: "200% zoom" is emulated as a 640px-wide viewport (1280/2, the
// standard Lighthouse-style approximation); the 320px run covers reflow.
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const PAGES = [
  { name: 'p-core-journey.html (Guided)', file: 'C:/skilltrace/prototype/p-core-journey.html' },
  { name: 'p-operations-workspace.html (Operations)', file: 'C:/skilltrace/prototype/p-operations-workspace.html' },
];
const VIEWPORTS = [
  { label: '1280px (desktop, 100%)', width: 1280 },
  { label: '640px (approximates 200% zoom)', width: 640 },
  { label: '320px (reflow)', width: 320 },
];

(async () => {
  const axePath = path.join(__dirname, 'node_modules', 'axe-core', 'axe.min.js');
  const axeVersion = require(path.join(__dirname, 'node_modules', 'axe-core', 'package.json')).version;
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: true });
  const runs = [];
  for (const p of PAGES) {
    for (const v of VIEWPORTS) {
      const page = await browser.newPage();
      await page.setViewport({ width: v.width, height: 900 });
      await page.goto('file:///' + p.file, { waitUntil: 'load' });
      await page.addScriptTag({ path: axePath });
      const res = await page.evaluate(async () => {
        const r = await window.axe.run(document, {
          runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag22aa'] },
          resultTypes: ['violations'],
        });
        return {
          violationCount: r.violations.length,
          violations: r.violations.map((x) => ({
            id: x.id,
            impact: x.impact,
            help: x.help,
            tags: x.tags.filter((t) => t.startsWith('wcag')),
            nodes: x.nodes.map((n) => ({ target: n.target, snippet: (n.html || '').slice(0, 160) })),
          })),
        };
      });
      runs.push({ page: p.name, viewport: v.label, ...res });
      await page.close();
      console.log(`scanned ${p.name} @ ${v.label}: ${res.violationCount} violations`);
    }
  }
  await browser.close();
  const out = {
    tool: 'axe-core',
    axeVersion,
    browser: 'Microsoft Edge (headless), via puppeteer-core',
    executedBy: 'agent (Cline) on behalf of T-ValidationExecution #344 — machine scan only; manual and screen-reader checks remain with the learner',
    date: new Date().toISOString(),
    emulationNote: '200% zoom emulated as a 640px viewport (1280/2); 320px run covers reflow.',
    runs,
  };
  fs.writeFileSync(path.join(__dirname, 'axe-results.json'), JSON.stringify(out, null, 2));
  console.log('written axe-results.json');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
