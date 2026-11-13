# Orchestration Journal — F21 prova real

**Run:** `2026-11-13T19-47-43Z`
**Branch:** `feat/f21-prova-real`
**Started at:** 2026-11-13T19:47:43.759201+00:00
**Retry budget:** 3
**Status:** aborted — impedimento externo da qualificação positiva real

Implementação preservada da base 15b1f48. Item pendente: E2E-REAL-01. Referência assistida por IA autorizada, sem revisão humana independente; congelamento anterior mantido. O usuário autorizou publicação do trabalho; o coordenador verifica e integra a correção e suas evidências. A integração não conclui o contrato nem muda F21 para done. Recursos próprios, WAHA fake e perfil dedicado sem cópia de cookies.

## Cycle Log

| # | Kind | Status | Notes | Artifact |
|---|---|---|---|---|
| 0 | evaluator | pending | 25 itens previamente PASS; E2E-REAL-01 BLOCKED. Diagnóstico iniciado antes de qualquer mudança | eval-report-2026-11-13T18-20-00Z.md |
| 1 | fix-runner | fixed | `condition-evidence-v4`: referências curtas expandidas deterministicamente, schema no prompt, mensagem única no contador, status exclusivo da foto; políticas e limites conservados | evidence/proof-validation-2026-11-13/child-*.txt |
| 1 | evaluator | pending | Seis gates PASS / 50 testes focais PASS. Prova principal: 52 chamadas reais, 12 análises, 10 exclusões anteriores à inferência; 0 positivo ouro / 0 POST. Regressão completa em execução coordenada | evidence/real-model-proof-ef90.json |
| 2 | fix-runner | fixed | Isolamento de ambiente dos helpers, prontidão da amostra F16 e transporte hostil adaptado ao v4; corrigida a flag false explícita introduzida na fixture, após reprodução isolada. Fonte de produção preservada. | evidence/proof-validation-2026-11-13/test-harness-diagnosis.md |
| 2 | evaluator | pending | Rechecks finais46 PASS+103 PASS; consolidação913casos únicos PASS, seis gates Python e checks Django/migrations/wheel/harness aprovados. E2E-REAL-01 permanece BLOCKED; filtro atual não reaprova os25 itens anteriores. | eval-report-2026-11-13T21-22-17Z.md |

## Diagnóstico e correção

A reprodução inicial com bytes originais do corpus congelado gerou 1003 tokens e uma citação inexistente no campo indicado. A geração repetia metadados, trechos longos e hashes. O protocolo físico v4 usa códigos de referência fechados; a expansão para os hashes/trechos originais é determinística e passa novamente pelo validador canônico. O modelo decide exame/omissão; nenhuma foto é marcada examinada pela ausência de resposta. Dados sem prova continuam limitações, e contradições/defeitos não são removidos para obter aprovação.

Schema e contexto completos entram na mensagem efetiva e no mesmo contador. Mantidos contexto 4096, geração 1024 no perfil de condição, reserva visual 1536, margem 256, geração legada F19 512, modelo/digest e taxa 10%. Regressões observaram RED antes de GREEN para referências fora da chamada, expansão Unicode/hash, cobertura e mensagem contada. Uma tentativa de `oneOf` com propriedades exteriores produziu resposta física inválida no Ollama; substituída por status exclusivo da única foto, sem alterar o contrato canônico. Essa tentativa não é evidência de sucesso.

## Evidência real até a avaliação em curso

Referências IA anteriores preservadas, mais 12 links do usuário e coleta adicional. Não houve revisão humana independente. A execução principal terminou normalmente e conservou banco/volumes: 52 chamadas físicas, 270–571 tokens gerados, máximo de 1260 tokens de prompt medidos pelo servidor, nenhum `generation_length_limit` ou `text_reference_mismatch`. Duas avaliações completas/boas foram bloqueadas por lucro negativo; o candidato a 1400 foi classificado como defeito pelo modelo. Casos sem observação no recorte F04 não receberam análise local fictícia. Uma avaliação falhou por saída com alegação proibida; partes não enviadas permanecem explicitadas.

