async page => {
  const app = '__APP_ORIGIN__';
  const results = [];
  const assert = (ok, name) => { if (!ok) throw Error(name); results.push({name, pass:true}); };
  await page.route('**/static/**', route => route.continue());
  await page.setViewportSize({width:375,height:900});
  await page.goto(app + '/ofertas/');
  const menu = page.getByRole('button', {name:'Menu',exact:true});
  assert(!await page.locator('.primary-navigation').isVisible(), 'Narrow navigation starts collapsed');
  await menu.click();
  assert(await page.locator('.primary-navigation [aria-current=page]').isVisible(), 'Menu exposes the selected destination');
  await page.locator('.primary-navigation [aria-current=page]').focus();
  await page.keyboard.press('Escape');
  assert(!await page.locator('.primary-navigation').isVisible() && await menu.evaluate(el => el === document.activeElement), 'Escape closes the menu and restores its trigger focus');
  await page.screenshot({path:'docs/design/audit-2026-11-13/evidence/after-offers-mobile-viewport.png'});
  await page.setViewportSize({width:1440,height:960});
  assert(await page.locator('.primary-navigation').isVisible() && !await menu.isVisible(), 'Desktop navigation remains directly available');
  await page.screenshot({path:'docs/design/audit-2026-11-13/evidence/after-offers-desktop-viewport.png'});

  const touchContext = await page.context().browser().newContext({hasTouch:true, viewport:{width:375,height:900}});
  const touch = await touchContext.newPage();
  try {
    await touch.goto(app + '/ofertas/');
    await touch.getByRole('button',{name:'Menu',exact:true}).tap();
    await touch.getByRole('link',{name:'Sugestões',exact:true}).tap();
    await touch.waitForURL('**/sugestoes/');
    assert(new URL(touch.url()).pathname === '/sugestoes/', 'Menu navigation works with synthesized Chromium touch');
  } finally { await touchContext.close(); }

  for (const width of [1440,375]) {
    await page.setViewportSize({width,height:960});
    for (const path of ['/ofertas/','/ofertas/00000000-0000-0000-0000-000000000001/','/configuracoes/','/acompanhamento/','/integracoes/','/integracoes/ia/','/sugestoes/','/acompanhamento/backups/']) {
      await page.goto(app + path);
      await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `Text at 200% has no horizontal overflow: ${width}/${path}`);
    }
  }

  await page.setViewportSize({width:1440,height:960});
  const failedNavigation = route => route.abort('failed');
  await page.route('**/acompanhamento/navegacao/', failedNavigation);
  await page.goto(app + '/acompanhamento/');
  await page.getByText('Não foi possível carregar o percurso.',{exact:false}).waitFor();
  assert(await page.getByRole('button',{name:'Tentar carregar percurso'}).isVisible(), 'Initial navigation failure offers an immediate recovery action');
  await page.unroute('**/acompanhamento/navegacao/', failedNavigation);
  await page.getByRole('button',{name:'Tentar carregar percurso'}).click();
  await page.locator('#navigation-title').waitFor();
  assert(true, 'Navigation retry replaces the failed loading state with a confirmed reading');

  await page.emulateMedia({forcedColors:'active',reducedMotion:'reduce'});
  await page.goto(app + '/ofertas/');
  assert(await page.locator('.primary-navigation [aria-current]').evaluate(el => getComputedStyle(el).outlineStyle !== 'none'), 'Forced colors preserve the current-page outline');
  assert(await page.locator('.integration-notice').evaluate(el => getComputedStyle(el).animationName === 'none'), 'Reduced motion does not animate the connection feedback');
  await page.emulateMedia({forcedColors:'none',reducedMotion:'no-preference'});
  return results;
}
