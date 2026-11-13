# F15 — Ciclo4: executor revisável do corpus

Item afetado: `E2E-QUALIDADE-01`, cuja preparação técnica não podia ser atribuída apenas à revisão humana: `AssessmentLab.action(evaluate_corpus)` devolvia BLOCKED incondicional e não havia ingestão/execução. A regressão pública do protocolo do lab falhou contra esse stub (`evidence/retomada-quality-runner-red.txt`:1FAIL/14PASS).

Implementado `tests.factories.assessment_quality` e módulos de validação/runtime. O modo padrão valida; `mode=real` exige ambiente eval descartável próprio, fila exclusiva/ociosa, F19 habilitado e alertas desativados, reserva/runtime/modelo pinados reais. O processo pausa/resume somente o worker verificado desse ambiente. Nenhum download/modelo alternativo ou mudança do runtime principal integra o executor.

Antes de tocar runtime, valida hash do manifesto congelado, todosIDs humanos, reviewer/data com timezone, rótulos, referências literais/fotos, hashes, contenção dos caminhos no pacote, proveniência, splits separados e ausência de foto repetida entre ajuste/reservado. Export parcial continua pendente. Textos corrigidos/categorias alteradas exigem novo manifesto revisado; o agente não completa dados por inferência. Casos uncertain aceitam limitação concreta sem sinal inventado. Casos textuais/sem fotos são legítimos e não fabricam chamadas/métricas.

Depois da revisão efetiva, o driver real usa mídia local por origem loopback própria, download/pins F14, avaliação/preparação/política/publicação F15 e fila/gateway/schema F19 de produção. Somente reserved é executado; ajuste não vaza para o conjunto reservado. Relatório incremental registra IDs/hashes/versões, matriz, falsos bons/falsos defeitos/abstenções, erros, limitações, chamadas, GPU/F19 e amostras explícitas de RAM host/RSS avaliador. Uma falha antes de enviar fotos reais impede marcar o relatório completo. Resultado controlled_fake é recusado como qualidade real.

Verificação:19 unit PASS, incluindo ingestão inválida antes de runtime, matriz e proibição de completar relatório sem chamada real;1integração PASS exercita cadeia com foto sintética e recusa a telemetria fake antes de escrever qualidade real; seis gates Python aprovados. `retomada-real-runner-pending.txt`:CLI real sobre template humano nulo retorna exit2 e model_executed=false. Não houve execução do corpus reservado nem geração de rótulo humano.

Esta é a segunda correção real da retomada: histórico cycles 2→3→4; orçamento consumido2/3. O item permanece BLOCKED por revisão humana e execução real subsequente, sem enfraquecer o contrato.
