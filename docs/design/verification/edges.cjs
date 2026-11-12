async page => {
  const checks=[];
  const assert=(value,label)=>{if(!value)throw new Error(label);checks.push(label);};
  await page.route('**/*',route=>route.continue());await page.setViewportSize({width:375,height:900});
  await page.goto('http://127.0.0.1:4173/prototypes/?view=interests');await page.waitForFunction(()=>window.__GARIMPEI_DEMO__);
  const long='Sony_'+('Alpha6000'.repeat(18))+' <oferta & acessórios>';
  await page.locator('#product-name').fill(long);await page.getByRole('button',{name:'Adicionar produto',exact:true}).click();await page.waitForFunction(()=>window.__GARIMPEI_DEMO__.pending===null);
  assert(await page.getByText(long,{exact:true}).isVisible(),'Long product name stays visible as text');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Long name does not overflow page');
  assert(await page.locator('oferta').count()===0,'Product name is escaped as text');
  await page.getByRole('button',{name:'Abrir navegação'}).click();await page.getByRole('link',{name:'Configurações',exact:true}).click();
  await page.locator('#shipping').fill('9500000,50');await page.getByRole('button',{name:'Salvar configurações'}).click();await page.waitForFunction(()=>window.__GARIMPEI_DEMO__.pending===null);
  await page.getByRole('button',{name:'Abrir navegação'}).click();await page.getByRole('link',{name:'Seu garimpo',exact:true}).click();
  await page.locator('[data-offer="zero"]').first().click();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Large cost and negative result reflow without page overflow');
  await page.goto('http://127.0.0.1:4173/prototypes/?scenario=gaps&offer=removed-ad');await page.waitForFunction(()=>window.__GARIMPEI_DEMO__);
  assert(await page.getByText('Anúncio indisponível na origem',{exact:true}).isVisible(),'Unavailable source uses last-known-data notice');
  await page.screenshot({path:'docs/design/evidence/source-unavailable-mobile.png'});
  await page.evaluate(checks=>window.__EXTRA_CHECKS__=checks,checks);
}
