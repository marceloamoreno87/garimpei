import {conditionTabs,emptyState,pagination,updatesNotice,button} from '../../components/ui.js';
import {initialOffers} from '../../prototypes/data.js';

export default {title:'Mineral/Navegação e resultados'};
export const Abas= {render:()=>conditionTabs('good',initialOffers)+'<div id="offer-results" role="tabpanel" aria-labelledby="tab-good"><p>Ofertas desta condição.</p></div>'};
export const Paginacao= {render:()=>pagination(2,47)};
export const Atualizacao= {render:()=>updatesNotice(2)};
export const Vazio= {render:()=>emptyState({title:'Nenhuma oferta encontrada nesta coleta',text:'Revise seus interesses ou aguarde a próxima coleta.',action:button({label:'Revisar interesses'})})};
