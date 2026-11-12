# F15 — Pacote de revisão humana prévia

Rubrica `condition-policy-v1`; saídas de modelo ainda não foram consultadas para estes casos. Não há rótulos humanos preenchidos pelo agente. O conjunto controlado cobre seis categorias e leve/dano/suspeita, mais as três regressões textuais. As imagens sintéticas serão identificadas como controles, sem alegação de fotografia real.

Para cada caso, informar condição `good|defect|uncertain`, trecho/foto que sustenta o rótulo, gravidade `light_wear|clear_defect|suspected|unknown`, componente principal/acessório e limites. Preservar ambiguidade: reflexão/mancha indistinta é suspeita; aparência boa/tela ligada não comprova funcionamento. `good` exige declaração explícita válida e fotos úteis suficientes, sem omissão/conflito; leve desgaste permite ressalva; dano relevante claro ou falha funcional é defeito. Manual prevalece na aba mas não fabrica análise suficiente.

| Categoria | Leve permitido | Defeito claro | Abstenção |
|---|---|---|---|
| Eletrônicos gerais | risco superficial | carcaça quebrada/componentes expostos/corrosão | objeto ou reflexo não identificável |
| Câmera | riscos externos | lente/visor quebrado/corrosão | mancha ambígua, interior desconhecido |
| Computador | risco tampa/base | tela trincada/dobradiça quebrada/bateria estufada | componente não identificável |
| Console | riscos externos | conector/carcaça do console quebrados | controle com defeito não prova falha console |
| Fone | marcas sem ruptura | haste quebrada/condutor exposto | extensão do desgaste não clara |
| TV | marcas moldura/base | painel trincado/estrutura quebrada | linha/reflexo pode pertencer à imagem |

Dois anúncios reais já preservados pela F14 estão em `human-review-real.html` (abre somente imagens locais da instalação, sem URLs da fonte). Rótulos humanos reais e suficiência devem ser preenchidos antes da execução reservada do modelo. A cobertura real observada cobre somente as categorias presentes nessas ofertas; não será alegada cobertura real das seis sem material.

A revisão deve ser entregue em arquivo separado com case_id, reviewer, reviewed_at, label, findings e limitações. Não alterar rótulos após consultar predições no conjunto reservado. Sem revisão efetiva, E2E-QUALIDADE-01 fica BLOCKED.
