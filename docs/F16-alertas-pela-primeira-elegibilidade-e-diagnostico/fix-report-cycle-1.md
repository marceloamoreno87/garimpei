# Correção 1 — F16

Entrada: `eval-report-2026-11-12T13-49-00Z.md`. Orçamento: 1 de até 3 correções. A reavaliação completa depende da suíte congelada449, ainda em execução; este documento não atribui done.

| Item/fronteira | Causa demonstrada | Correção e prova |
|---|---|---|
| WRK-REDUCAO-04 | O histórico de eventos restringia authorized/uncertain a `authorized_at > now − policy.window`; a extensão do primeiro alerta não aplicava esse filtro. Probe observou espera indevida exatamente em24h e após. | `_first_intent_pending` aplica a mesma janela F09 ao primeiro efeito. RED1PASS/2FAIL; GREEN3PASS nos limites−1/0/+1s. Queda distinta ainda válida espera antes do limite, confirma primeiro e envia uma redução própria; ACK tardio não reabre queda excluída. Primeiro corpo e financeiro preservados. |
| Gate de regressão/F10 | Lookup do teste de troca de grupo fazia INNER JOIN obrigatório por evento. Primeiro alerta F16 usa first_decision; mensagem já havia chegado ao grupo fake correto, mas SELECT retornava0. | Consulta cobre ambas origens e espera por listing981/982. Mantém uma mensagem por identidade, destino antigo e corpo/financeiro originais após trocar grupo. PASS na matriz focal. Testes Facebook preservados. |
| SVC-DIAGNOSTICO-01/G9 | Alteração real para evidência sem modelo passou por F07 e voltou produto_incompativel, produzindo rótulo de variante divergente sem identidade reconhecida. | Em first_financial, composição indisponível com esse motivo e `identify(evidence) is None` torna-se produto_indeterminado. RED público em HTTP/DTO; GREEN com condição/revisões e todas as asserções anteriores preservadas. Não altera F07/F19, inferência, valores ou snapshot autorizado. |
| G1–G9/preparo | Faltavam assertivas temporais e de mesma identidade, embora os caminhos básicos já tivessem provas. | `evidence/coverage-closure.md` mapeia as extensões executadas. Releitura independente liberou freeze sem lacuna residual; corpus valida e alimenta BASE/LEGADO/QUEDAS/variações. |

Validação antes do novo full: seis gates backend, Django, drift, build wheel e harness exit0. Matriz focal conserva histórico34PASS/3FAIL iniciais e fecha com9PASS+8PASS; os três FAIL de preparo/expectativa não foram apagados nem convertidos em sucesso. Prova no navegador usa mesmo Listing/ref/grupo/recibo depois de reiniciar e confirma zero efeito dos GETs.

A transmissão real autorizada já concluída permaneceu preservada, sem POST adicional. O defeito canônico de janela e o gate interrompido não foram ocultados: a rodada anterior segue fail/38BLOCKED, e o ciclo1 exige relatório novo após449testes e comparação before/after reais.
