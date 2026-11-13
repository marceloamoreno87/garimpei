# Orchestration Journal — F17

**Run:** `2026-11-13T02-36-59Z`
**Branch:** `wave/20261113-f17`
**Status:** `success`
**Retry budget:** 3; nenhum ciclo de correção iniciado.

## Entrada e escopo

Retomada autorizada da implementação/avaliação paralela. Worktree própria confirmada; merge da master preservou o progresso de F17 mais recente e as demais entradas da master. Os commits `f12fdc5` e `b2fec10` foram preservados. Quatro artefatos não rastreados de sessões interrompidas foram preservados. Lock exclusivo em `.runtime/f17-orchestration.lock` com PID/host/branch/início.

## Ciclos

| Ciclo | Etapa | Resultado | Evidência |
|---|---|---|---|
| 0 | Implementação | Preservada; sem alteração de requisito/código | [impl-report](impl-report.md) |
| 0 | Pré-requisitos | Docker voltou; versão 29.9.3 | `docker info --format '{{.ServerVersion}}'` exit 0 |
| 0 | Verificação | Em execução: laboratório de falhas e seis gates | Evidências serão anexadas ao finalizar |

## Limites

Contrato permanece preliminar: controles de mesma carga para quedas, métricas de pico e matriz integral ainda pendentes. A calibração combinada histórica não comprova o aceite desta execução. Fases posteriores exigem o gate documental previsto no plano; nenhuma política real foi habilitada.

## Incremento de calibração e avaliação dirigida

- Regressão completa do laboratório recuperada após Docker: 1 PASS em 245,76 s; seis gates Python aprovados no snapshot.
- Ausência de relatório de métricas reproduzida (1 FAIL em 39,54 s), seguida de controles/falhas pareados e sampler do banco/filas/armazenamento da instância correta. POST: 2 PASS/72,70 s; commit/publicação: 2 PASS/27,86 s; confirmação: 2 PASS/65,86 s; autorização: 4 PASS/72,40 s.
- 25 pares em cinco fronteiras foram medidos com o mesmo hash de carga, runtime, testes e lock; 5 pares de carga mista demonstraram runtime/coleta/backup enquanto valoração e POST estavam retidos. Evidências `paired-*.json` e `mixed-load-isolation-*.json`.
- O primeiro comparador de carga mista detectou timestamps diferentes porque o helper avançava o relógio; entradas foram fixadas no artefato reproduzível e a nova execução concluiu os cinco pares. Não se alterou política de produto para ajustar o ensaio.
- Avaliação CLI real encontrou omissão de instante/escopo em `CLI-RESTORE-01` e de escopo/última falha em `CLI-VERIFY-01`. A avaliação HTTP encontrou motivo genérico em `API-RESUME-02`. Relatórios/evidências anteriores preservados.
- Ciclo de correção 1 preparado em cópias temporárias para preservar a suíte congelada em andamento: CLI 2 FAIL → 2 PASS, seis gates; HTTP patch do agente auxiliar com 11 PASS e seis gates. Patches ainda não aplicados à branch nesta etapa.
- Calibração canônica com amostragem adicional de origem/destino está em andamento; não se confirma o perfil antes de consolidar seus resultados.

## Encerramento

- Gate fase1 concluído e spec/plano/contrato regenerados preservando os58IDs e todos os limites.
- Ciclo1 aplicado com CLI/HTTP e validação de assinatura; candidata final22PASS/28,70s e seis gates exit0, hashes exatos de src/tests/perfile verificados após aplicação.
- Baseline700PASS em partições disjuntas, semFAIL/ERROR/SKIP; coleção final712, os12novos pertencem à candidata22PASS, nenhuma falta.
- Django/check, makemigrations dryrun e migratecheck0 na mesma fonte final.
- Todos58itens e10ACs aprovados no relatório final abaixo, incluindo RetryAfter900 real, A/B com BapósfalhaA e preservação conjunta de observação/escolha/recibo nas duasfronteirasSIGKILL.
- Ambientes próprios encerrados; manifests de falha de rollback sem PID vivo preservados. Habilitação real permanece desligada.

Relatório canônico: [eval-report-2026-11-13T03-39-54Z.md](eval-report-2026-11-13T03-39-54Z.md).
