async page => {
  const matrix=[];
  const open=async query=>{await page.goto('http://127.0.0.1:4173/prototypes/?'+query);await page.waitForFunction(()=>window.__GARIMPEI_DEMO__);await page.evaluate(()=>document.fonts.ready);};
  const capture=async name=>{await page.locator('img').evaluateAll(images=>Promise.all(images.map(img=>{img.loading='eager';return img.decode().catch(()=>{});})));await page.screenshot({path:'docs/design/evidence/'+name+'.png'});};
  await page.route('**/*',route=>route.continue());
  for(const width of [320,375,768,1024,1440]) {
    await page.setViewportSize({width,height:1000});
    for(const variant of ['editorial','compact','night'])for(const query of ['view=offers','view=interests','view=settings','view=alerts','view=system','scenario=gaps','offer=camera','offer=unknown','scenario=first-use']) {
      await open(`variant=${variant}&${query}`);
      const measurements=await page.evaluate(()=>({width:innerWidth,content:document.documentElement.scrollWidth}));
      if(measurements.content>measurements.width)throw new Error(`Overflow ${width}/${variant}/${query}: ${measurements.content}`);
      matrix.push(`${width}/${variant}/${query}`);
    }
  }
  await page.setViewportSize({width:375,height:900});await open('scenario=first-use');await capture('setup-mobile-region');
  await page.locator('#cep').fill('01310-930');await page.getByRole('button',{name:'Continuar',exact:true}).click();await capture('setup-mobile-costs');
  await page.getByRole('button',{name:'Abrir navegação'}).click();await page.keyboard.press('Escape');
  if(!await page.getByRole('button',{name:'Abrir navegação'}).evaluate(e=>e===document.activeElement))throw new Error('Menu does not restore focus');
  await open('scenario=gaps');await capture('gaps-mobile');
  await page.setViewportSize({width:1440,height:1050});await open('scenario=updates');await capture('updates-desktop');
  await open('offer=unknown');await page.locator('.classification').scrollIntoViewIfNeeded();await capture('classification-controls');
  await open('scenario=partial');await capture('partial-desktop');
  await page.setViewportSize({width:768,height:1000});await open('scenario=first-use');await capture('setup-tablet');
  await page.setViewportSize({width:1280,height:1000});await open('view=settings');
  await page.evaluate(()=>document.documentElement.style.fontSize='200%');
  const textReflow=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,body:getComputedStyle(document.body).fontSize,save:[...document.querySelectorAll('button')].find(e=>e.textContent.includes('Salvar configurações'))?.getBoundingClientRect().toJSON()}));
  if(textReflow.overflow)throw new Error('Text 200% overflows');await capture('text-200-settings');
  await page.emulateMedia({reducedMotion:'reduce'});
  if(!await page.evaluate(()=>getComputedStyle(document.querySelector('.btn')).transitionDuration==='0s'))throw new Error('Reduced motion failed');
  await page.evaluate(data=>window.__RESPONSIVE__=data,{matrix,textReflow,menuFocus:true,reducedMotion:true});
}
