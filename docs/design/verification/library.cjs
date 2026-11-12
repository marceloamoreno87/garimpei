async page => {
  await page.route('**/*',route=>route.continue());
  const entries=await page.evaluate(async()=>Object.keys((await(await fetch('/index.json')).json()).entries));
  const checked=[];
  for(const id of entries){
    await page.goto(`http://127.0.0.1:6006/iframe.html?id=${id}&viewMode=story`);await page.waitForSelector('#storybook-root > *');
    if(await page.locator('.sb-errordisplay').isVisible())throw new Error(id);
    await page.locator('img').evaluateAll(images=>Promise.all(images.map(img=>{img.loading='eager';return img.decode().catch(()=>{});})));
    if(!await page.evaluate(()=>[...document.images].every(img=>img.complete&&img.naturalWidth>0)))throw new Error('Broken story asset: '+id);
    checked.push(id);
  }
  await page.goto('http://127.0.0.1:6006/iframe.html?id=mineral-jornadas--custos-em-branco&viewMode=story&globals=theme:night');
  await page.waitForFunction(()=>document.documentElement.dataset.variant==='night');await page.evaluate(()=>document.fonts.ready);
  await page.screenshot({path:'docs/design/evidence/storybook-setup-night.png'});
  await page.evaluate(checked=>window.__LIBRARY_CHECKS__=checked,checked);
}
