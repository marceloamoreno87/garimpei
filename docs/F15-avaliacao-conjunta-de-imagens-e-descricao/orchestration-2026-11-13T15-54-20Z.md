# Orchestration Journal — F15 Nova onda de diagnóstico e qualidade

**Run:** `2026-11-13T15-54-20Z`
**Branch:** `feat/F15-avaliacao-multimodal`
**Started at:** `2026-11-13T15:54:20.368457+00:00`
**Retry budget:** 3 novas correções, além do histórico cycles=5.
**Status:** `running`

Nova onda autorizada pelo usuário, base4216a13; avaliação anterior15:39:09 preservada. Objetivo: diagnosticar13invalid_output, preservar telemetria em falhas e corrigir apenas causa confirmada, mantendo512tokens de saída/4096context, schema/pins/regras. GPU exclusivamente com agente designado; sem Facebook/WAHAreal ou runtime principal. TMPDIR em disco para todos os filhos.

Referênciae13/splits congelados. O reservado já foi exposto e a repetição será declarada como tal, sem fingir novo heldout. Critério aprovado reference_method=ai_assisted preservado, sem fabricar humano ou metaqualidade. Somente entradaF15 do progresso será alterada.

## Cycle Log

| # | Kind | Status | Artifact |
|---|---|---|---|
| initial | diagnosis | confirmed | [sondagem v1: length/512 e JSON truncado](evidence/wave2-baseline-length-summary.json) |
| 6 | correction (1/3 nesta onda) | checkpoint verified | [correção e regressões](correction-cycle-6.md): 28 unitários, 13 integração e seis gates PASS; prova v2/full pendentes |

| 7 | correction (2/3 nesta onda) | checkpoint verified | [filtragem P2](correction-cycle-7.md): 34 unitários, 7 integração e seis gates PASS |

| 8 | correction (3/3 nesta onda) | checkpoint verified | [perfil v3/1024 autorizado](correction-cycle-8.md): 50 unitários, integrações14/9 e seis gates PASS; GPU/full pendentes |

## Final Verdict

Causa confirmada e checkpoint corrigido/verificado. Avaliação canônica permanece pendente da prova física v2 e full do coordenador. Sem veredito done antecipado.