Os 36 detalhes adicionais de iPhone12 não produziram amostra F06 válida. A última seleção de candidatos baratos de iPhone13 usa apenas IDs da pesquisa já verificada; ela não seleciona comparáveis para aumentar a mediana. O novo candidato1902857791096295 recebeu referência IA inconclusiva antes da inferência: aviso de bateria não verificável e ambiguidade de galeria. As seis chamadas adicionais terminaram com avaliação parcial: cinco de seis fotos examinadas, defeito segundo o modelo e condição insuficiente. A aplicabilidade da análise foi conferida; a espera resulta de cobertura parcial, sem substituir a foto omitida por evidência fictícia.

O total final é58 chamadas físicas, sem limite de geração ou referência textual inválida, e zero Ouro/POST fake/POST real. As duas análises suficientes/boas têm compra1600, venda1600 e lucro−160 após10%; o candidato1400/1600 com lucro40 não satisfez condição. A coleta complementar limitada de Xbox, PS5 e Sony foi encerrada pelo coordenador, com perfil fechado, sem obter alvo mais cinco comparáveis elegíveis. O impedimento positivo permanece externo ao encerramento de truncamento/referências. Não se trata de benchmark humano: há divergências e achados visuais falsos/sem sustentação nas saídas locais.

## Isolamento e ocorrências de ambiente

Lock exclusivo em `.git/garimpei-feature-locks/F21.lock`, com PID/host/branch/início próprios. As instâncias `eval_f21_proof_ef90` e `eval_f21_proof2_ef90` pertencem a esta worktree. Nenhum envio WhatsApp real. O uso de `/tmp` por recursos existentes esgotou o tmpfs; a regressão coordenada reiniciou com temporários próprios em `/var/tmp`, sem limpeza de outras sessões. Os 462 arquivos Python de produção mantêm os hashes congelados em `source-freeze.json`; quatro arquivos de testes/helpers foram corrigidos depois e reavaliados integralmente.

## Resultado e finalização

- Avaliação focal atual: `eval-report-2026-11-13T21-22-17Z.md`, status pending, 0 PASS/1 BLOCKED/25 SKIPPED; nove ACs indeterminados neste filtro. Os 25 PASS do relatório anterior permanecem históricos, sem convertê-los em execução atual.
- Prova final:58 chamadas reais locais, zero limite de geração/referência textual inválida, zero Ouro positivo e zero POST fake/real. Referências assistidas por IA congeladas; sem revisão humana independente. Taxa 10%, políticas, limites e modelo preservados.
- Engenharia:913/913 casos únicos PASS por consolidação auditada, sem alegar um processo único ininterrupto. Reexecução integral dos 149 casos afetados após a última correção:46 PASS/573,07 s e 103 PASS/582,95 s, ambos exit 0/drift 0. Tentativas anteriores mantidas, inclusive61 PASS/6 FAIL/SIGINT, RED multimodal e logs ENOSPC sanitizados com recibo.
- Revisão independente sem P1/P2 confirmado; seis gates Python após a última alteração; Django, migrations, wheel e harness aprovados. `all_contract_gates_passed=false` e `feature_done=false` em `final-validation.json`, porque a dimensão real positiva continua pendente.
- Duas correções neste run: `cycles` acumulado 2→4. F21 conserva `implemented` e `completed_at:null`; nenhuma outra feature do progresso foi modificada. IDs, dependências, contratos e avaliações anteriores preservados.
- Web/worker e serviços das duas instâncias reais encerrados por stop normal, sem limpeza de dados. Bancos/volumes mantidos para auditoria. Sessões próprias de navegador e perfil adicional fechados; nenhum recurso de terceiro removido. Lock próprio liberado após finalizar os testes, com recibo em `child-proof-resource-finalization.json`.
- Commit dos ciclos e evidências entregue ao coordenador; revisão/integração/publicação são responsabilidade da sessão coordenadora. Esta worktree não realiza merge nem push.

O ciclo encerra por não obter um conjunto real suficiente e lucrativo na coleta limitada autorizada. Uma fixture ou mudança de taxa/condição/histórico não substitui essa dimensão. A correção técnica e os checks de engenharia são aproveitáveis, sem concluir F21.
