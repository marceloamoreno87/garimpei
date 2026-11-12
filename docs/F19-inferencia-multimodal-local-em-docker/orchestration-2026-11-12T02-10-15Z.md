# Orchestration Journal — F19 Inferência multimodal local em Docker

**Run:** `2026-11-12T02-10-15Z`
**Feature folder:** `docs/F19-inferencia-multimodal-local-em-docker`
**Branch:** `feat/F19-inferencia-multimodal-local`
**Started at:** `2026-11-12T02:10:15.593964+00:00`
**Retry budget:** 3
**Status:** `success`
**Finished at:** `2026-11-12T04:35:31.563965+00:00`

## Scope

Implementação, avaliação e correção locais na worktree própria. Sem novos commits, merge, push, PR, deploy ou mensagem real. F20 executa em outra worktree. Preparação de imagem/pesos oficiais explicitamente incluída. Provas externas ausentes permanecem pendentes.

## Cycle Log

| # | Kind | Status | Counts / Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | prepared | implementação, preparo oficial e incrementos TDD | impl-report.md |
| 1 | evaluator | fail (gate suíte) | 11 FAIL / 342 PASS / 1 ERROR; 21 BLOCKED | eval-report-2026-11-12T03-53-53Z.md |
| 2 | fix-runner + evaluator | interrupted | 26 PASS; UI-OPERACAO-01 FAIL, 20 BLOCKED; fontes preservadas | eval-report-2026-11-12T04-12-39Z.md |
| 3 | fix-runner + evaluator | clean | 386 testes PASS; 21 itens PASS; 10 ACs verificados | eval-report-2026-11-12T04-34-29Z.md |

## Cycle Detail

### Cycle 0

Leitura de fontes canônicas e preparação do ambiente isolado `eval_wave11_f19`. Lock exclusivo em `.runtime/F19-orchestration.lock`.

## Marco — regras, artefatos e persistência

- Baseline `./scripts/init.sh --disposable`: exit 0, eval_wave11_f19, web 15351; parada normal posterior exit 0, dados preservados.
- Baseline `node scripts/run-gates.mjs`: seis grupos Python PASS, exit 0 (antes da implementação).
- RED: `pytest tests/unit/test_inference_policy.py`: exit 2, módulos da feature ausentes.
- GREEN após incremento de domínio: mesmo comando, 6 testes PASS, exit 0. Regressões cobrem assinatura/revisão/modelo, referência textual/visual e rejeição de comandos/valor monetário fora do schema.
- Metadados oficiais resolvidos: imagem Ollama 0.40.16 com digest completo; manifesto Qwen3.5 4B Q4_K_M e blobs completos; tokenizer Qwen/Qwen3.5-4B com revisão e SHA-256. `model-lock.json` ainda distingue runtime_verified=false e visual_context_verified=false.
- `docker pull` da imagem fixada: exit 0. Nenhum peso ou inferência real confirmado até este marco.
- Introduzidas portas/casos de uso, modelos de controle/requisição/parte, admissão serializada, generation/revisão na publicação, checkpoint e reserva GPU por proprietário. Implementação ainda em construção, não avaliada.
- Extensões de lifecycle/worker/HTTP próprias entregues para validação inicial. Controles incluem revisão/CSRF e erros centralizados.
- Tentativa de `makemigrations --settings` sem DJANGO_SETTINGS_MODULE prévio: exit 1 pelo guard de segredos de manage.py; corrigir invocação usando configuração de teste no ambiente. Não é prova de migration aplicada.
- Próximo marco: migration, testes de persistência/posse/gateway e validação de gates; depois preparo de pesos/GPU e jornadas. Foto real autorizada ainda ausente, itens reais permanecem pendentes.

## Marco — preparo real, revisão e testes (02:36 UTC)

