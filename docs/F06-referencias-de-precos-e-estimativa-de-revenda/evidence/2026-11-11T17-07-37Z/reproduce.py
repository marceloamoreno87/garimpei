"""Phase-one audit: conservative explicit variant and source statements, without manual labels."""
import json,re,unicodedata
from collections import Counter, defaultdict
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
from datetime import datetime,timezone,timedelta

def normalize(value):
 return ' '.join(unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower().split())

def inspect(row):
 e=row.get('evidence')
 if not e:return {'identity':row['external_id'],'accepted':False,'reason':row.get('failure','missing_evidence')}
 t=normalize((e.get('title') or '')+' '+(e.get('description') or ''))
 reasons=[];product=None
 if row['family']=='phone':
  model=re.search(r'iphone\s*(12|13)\s*(pro\s*max|pro|mini)?',t)
  caps=set(re.findall(r'(?<!\d)(64|128|256|512)\s*gb',t))
  if model and len(caps)==1:product='apple:iphone'+model[1]+':'+(''.join((model[2] or 'standard').split()))+':'+next(iter(caps))+'gb'
 else:
  generations={g for g in ['slim','fat','pro'] if re.search(r'\b'+g+r'\b',t)}
  caps=set(re.sub(r'\s','',v).replace('tera','tb') for v in re.findall(r'(?<!\d)(825\s*gb|1\s*tb|1\s*tera|2\s*tb)',t))
  physical=bool(re.search(r'com leitor|c/\s*leitor|midia fisica|versao disco|\bdisco\b|\bdisk\b',t))
  digital=bool(re.search(r'slim\s+digital|edicao digital|midia digital|digital edition',t))
  if len(generations)==1 and len(caps)==1 and physical!=digital:
   product='sony:ps5:'+next(iter(generations))+':'+('disc' if physical else 'digital')+':'+next(iter(caps))
 if product is None:reasons.append('produto_indeterminado')
 if not normalize(e.get('condition') or '').startswith('usado'):reasons.append('usado_nao_confirmado')
 positive=re.search(r'\b(funcionando (perfeitamente|normalmente)|testado e funcionando|funcionamento 100\s*%|100\s*% funcional)\b',t)
 if positive is None:reasons.append('funcionamento_nao_confirmado')
 negative=re.search(r'\b(nao (?:esta )?funciona\w*|nao liga|com defeito|defeituoso|precisa de reparo|para pecas|trincos?|trincad\w*)\b',t)
 if negative:reasons.append('defeito_indicado')
 if not e.get('source_available'):reasons.append('disponibilidade_nao_confirmada')
 price=Decimal(e.get('price') or '0')
 if price<=0:reasons.append('preco_nao_positivo')
 if re.search(r'\b(entrada de|somente troca|apenas troca|lote de|somente pecas)\b',t):reasons.append('preco_ou_unidade_inelegivel')
 return {'identity':row['external_id'],'product':product,'accepted':not reasons,'reasons':reasons,'price':str(price),'functional_evidence':positive.group() if positive else None,'defect_evidence':negative.group() if negative else None}

def audit(rows):
 decisions=[inspect(r) for r in rows];groups=defaultdict(list)
 for d in decisions:
  if d.get('accepted'):groups[d['product']].append(d)
 results=[]
 for product,candidates in sorted(groups.items()):
  prices=sorted(Decimal(c['price']) for c in candidates)
  n=len(prices);median=prices[n//2] if n%2 else (prices[n//2-1]+prices[n//2])/2
  retained=[c for c in candidates if median/2<=Decimal(c['price'])<=median*Decimal('1.5')]
  spread=max(Decimal(c['price']) for c in retained)/min(Decimal(c['price']) for c in retained)
  values=sorted(Decimal(c['price']) for c in retained);n=len(values)
  final=values[n//2] if n%2 else (values[n//2-1]+values[n//2])/2
  results.append({'product':product,'before':len(candidates),'after':len(retained),'spread':str(spread),'identities':[c['identity'] for c in retained],'median_announced':str(final.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)) if n>=5 and spread<=Decimal('1.5') else None,'reason': 'amostra_insuficiente' if n<5 else 'amostra_dispersa' if spread>Decimal('1.5') else None,'note':'Includes all candidates; an evaluated target must additionally be excluded.'})
 return {'observations':len(rows),'rejections':dict(Counter(reason for d in decisions for reason in d.get('reasons',[d.get('reason','')]) if reason)),'decisions':decisions,'groups':results}

if __name__=='__main__':
 source=Path(__file__).with_name('used-probe.json');out=Path(__file__).with_name('audit.json');result=audit(json.loads(source.read_text())['observations']);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='decisions'},ensure_ascii=False,indent=2))
