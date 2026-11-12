# Implementação — F19 Inferência multimodal local em Docker

**Branch/worktree:** `feat/F19-inferencia-multimodal-local`, `/home/marce/.codex/worktrees/6c3f/garimpei`. Base `bc1bc84`. **Estado:** concluída após avaliação canônica clean do ciclo 3: 21 itens PASS e 10 critérios de aceite verificados.

## Entrega implementada

A aplicação admite análises versionadas por observação, prepara texto e imagens autorizadas, agenda partes persistentes e publica somente respostas validadas que ainda pertencem à revisão/geração atual. A interface de serviço para F15 fornece requisição, consulta, cobertura e proveniência; F15 não precisa existir para exercitá-la. Repetições idênticas reaproveitam a assinatura; mudanças relevantes criam outra análise e conservam o resultado anterior identificado.

`domain/inference` contém entrada, assinatura, schema, referências e contratos puros. `usecase/inference` implementa admissão, execução, consulta e pausa/retomada. `infra/repository/inference` serializa controle/admissão/claim/publicação no PostgreSQL; `infra/gateway/inference` implementa artefatos, preparo, quota, registro autorizado, Ollama, transporte, exclusividade e amostragem. A composição é explícita em `main.py`. A migration `0013_local_inference` depende de `0012_opportunity_collection`; cria somente estruturas da inferência. A integração futura com a migration 0013_alert_message_snapshot de F20, também dependente de0012, deve preservar ambas as pontas por migration de união.

O gateway envia JSON estruturado com referências limitadas à entrada, desabilita tools/thinking/cloud/streaming e valida schema, campos extras, motivos de término, métricas, orçamento, offsets/quotes e IDs realmente examinados. O material recebido é dado não confiável. Resultados de IA não modificam condição manual, composição financeira ou recibos e não iniciam contatos. A preparação deriva PNG até512px preservando original/hash/revisão/autorização em área privada; não usa perfil Facebook.

O worker usa uma única instância Procrastinate, fila inference e pelo menos quatro slots, com no máximo uma parte AI em execução e reconciliador independente a cada5s. Claim usa geração e lease240s; chamada180s, até3tentativas com recuos15/30s. Perda de transporte após possível envio conserva posse incerta até prova de encerramento do contêiner próprio. A pausa bloqueia novos despachos e drena somente a chamada atual; a retomada exige confirmação persistida. Modelo ocioso é descarregado após300s sem apagar pesos/resultados.

## Operação e superfícies

- `GET /integracoes/ia/` exibe causa, ação, fila, servidor, residência, versão/digest, horário e análise anterior.
- `POST /integracoes/ia/pausar/` e `/retomar/` usam CSRF/revisão;ações não confirmadas são anunciadas como sucesso. Formato/CSRF/conflito retornam400/403/409, banco503, sucesso303.
- `local_ai prepare --download` prepara explicitamente pesos/tokenizer e calibra perfil visual; `status` lê diagnóstico datado e `smoke --fixture ...` usa somente corpus de avaliação. Códigos0/2/1 distinguem sucesso/pré-requisito/falha. Saída do smoke contém resumo tipado, sem conteúdo das conclusões.
- Compose opcional fixa Ollama0.40.16/digest, qwen3.5:4b-q4_K_M/digest, um modelo/uma inferência, contexto4096/saída512, volume próprio e GPU NVIDIA. Rede de inferência é interna e publicação loopback; somente preparo explícito permite rede externa temporária.

No Docker Desktop deste host a porta publicada não respondeu com rede exclusivamente interna. O transporte usa REST no loopback do contêiner por canal `docker exec` persistente, com script estático e payload apenas stdin, ownership verificado por run, framing completo e deadline total. Comando Docker separado custou~3,07s; aquecimento indica indisponibilidade sem ampliar diagnóstico3s. O canal aquecido medido respondeu em~47ms. A adaptação, limites e recuperação estão em [operations.md](operations.md).

