async page => {
  const base='http://127.0.0.1:14477';
  const original='4738c8b4-3685-4df5-a543-82eb56cbfb8c';
  await page.goto(base+'/ofertas/00000000-0000-0000-0000-000000000031/?aba=incerta&q=incerta&categoria=cameras&modalidade=todas&pagina=1&versao='+original);
  await page.getByRole('radio',{name:'Funciona bem',exact:true}).check();
  await page.getByRole('button',{name:'Salvar classificação',exact:true}).click();
  await page.getByText('Sua classificação foi salva.',{exact:false}).waitFor();
  if(!page.url().includes('versao='+original)) throw Error('classification applied another revision');
  await page.getByRole('link',{name:'Ver em Funcionam bem',exact:true}).click();
  await page.getByText('Câmera Incerta',{exact:true}).waitFor();
  if(await page.locator('[data-key="10049"]').count()!==1) throw Error('classified identity missing');
  await page.goto(base+'/ofertas/00000000-0000-0000-0000-000000000004/?aba=funcionam&versao='+original);
  await page.getByText('R$ 530,00',{exact:true}).waitFor();
  // The native link opens the exact synthetic canonical URL, intercepted outside the application.
  const expected='https://www.facebook.com/marketplace/item/10004/';
  await page.context().route(expected,route=>route.fulfill({status:200,contentType:'text/html',body:'<h1>Origem teste CAM04</h1>'}));
  const popupPromise=page.waitForEvent('popup');
  await page.getByRole('link',{name:'Abrir anúncio original',exact:true}).click();
  const popup=await popupPromise;
  await popup.waitForLoadState();
  if(popup.url()!==expected || !await popup.getByText('Origem teste CAM04').count()) throw Error('wrong original identity');
  await popup.close();
  await page.goto(base+'/ofertas/?aba=funcionam&q=camera&categoria=cameras&modalidade=retirada&pagina=1&versao='+original);
  await page.evaluate(()=>htmx.trigger(document.body,'exploration-poll'));
  await page.getByRole('link',{name:'Atualizar lista',exact:true}).waitFor();
  const before=await page.locator('#exploration').getAttribute('data-version');
  const fail=route=>route.fulfill({status:503,contentType:'text/html',body:'<p>Falha de consulta controlada</p>'});
  await page.route(url=>url.pathname==='/ofertas/' && url.searchParams.get('aplicar')==='1' && !url.searchParams.has('versao'),fail);
  await page.getByRole('link',{name:'Atualizar lista',exact:true}).click();
  await page.getByText('Seus resultados foram mantidos.',{exact:false}).waitFor();
  if(await page.locator('#exploration').getAttribute('data-version')!==before || await page.locator('[data-key]').first().getAttribute('data-key')!=='10002') throw Error('failed refresh replaced existing results');
  await page.unroute(url=>url.pathname==='/ofertas/' && url.searchParams.get('aplicar')==='1' && !url.searchParams.has('versao'),fail);
  // Unroute by function identity is deliberately not assumed; clear the application interception explicitly.
  await page.unrouteAll({behavior:'wait'});
  await page.route('https://media.exploration.invalid/**',route=>route.fulfill({path:'/home/marce/dev/garimpei/docs/design/prototypes/assets/camera.jpg',contentType:'image/jpeg'}));
  await page.getByRole('link',{name:'Atualizar lista',exact:true}).click();
  await page.getByText('Lista atualizada.',{exact:false}).waitFor();
  if(await page.locator('[data-key]').first().getAttribute('data-key')!=='10004') throw Error('refresh ordering');
  await page.getByText('R$ 830,00',{exact:true}).waitFor();
  const active=await page.evaluate(()=>document.activeElement.textContent);
  if(active!=='Câmera 04') throw Error('focus after applying: '+active);
  if(!page.url().includes('q=camera')||!page.url().includes('modalidade=retirada')||!page.url().includes('categoria=cameras')) throw Error('lost filters');
  await page.screenshot({path:'/tmp/f08-updated.png'});
  await page.goto(base+'/ofertas/?aba=funcionam&q=camera&categoria=cameras&modalidade=retirada&pagina=3&versao='+original);
  await page.getByText('41–42 de 42',{exact:true}).waitFor();
  await page.screenshot({path:'/tmp/f08-third-page.png'});
}
