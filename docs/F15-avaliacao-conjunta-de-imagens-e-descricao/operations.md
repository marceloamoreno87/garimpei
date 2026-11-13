# F15 — Operação controlada e adoção

F15 é opt-in: `GARIMPEI_ASSESSMENT_ENABLED=false` por padrão. A ativação usa configuração central e migrations aditivas; não reescreve recibos, corpos enviados ou decisões terminais. A condição manual continua na fronteira F05, com revisão otimista e CSRF. Escolha manual boa não transforma análise ausente/parcial em suficiente.

O reconciliador separado prepara/conclui até 10 ofertas a cada rodada de 5 segundos. A execução de inferência permanece na fila/capacidade `inference` de F19. Cada requisição admite até quatro fotos; galerias maiores usam uma coorte por avaliação, com geração monotônica, sem invalidar lotes irmãos nem o perfil legado. O perfil atual é `condition-evidence-v3`; política `condition-policy-v1`. Prompt/schema e revisão exata do modelo participam da identidade. F19 mantém concorrência, contexto, fila, timeout e tentativas limitados; nenhuma rota HTML chama inferência síncrona.

O usuário aprovou saída até1024 tokens exclusivamente para F15. O legado `local-evidence-v1` permanece até512; ambos usam contexto total4096. Os limites finitos por perfil ficam em `domain/inference/profile_limits.py`; `InferenceSettings.output_tokens` continua representando o teto legado. O gateway e a assinatura usam `output_token_limit(profile)`. Não elevar o campo global nem alterar modelo/pins para essa adoção.

Para F15 multimodal, a reserva visual1536 é preservada e sobram até1536 tokens textuais incluindo prompt/schema/margem256, mais1024 de saída. O preparador recusa contexto que não cabe; o envelope verifica contagem real+reserva≤4096. A auditoria offline de23textos com identidade vazia tem máximo1506; identidade/contexto reais precisam passar novamente. Perfis v1/v2 históricos são recusados para nova execução e não reutilizados como análise aplicável v3; corpos/resultados históricos permanecem identificados. Recalibração e prova GPU da nova reserva são exigidas antes de concluir a avaliação.

Originais F14 permanecem intactos e protegidos por pins versionados. JPEG/PNG/WebP estáticos são convertidos pelo adaptador F15 em PNG independente de até 512 px; EXIF é aplicado e transparência recebe fundo branco. Hash do original e identidade de cada foto permanecem nas referências. O derivado usa a quota/registro F19 existente; temporários saem de diretório privado. Duplicatas por hash usam a mesma inferência. Fotos omitidas mantêm motivo e impedem promoção automática a boa.

Para laboratório descartável, na raiz desta worktree:

```sh
uv run --directory apps/backend --frozen --no-sync python -m tests.factories.assessment_lab
```

O processo cria configuração privada, banco/portas/mídia próprios, executa `init.sh`, pausa seu worker e imprime manifesto sanitizado. Recebe JSON por stdin: `status`, `prepare_case` (ID do corpus), `collect`, `complete`, `change_input`, `fail`, `clear_fault`, `restart`, `quit`. `status` permite conferir observação, geração, avaliação, requisições, chamadas fake e transmissões. `quit` fecha fonte/temporários e executa `stop.sh --clean` somente na instância pertencente ao laboratório. Os fakes são nomeados e o resultado aparece explicitamente como controlado na interface.

O laboratório não muda política/modelo por string arbitrária nem modifica o lock aprovado. A implementação calcula fingerprint de política/prompt/schema/modelo; `tests/integration/test_assessment_boundaries.py` verifica migração de quatro metadados legados sintéticos persistidos para o perfil atual aprovado, com nova geração/requisição, histórico intacto e abstenção imediata. É prova controlada de versionamento; não é troca física de pesos. O contrato aprovado em9ce6a75 exige inferência real/GPU e comparação com referência assistida por IA explicitamente atribuída em E2E-QUALIDADE-01. O laboratório bloqueia execução real antes da validação da referência congelada, origem/método e ambiente próprio.

