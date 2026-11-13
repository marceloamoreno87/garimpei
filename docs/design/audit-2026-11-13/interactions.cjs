async page => {
  const app = '__APP_ORIGIN__';
  const setup = '__SETUP_ORIGIN__';
  const passed = [];
  const assert = (ok, name) => { if (!ok) throw Error(name); passed.push(name); };
  await page.route('**/static/**', route => route.continue());
  await page.setViewportSize({width: 1440, height: 960});
  await page.goto(app + '/ofertas/');
  await page.getByRole('tab', {name: /Com defeito/}).click();
  await page.waitForFunction(() => document.activeElement.matches('[role=tab][aria-selected=true]') && document.activeElement.textContent.includes('Com defeito'));
  assert(true, 'Clicking a condition tab preserves focus on its selected replacement');
  await page.keyboard.press('ArrowRight');
  await page.waitForURL('**/ofertas/?aba=incerta&**');
  await page.waitForFunction(() => document.activeElement.matches('[role=tab][aria-selected=true]'));
  assert(true, 'ArrowRight selects the next condition and restores keyboard focus');
  await page.keyboard.press('Home');
  await page.waitForURL('**/ofertas/?aba=funcionam&**');
  await page.waitForFunction(() => document.activeElement.matches('[role=tab][aria-selected=true]'));
  assert(true, 'Home returns to the first condition');
  await page.locator('#exploration-search').fill('Câmera');
  await page.locator('#exploration-search').press('Enter');
  await page.waitForFunction(() => document.querySelector('#exploration')?.dataset.canonical.includes('q=C%C3%A2mera'));
  await page.waitForFunction(() => document.activeElement.id === 'exploration-search');
  assert(await page.locator('#exploration-search').inputValue() === 'Câmera', 'Enter preserves search text and focus');
  await page.getByRole('button', {name:'Filtrar ofertas'}).click();
  await page.waitForFunction(() => document.activeElement.id === 'results-title');
  assert(true, 'Filter button moves focus to the result summary');
  await page.getByRole('link', {name:'Próxima',exact:true}).click();
  await page.waitForFunction(() => document.querySelector('#exploration')?.dataset.canonical.includes('pagina=2') && document.activeElement.id === 'results-title');
  assert(true, 'Pagination announces and focuses its new result summary');
  await page.locator('.offer-title').first().click();
  const detailUrl = new URL(page.url());
  assert(detailUrl.searchParams.get('q') === 'Câmera' && detailUrl.searchParams.get('pagina') === '2', 'Offer detail preserves search and page context');
  await page.getByRole('link',{name:'Voltar aos resultados'}).click();
  assert(new URL(page.url()).searchParams.get('pagina') === '2', 'Return to results preserves the selected page');
  await page.locator('.filter-reset').click();
  await page.waitForFunction(() => document.querySelector('#exploration-search')?.value === '' && document.activeElement.id === 'results-title');
  assert(true, 'Clear filters resets the search with an announced result summary');

  await page.goto(setup + '/configuracao/regiao/');
  await page.locator('#cep').fill('12');
  await page.getByRole('button',{name:'Salvar e continuar'}).click();
  await page.locator('#form-error').waitFor();
  await page.waitForFunction(() => document.activeElement.id === 'form-error');
  assert(await page.locator('#cep').inputValue() === '12', 'Invalid form focuses its error and preserves input');
  await page.locator('#cep').fill('01001000');
  const failSave = route => route.request().method() === 'POST' ? route.abort('failed') : route.continue();
  await page.route(setup + '/configuracao/regiao/', failSave);
  await page.getByRole('button',{name:'Salvar e continuar'}).click();
  await page.locator('#transport-error').waitFor();
  assert(await page.locator('#cep').inputValue() === '01001000', 'Transport failure preserves the filled form');
  assert(await page.locator('button[type=submit]').isEnabled(), 'Failed save restores the submit action');
  assert(await page.evaluate(() => document.activeElement.id === 'transport-error'), 'Transport error receives visible keyboard focus');
  await page.unroute(setup + '/configuracao/regiao/', failSave);
  await page.screenshot({path:'docs/design/audit-2026-11-13/evidence/after-save-network-error.png',fullPage:true});

  await page.goto(app + '/integracoes/');
  const failStatus = route => route.abort('failed');
  await page.route('**/integracoes/facebook/status/**', failStatus);
  await page.evaluate(() => htmx.ajax('GET', '/integracoes/facebook/status/', {target:'#facebook-access',swap:'outerHTML'}).catch(() => {}));
  assert(await page.locator('#transport-error').count() === 0, 'Connection status failures do not inject a save error into another form');
  await page.unroute('**/integracoes/facebook/status/**', failStatus);
  await page.locator('.cookie-help summary').click();
  await page.locator('#facebook-cookies').focus();
  assert(await page.locator('#facebook-cookies').isVisible(), 'Advanced integration fields remain discoverable and keyboard accessible');

  await page.goto(app + '/ofertas/');
  await page.keyboard.press('Tab');
  // A fresh document always begins keyboard navigation at the skip link.
  assert(await page.evaluate(() => document.activeElement.matches('.skip')), 'Skip link is the first keyboard destination');
  await page.keyboard.press('Enter');
  assert(await page.evaluate(() => document.activeElement.id === 'main'), 'Skip link moves keyboard focus into main content');

  const noScriptContext = await page.context().browser().newContext({javaScriptEnabled:false});
  const native = await noScriptContext.newPage();
  try {
    await native.goto(app + '/ofertas/');
    await native.locator('#exploration-search').fill('inexistente-xyz');
    await native.getByRole('button',{name:'Filtrar ofertas'}).click();
    assert(await native.getByText('Nenhuma oferta neste recorte').isVisible(), 'Filtering works without JavaScript');
    await native.locator('.filter-reset').click();
    assert(await native.locator('.offer-card').count() > 0, 'Recovery from empty results works without JavaScript');
  } finally { await noScriptContext.close(); }
  await page.goto(app + '/ofertas/?q=C%C3%A2mera+41');
  const negative = page.locator('.financial-profit--negative');
  assert(await negative.count() === 1 && (await negative.textContent()).includes('−R$ 50,00'), 'Negative profit keeps its sign and uses the loss state');
  await page.goto(app + '/ofertas/?q=C%C3%A2mera+42');
  assert(await page.locator('.financial-profit--unavailable').count() === 1, 'Unavailable profit uses a neutral state rather than success color');
  await page.goto(app + '/ofertas/?q=C%C3%A2mera+40');
  assert((await page.locator('.financial-profit dd').textContent()).includes('R$ 0,00'), 'Zero profit remains visible');
  return passed;
}