- Foto pública autorizada pelo usuário via coordenador: PlayStation 5 and DualSense, Osh33m, CC-BY-SA-4.0, Wikimedia oldid1216350292. Manifesto privado recebido em /tmp/garimpei-f19-public-photo-8ne5lm97/manifest.json; SHA256 08905d5f2bbb73fd08c4f1e21463052d9c2f7d260d083eb2114a47247a2943db. Ausência de foto deixou de ser pendência; original será preservado.
- Pesos Qwen3.5 baixados no volume próprio, tokenizer oficial privado materializado e hashes dos blobs conferidos por `local_ai prepare --download`: exit 0 após adaptação do transporte. Pin não equivale a inferência verificada.
- Docker Desktop não permite alcançar a porta publicada quando somente a rede internal=true permanece conectada; prova real guardada nos diagnósticos privados. Transporte REST local adaptado por docker exec/bash /dev/tcp em contêiner de propriedade verificada; script estático, payload via stdin. Nenhum mount de sessão/segredo e rede externa somente no preparo explícito, desconectada ao concluir.
- Revisão independente encontrou seis falhas concretas: recuperação fora da seleção due; parte incerta tornada terminal cedo; perda de conexão pós-envio classificada como retry seguro; métricas inválidas escapando como ValueError; prazo HTTP direto apenas por inatividade; novo transporte Docker com framing truncado e orçamento de ownership fora do prazo. As primeiras cinco estão corrigidas em código; framing/ownership do transporte Docker em correção neste marco.
- RED do transporte interrompido observado (service_unavailable incorreto). RED de métricas inválidas observado (ValueError). GREEN da suíte focada principal: 12 PASS, exit 0; inclui drip com deadline real.
- RED dos testes novos Docker: três corpos HTTP truncados falham conforme esperado (inclui corpo {} aceito indevidamente), um caso de JSON inválido completo passa. Ainda não GREEN neste marco.
- Migration 0013_local_inference gerada, aplicada no ambiente próprio pelo init; novo init/stop exit 0.
- Gates de incremento: tipos/lint/limites/arquitetura/ciclos passaram no último percurso, mas gate não utilizados falhou em oito símbolos novos. Arquitetura isolada confirmou zero violações. Nenhuma aprovação final declarada.
- Primeiro smoke real de texto: exit 1, request persistida failed/service_unavailable; GPU ainda sem inferência comprovada. Há custo elevado de comandos Docker no host (~6 s para diagnóstico) a confrontar com prazo contratual de 3 s.
- Primeira suíte PostgreSQL de F19: setup falhou em uma instância de avaliação por worker/readiness; investigando concorrência de dois consumidores Procrastinate no mesmo processo e adequação das observações sintéticas. Ainda não é evidência de regressões de persistência aprovadas.
- Pendências atuais: corrigir transportes/worker/preparo sintético; estabilizar integração e seis gates; provas GPU texto/imagem, foto autorizada, idle de 300 s, coexistência/isolamento, navegador e relatórios. Não há bloqueio por foto ou download dos pesos.

## Marco — retomada PostgreSQL e transporte persistente

- Consumidor Procrastinate unificado em um único call_command com fila inference e >=4 slots. Revisão independente confirmou disputa global replace_connector como causa da falha anterior. Novo init/readiness próprio: exit 0. Suíte PostgreSQL F19: 3 PASS em 13,85 s, exit 0; cobre prova de encerramento antes de recovery, prazo due, três tentativas, geração, admissão concorrente, publicação idempotente, CSRF/409/503 e gravação não confirmada.
- Suíte unitária de domínio/gateway/framing Docker: 16 PASS, exit 0 (02:41 UTC). Framing truncado agora usa leitura completa conforme Content-Length/chunking e mantém execução incerta; timeout inclui ownership e transporte.
- Docker exec mostrou custo constante ~3,07 s até para `true`, fora do teto de diagnóstico de 3 s. Não houve aumento do teto. Transporte está sendo adaptado para um único canal persistente por run com script bash estático e frames REST em stdin/stdout; aquecimento explícito não despacha análise. Referência imutável do contêiner é verificada no lifecycle e preservada no manifest por run para evitar ps/inspect em cada chamada.
- Smoke Unicode adicional: falhou explicitamente service_unavailable antes de inferência pelo custo do transporte antigo. Requisição e motivos preservados; nenhum resultado confirmado/GPU reivindicado.
- Modelos, pesos e tokenizer continuam íntegros no volume/diretório próprios. Foto autorizada está recebida conforme marco anterior. Próximos passos: estabilizar canal aquecido, smoke integrado, perfil visual medido, provas de residência/idle/GPU e contratos restantes. Verificação final ainda não realizada.