## Preparo e medições reais

Imagem oficial e digests completos, manifesto/blobs e tokenizer da revisão oficial estão em [model-lock.json](model-lock.json). O helper compara metadados aos pins aprovados; o preparo verifica arquivos físicos. Pesos3,3GB permanecem no volume próprio. A RTX5070 foi usada pelo Ollama/CUDA real: logs mostram offload de camadas; `/api/ps` confirma residência integral3140495604bytes/contexto4096; amostras durante chamadas registram atividade/VRAM. Isso vai além da visibilidade do host.

Foto pública autorizada pelo usuário: *PlayStation 5 and DualSense*, Osh33m, [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:PlayStation_5_and_DualSense.jpg), revisão1216350292, CC-BY-SA4.0. SHA256 original `08905d5f2bbb73fd08c4f1e21463052d9c2f7d260d083eb2114a47247a2943db`; derivado512px `2a7f38a5129e7b44e975057e53842e929771683b828b55f61a1fe6dfb3ce2a5e`. Original/manifesto/autorização e derivado ficam privados, fora do versionamento.

| Cenário realmente executado | Observado | Evidência |
|---|---|---|
| Texto frio | succeeded;3,531s, carga2,414s;13amostras, pico host6274MiB/67% | logs privados `.runtime/smoke-text-final.log` e métricas persistidas |
| Foto autorizada quente | succeeded;1,802s, carga4,465ms;7amostras, pico6324MiB/72% | `.runtime/smoke-photo-final.log`, metadados públicos de localidade |
| Imagem sintética B fria | succeeded;4,062s, carga2,433s;15amostras, pico6326MiB/76% | `.runtime/smoke-image-b.log` e `idle-300s.json` |
| Idle300 e recarga | unloaded confirmado~305s;VRAM6326→2439MiB; recarga4,061s/carga2,229s, sem novo pull | [idle-300s](evidence/idle-300s.json), [reload/RAM](evidence/reload-and-ram.json) |
| RAM no cenário frio de imagem | máximo amostrado contêiner881,4MiB; app213164032bytes; host16970485760bytes | [reload/RAM](evidence/reload-and-ram.json) |
| Texto hostil quente/RAM | succeeded~0,514s/carga0,742ms; RAM e saúde amostradas | [warm-hostile-text-and-ram](evidence/warm-hostile-text-and-ram.json) |
| Texto + bitmap hostis | succeeded2partes em nova revisão; snapshots de negócio iguais, sem ações externas | [hostile-new-revision](evidence/hostile-text-and-image-new-revision.json) |
| Foto autorizada nova revisão/RAM | succeeded1,501s, carga3,895ms; contêiner até1023MiB e app207314944bytes; snapshots não vazios iguais, sem pull | [foto/RAM](evidence/authorized-photo-ram.json) |
| Texto Unicode frio/RAM | succeeded3,229s/carga2,128s; contêiner até722,4MiB,3amostras e snapshots não vazios iguais | [texto/RAM](evidence/cold-text-ram.json) |
| IA indisponível convivendo | coleta27→64,3mensagens exclusivamente fake, HTTP200 em saúde/IA/ofertas | [coexistence](evidence/coexistence.json) |

Tempos/picos são observações locais amostradas, sem meta de latência ou avaliação universal de qualidade. RAM host/VRAM incluem outros programas; não foram encerrados para preparar o teste. O teste de foto valida execução/referências, não classificação perfeita de condição ou preço.

## Correções verificadas

Foram preservados REDs e artefatos históricos, incluindo casos de recovery perdido, transporte incerto, métricas inválidas, deadline, framing incompleto e reutilização de bytes da resposta anterior. O canal agora é descartado em toda falha de framing; resposta JSON inválida dentro de frame completo continua falha de validação. Retry bem-sucedido limpa motivo anterior; cobertura enviado/examinado é persistida corretamente; pause/resume não apresenta título transitório indevido.

