/* Isolated design prototype. Saves, collection, restarts and failures are simulated in memory. */
import {updatesNotice} from '../components/ui.js';
import {createState,decorateOffers,filteredOffers,offersFor,parseCosts,scenarios,validateCosts} from './model.js';
import {alertsView,detailView,interestsView,offersView,prototypeControls,referenceView,resultsView,settingsView,setupView,shell,variants,viewNames} from './views.js';
import {systemView} from './gallery.js';

const state=createState(new URLSearchParams(location.search));
let toastTimer,saveVersion=0,collectionTimer;
const tokenSource=await fetch('../tokens.json').then(response=>response.json()).catch(()=>null);
const focus=selector=>document.querySelector(selector)?.focus({preventScroll:false});
const formErrors=()=>{state.errors={};state.saveMessage='';state.errorForm=null;};

function exposeState() {
  window.__GARIMPEI_DEMO__=structuredClone(state);
  const inspector=document.querySelector('#prototype-state');
  if(inspector)inspector.textContent=JSON.stringify({scenario:state.scenario,configured:state.setup.complete,step:state.setup.step,collectionStarted:state.collectionStarted,page:state.page,filters:{condition:state.condition,category:state.category,search:state.search,delivery:state.delivery},settings:state.settings,products:state.products,pendingUpdates:state.pendingUpdates.length,pendingSave:state.pending,alerts:state.alerts.length,classifications:state.offers.filter(offer=>offer.manualCondition).map(({id,manualCondition})=>({id,manualCondition}))},null,2);
}
function toast(message) {
  const target=document.querySelector('#toast');target.textContent=message;target.hidden=false;
  clearTimeout(toastTimer);toastTimer=setTimeout(()=>{target.hidden=true;},4500);exposeState();
}
function syncUrl(push=false) {
  const query=new URLSearchParams({variant:state.variant,view:state.view,scenario:state.scenario});
  if(state.offer)query.set('offer',state.offer);
  if(state.reference)query.set('ref',state.reference);
  history[push?'pushState':'replaceState']({},'',`${location.pathname}?${query}`);
}
function render() {
  if(!Object.hasOwn(viewNames,state.view)||(state.view==='setup'&&state.setup.complete))state.view='offers';
  document.documentElement.dataset.variant=state.variant;
  document.documentElement.style.colorScheme=state.variant==='night'?'dark':'light';
  const views={offers:offersView,setup:setupView,interests:interestsView,settings:settingsView,alerts:alertsView,reference:referenceView,system:()=>systemView(tokenSource)};
  document.querySelector('#app').innerHTML=shell(state,state.offer&&state.view!=='reference'?detailView(state):views[state.view](state));
  document.querySelector('#prototype-controls').innerHTML=prototypeControls(state);
  document.title=`${state.offer?'Detalhes da oferta':viewNames[state.view]} · Garimpei — protótipo`;
  exposeState();
}
function navigate(view,offer=null,push=true) {
  if(state.pending){toast('Aguarde a conclusão da gravação de demonstração.');return;}
  clearTimeout(toastTimer);document.querySelector('#toast').hidden=true;
  state.view=!state.setup.complete&&['interests','settings'].includes(view)?'setup':view;
  state.offer=offer;state.menu=false;state.original=false;state.message=null;formErrors();syncUrl(push);render();
  window.scrollTo({top:0,behavior:'instant'});focus('main h1');
}
function updateResults() {
  const target=document.querySelector('#offer-results');if(!target)return;
  target.innerHTML=resultsView(state);target.setAttribute('aria-labelledby',`tab-${state.condition}`);
  document.querySelectorAll('[data-condition]').forEach(tab=>{const active=tab.dataset.condition===state.condition;tab.classList.toggle('is-active',active);tab.setAttribute('aria-selected',active);tab.tabIndex=active?0:-1;});
  document.querySelectorAll('[data-category]').forEach(chip=>{const active=chip.dataset.category===state.category;chip.classList.toggle('is-active',active);chip.setAttribute('aria-pressed',active);});
  const count=document.querySelector('#offer-count');
  if(count)count.textContent=`${['loading','initial','empty','unavailable'].includes(state.scenario)?0:filteredOffers(state).length} ofertas nesta seleção. Página ${state.page}.`;
  exposeState();
}
function switchVariant(delta) {
  if(state.pending)return;
  state.variant=variants[(variants.indexOf(state.variant)+delta+variants.length)%variants.length];syncUrl();render();focus(`[data-variant-delta="${delta}"]`);
}
function failForm(form,errors={},message='') {
  state.errorForm=form;state.errors=errors;state.saveMessage=message;render();focus(`#${form}-error`);
}
async function save(form,commit,message) {
  if(state.pending)return;
  const version=++saveVersion;state.pending=form;formErrors();render();
  await new Promise(resolve=>setTimeout(resolve,650));
  if(version!==saveVersion)return;
  state.pending=null;
  if(state.writeError){failForm(form,{},'Não foi possível salvar. Seus dados foram preservados; desative a falha nas ferramentas de demonstração e tente novamente.');return;}
  commit();formErrors();syncUrl();render();toast(message);
  if(form==='product')focus('#product-name');
  if(form==='classification')focus('main h1');
}
function startInitialCollection() {
  state.scenario='initial';state.collectionStarted=true;state.view='offers';state.offer=null;state.offers=[];
  clearTimeout(collectionTimer);
  collectionTimer=setTimeout(()=>{if(state.scenario!=='initial')return;state.scenario='populated';state.offers=offersFor('populated');syncUrl();render();toast('Primeira coleta de demonstração concluída, sem gerar alertas.');},3500);
}
function setScenario(value) {
  if(!Object.hasOwn(scenarios,value))return;
  clearTimeout(collectionTimer);saveVersion++;state.pending=null;formErrors();
  if(value==='first-use') {
    Object.assign(state,createState(new URLSearchParams({scenario:'first-use',variant:state.variant})));
  } else if(value==='updates') {
    state.scenario='populated';if(!state.setup.complete)state.setup.complete=true;
    state.view='offers';state.offer=null;queueUpdates();return;
  } else {
    if(!state.setup.complete)Object.assign(state,createState(new URLSearchParams({scenario:value,variant:state.variant})));
    state.scenario=value;state.view='offers';state.offer=null;state.page=1;
    if(value==='many'||value==='gaps')state.offers=offersFor(value);
  }
  syncUrl();render();focus('#scenario');
}
function queueUpdates() {
  const tools=document.querySelector('.prototype-inspector');if(tools?.open){tools.open=false;tools.querySelector('summary').focus();}
  if(state.pendingUpdates.length){toast('Já há atualizações aguardando sua revisão.');return;}
  const camera=state.offers.find(offer=>offer.manualCondition)||state.offers.find(offer=>offer.id==='camera');
  state.pendingUpdates=camera?[{id:camera.id,price:Math.max(100,camera.price-10000),condition:camera.manualCondition?'unknown':camera.condition}]:[];
  if(!state.offers.some(offer=>offer.id==='fresh-camera'))state.pendingUpdates.push(decorateOffers([{...offersFor('populated')[0],id:'fresh-camera',title:'Sony a6000 · nova oferta de demonstração',price:160000,age:'Identificada agora no exemplo'}])[0]);
  if(state.pendingUpdates.length>1)state.pendingUpdates[1].firstSeenAt='2026-11-10T13:00:00.000Z';
  const region=document.querySelector('#update-region');
  if(region)region.innerHTML=updatesNotice(state.pendingUpdates.length,!!state.offer);
  exposeState();
}
function applyUpdates() {
  for(const patch of state.pendingUpdates) {
    const current=state.offers.find(offer=>offer.id===patch.id);
    if(current){const condition=current.manualCondition||patch.condition||current.condition;Object.assign(current,patch,{condition,manualCondition:current.manualCondition});}
    else state.offers.push(patch);
  }
  state.pendingUpdates=[];render();toast('Lista atualizada; seus filtros foram mantidos.');focus('#offer-results .offer-card a, #offer-results tbody a');
}
function restartDemo() {
  clearTimeout(collectionTimer);saveVersion++;state.pending=null;formErrors();state.menu=false;
  state.settingsDraft={...state.settings};state.productDraft='';state.categoryDraft=[...state.selectedCategories];
  state.view=state.setup.complete?'offers':'setup';state.offer=null;
  state.scenario=state.setup.complete?'populated':'first-use';syncUrl();render();focus('main h1');
  toast(state.setup.complete?'Reinício simulado: configuração, classificações e histórico mantidos.':'Configuração ainda não concluída; nenhuma coleta foi iniciada.');
}