## Marco — inferência real e fechamento do núcleo

- `local_ai prepare --download` com calibração visual: exit 0. Saída estruturada real com image-a válida e contexto428/saída141 tokens, 10,844 s; 39 amostras durante a chamada, pico host6340 MiB/73% de utilização, modelo residente3140495604 bytes/contexto4096. Não são metas de latência.
- Texto com referências enum anotadas pela aplicação: probe real validou AnalysisResult, sem aceitar os offsets incorretos observados antes. Schema posterior continua conferindo quote/offset/imagem.
- Smoke persistente texto via worker: succeeded, chamada fria3,531 s, carga2,414 s, 13 amostras durante chamada com pico host6274 MiB/67%. Modelo/contexto/prompt/schema e material efetivamente examinado preservados.
- Smoke persistente da foto pública autorizada: succeeded, chamada1,802 s, carga4,465 ms, 7 amostras com pico host6324 MiB/72%. SHA fonte08905d5f...a2943db; derivado2a7f38a5...b3ce2a5e. Sem imagem bruta/payload privado em evidência pública.
- Playwright abriu tela real, observou análise ativa e confirmou pausa via botão. Screenshots desktop/mobile produzidos e examinados; acompanhamento conservou resultado anterior e controle de retomada. Essa pausa descarregou o modelo, portanto NÃO constitui prova de idle300s.
- Corrigido diagnóstico residual após retry: publicação limpa part.reason; regressão PG adicionada. Cobertura sent distingue preparação de resposta recebida; exame só é confirmado após validação.
- Revisão final do canal encontrou contaminação de próxima chamada após framing inválido: RED observado com duas chamadas e frame remanescente; código agora aborta canal e mantém execução incerta. Teste garante que a segunda chamada não consome resposta antiga.
- Nova proteção de autorização antes do envio respeita pausa confirmada após claim. Regressão de pausa durante chamada usa caso de uso com repositório PostgreSQL: conclui só a parte em curso, mantém seguinte pendente e exige retomada.
- Orçamento total de inferência/diagnóstico é compartilhado entre operações; caches ignoram métricas não semânticas, preservando reaproveitamento após novo diagnóstico. Quota inclui reserva conservadora de2 MiB por assinatura para resultados PostgreSQL, além dos arquivos privados; sem apagar resultados confirmados.
- Seis gates passaram em increment-gates-9.log antes dos ajustes finais. Pré-freeze encontrou colisão de nome do timer (mypy) e argumento de fake de teste; ambos corrigidos, rodada pré-freeze final em andamento. Próxima etapa congela hashes de código/testes/lock/Compose e executa suíte ampla sem editar fontes.
- Idle300s, recarga e prova integrada de coexistência/isolamento continuam em verificação; não há sucesso final declarado.

## Rodada congelada — 03:13 UTC

- Pré-freeze: 26 testes focados PASS17,21s; seis grupos Python PASS. Corrigidos todos os findings recebidos, com regressão específica de framing/duas chamadas e retry sem motivo residual.
- Fontes, testes, lock, scripts e Compose congelados: SHA256 f290cc11f4c429d40a0cb8c7766479121b2e29ac2e236867aea9260858684aa4, 384 arquivos. Manifesto before em evidence/final-source-before.json. Nenhuma fonte/teste será alterada durante a suíte ampla; alterações documentais/evidências ficam fora desse recorte.
- Init final: exit0, eval_wave11_f19, web15351, run56e042f6-7fcb-4702-97b1-b446625eb319. Django check final: exit0, zero problemas. Suíte ampla, gates finais e build iniciados.
- Playwright reabriu a UI final a360px, confirmou persistência da pausa através do reinício, ausência de console errors e modelo não residente confirmado. Retomada explícita iniciada para ensaio image-b/idle300s.