A rodada ampla do ciclo1 teve11FAIL/342PASS/1ERROR (1113,28s), 384arquivos congelados `3a7119de...db488`. Duas falhas diretas de shutdown sem registry causaram oito falhas em cascata e um teardown; outro teste expôs tarefas AI vazias e fixtures compartilhadas. O ciclo2 retirou dependência main/ORM da liberação runtime, enfileira só trabalho elegível e isola testes F19. Regressões críticas4/4PASS29,16s e focados58PASS42,80s.

As matrizes independentes preservam resultados negativos históricos: [controls original](evidence/controls-20261112.md)19PASS/1FAIL e [pins original](evidence/pins-report.md)6falsos-ready. Após correção: [controls C2](evidence/controls-correction-20261112.md)20PASS/0FAIL, [pins D2](evidence/pins-correction-report.md)15/15PASS, mais [SHA tokenizer](evidence/pins-tokenizer-report.md) negativo após controle positivo. Fakes de I/O são identificados; essas matrizes comprovam causas/regras e não OOM físico ou GPU real.

O ciclo2 foi interrompido graciosamente por finding UI (26PASS395,06s, exit2): posse execution_unknown era apresentada running. O relatório histórico04:12:39 registra1FAIL/20BLOCKED. Ciclo3 corrigiu somente projeção query/handler/template, mantendo causa timeout e encerramento/residência não confirmados. Regressão RED1FAIL6,61s→GREEN1PASS6,88s, inclusive pausa com posse incerta; probe navegador ampliado14PASS/0FAIL. Nenhuma fonte foi editada durante as rodadas congeladas.

## Verificação final e recursos

Seis gates Python do ciclo3: PASS,243fontes/317arquivos tipados, zero violações arquiteturais/ciclos/dependências não utilizadas. Django check e build: exit0. Fontes/testes/scripts/lock/Compose congelados no manifesto [cycle3-before](evidence/final-source-cycle-3-before.json):386arquivos, SHA256 `24a9461bf078495f0150612955a1bd880721e9d6b2ce91ca06ff23b4e245970e`. Suíte integral: **386 passed in 1161.81s (0:19:21), exit0**. [Manifesto posterior](evidence/final-source-cycle-3-after-suite.json) idêntico ao anterior; nenhuma fonte/teste mudou durante a suíte. [Avaliação canônica](eval-report-2026-11-12T04-34-29Z.md): clean, 21 PASS, 10 ACs verificados. Harness4testes e checker estrutural também exit0; git diff --check0.

Instância A `eval_wave11_f19`, portas15351/15451/15551/15651; segredos novos somente `.runtime/f19.env` privado. Ambientes auxiliares C/C2/D/D2 e B de coexistência limpos pelos scripts próprios. Prova final A/B PASS em evidence/isolation-restart.json: snapshots não vazios, pesos/resultados preservados em A, B intacto e cleanup0; interrupção usa segunda posse controlada sem HTTP, sem alegar chamada GPU física interrompida. UI final14PASS/0FAIL, desktop1440/mobile360 sem overflow, teclado, pausa/retomada e residência conferidos; avaliação visual7,67/10 em ui-evaluation.md. Nenhum WhatsApp real, perfil Facebook, processo/volume de outra worktree ou programa alheio foi usado/encerrado. Nenhum novo commit, push, PR, merge ou deploy foi realizado.

Encerramento final: browser fechado; normalstopA exit0, processos/contêineres parados, reserva própria de GPU liberada e três volumes preservados. [Estado final](evidence/final-runtime.json). Quatro laboratórios históricos próprios também foram limpos com ownership verificado, sem afetar a suíte corrente: [cleanup](evidence/historical-cleanup.json). Para reabrir o laboratório preservado, use o arquivo privado já existente com `GARIMPEI_ENV_FILE="$PWD/.runtime/f19.env" ./scripts/init.sh --disposable`; não imprima suas credenciais.