function submitSetup() {
  const {step,draft}=state.setup;
  if(step===1) {
    if(!/^\d{5}-?\d{3}$/.test(draft.cep.trim())){failForm('setup',{cep:'Informe o CEP no formato 00000-000.'});return;}
    state.setup.step=2;formErrors();render();focus('#shipping');return;
  }
  if(step===2) {
    const errors=validateCosts(draft,false);if(Object.keys(errors).length){failForm('setup',errors);return;}
    state.setup.step=3;formErrors();render();focus('#setup-product');return;
  }
  if(!draft.products.length&&!draft.categories.length){failForm('setup',{interests:'Selecione uma categoria ou adicione um produto para acompanhar.'});return;}
  save('setup',()=>{
    state.settings=parseCosts(draft);state.settingsDraft={...state.settings};
    state.products=[...draft.products];state.selectedCategories=[...draft.categories];state.categoryDraft=[...draft.categories];
    state.setup.complete=true;state.alerts=[];startInitialCollection();
  },'Configuração salva na demonstração. A primeira coleta é silenciosa.');
}

document.addEventListener('submit',event=>{
  const form=event.target;event.preventDefault();if(state.pending)return;
  if(form.id==='setup-form'){submitSetup();return;}
  if(form.id==='product-form') {
    const value=state.productDraft.trim();if(!value){failForm('product',{'product-name':'Informe um nome ou modelo.'});return;}
    save('product',()=>{state.products.push(value);state.productDraft='';},'Produto adicionado aos interesses de demonstração.');return;
  }
  if(form.id==='settings-form') {
    const errors=validateCosts(state.settingsDraft);if(Object.keys(errors).length){failForm('settings',errors);return;}
    save('settings',()=>{state.settings=parseCosts(state.settingsDraft);state.settingsDraft={...state.settings};},'Configurações salvas no exemplo; estimativas recalculadas.');return;
  }
  if(form.id==='categories-form')save('categories',()=>{state.selectedCategories=[...state.categoryDraft];},'Categorias salvas na demonstração.');
});