## Ciclo de correção agrupado 2 — 2026-11-12T03:53:53.445771+00:00

**evaluator:** fail(gate suíte), relatório `eval-report-2026-11-12T03-53-53Z.md`; 21 BLOCKED,10AC indeterminados. Fontes before/after inalteradas:3a7119de...db488. Resultado amplo11FAIL/342PASS/1ERROR em1113,28s. Os relatórios de tentativas anteriores são QA incremental e não foram falsamente apresentados como avaliações canônicas limpas.

**Causas comprovadas antes de editar:** shutdown/cleanup importa main com registry ausente; tarefas AI vazias a cada5s; fixtureF19 compartilha listings com fundação, gerando valuations; diagnose anuncia serviço sem sondagem; seis pins inválidos passam e CLI usa64 em vez2/1. Histórico e contratos preservados.

**Plano fix-runner:** separar composição da parada de main/ORM sem enfraquecer ownership; enfileirar AI só com pendência e isolar cada teste F19 em DB próprio; confirmar serviço antes de bool positivo; validar lock completo com controle positivo e códigos0/2/1. Worker F20 autorizado é dono somente artifact_policy/local_ai/teste pins/factoryInference; este agente mantém wiring/gateway/runtime/repo/progresso e relatórios. Não há writers concorrentes nos mesmos arquivos.

**Provas complementares desde03:13:** idle confirmado309,87s desde uso (checked_at~305s), residentefalse/idle_unloaded,VRAM6326→2439MiB ehealth200; recarga pós-idle4,061s/carga2,229s,RAMcontêiner até881,4MiB observados, appRSS213MiBbytes ehostRAM16970485760bytes, sem novo /pull e snapshots de negócio inalterados; coexistênciaPASS27,86s/coleta27→64/fakeWAHA3/HTTP200; matriz C19PASS1FAIL; pins D6falsosready; texto hostil real succeeded e bitmap hostil em nova revisão succeeded com2partes, sem alteração de negócios.

**Estado:** corrigindo; sem conclusão de feature ou publicação. Fontes só serão congeladas de novo após regressões focadas e alinhamento dos escritores.

## Marco — correções agrupadas e regressões do ciclo 2

- Shutdown retirou importação de main/ORM da liberação de reserva de GPU; repetição da parada e rollback parcial funcionam sem registry Django. Quatro regressões críticas (parada/reinício, partial_start, isolamento de monitoring e diagnóstico sem HTTP) PASS29,16s, exit0, `.runtime/cycle-2-regression.log`.
- Reconciliador enfileira análise apenas se há requisição elegível; testes F19 usam instância/banco por teste, preservando o contrato original de F03. Diagnóstico só anuncia serviço após uma sondagem HTTP bem-sucedida.
- Helper estrito de artefatos integra `read_lock`: ausência/incompletude/divergência distintas; SHA do tokenizer comparado ao aprovado, além de imagem/plataforma/tag/manifesto/blobs/revisões. CLI usa0/2/1 e imprime apenas resumo sanitizado no smoke. Testes de entrada usam explicitamente tokenizer/lock fake nomeado; integridade de produção permanece estrita.
- Focados integrados:58PASS42,80s, exit0, `.runtime/cycle-2-focused.log`. Matriz independente D2:15/15PASS, controle positivo0 e negativos rejeitados, prepare sem download2; fontes estáveis, nenhum chat/pull/GPU/download. Evidências `evidence/pins-correction-report.md` e `evidence/pins-tokenizer-report.md`, com RED histórico preservado.
- Pré-freeze detectou três tipos ausentes somente no novo teste de artefatos; corrigidos pelo seu proprietário e rechecados. Seis gates em execução antes do congelamento. Matriz C2 independente em instância própria sem GPU; prova A/B de pesos/resultados/recibos/parada normal sendo preparada em script privado, sem alterações de fontes durante a futura suíte ampla.

