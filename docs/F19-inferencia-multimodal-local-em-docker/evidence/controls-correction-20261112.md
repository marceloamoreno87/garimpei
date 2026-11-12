# F19 — confirmação dos controles após correção agrupada

**Resultado do subconjunto: 20 PASS · 0 FAIL.** A execução anterior `controls-20261112.*` permanece preservada com seu FAIL histórico. Este relatório não declara `clean` global nem altera progresso.

## Ambiente e fronteiras

Instância exclusiva **C2: `eval_wave11_f19_controls_fix2`**, banco/portas/segredos próprios, `GARIMPEI_AI_SERVICE_ENABLED=false`. Nenhum recurso de A/B/D, GPU ou modelo Ollama foi usado, iniciado ou encerrado. Foi executado apenas o script privado `.runtime/f19-controls-correction-20261112.py`, derivado do roteiro anterior sem editar fontes, testes, lock, Compose ou requisitos.

Comando: `PYTHONDONTWRITEBYTECODE=1 apps/backend/.venv/bin/python .runtime/f19-controls-correction-20261112.py`.

- `./scripts/init.sh --disposable`: exit 0; `/health/ready` 200; manifesto C2 confirmado sem contêiner de inferência.
- `manage.py shell` executando o roteiro: exit 0. Somente o worker C2 ficou pausado em ponto sem transação para asserções determinísticas.
- Worker C2 retomado; `./scripts/stop.sh --clean`: exit 0. Apenas recursos marcados C2 foram limpos.
- Logs integrais e segredos permanecem privados em `.runtime/f19-controls-correction-private/`.

## Resultados

| Caso | Resultado | Itens alcançados |
|---|---|---|
| owned-init | PASS | prerequisite |
| persistent-failure-service_unavailable | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| persistent-failure-model_missing | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| persistent-failure-model_corrupt | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| persistent-failure-gpu_unavailable | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| persistent-failure-gpu_degraded | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| persistent-failure-out_of_memory | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| persistent-failure-timeout | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| persistent-failure-execution_unknown | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| persistent-failure-invalid_output | PASS | WRK-FALHAS-01, WRK-VALIDACAO-01 |
| schema-invalid-results-persist-and-no-business-effects | PASS | WRK-VALIDACAO-01 |
| hostile-material-is-data-in-service-pipeline | PASS | WRK-VALIDACAO-02 |
| service-invalidation-and-compatible-cache | PASS | SVC-ANALISE-01, SVC-ANALISE-02, WRK-RETOMADA-02 |
| queue-100-concurrent-admissions | PASS | WRK-LIMITES-01 |
| input-image-context-and-concurrent-disk-boundaries | PASS | SVC-COBERTURA-01, WRK-LIMITES-01 |
| output-context-and-cpu-fallback-envelope-boundaries | PASS | WRK-LIMITES-01, WRK-FALHAS-01, WRK-VALIDACAO-01 |
| unprobed-service-must-not-be-announced-responding | PASS | UI-OPERACAO-01, WRK-FALHAS-01-diagnostic-subset |
| business-control-invariants-final | PASS | WRK-VALIDACAO-01, WRK-VALIDACAO-02, E2E-ISOLAMENTO-01-subset |
| inner-process | PASS | execution |
| owned-cleanup | PASS | prerequisite |

## Correção confirmada

A sondagem `unprobed-service-must-not-be-announced-responding`, com guard local ausente, lock privado completo e `_request` monitorado, retornou `service=false`, `resident=false`, `reason=gpu_unavailable`, `artifact=""` e **zero chamadas HTTP**. A falha observável da rodada original foi resolvida neste cenário.

## Alcance das verificações

Nove causas controladas atravessaram `RunAnalysisUseCase`/`authorize` e o repositório PostgreSQL real. Falhas recuperáveis respeitaram o teto de três tentativas e recuos de 15/30 segundos. Execução incerta manteve o bloqueio até confirmação de encerramento no cenário controlado. Payload anterior, classificação manual, decisão financeira persistida, intenção autorizada e recibo confirmado permaneceram iguais.

As 120 admissões concorrentes por oito clientes produziram exatamente 100 pendentes e 20 recusas `queue_full`. Foram repetidas as fronteiras de 4/5 imagens, 16 KiB de texto, 2.048 tokens com tokenizer oficial verificado, 10 MiB e 20 MP por imagem, derivados até 512 px sem ampliar, saída 512/contexto 4.096, detecção de offload parcial por registro controlado e quota concorrente.

Cache idêntico reutilizou a requisição; texto, revisão/hash de imagem, artefato e observação/revisão diferentes não reutilizaram resultado incompatível. Prompt/schema não aprovados foram recusados. Saídas com dinheiro/comandos/referência ausente/JSON incompleto falharam sem mudança nos registros de negócio sintéticos.

## Integridade e limites

Hashes de **363 arquivos selecionados** de fonte/testes/quality/scripts, pyproject, uv.lock, Compose e model-lock foram iguais antes/depois. Essa seleção não é apresentada como o manifesto completo de congelamento do coordenador; os manifestos de comparação descrevem exatamente os caminhos conferidos. Nenhuma divergência concorrente foi observada nesse recorte.

Falhas de OOM/GPU/modelo usam fakes nomeados explícitos; não houve OOM físico, inferência, download de pesos ou diagnóstico de GPU real. A foto hostil é uma referência sintética nomeada no pipeline controlado; não foi medida sua interpretação por um modelo. O tokenizer oficial foi baixado somente em diretório privado C2 e seu SHA-256 conferido. Os controles de negócio não substituem a prova real A/B de parada/retomada. Pins/CLI e avaliação global pertencem às evidências dos outros executores.

## Evidências

- [Resultados completos por caso](controls-correction-20261112.json).
- [Hashes antes](controls-correction-20261112-source-before.json).
- [Hashes depois](controls-correction-20261112-source-after.json).
- [Rodada original preservada](controls-20261112.md).
