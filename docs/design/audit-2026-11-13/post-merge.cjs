async page => {
  const app = '__APP_ORIGIN__';
  const cases = [];
  const flow = [];
  const errors = [];
  const recordError = error => errors.push(error.message);
  page.on('pageerror', recordError);
  await page.route('**/static/**', route => route.continue());
  const audit = async (name, status, width) => {
    await page.evaluate(() => document.fonts.ready);
    await page.addScriptTag({path:'docs/design/storybook/node_modules/axe-core/axe.min.js'});
    const result = await page.evaluate(async () => {
      const r = await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
      return {
        violations:r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),
        incomplete:r.incomplete.map(v=>v.id),
        overflow:document.documentElement.scrollWidth > innerWidth + 1,
        h1:document.querySelectorAll('h1').length,
        current:[...document.querySelectorAll('.primary-navigation [aria-current=page]')].map(a=>a.getAttribute('href')),
      };
    });
    cases.push({name,width,status,...result});
    if (result.violations.length || result.incomplete.length || result.overflow || result.h1 !== 1 || result.current.length !== 1) throw Error(JSON.stringify(cases.at(-1)));
    if (['tracking','offers','robot-paused','robot-save-error'].includes(name)) {
      await page.screenshot({path:`docs/design/audit-2026-11-13/evidence/integrated-${name}-${width}.png`,fullPage:true});
    }
  };
  for (const width of [1440,375]) {
    await page.setViewportSize({width,height:960});
    for (const [name,path] of [['tracking','/acompanhamento/'],['offers','/ofertas/'],['detail','/ofertas/00000000-0000-0000-0000-000000000001/'],['settings','/configuracoes/'],['ai','/integracoes/ia/'],['backups','/acompanhamento/backups/'],['suggestions','/sugestoes/']]) {
      const response=await page.goto(app+path);
      if (name==='tracking') await page.locator('#navigation-title').waitFor();
      await audit(name,response.status(),width);
    }
    await page.goto(app+'/acompanhamento/');
    await page.getByRole('button',{name:'Desligar robô',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#robot-heading')?.textContent==='Robô desligado');
    await page.reload();
    if ((await page.locator('#robot-heading').textContent())!=='Robô desligado') throw Error('Paused intent lost on reload');
    flow.push(`Pause persisted through reload at ${width}px`);
    await audit('robot-paused',200,width);
    await page.goto(app+'/ofertas/');
    if (!(await page.locator('aside[aria-label="Estado do robô"]').textContent()).includes('Robô desligado')) throw Error('Offers lost paused summary');
    if (!(await page.locator('.offer-card').count())) throw Error('Paused robot blocked offer consultation');
    flow.push(`Paused robot preserves offer consultation at ${width}px`);
    await audit('offers-paused',200,width);
    await page.goto(app+'/acompanhamento/');
    await page.locator('#robot-control input[name=revision]').evaluate(el=>{el.value='invalid';});
    const failure = page.waitForResponse(response=>response.request().method()==='POST' && response.url().includes('/robo/ligar/'));
    await page.getByRole('button',{name:'Ligar robô',exact:true}).click();
    const response=await failure;
    await page.getByRole('heading',{name:'Não foi possível confirmar a ação',exact:true}).waitFor();
    await audit('robot-save-error',response.status(),width);
    if ((await page.locator('.primary-navigation [aria-current]').getAttribute('href'))!=='/acompanhamento/') throw Error('Robot error selects wrong destination');
    flow.push(`Robot command error retains Acompanhamento orientation at ${width}px`);
    await page.getByRole('link',{name:'Reabrir acompanhamento'}).click();
    await page.getByRole('button',{name:'Ligar robô',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#robot-heading')?.textContent==='Robô ligado');
    flow.push(`Explicit resume restores confirmed intent at ${width}px`);
  }
  page.off('pageerror',recordError);
  if (errors.length) throw Error(JSON.stringify(errors));
  return {cases,flow,page_errors:errors};
}