document.addEventListener('click',event=>{
  const target=event.target.closest('button,a,summary');if(!target||target.disabled)return;
  if(state.pending&&!target.closest('#prototype-controls')){event.preventDefault();return;}
  if(target.dataset.nav){event.preventDefault();navigate(target.dataset.nav);return;}
  if(target.dataset.offer){event.preventDefault();navigate('offers',target.dataset.offer);return;}
  if(target.dataset.reference){event.preventDefault();state.reference=target.dataset.reference;navigate('reference',state.offer);return;}
  if(target.dataset.condition){state.condition=target.dataset.condition;state.page=1;updateResults();return;}
  if(target.dataset.category){state.category=target.dataset.category;state.page=1;updateResults();return;}
  if(target.dataset.page){state.page=Number(target.dataset.page);updateResults();document.querySelector('#offer-results')?.scrollIntoView({block:'start'});focus('#offer-results .offer-card a, #offer-results tbody a');return;}
  if(target.dataset.variantDelta){switchVariant(Number(target.dataset.variantDelta));return;}
  if(target.dataset.review){state.selectedReview=target.dataset.review;updateResults();return;}
  if(target.dataset.classify) {
    const offer=state.offers.find(item=>item.id===target.dataset.id),condition=target.dataset.classify;
    save('classification',()=>{offer.condition=condition;offer.manualCondition=condition;state.condition=condition;state.view='offers';state.offer=null;state.page=1;},'Classificação salva no exemplo. A aba foi alterada; nenhum alerta foi gerado.');return;
  }
  if(target.dataset.removeProduct!==undefined){const index=Number(target.dataset.removeProduct);save('product',()=>state.products.splice(index,1),'Produto removido no exemplo.');return;}
  if(target.dataset.setupRemove!==undefined){state.setup.draft.products.splice(Number(target.dataset.setupRemove),1);render();return;}
  if(target.dataset.message){state.message=target.dataset.message;render();document.querySelector('.message-heading')?.scrollIntoView({block:'nearest'});return;}
  const actions={
    menu:()=>{state.menu=!state.menu;render();focus(state.menu?'.sidebar nav a':'.mobile-menu');},
    original:()=>{state.original=true;render();},
    retry:()=>{state.scenario='populated';syncUrl();render();toast('Cenário de consulta restabelecida, sem acessar fontes reais.');},
    'clear-filters':()=>{state.search='';state.category='Todas';state.delivery='all';state.page=1;render();},
    'setup-back':()=>{state.setup.step=Math.max(1,state.setup.step-1);formErrors();render();focus(state.setup.step===1?'#cep':'#shipping');},
    'setup-add-product':()=>{const value=state.setup.draft.product.trim();if(!value){toast('Informe um nome ou modelo para adicionar.');focus('#setup-product');return;}state.setup.draft.products.push(value);state.setup.draft.product='';render();focus('#setup-product');},
    'queue-updates':queueUpdates,'apply-updates':applyUpdates,restart:restartDemo,
    'finish-initial':()=>{if(!state.setup.complete){toast('Conclua a configuração para iniciar a coleta.');return;}clearTimeout(collectionTimer);if(!state.offers.length)state.offers=offersFor('populated');state.scenario='populated';syncUrl();render();toast('Coleta simulada concluída; nenhum alerta enviado.');},
    'back-detail':()=>navigate('offers',state.offer),
    'component-demo':()=>toast('Exemplo de ação do componente.')
  };
  actions[target.dataset.action]?.();
});