## Rodada final do ciclo 2 — fontes congeladas

- Seis gates PASS,243fontes/317arquivos tipados; Django check0 e build0. Manifesto `evidence/final-source-cycle-2-before.json`,386arquivos, SHA256 `2d242aa0272fc19b06372ac25449102f0d1548da50eb553dcdbe07237edc9693`. Snapshot viauv foi coletado segundos após começar pytest porque `python` simples não existe no PATH; não houve edição de fontes/testes nesse intervalo.
- Suíte ampla em `.runtime/final-suite-cycle-2.log`, ambiente Django explícito; fontes/testes permanecem congelados. Somente relatórios e scripts privados de avaliação continuam sendo escritos.
- C2 independente repetiu matriz inteira:20PASS/0FAIL, diagnóstico semsondagem agora serviceFalse/0HTTP, cleanup0 e363arquivos selecionados idênticos. D2 e SHA tokenizer concluídos conforme artefatos próprios. Histórico falho preservado.
- Impl-report inicial publicado, ainda marcado pendente de avaliação final. Prova A/B em andamento: B com pesos públicos completos em serviço parado, resultado controlado e dados não vazios; A com primeira parte real confirmada e segunda posse em curso simulada explicitamente semHTTP, permitindo interrupção/recovery determinístico sem fingir uma chamada GPU interrompida. Duas tentativas anteriores do script falharam na preparação (destino docker cp e namespace smoke); B foi limpo exit0 e fontes não foram alteradas.

## Ciclo dirigido 3 — projeção de execução incerta na UI

- Prova A/B concluídaPASS: `evidence/isolation-restart.json`. Baselines não vazios de condição/composição/recibos, resultados e pesos completos próprios nos dois ambientes; A conserva parte real confirmada e recupera segunda posse controlada após normalstop/restart; B conserva run/processos/saúde200/pesos/resultados e cleanup0. Probe foto pública nova revisão+RAMPASS, sem pull nem efeito de negócio, `authorized-photo-ram.json`.
- UI real1440/360 semoverflow(360=scrollWidth), botão100,9×44,4px, fontes carregadas e console0. Teclado skip→conteúdo→Pausar/Enter confirmou pausa; UI manteve residente antes do unload e somente depois confirmou não residente.
- Probe de causas persistidas:8PASS/1FAIL. `execution_unknown` com active_request preservada era sobreposto por running. Evidência histórica `ui-causes.json` e screenshot `ui-cause-execution_unknown.png`. Nenhuma falha físicaGPU foi simulada como real.
- Coordenador autorizou interromper somente pytest próprio para corrigir antes de repetir18min: SIGINT noPID1337936, teardown concluído,26PASS395,06s/exit2. Fonte386/SHA2d242aa before/after-interrupt idêntica. Avaliação `eval-report-2026-11-12T04-12-39Z.md`:1FAIL/20BLOCKED,AC07FAIL e9indeterminados. ProgressoF19cycles3; nenhuma conclusão declarada.
- TDD: regressão HTTP+repo PostgreSQL real falhou1/6,61s pelo título incorreto. Correção consulta projeta timeout factual quando controleincerto; handler prioriza causa e mantém encerramento/residência não confirmados, inclusive pausa com execução incerta. Somente query/handler/template/teste mudaram; posse/gateway permanecem estáveis. GREEN e reinícioA/probevisual ampliado em andamento antes do próximo freeze.

## Freeze final ciclo 3 — 04:15 UTC

