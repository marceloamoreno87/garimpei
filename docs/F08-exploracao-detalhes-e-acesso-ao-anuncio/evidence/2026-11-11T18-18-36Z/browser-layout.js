async page => {
 const base='http://127.0.0.1:14477';
 await page.goto(base+'/ofertas/00000000-0000-0000-0000-000000000004/?aba=funcionam&q=camera&categoria=cameras&modalidade=retirada&pagina=2');
 for(const value of ['R$ 700,00','R$ 1.700,00','R$ 830,00','R$ 796,00','R$ 2.400,00']) {
   if(!await page.getByText(value,{exact:true}).count()) throw Error('detail value '+value);
 }
 if(await page.getByRole('link',{name:'Abrir referência',exact:true}).count()!==5) throw Error('used comparables');
 await page.screenshot({path:'/tmp/f08-detail.png',fullPage:true});
 await page.getByRole('link',{name:'Voltar aos resultados',exact:true}).click();
 if(!page.url().includes('pagina=2')||!page.url().includes('categoria=cameras')||!page.url().includes('versao=')) throw Error('lost return context');
 await page.goto(base+'/ofertas/?aba=funcionam&pagina=2');
 await page.getByRole('combobox',{name:'Modalidade',exact:true}).selectOption('envio');
 await page.getByRole('button',{name:'Filtrar ofertas',exact:true}).click();
 await page.getByText('Página 1 de 1',{exact:true}).waitFor();
 if(await page.locator('[data-key="10004"]').count()!==1) throw Error('dual modality duplicated');
 for(const n of [43,44,45,46,47]) if(!await page.locator('[data-key="100'+n+'"]').count()) throw Error('missing audio');
 await page.getByRole('searchbox').fill('zzzz-no-result');
 await page.getByRole('button',{name:'Filtrar ofertas',exact:true}).click();
 await page.getByText('Nenhuma oferta neste recorte',{exact:true}).waitFor();
 await page.getByRole('link',{name:'Limpar filtros',exact:true}).click();
 if(!await page.getByText('Página 1 de 3',{exact:true}).count()) throw Error('clear page');
 const selected=page.getByRole('tab',{selected:true});
 await selected.focus();
 await page.keyboard.press('End');
 await page.getByRole('tab',{name:/Condição não confirmada/,selected:true}).waitFor();
 if(await page.evaluate(()=>document.activeElement.getAttribute('aria-selected'))!=='true') throw Error('keyboard tab focus');
 await page.keyboard.press('Home');
 await page.getByRole('tab',{name:/Funcionam bem/,selected:true}).waitFor();
 const checks=[];
 for(const width of [360,768,1440]) {
   await page.setViewportSize({width,height:1000});
   await page.evaluate(()=>scrollTo(0,0));
   const metrics=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,tabs:[...document.querySelectorAll('[role=tab]')].map(x=>({width:x.getBoundingClientRect().width,scroll:x.scrollWidth,client:x.clientWidth})),media:[...document.querySelectorAll('img')].filter(x=>x.getBoundingClientRect().top<innerHeight).map(x=>({loaded:x.complete&&x.naturalWidth>0}))}));
   if(metrics.scroll>width || metrics.tabs.some(t=>t.scroll>t.client+1) || metrics.media.some(x=>!x.loaded)) throw Error('layout/media at '+width+JSON.stringify(metrics));
   checks.push(metrics);
   await page.screenshot({path:'/tmp/f08-'+width+'.png'});
 }
 const cdp=await page.context().newCDPSession(page);
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:720,height:500,deviceScaleFactor:2,mobile:false});
 await page.evaluate(()=>scrollTo(0,0));
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('200% zoom reflow');
 await page.screenshot({path:'/tmp/f08-zoom200.png'});
 await cdp.send('Emulation.clearDeviceMetricsOverride');
 return checks;
}
