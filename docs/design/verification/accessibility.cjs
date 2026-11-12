async page => {
  const results=[];
  await page.route('**/*',route=>route.continue());
  const open=async query=>{await page.goto('http://127.0.0.1:4173/prototypes/?'+query);await page.waitForFunction(()=>window.__GARIMPEI_DEMO__);await page.evaluate(()=>document.fonts.ready);};
  const audit=async label=>{
    if(!await page.evaluate(()=>!!window.axe))await page.addScriptTag({path:'docs/design/storybook/node_modules/axe-core/axe.min.js'});
    const data=await page.evaluate(async()=>{
      const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
      return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.length})),passes:r.passes.length};
    });results.push({label,...data});
  };
  for(const width of [1440,375]) {
    await page.setViewportSize({width,height:1000});
    for(const query of ['', 'offer=camera','offer=unknown','view=interests','view=settings','view=alerts','view=system','scenario=gaps','scenario=empty','scenario=unavailable','scenario=stopped','scenario=partial','scenario=gaps&offer=removed-ad','view=reference&offer=camera&ref=CMP-camera-1','variant=compact','variant=night']) {
      await open(query);await audit(`${width}/${query||'editorial'}`);
    }
    await open('scenario=first-use');await audit(`${width}/setup-region`);
    await page.locator('#cep').fill('01310-930');await page.getByRole('button',{name:'Continuar',exact:true}).click();await audit(`${width}/setup-costs`);
    await page.getByRole('button',{name:'Continuar',exact:true}).click();await audit(`${width}/setup-errors`);
    await page.locator('#shipping').fill('35');await page.locator('#rate').fill('12');await page.getByRole('button',{name:'Continuar',exact:true}).click();await audit(`${width}/setup-interests`);
  }
  await page.evaluate(results=>window.__A11Y_RESULTS__=results,results);
  if(results.some(result=>result.violations.length||result.incomplete.length))throw new Error("Acessibilidade requer revisão: consulte window.__A11Y_RESULTS__.");
}