- Regressores: RED1FAIL6,61s→GREEN1PASS6,88s; consulta distingue timeout factual preservando controle de posse incerta. Seis gatesPASS; Django/buildexit0. Correção somente query/handler/template/teste, sem alterar gateway/posse/retries.
- Probes reais de UI:14PASS/0FAIL, `ui-causes-correction.json`, quatro screenshots de causas inspecionadas; viewport360/scroll360, botão44,39px, foco solid/skiplink econsole0. Pausa/resume via teclado/navegador confirmados, persistência de pausa no restart e unload observados. `ui-evaluation.md`:8/7/8/8, média7,67, sem dimensão≤3.
- Fonte novamente congelada386arquivos, SHA256 `24a9461bf078495f0150612955a1bd880721e9d6b2ce91ca06ff23b4e245970e`, before salvo. Suíte integral ativa em `.runtime/final-suite-cycle-3.log`; nenhuma alteração de fonte/teste depois do freeze. Relatórios/scripts privados continuam.
- Auditoria independente readonly de suficiência confirmou mapa dos21itens coberto, sem novo impedimento concreto além de suíte/gates/hashes finais; não constitui clean por si só.
- `real-inference-summary.json` consolida3smokes reais sem findings textuais. Foto pública nova revisãoPASS1,501s/carga3,895ms, RAMcontêiner1023MiB; textoUnicodefrioPASS3,229s/carga2,128s,RAM722,4MiB. Ambos tiveram snapshots não vazios de negócio iguais e nenhum novo pull. Evidências authorized-photo-ram/cold-text-ram.

## Encerramento do laboratório e espera do gate integral

- Suíte3 continua ativa sem edição de fontes/testes. CLI atual status0 e smokeimage-b0/reusedtrue em `evidence/final-cli.json`; harness4testesPASS e checkerestrutural0.
- Browser garimpei-f19 fechado. NormalstopA exit0 em04:23:19Z, manifeststopped, processos/contêineres próprios parados e3volumes preservados; reservaGPU própria liberada. `evidence/final-runtime.json`. Não foi usado --cleanA; DB/pesos/resultados continuam para revisão/reprodução.
- Quatro ambientes descartáveis históricos desta própria worktree, sobreviventes dos erros antigos, foram identificados por manifest/checkout/disposable/synthetic e limpos com stop--cleanexit0: test_69e3be10_a/b, test_3f2d14d5_b e partial_a5cc6094b6. `evidence/historical-cleanup.json`. Fixtures da suíte corrente e outros checkouts preservados.
- Nenhum item pendente externo identificado pelo auditor; relatório final ainda aguarda exit0 da suíte e hashdepois correspondente. Não há conclusão clean/done antecipada.

## Veredito canônico final — 2026-11-12T04:35:31.563965+00:00

- **success / clean**. Relatório [eval-report-2026-11-12T04-34-29Z.md](eval-report-2026-11-12T04-34-29Z.md):21PASS,0FAIL/BLOCKED/MANUAL/SKIPPED;10ACs verificados.
- Suíte integral386PASS1161,81s/exit0; seis grupos PythonPASS; Django0; build0; harness4testes0/checker0; gitdiff--check0. Saídas preservadas em .runtime/cycle-3-gates.log, final-suite-cycle-3.log, cycle-3-django.log, cycle-3-build.log e final-harness*.log.
- Fonte386arquivos SHA24a9461bf078495f0150612955a1bd880721e9d6b2ce91ca06ff23b4e245970e before/after idêntica. Provas GPU reais,14variantesUI,20controlesC2 e15pinsD2, idle300, recarga/RAM e isolamento A/B permanecem referenciadas por item.
- Dados/pesos/resultados deA preservados com processos/contêineres parados e reservaGPU liberada; auxiliares limpos somente com ownership próprio. Limitações explícitas: fakes para falhas físicas, máximos amostrados e interrupção de segunda posse controlada semHTTP; não são pendências contratuais.
- Nenhum novo commit/push/PR/merge/deploy/mensagem real. Integração futura com migration0013_alert_message_snapshot deF20 requer união de pontas0012; não executada neste escopo.

- Lock exclusivo desta execução liberado após verificar PID/host/branch/cwd/início e terminar seu holder; `evidence/feature-lock-release.json`. Logs finais sanitizados copiados para evidence/cycle-3-gates.txt e evidence/final-suite-cycle-3.txt; referências canônicas independem de runtime privado.
