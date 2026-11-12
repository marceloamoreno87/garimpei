export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));

const paths = {
  compass: '<circle cx="12" cy="12" r="8"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/>',
  sliders: '<path d="M4 7h9m4 0h3M4 17h3m4 0h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  settings: '<path d="m9 3-1 3-3 1 1 3-2 2 2 2-1 3 3 1 1 3h6l1-3 3-1-1-3 2-2-2-2 1-3-3-1-1-3z"/><circle cx="12" cy="12" r="3"/>',
  arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  left: '<path d="m14 6-6 6 6 6"/>',
  right: '<path d="m10 6 6 6-6 6"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  up: '<path d="m7 14 5-5 5 5M12 9v11"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  close: '<path d="m6 6 12 12M18 6 6 18"/>',
  pin: '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0Z"/><circle cx="12" cy="10" r="2"/>',
  truck: '<path d="M3 5h11v12H3zM14 9h4l3 4v4h-7"/><circle cx="7" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v1"/>',
  external: '<path d="M14 3h7v7m0-7L10 14M10 5H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h1M3 12h1M3 18h1"/>',
  leaf: '<path d="M20 3C9 3 3 7 5 14c2 6 12 7 15-11ZM5 20 16 9"/>',
  refresh: '<path d="M20 10a8 8 0 0 0-14-5L3 8m0-5v5h5M4 14a8 8 0 0 0 14 5l3-3m0 5v-5h-5"/>',
};

export const icon = (name, className = '') => `<svg class="icon ${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.info}</svg>`;

export function button({ label = 'Ver detalhes', variant = 'primary', iconName = '', disabled = false, loading = false, attributes = '' } = {}) {
  return `<button class="btn btn--${escapeHtml(variant)}" ${disabled || loading ? 'disabled' : ''} ${loading ? 'aria-busy="true"' : ''} ${attributes}>${loading ? '<span class="spinner" aria-hidden="true"></span>' : iconName ? icon(iconName) : ''}<span>${escapeHtml(loading ? 'Salvando…' : label)}</span></button>`;
}

export function badge(label, kind = 'neutral', iconName = '') {
  return `<span class="badge badge--${escapeHtml(kind)}">${iconName ? icon(iconName) : ''}${escapeHtml(label)}</span>`;
}

export function notice({ title, text, kind = 'info', action = '' }) {
  return `<div class="notice notice--${escapeHtml(kind)}">${icon('info')}<div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(text)}</p>${action}</div></div>`;
}

export const money = cents => cents === null || !Number.isFinite(cents) ? 'Não informado' : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: cents % 100 === 0 ? 0 : 2, maximumFractionDigits: 2 }).format(cents / 100);

export function profitOf(offer, rate = 12, estimatedShipping = 3500) {
  if (!Number.isFinite(offer.resale) || !Number.isFinite(offer.price) || offer.delivery === 'unknown') return null;
  const freight = offer.delivery === 'pickup' ? 0 : offer.freight ?? estimatedShipping;
  return offer.resale - offer.price - Math.round(offer.resale * rate / 100) - freight;
}

export function offerCard(offer, { feature = false, rate = 12, shipping = 3500, assetBase = 'assets/' } = {}) {
  const profit = profitOf(offer, rate, shipping);
  const title = escapeHtml(offer.title);
  return `<article class="offer-card ${feature ? 'offer-card--feature' : ''}" aria-label="${title}">
    <a class="offer-photo" href="?offer=${escapeHtml(offer.id)}" data-offer="${escapeHtml(offer.id)}"><span class="sr-only">Ver detalhes de ${title}. </span>
      ${productImage(offer, assetBase, !feature)}
      ${offer.previous ? badge('Preço reduzido', 'positive', 'down') : offer.isNew ? badge('Nova oferta', 'neutral') : ''}
      ${offer.image?'<span class="photo-credit">Imagem ilustrativa</span>':''}
    </a>
    <div class="offer-body"><div class="offer-meta"><span>${escapeHtml(offer.category)}</span><span>${escapeHtml(offer.age)}</span></div>
      <h2><a href="?offer=${escapeHtml(offer.id)}" data-offer="${escapeHtml(offer.id)}">${title}</a></h2>
      <p class="offer-description">${escapeHtml(offer.description)}</p>
      <div class="offer-price"><strong>${money(offer.price)}</strong>${offer.previous ? `<s>${money(offer.previous)}</s>` : ''}</div>
      <div class="profit-line ${profit === null ? 'profit-line--unavailable' : profit < 0 ? 'profit-line--negative' : ''}"><span>${profit === null ? 'Estimativa indisponível' : 'Lucro estimado'}</span>${profit === null ? icon('info') : `<strong>${profit >= 0 ? '+' : '−'} ${money(Math.abs(profit))}</strong>`}</div>
      <div class="offer-footer"><span>${icon(offer.delivery === 'pickup' ? 'pin' : offer.delivery === 'unknown' ? 'info' : 'truck')}${escapeHtml(offer.location || 'Localização não informada')}</span><a class="text-link" href="?offer=${escapeHtml(offer.id)}" data-offer="${escapeHtml(offer.id)}">Ver detalhes ${icon('arrow')}</a></div>
    </div></article>`;
}

