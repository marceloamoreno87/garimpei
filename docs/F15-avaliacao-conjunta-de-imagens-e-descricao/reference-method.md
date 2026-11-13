# F15 — Origem explícita da referência

O usuário pediu que Codex faça a revisão com auxílio de IA. A autoria é identificada como `Codex (IA)` e o arquivo exportado declara `reference_method: "ai_assisted"`. Essa instrução permite preparar a referência de IA sem fingir participação humana. Os critérios canônicos de qualidade e o histórico de avaliações permanecem preservados; uma eventual alteração de aceite será documentada pelo coordenador separadamente.

O export/template adiciona somente o campo top-level `reference_method`; valores válidos são `human` e `ai_assisted`. O template começa em `null`. Método ausente, nulo ou desconhecido bloqueia a operação antes de ler manifesto/fotos ou tocar runtime. O nome de reviewer nunca define o método. Export de revisão, casos, sinais e evidências têm campos conhecidos; dados extras e envelopes de rascunho são rejeitados pelo executor. Todos os metadados/rótulos/splits são validados antes dos bytes das fotos. Os IDs, hashes, fotos e bytes do manifesto permanecem iguais: SHA256 `26c3ee5e9d34a51b8d3827e9700134e7e45d6cea3dbf2f86a0c81f3f05c3a59b`.

O caminho real permanece opt-in por `mode=real`, após validação completa e seleção de eval próprio com F19 real, sem canais reais. Esta mudança não executou corpus reservado nem iniciou GPU. O método da referência não é enviado ao modelo como instrução, assim como rótulos/reviewer; a entrada continua limitada ao texto e às fotos do caso.

| Método | Relatório |
|---|---|
| `human` | `comparison_kind=human_reference_comparison`, `independent_human_review=true` como método declarado; matriz referência×automático e contagens `false_good`/`false_defect`. A aprovação do contrato continua separada (`legacy_human_acceptance_satisfied=null`). |
| `ai_assisted` | `comparison_kind=ai_agreement`, `independent_human_review=false`, `legacy_human_acceptance_satisfied=false`; concordância entre referência assistida por IA e modelo avaliado. Usa `automatic_good_reference_other`/`automatic_defect_reference_other`, sem chamar divergência entre IAs de falso positivo/negativo humano. |

Resultados por caso usam `reference`, nunca o antigo campo `human`. Ambos os métodos preservam versões, IDs/hashes, métricas reais quando houver execução, erros e abstenções; a origem sintética/real das imagens continua separada da autoria da referência. Um arquivo marcado como `human` declara esse método, não constitui por si só prova de independência nem aprovação de todos os critérios. Arquivos legados sem origem precisam ser exportados novamente com a origem efetivamente conhecida; não há fallback que presuma humano.

Verificação desta etapa:12falhas esperadas/18PASS antes da mudança;34unit PASS depois, cobrindo ambos os métodos, metadados nulos/legados/extras, bloqueio anterior a foto/runtime e nomenclatura da matriz. Integração do executor:1PASS/8deselected usando controle local e recusando resultado fake como prova real. Seis gates Python aprovados. CLI sobre o template com método nulo retorna exit2/model_executed=false. Evidências `evidence/reference-method-{red,unit,integration,six-gates,template-blocked}.txt`.

`cycles=4` permanece: esta etapa adapta requisito explicitamente solicitado; não inventa uma nova correção do ciclo anterior. A suíte integral do coordenador foi interrompida por SIGINT antes desta mudança, sem declaração de aprovação. Uma nova consolidação pode usar o checkpoint desta etapa.
