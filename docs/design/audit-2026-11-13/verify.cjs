async page => {
  const app = '__APP_ORIGIN__';
  const setup = '__SETUP_ORIGIN__';
  const results = [];
  // Routing also disables the browser cache, so captures always use current CSS.
  await page.route('**/static/**', route => route.continue());
  const cases = [
    ['setup-region', setup, '/configuracao/regiao/'],
    ['setup-costs', setup, '/configuracao/custos/'],
    ['setup-interests', setup, '/configuracao/interesses/'],
    ['setup-offers', setup, '/ofertas/'],
    ['offers', app, '/ofertas/'],
    ['defects', app, '/ofertas/?aba=defeitos'],
    ['uncertain', app, '/ofertas/?aba=incerta'],
    ['filtered-empty', app, '/ofertas/?q=inexistente-xyz'],
    ['offers-last', app, '/ofertas/?pagina=3'],
    ['detail', app, '/ofertas/00000000-0000-0000-0000-000000000001/'],
    ['detail-uncertain', app, '/ofertas/00000000-0000-0000-0000-000000000031/'],
    ['settings', app, '/configuracoes/'],
    ['tracking', app, '/acompanhamento/'],
    ['suggestions', app, '/sugestoes/'],
    ['suggestions-error', app, '/sugestoes/?pagina=0'],
    ['backups', app, '/acompanhamento/backups/'],
    ['integrations', app, '/integracoes/'],
    ['ai', app, '/integracoes/ia/'],
    ['offer-error', app, '/ofertas/?pagina=-1'],
    ['offer-missing', app, '/ofertas/ffffffff-ffff-ffff-ffff-ffffffffffff/'],
  ];
  for (const width of [1440, 768, 375, 320]) {
    await page.setViewportSize({width, height: 960});
    for (const [name, origin, path] of cases) {
      const response = await page.goto(origin + path);
      await page.evaluate(() => document.fonts.ready);
      if (name === 'tracking') await page.locator('#navigation-title').waitFor();
      await page.addScriptTag({path: 'docs/design/storybook/node_modules/axe-core/axe.min.js'});
      const audit = await page.evaluate(async () => {
        const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
        return {
          violations: r.violations.map(v => ({id: v.id, impact: v.impact, nodes: v.nodes.map(n => ({target: n.target, summary: n.failureSummary}))})),
          incomplete: r.incomplete.map(v => ({id: v.id, nodes: v.nodes.length})),
          passes: r.passes.length,
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
          overflowElements: [...document.querySelectorAll('main *, .sidebar *')].filter(el => el.getBoundingClientRect().right > innerWidth + 1).slice(0, 5).map(el => el.tagName + '.' + el.className),
          headings: document.querySelectorAll('h1').length,
          selectedDestinations: document.querySelectorAll('.primary-navigation [aria-current=page]').length,
        };
      });
      results.push({name, width, status: response.status(), ...audit});
      if ([1440, 375].includes(width) && ['setup-region','setup-offers','offers','detail','settings','tracking','suggestions','backups','integrations','ai','offer-error'].includes(name)) {
        await page.screenshot({path: `docs/design/audit-2026-11-13/evidence/after-${name}-${width}.png`, fullPage: true});
      }
    }
  }
  return results;
}