export function productImage(offer, assetBase = 'assets/', lazy = false) {
  return `${offer.image ? `<img data-product-image src="${escapeHtml(assetBase+offer.image)}" alt="${escapeHtml(offer.imageAlt || offer.title)} — imagem ilustrativa" ${lazy?'loading="lazy"':''} width="720" height="520">` : ''}<span class="image-fallback" ${offer.image?'hidden':''} role="img" aria-label="Imagem não disponível">${icon('grid')}<span>Imagem não disponível</span></span>`;
}

export function field({id,label,value='',help='',error='',inputmode='',autocomplete='off',name=id}) {
  return `<div class="field"><label for="${id}">${escapeHtml(label)}</label><input id="${id}" name="${name}" value="${escapeHtml(value)}" ${inputmode?`inputmode="${inputmode}"`:''} autocomplete="${autocomplete}" aria-describedby="${id}-help${error?` ${id}-error`:''}" ${error?'aria-invalid="true"':''}><small id="${id}-help">${escapeHtml(help)}</small>${error?`<small id="${id}-error" class="field-error">${escapeHtml(error)}</small>`:''}</div>`;
}

export function errorSummary(id, errors = {}, message = '') {
  if (!message && !Object.keys(errors).length) return '';
  return `<div id="${id}" class="form-error" role="alert" tabindex="-1"><strong>${escapeHtml(message || 'Confira os campos antes de continuar.')}</strong>${Object.entries(errors).map(([key,text])=>`<a href="#${key}">${escapeHtml(text)}</a>`).join('')}</div>`;
}

export function conditionTabs(condition, offers) {
  return `<div class="condition-tabs" role="tablist" aria-label="Condição das ofertas">${[['good','Funcionam bem'],['defect','Com defeito'],['unknown','Condição não confirmada']].map(([id,label])=>`<button id="tab-${id}" role="tab" aria-controls="offer-results" aria-selected="${condition===id}" tabindex="${condition===id?0:-1}" class="condition-tab ${condition===id?'is-active':''}" data-condition="${id}">${label}<span>${offers.filter(offer=>offer.condition===id).length}</span></button>`).join('')}</div>`;
}

export function pagination(page,total,pageSize=20) {
  const pages=Math.max(1,Math.ceil(total/pageSize));
  return `<nav class="pagination" aria-label="Paginação das ofertas"><span>${total?`${(page-1)*pageSize+1}–${Math.min(page*pageSize,total)} de ${total}`:'0 ofertas'} · ${pageSize} por página</span><div class="row">${button({label:'Anterior',variant:'secondary',iconName:'left',disabled:page===1,attributes:`data-page="${page-1}"`})}<span aria-current="page">Página ${page} de ${pages}</span>${button({label:'Próxima',variant:'secondary',iconName:'right',disabled:page===pages,attributes:`data-page="${page+1}"`})}</div></nav>`;
}

export function emptyState({title,text,action=''}) {
  return `<div class="empty-state">${icon('search')}<h2>${escapeHtml(title)}</h2><p>${escapeHtml(text)}</p>${action}</div>`;
}

export function updatesNotice(count=1, detail=false) {
  return notice({title:'Há atualizações',text:`${count} ${count===1?'alteração processada':'alterações processadas'}. ${detail?'Confira os novos dados quando estiver pronto.':'Sua lista e seus filtros continuam no lugar até você atualizar.'}`,kind:'info',action:button({label:detail?'Atualizar dados':'Atualizar lista',variant:'secondary',attributes:'data-action="apply-updates"'})});
}
