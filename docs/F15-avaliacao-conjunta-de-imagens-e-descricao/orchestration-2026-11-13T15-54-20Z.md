# Orchestration Journal — F15 Nova onda de diagnóstico e qualidade

**Run:** `2026-11-13T15-54-20Z`
**Branch:** `feat/F15-avaliacao-multimodal`
**Started at:** `2026-11-13T15:54:20.368457+00:00`
**Retry budget:** 3 novas correções, além do histórico cycles=5.
**Status:** `success`

Nova onda autorizada pelo usuário, base4216a13; avaliação anterior15:39:09 preservada. Objetivo: diagnosticar13invalid_output, preservar telemetria em falhas e corrigir apenas causa confirmada, mantendo512tokens de saída/4096context, schema/pins/regras. GPU exclusivamente com agente designado; sem Facebook/WAHAreal ou runtime principal. TMPDIR em disco para todos os filhos.

Referênciae13/splits congelados. O reservado já foi exposto e a repetição será declarada como tal, sem fingir novo heldout. Critério aprovado reference_method=ai_assisted preservado, sem fabricar humano ou metaqualidade. Somente entradaF15 do progresso será alterada.

## Cycle Log

| # | Kind | Status | Artifact |
|---|---|---|---|
| initial | diagnosis | confirmed | [sondagem v1: length/512 e JSON truncado](evidence/wave2-baseline-length-summary.json) |
| 6 | correction (1/3 nesta onda) | checkpoint verified | [correção e regressões](correction-cycle-6.md): 28 unitários, 13 integração e seis gates PASS; prova v2/full pendentes |
| 7 | correction (2/3 nesta onda) | checkpoint verified | [filtragem P2](correction-cycle-7.md): 34 unitários, 7 integração e seis gates PASS |
| 8 | correction (3/3 nesta onda) | checkpoint verified | [perfil v3/1024 autorizado](correction-cycle-8.md): 50 unitários, integrações14/9 e seis gates PASS; GPU/full pendentes |

Durante a onda, o usuário aprovou até1024 exclusivamente na F15; ciclo8 aplica a canon atual, com legado512/contexto4096 inalterados. O escopo inicial512 acima é histórico, não limite da execução final v3.

## Final Verdict

Avaliação canônica final: [eval-report-2026-11-13T16-58-43Z.md](eval-report-2026-11-13T16-58-43Z.md),31PASS/8ACs verificados. Perfil v3/1024 aprovado pelo usuário, prova física comparativa/recursos completos;6rejeições/2pendentes/13abstenções preservadas como limitações, sem metaaccuracy. Full bruto811PASS/1FAIL e retry exato após reparo Chromium resultam em812IDs finais PASS/813tentativas,664inputs estáveis. Seis gates PASS. Três correções desta onda consumidas, histórico cycles8. Recursos próprios parados/reserva liberada; histórico/pesos/fila preservados. Lock desta execução será liberado após o commit documental.

**Completed at:** `2026-11-13T16:58:43.821396+00:00`