Adoção controlada verificou que recibo confirmado, transmissão incerta e exclusão terminal anteriores mantêm corpo/ID/estado/tentativa. A ativação sem avaliação concluída conserva a assinatura pré-F15. Nova análise suficiente pode reavaliar apenas decisões pendentes pelo fluxo existente. O financeiro continua em F06/F07/F20, sem preço sugerido pela IA. Nenhum envio WhatsApp real integra a validação.


## Regressões de fronteira da retomada

Execute com `TMPDIR` em disco, fora do tmpfs. O comando normal usa transporte controlado e controla apenas a contagem de tokens, mantendo registro/hash/derivação, gateway, schema, persistência e publicação reais:

```sh
uv run --directory apps/backend --frozen --no-sync pytest tests/integration/test_assessment_boundaries.py -v -s
```

Se `GARIMPEI_TEST_APPROVED_TOKENIZER` apontar para tokenizer oficial já disponível, a mesma regressão verifica SHA256 e orçamento de contexto reais; nenhum download é feito pelo teste. A evidência desta retomada registra `real_tokenizer=True`. A reserva de GPU do teste é privada e simulada, e o transporte retorna respostas hostis controladas. Imagem com instruções foi criada exclusivamente para a regressão, sem tocar o corpus reservado. O runtime/modelo real não foi exercitado.


## Receber revisão e executar qualidade real

A página offline exporta `schema_version`, `rubric`, `manifest_sha256` e os23 casos com reference_method explícito. Export parcial é salvo para continuidade, mas o executor retorna BLOCKED antes de consultar runtime. Rascunho do formulário é um envelope separado, não uma revisão final. Referência produzida por IA declara autoria e reference_method=ai_assisted; o agente não se apresenta como humano. O formulário pode ser reconstruído com `python3 docs/F15-avaliacao-conjunta-de-imagens-e-descricao/build-review-ui.py /caminho/do/pacote`; a saída é impedida de ficar no repositório. Template e fontes de UI não incluem cópias das fotos reais.

Primeiro validar, sem GPU/serviços:

```sh
uv run --directory apps/backend --frozen --no-sync python -m tests.factories.assessment_quality \
  --manifest /caminho/do/pacote/manifest.json \
  --review /caminho/revisoes-finais.json --package /caminho/do/pacote --mode validate
```

Somente após referência atribuída, congelada e validada, com splits fechados, selecionar runtime F19 próprio já preparado, `GARIMPEI_ENV=eval`, descartável e alertas desativados. O coordenador preservou pesos/banco na cópia `/home/marce/.cache/garimpei-evaluations/f15-next-wave/gpu-preparation/checkout` com arquivo privado irmão `f15_gpu_20261113.env`; essa prontidão não executou o reservado. Antes de usar a cópia, sincronizar apenas fontes/testes/docs finais auditados e comparar hashes, preservando `.venv`, `.runtime`, env, volumes e lock preparado. Executar o módulo a partir dessa raiz sincronizada, que é a dona do ambiente; o executor não flexibiliza propriedade do checkout.

Preparar F14 no mesmo arquivo privado antes de iniciar o runtime. A execução real de F15 depende tanto da inferência F19 quanto de root/cota de mídia F14 válidos; os segredos já preparados permanecem fora do repositório:

```text
GARIMPEI_ENV=eval
GARIMPEI_AI_SERVICE_ENABLED=true
GARIMPEI_ASSESSMENT_ENABLED=true
GARIMPEI_ALERTS_ENABLED=false
GARIMPEI_MEDIA_ROOT=/diretorio/privado-deste-eval/media
GARIMPEI_MEDIA_BUDGET_BYTES=67108864
```

`GARIMPEI_MEDIA_ROOT` deve ficar fora do checkout e pertencer a esse eval. A cota de64 MiB é a mesma do laboratório controlado; não amplia limites de arquivo/pixels nem substitui espaço livre. Sem cota válida, F14 registra `configuration_required`, conserva a política de proteção e não fornece assets para o modelo. Resultados parciais de condição nesse estado não comprovam inferência. Uma tentativa física desta execução revelou essa pré-condição omitida; o coordenador corrigiu somente root/cota no env privado, sem mudar fonte/pins/limites ou referência. O runner cria sua origem loopback temporária para servir as cópias autorizadas; não usa Facebook nessa avaliação.

