# F18 — avaliação de UI e reprodução focal

Fonte congelada `f2bbf39`. Sessão exclusiva `garimpei-f18`, Chromium via `playwright-cli`; aplicação descartável `eval_f18_work_a6191237`, porta23511, init/stop normais, IA e alertas reais desabilitados. Os anúncios, valores, fotos ausentes, contexto geográfico confirmado e comparáveis destas capturas são **controlados**. A prova real separada está em `live-validation.json`; nenhuma captura de UI comprova a geografia real.

## Jornadas observadas

1. Abrir lista com `aba=funcionam&q=PlayStation&categoria=479353692612078&pagina=1&versao=<fixada>`, ir aos detalhes e retornar em1440px/390px. Os cinco parâmetros foram preservados, inclusive no redirect303 da edição opcional.
2. Alvo18901 inicialmente sem capacidade. Abrir o formulário opcional, enviar999gb:422 com valor preservado; corrigir825gb:303, origem manual/revisão1/observação1. Nenhum cadastro de interesse ganhou campos obrigatórios.
3. Publicar pesquisa controlada em três fatias:1página/5detalhes/5retidos, compra1000, mediana2300, taxa12.5%=287.50, lucro1012.50. A versão fixada conservou a leitura anterior até clicar explicitamente em atualizar. Depois, lista/detalhes mostraram os mesmos números e cinco links, preços pedidos e datas. Fonte controlada; nenhuma venda realizada foi alegada.
4. Atualização HTMX substituiu o formulário: antes do ajuste, marca/tipo de memória reapareciam habilitados para PS5; após o initializer em `htmx:afterSwap`, os campos irrelevantes ficaram hidden+disabled em desktop/390px. O inicializador tem marcador de propriedade para não duplicar listeners.
5. Corrigir clipping do texto longo indisponível no card: largura do documento390=viewport390 e todos os seis valores financeiros com clientWidth=scrollWidth300. O cache estático da sessão anterior foi invalidado apenas para observar o CSS coletado atual; a captura final de motivos em nova navegação também confirmou wrapping normal.
6. Nova observação2, título1TB, contradisse825gb manual. A tela mostrou ambos os valores, bloqueou venda/lucro e diagnóstico atual, abriu as três escolhas explícitas. Clique público em “Manter minha correção revisada”:303, revisão2 ligada à1, observações originais preservadas. Nenhum resultado antigo desbloqueou a leitura fixada. Reavaliação posterior usou observação2/manual2 e referências ainda válidas.
7. Lista única com quatro ofertas confirmou simultaneamente: identidade não reconhecida, atributo ausente, conflito real, avaliação pendente; banner de falha da fonte separado. Compra conhecida permaneceu1000; venda/lucro indisponíveis não apareceram comozero.
8. Abrir Acompanhamento e expandir cobertura: sete interesses, versão/data do recorte, famílias/atributos, reconhecimentos/lacunas/amostra insuficiente e zero observações de CellPhones. Somente16 propostas textuais humanas estão aprovadas; restantes contagens se identificam como automáticas e a tela rejeita alegação de suporte universal da categoria.

Capturas abertas e examinadas: `ui-desktop-detail.png`, `ui-mobile-list.png`, `ui-mobile-detail.png`, `ui-mobile-review.png`, `ui-mobile-conflict.png`, `ui-mobile-resolution.png`, `ui-mobile-coverage-viewport.png`, `ui-mobile-reasons.png`. DOM/assertivas: `ui-conflict-dom.txt`, `ui-resolution-dom.txt`, `ui-coverage-check.txt`, `ui-reasons.txt`. Não há overlays nessa jornada; painéis nativos details foram examinados abertos antes da ação seguinte. Console da última navegação:0erros/0warnings; isso não apaga erros422 esperados e transportes durante reinícios anteriores da própria instância.

## Avaliação visual — frontend-ui-design

| Dimensão | Nota | Evidência observada |
|---|---:|---|
| Design, peso2 | 7 | Verde/creme, hierarquia de compra/venda/lucro e cabeçalhos coerentes com o design existente; blocos de prova seguem os mesmos tokens. |
| Originalidade, peso2 | 6 | Linguagem e dados específicos de garimpo, procedência e revisão; formulários e details ainda seguem padrões convencionais. |
| Acabamento, peso1 | 7 | Sem overflow/clipping após ajuste; campos/touch targets legíveis390px. Proveniência extensa e chave técnica `capacity` no conflito ainda poderiam receber polimento. |
| Funcionalidade, peso1 | 7 | Motivos e ação de revisão claros, edição opcional e contexto preservado; cobertura expandida é densa e exige rolagem. |

Média ponderada `(7*2+6*2+7+7)/6 = 6.67/10`. Nenhuma dimensão≤3. Julgamento visual não substitui assertivas contratuais.

## Reprodução controlada e limites

- Unit: em `apps/backend`, `uv run --frozen --no-sync pytest tests/unit` —337PASS4.08s, `ui-final-unit.txt`.
- Gates: na raiz, `node scripts/run-gates.mjs` — seis gruposPASS, `ui-final-gates.txt`.
- Regressões de primeira elegibilidade já executadas: `tests/integration/test_identity_first_alert.py` —2PASS42.20s, `identity-first-alert-final.txt`. Cobrem primeiro envio recente, recibo confirmado após reinício e condição-only/no-op.
- Matriz adicional reproduzível sem credenciais: na raiz, `uv run --project apps/backend --frozen --no-sync python docs/F18-identificacao-de-produtos-e-busca-ativa-de-comparaveis/evidence/ac14_matrix.py`. Usa factory existente, fonte e canal HTTP loopback, banco/portas únicos e stop--clean emfinally. Não carrega perfil real nem WAHA real. `ac14-matrix.txt` registra antiga/ausente/conflito/uncerta, uma tentativa e nenhum reenvio após restart/manual/contradição.
- `retention_check.py` e `preservation_check.py` registram os drivers exatos usados na instância UI controlada. Exigem o apontador privado da instância própria em `.runtime/f18-execution/envfile-path.txt` e os alvos18901/19702 preparados pela jornada acima; falham sem esses pré-requisitos. Não apontar esse arquivo para a principal. Retenção: alvo18901 reconhecido manual2/observação2 com cinco referências2300. Preservação:19702 com match ativo/preço1000; cria recibos/corpos sintéticos próprios e compara estado antes/depois. Outputs sanitizados em `retention-check.txt` e `preservation-check.txt`.
- A UI foi encerrada e a instância23511 removida com `stop.sh --clean`. Para repetir a jornada, criar outra instância descartável com `tests.factories.runtime.prepare_instance`, `configure` e `tests.factories.comparable_research.seed_case`; nenhum banco privado principal é requisito.

A suíte completa final pertence ao coordenador, congelada em6144193 com675nodeids/110arquivos/três shards. Está pendente neste checkpoint; os resultados acima se sobrepõem e não são apresentados como uma nova suíte completa. A ativação automática real permanece bloqueada: fonte respondeu6km ao pedido500km.
