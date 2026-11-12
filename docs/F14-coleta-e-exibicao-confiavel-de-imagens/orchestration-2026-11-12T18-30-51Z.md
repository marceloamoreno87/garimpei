# F14 — Orquestração

Entrada: implementação e avaliação em worktree feat/F14-imagens-locais, base 3ce35d5. Máximo três correções. Commit autorizado; integração pelo coordenador. Nenhum envio WhatsApp nem uso concorrente do perfil real.

## Implementação inicial

Em andamento: extração, cópias locais, retenção, galeria, laboratório e testes.

## Avaliação inicial / ciclo1

Relatório: eval-report-2026-11-12T19-05-22Z.md. Falhas: assinatura F16 e reflow estreito; fonte real bloqueada. Correção1 em andamento; máximo3. Base preliminar789eb44 integrada pelo coordenador.


## Encerramento canônico da execução

**Run:** `2026-11-12T18-30-51Z`
**Feature folder:** `docs/F14-coleta-e-exibicao-confiavel-de-imagens/`
**Branch:** `feat/F14-imagens-locais`
**Retry budget:** `3`
**Status:** `manual-pending`

## Cycle Log

| # | Kind | Status | Counts / Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | success | Base789eb44; implementação controlada e fronteiras públicas entregues | impl-report.md |
| 0 | evaluator | fail | P20 F2 B13 M0 S0; assinatura F16 e reflow | eval-report-2026-11-12T19-05-22Z.md |
| 1 | fix-runner | fixed | b72b351,507e373,f58b7fc,e253e9e,4793cc1; assinatura/fragmentos/schema/ownership/scheduler/reflow | correction-cycle1*.md |
| 1 | evaluator | pending | Full533 PASS congelado, fonte real parcial e checagens visuais complementadas no ciclo2 | evidence/final-summary.json |
| 2 | fix-runner | fixed | e311eba; UI-ATUALIZACAO-03 rótulo removido versus conservado | correction-cycle2.md |
| 2 | evaluator | pending | P34 F0 B1 M0 S0; ACs6 verificadas/2 indeterminadas | eval-report-2026-11-12T20-12-37Z.md |

## Cycle Detail

### Ciclo1

As duas falhas iniciais foram corrigidas com regressões. Revisões do coordenador também identificaram: fragmentos do mesmo listingID separados, fastpath de galeria incompleto, colisão física de photoskeys, enumeração de backup, remoção sem owner e fluxo de agendamento em lotes. As correções e provas estão em correction-cycle1*.md. A fonte real obteve principal/adicionais após integração coordenada. A primeira suíte interrompida é apenas diagnóstico; a fonte congelada a7e7469 passou533 testes sem skip/erro/duplicação com513 hashes iguais antes/depois. Circuit breaker: sem repetição de falhas sem ganho; bloqueio externo preservado.

### Ciclo2

Falha visual reproduzida na remoção: legenda global prometia cópias conservadas quando todas haviam sido removidas. Regressão parametrizada3FAIL/1PASS antes,4PASS após, foco14PASS; seis gates PASS. Nenhuma outra lógica de produto foi modificada. Foram adicionadas provas controladas de quatro estados, página2/foco/atualização explícita, falhas de rede/gravação/rename/quota, LEGADO com manual/histórico/recibo confirmado fake e reinício. Suplementos novos:14PASS19,91s +1PASS34,06s. Inventário atual548. Full533 não é extrapolado ao único input anterior alterado (presentation.py); delta exato registrado em cycle2-input-delta.json. Circuit breaker: nenhuma falha local restante; prova externa insuficiente impede clean.

## Final Verdict

**Status:** `manual-pending`
**Total cycles:** `2` correções de3 autorizadas
**Last evaluation:** `eval-report-2026-11-12T20-12-37Z.md`
**Items:** `34 PASS · 0 FAIL · 1 BLOCKED · 0 MANUAL · 0 SKIPPED`
**ACs:** `6 verified · 0 failed · 2 undetermined`

Item bloqueado: E2E-FONTE-01. A fonte forneceu13 originais de dois anúncios verificados por hash/HTTP/dimensões locais, mas as observações autorizadas não provaram duas resoluções da mesma foto. A inspeção CLI final confirmou thumbnail nativa visualmente menor com mesmos bytes/dimensões naturais; não conta como variante. Coordenador encerrou investigação externa desta onda. Não há waiver nem done; F15 só pode avançar implementação independente e conserva dependência de aceite.

Recursos criados nesta execução foram parados por ownership: laboratórios antigos e final, servidores loopback, sessões Playwright locais. Principal/perfil permanecem sob coordenação root; nenhum envio WhatsApp real. Configuração real5GiB aprovada ficou privada. Lock F14 desta execução liberado no fechamento.

## Soft-fails (run-level)

O full da união final posterior ao delta UI será reportado pelo coordenador. Evidências antigas com overflow/500 pré-restart/preparo incorreto permanecem diagnosticadas, sem substituir resultados corrigidos. Screenshots da fonte real com navbar da conta não foram versionadas.