Iniciar a instância própria por `scripts/init.sh --disposable` com seu arquivo privado; depois usar o mesmo comando de validação acrescido de `--mode real --runtime-env /arquivo/privado-deste-eval.env --output /diretorio-privado/quality-run-novo.json`. O lab também aceita `{"action":"evaluate_corpus","mode":"real","manifest":"...","review":"...","package":"...","runtime_env":"...","output":"..."}`. Não apontar para ambiente principal. Saída existente ou interna ao checkout é recusada. O driver pausa/resume somente o worker verificado e não gerencia o ciclo de vida do serviço selecionado; encerrar pelo `scripts/stop.sh` desse ambiente ao terminar, preservando pesos conforme a política de retenção autorizada.

O executor usa modelos/pins/DI F19 reais, F14 local e política/publicação F15; não oferece bypass fake. Executa somente reserved, registra arquivo privado de entrada com hashes da revisão/manifesto antes da primeira chamada e relatório incremental. Dados corrigidos exigem novo manifesto revisado. Matriz e erros separam ilustração/real e categoria; RAM host/RSS do avaliador não é anunciada como RAM exclusiva do modelo. O primeiro envio após unload confirmado é identificado; load_duration por chamada permite conferir recargas. Se nenhuma foto real for efetivamente enviada, complete permanece false. Casos sem fotos/textuais usam política determinística sem fabricar medidas de inferência. Falha preserva relatório parcial/filas e diagnóstico privado, sem descarregar recursos de terceiros.


## Método da referência — instrução atual

O usuário autorizou Codex a revisar o pacote com auxílio de IA. A autoria deve ser explícita (`Codex (IA)`) e o export usa `reference_method=ai_assisted`; isso gera concordância entre IAs, sem alegação de revisão humana independente. O método é obrigatório no arquivo e não é inferido por reviewer. O template começa nulo e não pode executar o corpus. Referências declaradas humanas usam `reference_method=human`. O relatório separa esses métodos e usa `reference` por caso; a opção assistida registra `independent_human_review=false` e legacy_human_acceptance_satisfied=false, preservando a verdade histórica. O aceite atual de E2E-QUALIDADE-01/F15-AC05 adota explicitamente essa referência de IA conforme canon 9ce6a75; não exige falsificar o legado ou alegar revisão humana independente. Ver `reference-method.md`. Os exemplos de CLI continuam iguais; método vem do arquivo exportado, nunca de um argumento que substitua sua autoria.


## Leitura do relatório e falhas conhecidas

`complete=true` e CLI exit0 informam que o driver terminou os casos selecionados; não aprovam o contrato, a cobertura de todas as fotos ou a qualidade das predições. Conferir partes enviadas, aceitas, falhas e pendentes separadamente. O relatório real desta rodada enviou13 partes e recebeu13 invalid_output, sem resposta aceita, deixando3 partes do caso real pendentes. A interface/política permaneceu conservadora; isso não demonstra reconhecimento visual suficiente.

A prontidão tolera somente `service_unavailable` durante uma janela limitada de 15 s, com pausas de até200 ms no mesmo gateway. Falhas definitivas de pin/GPU/modelo encerram imediatamente. Serviço e digest exatos, além de unload confirmado, continuam obrigatórios. O orçamento de diagnose individual continua3 s; não existe espera indefinida nem bypass F19. Marcadores privados de execução vinculados a um nonce distinguem zero chamadas comprovado de estado desconhecido.

Os tempos de parede por caso são publicados como tais; o primeiro caso após unload e os posteriores usaram materiais distintos. Falhas guardaram somente sent=true e perderam métricas detalhadas do envelope: não renomear esses tempos como latência fria/quente quantitativamente comprovada. Recursos medidos têm escopo explícito: snapshot hostGPU, offload Ollama e RAM host/RSS do avaliador. E2E permanece pendente até comprovar os observáveis restantes, independentemente de não haver meta numérica de precisão. Uma nova correção/instrumentação e reavaliação exige escopo/orçamento próprio; as três correções desta retomada foram consumidas.
