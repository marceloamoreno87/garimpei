import { offerCard } from '../../components/ui.js';
import { initialOffers } from '../../prototypes/data.js';

export default { title: 'Mineral/Ofertas' };
const card = (id, feature = false) => ({ render: () => `<div style="max-width:${feature?'1040':'360'}px">${offerCard(initialOffers.find(offer=>offer.id===id),{feature,assetBase:'/assets/'})}</div>` });
export const Destaque = card('camera',true);
export const NovaOferta = card('audio');
export const LucroNegativo = card('negative');
export const LucroZero = card('zero');
export const SemEstimativa = card('unavailable');
