/* Demo-only state and fixtures. No persistence, integrations or production rules. */
import {initialOffers,initialSettings,initialProducts} from './data.js';
import {profitOf} from '../components/ui.js';

export const PAGE_SIZE=20;
export const scenarios={populated:'Com dados', 'first-use':'Primeiro uso', loading:'Carregando',empty:'Coleta sem resultados',error:'Falha na fonte',initial:'Primeira coleta',stopped:'Acompanhamento parado',stale:'Dados desatualizados',partial:'Coleta parcial',unavailable:'Consulta indisponível',many:'Muitas ofertas',gaps:'Dados ausentes',updates:'Novos dados'};
export const decorateOffers=offers=>structuredClone(offers).map((offer,index)=>({...offer,manualCondition:null,firstSeenAt:new Date(Date.UTC(2026,10,10,12,0)-index*60000).toISOString(),sourceId:`DEMO-${offer.id}`,origin:'Fonte de demonstração',sourceUrl:`https://exemplo.invalid/anuncios/${offer.id}`}));

export function offersFor(scenario) {
  const offers=decorateOffers(initialOffers);
  if(scenario==='many') {
    const examples=offers.filter(offer=>offer.condition==='good');
    for(let index=0;index<40;index++)offers.push({...examples[index%examples.length],id:`volume-${index+1}`,sourceId:`DEMO-VOLUME-${index+1}`,sourceUrl:`https://exemplo.invalid/anuncios/volume-${index+1}`,title:`${examples[index%examples.length].title} · exemplar ${index+1}`,firstSeenAt:new Date(Date.UTC(2026,10,9,12,0)-index*60000).toISOString()});
  }
  if(scenario==='gaps')offers.unshift(...decorateOffers([
    {id:'missing-photo',title:'Câmera com lente, bateria, carregador, estojo de transporte e descrição extensa para conferir os acessórios antes de decidir pela compra',category:'Câmeras',image:null,description:'Funcionamento informado; anúncio de demonstração sem fotografia.',price:150000,resale:240000,newReference:null,freight:null,delivery:'shipping',location:null,condition:'good',age:'Data de publicação não informada',sample:3},
    {id:'missing-price',title:'Fone com preço a consultar',category:'Áudio',image:null,description:'O valor de compra não foi informado. Nenhum preço ou lucro foi presumido.',price:null,resale:110000,newReference:169900,freight:null,delivery:'shipping',location:null,condition:'good',age:'Data de publicação não informada',sample:3},
    {id:'removed-ad',title:'Oferta com anúncio indisponível na origem',category:'Consoles',image:null,description:'Os dados desta oferta são da última consulta conhecida. A origem não está disponível neste exemplo.',price:125000,resale:null,newReference:null,freight:null,delivery:'shipping',location:null,condition:'unknown',availability:'unavailable',age:'Disponibilidade não confirmada',sample:0},
    {id:'missing-location',title:'Smartphone com modalidade a confirmar',category:'Celulares',image:'phone.jpg',description:'Localização e entrega não confirmadas. Não é possível comprovar cobertura do CEP.',price:80000,resale:130000,newReference:null,freight:null,delivery:'unknown',location:null,condition:'unknown',age:'Data de publicação não informada',sample:3}
  ]));
  return offers;
}

export function createState(query) {
  const scenario=Object.hasOwn(scenarios,query.get('scenario'))?query.get('scenario'):'populated';
  const first=scenario==='first-use';
  const settings={...initialSettings};
  return {variant:['editorial','compact','night'].includes(query.get('variant'))?query.get('variant'):'editorial',view:first?'setup':query.get('view')||'offers',offer:query.get('offer'),reference:query.get('ref'),scenario,condition:'good',search:'',category:'Todas',delivery:'all',page:1,selectedReview:'camera',offers:first?[]:offersFor(scenario),settings,settingsDraft:{...settings},products:first?[]:[...initialProducts],productDraft:'',selectedCategories:first?[]:['Câmeras','Áudio','Consoles'],categoryDraft:first?[]:['Câmeras','Áudio','Consoles'],menu:false,message:null,original:false,pending:null,writeError:false,errors:{},saveMessage:'',errorForm:null,pendingUpdates:[],setup:{step:1,complete:!first,draft:{cep:'',shipping:'',rate:'',products:[],categories:[],product:''}},alerts:first?[]:['price','new','uncertain'],collectionStarted:!first};
}

export function filteredOffers(state) {
  const query=state.search.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  return state.offers.filter(offer=>offer.condition===state.condition)
    .filter(offer=>state.category==='Todas'||offer.category===state.category)
    .filter(offer=>state.delivery==='all'||offer.delivery===state.delivery)
    .filter(offer=>`${offer.title} ${offer.category}`.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().includes(query))
    .sort((a,b)=>{
      const left=profitOf(a,state.settings.rate,state.settings.shipping*100);
      const right=profitOf(b,state.settings.rate,state.settings.shipping*100);
      if(left===null&&right!==null)return 1;
      if(right===null&&left!==null)return -1;
      if(left!==right)return right-left;
      return b.firstSeenAt.localeCompare(a.firstSeenAt)||a.id.localeCompare(b.id);
    });
}

export function validateCosts(draft,includeCep=true) {
  const errors={};
  if(includeCep&&!/^\d{5}-?\d{3}$/.test(String(draft.cep).trim()))errors.cep='Informe o CEP no formato 00000-000.';
  for(const [key,label] of [['shipping','frete em reais'],['rate','percentual provisório']]) {
    const value=String(draft[key]).trim();
    if(!value||!/^\d+(?:[,.]\d+)?$/.test(value)||!Number.isFinite(Number(value.replace(',','.'))))errors[key]=`Informe um ${label} válido, maior ou igual a zero.`;
  }
  return errors;
}
export const parseCosts=draft=>({cep:String(draft.cep).trim(),shipping:Number(String(draft.shipping).replace(',','.')),rate:Number(String(draft.rate).replace(',','.'))});
export const comparablesFor=offer=>offer?.resale===null?[]:[.94,1,1.06].map((factor,index)=>({id:`CMP-${offer.id}-${index+1}`,title:`${offer.title} — ${['corpo e acessórios','conjunto usado','anúncio semelhante'][index]}`,price:Math.round(offer.resale*factor),origin:'Fonte de demonstração',observedAt:'10/11/2026, 10:20',url:`https://exemplo.invalid/comparaveis/${offer.id}/${index+1}`}));