document.addEventListener('input',event=>{
  const input=event.target;
  if(input.id==='offer-search'){state.search=input.value;state.page=1;updateResults();return;}
  if(input.closest('#setup-form')) {
    if(['cep','shipping','rate'].includes(input.id))state.setup.draft[input.id]=input.value;
    if(input.id==='setup-product')state.setup.draft.product=input.value;
  }
  if(input.closest('#settings-form')&&['cep','shipping','rate'].includes(input.id))state.settingsDraft[input.id]=input.value;
  if(input.id==='product-name')state.productDraft=input.value;
  exposeState();
});
document.addEventListener('change',event=>{
  const input=event.target;
  if(input.id==='delivery-filter'){state.delivery=input.value;state.page=1;updateResults();}
  if(input.id==='scenario')setScenario(input.value);
  if(input.id==='write-error'){state.writeError=input.checked;exposeState();}
  if(input.name==='category')state.categoryDraft=[...document.querySelectorAll('input[name=category]:checked')].map(item=>item.value);
  if(input.name==='setup-category')state.setup.draft.categories=[...document.querySelectorAll('input[name=setup-category]:checked')].map(item=>item.value);
  exposeState();
});
document.addEventListener('error',event=>{
  if(!event.target.matches?.('[data-product-image]'))return;
  const container=event.target.parentElement;event.target.remove();container.querySelector('.photo-credit')?.remove();container.querySelector('.image-fallback')?.removeAttribute('hidden');
},true);
document.addEventListener('focusin',event=>{
  const bar=document.querySelector('.prototype-bar');if(!bar||bar.contains(event.target))return;
  const target=event.target.getBoundingClientRect(),overlay=bar.getBoundingClientRect();
  if(target.bottom>overlay.top&&target.top<overlay.bottom&&target.right>overlay.left&&target.left<overlay.right)event.target.scrollIntoView({block:'center'});
});
document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&state.menu){state.menu=false;render();focus('.mobile-menu');return;}
  const tab=event.target.closest('[role=tab]');
  if(tab&&['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) {
    event.preventDefault();const ids=['good','defect','unknown'],index=ids.indexOf(state.condition);
    const next=event.key==='Home'?0:event.key==='End'?2:(index+(event.key==='ArrowRight'?1:2))%3;
    state.condition=ids[next];state.page=1;updateResults();focus(`#tab-${state.condition}`);return;
  }
  if(event.target.closest('input,textarea,select,summary,[contenteditable=true]'))return;
  if(['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();switchVariant(event.key==='ArrowRight'?1:-1);}
});
window.addEventListener('popstate',()=>{
  const query=new URLSearchParams(location.search);
  state.variant=variants.includes(query.get('variant'))?query.get('variant'):'editorial';
  state.view=Object.hasOwn(viewNames,query.get('view'))?query.get('view'):'offers';state.offer=query.get('offer');state.reference=query.get('ref');render();
});
if(state.scenario==='updates'){state.scenario='populated';render();queueUpdates();}
else {syncUrl();render();}
