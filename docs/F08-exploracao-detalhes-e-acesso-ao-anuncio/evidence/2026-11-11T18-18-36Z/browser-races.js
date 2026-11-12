async page => {
 const base='http://127.0.0.1:14477';
 const version='4738c8b4-3685-4df5-a543-82eb56cbfb8c';
 const address=base+'/ofertas/?aba=funcionam&q=camera&categoria=cameras&modalidade=retirada&pagina=2&versao='+version;
 const native=await page.context().browser().newContext({javaScriptEnabled:false});
 const p=await native.newPage();
 await p.goto(address);
 await p.getByRole('link',{name:'Conferir detalhes de Câmera 21',exact:true}).click();
 if(!await p.getByRole('heading',{name:'Câmera 21',exact:true}).count())throw Error('native detail');
 await p.getByRole('link',{name:'Voltar aos resultados',exact:true}).click();
 if(!p.url().includes('pagina=2')||!p.url().includes('versao='+version))throw Error('native context');
 await p.getByRole('searchbox').fill('incerta');
 await p.getByRole('button',{name:'Filtrar ofertas',exact:true}).click();
 if(!await p.getByRole('heading',{name:'Nenhuma oferta neste recorte',exact:true}).count()||!await p.getByText('Página 1 de 1',{exact:true}).count())throw Error('native filters');
 await native.close();
 await page.goto(address);
 await page.route('**/ofertas/atualizacoes/**', async route=>{
   await new Promise(resolve=>setTimeout(resolve,600));
   try {await route.fulfill({status:200,contentType:'text/html',body:'<strong id="stale-response">Stale old context</strong>'});} catch(_) {}
 });
 await page.evaluate(()=>htmx.trigger(document.body,'exploration-poll'));
 await page.getByRole('tab',{name:/Com defeito/}).click();
 await page.getByRole('tab',{name:/Com defeito/,selected:true}).waitFor();
 await page.waitForTimeout(700);
 if(await page.locator('#stale-response').count())throw Error('stale poll applied');
 await page.unrouteAll({behavior:'wait'});
 await page.goto(address);
 await page.route(url=>url.pathname==='/ofertas/'&&url.searchParams.get('q')==='slow-missing',async route=>{
   await new Promise(resolve=>setTimeout(resolve,500));
   try {await route.continue();}catch(_){}
 });
 await page.getByRole('searchbox').fill('slow-missing');
 await page.getByRole('button',{name:'Filtrar ofertas',exact:true}).click();
 await page.getByRole('searchbox').fill('camera');
 await page.getByRole('button',{name:'Filtrar ofertas',exact:true}).click();
 await page.getByText('1–20 de 42',{exact:true}).waitFor();
 await page.waitForTimeout(650);
 if(!await page.locator('[data-key="10002"]').count() || page.url().includes('slow-missing'))throw Error('stale navigation applied');
 await page.unrouteAll({behavior:'wait'});
 return {native:true,stale_poll_discarded:true,stale_navigation_discarded:true};
}
