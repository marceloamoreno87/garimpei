# Orchestration Journal — F17 Resiliência operacional e progresso verificável

**Run:** `2026-11-13T00-11-03Z`
**Branch:** `wave/current-f17`
**Retry budget:** 3
**Status:** `aborted`

## Cycle Log

| # | Kind | Status | Counts / Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | running | Retomada da matriz de falhas de rede, posse, cursor e quedas | [contrato](contract.md) |
| 0 | testes dirigidos | passed | CLI: 1 teste em 32,99 s; SIGKILL após POST: 1 teste em 39,42 s; seis gates aprovados | [implementação](impl-report.md) |
| 0 | calibração | partial | 30 medições, cinco restaurações verificadas; 1 teste em 320,95 s | [implementação](impl-report.md) |

## Cycle Detail

Continuação autorizada após a integração dos incrementos anteriores; o perfil de produção permanece preliminar.

Os casos de rede usam origem loopback, controle e timeout reduzido apenas em eval. Cursor repetido, geração anterior, revisão obsoleta e falha anterior ao commit usam transação revertida; a troca sintética de geração não mede expiração de lease por tempo. O destino PostgreSQL próprio foi interrompido e recuperado, com a origem independente disponível. O cenário existente de SIGKILL real após POST passou. A regressão da calibração anterior não cobre a matriz integral nem confirma o perfil.

Posteriormente passaram os testes de expiração temporal real de lease (36,57 s), SIGKILL antes do commit da coleta (15,22 s), arquivo órfão após publicação simulada (12,73 s) e autorização/reconciliação (18,53 s). A regressão da calibração direta passou em 320,95 s; a própria verificação conserva perfil não confirmado e habilitação desativada.

## Final Verdict

**Status:** `aborted`

O coordenador solicitou o encerramento deste incremento para integração. Não foi identificada impossibilidade externa: ainda são tarefas locais implementar e medir os demais pontos de queda da CLI, repetir falhas com controles e dados de fila/idade e pico de armazenamento, fechar o perfil com as medições e executar a avaliação completa. Não foi alegado sucesso nem promovido o progresso da F17.
