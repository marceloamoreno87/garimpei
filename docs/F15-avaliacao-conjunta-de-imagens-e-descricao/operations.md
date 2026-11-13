# F15 — Operação controlada e adoção

F15 é opt-in: `GARIMPEI_ASSESSMENT_ENABLED=false` por padrão. A ativação usa configuração central e migrations aditivas; não reescreve recibos, corpos enviados ou decisões terminais. A condição manual continua na fronteira F05, com revisão otimista e CSRF. Escolha manual boa não transforma análise ausente/parcial em suficiente.

O reconciliador separado prepara/conclui até 10 ofertas a cada rodada de 5 segundos. A execução de inferência permanece na fila/capacidade `inference` de F19. Cada requisição admite até quatro fotos; galerias maiores usam uma coorte por avaliação, com geração monotônica, sem invalidar lotes irmãos nem o perfil legado. O perfil é `condition-evidence-v1`; política `condition-policy-v1`. Prompt/schema e revisão exata do modelo participam da identidade. F19 mantém concorrência, contexto, saída, fila, timeout e tentativas limitados; nenhuma rota HTML chama inferência síncrona.

Originais F14 permanecem intactos e protegidos por pins versionados. JPEG/PNG/WebP estáticos são convertidos pelo adaptador F15 em PNG independente de até 512 px; EXIF é aplicado e transparência recebe fundo branco. Hash do original e identidade de cada foto permanecem nas referências. O derivado usa a quota/registro F19 existente; temporários saem de diretório privado. Duplicatas por hash usam a mesma inferência. Fotos omitidas mantêm motivo e impedem promoção automática a boa.

Para laboratório descartável, na raiz desta worktree:

```sh
uv run --directory apps/backend --frozen --no-sync python -m tests.factories.assessment_lab
```

O processo cria configuração privada, banco/portas/mídia próprios, executa `init.sh`, pausa seu worker e imprime manifesto sanitizado. Recebe JSON por stdin: `status`, `prepare_case` (ID do corpus), `collect`, `complete`, `change_input`, `fail`, `clear_fault`, `restart`, `quit`. `status` permite conferir observação, geração, avaliação, requisições, chamadas fake e transmissões. `quit` fecha fonte/temporários e executa `stop.sh --clean` somente na instância pertencente ao laboratório. Os fakes são nomeados e o resultado aparece explicitamente como controlado na interface.

O laboratório não muda política/modelo por string arbitrária nem modifica o lock aprovado. A implementação calcula fingerprint de política/prompt/schema/modelo; `tests/integration/test_assessment_boundaries.py` verifica migração de quatro metadados legados sintéticos persistidos para o perfil atual aprovado, com nova geração/requisição, histórico intacto e abstenção imediata. É prova controlada de versionamento; não é troca física de pesos. O contrato reserva a inferência real/GPU e comparação humana para E2E-QUALIDADE-01. O laboratório mantém o corpus reservado bloqueado antes da revisão humana e coordenação de runtime real.

Adoção controlada verificou que recibo confirmado, transmissão incerta e exclusão terminal anteriores mantêm corpo/ID/estado/tentativa. A ativação sem avaliação concluída conserva a assinatura pré-F15. Nova análise suficiente pode reavaliar apenas decisões pendentes pelo fluxo existente. O financeiro continua em F06/F07/F20, sem preço sugerido pela IA. Nenhum envio WhatsApp real integra a validação.


## Regressões de fronteira da retomada

Execute com `TMPDIR` em disco, fora do tmpfs. O comando normal usa transporte controlado e controla apenas a contagem de tokens, mantendo registro/hash/derivação, gateway, schema, persistência e publicação reais:

```sh
uv run --directory apps/backend --frozen --no-sync pytest tests/integration/test_assessment_boundaries.py -v -s
```

Se `GARIMPEI_TEST_APPROVED_TOKENIZER` apontar para tokenizer oficial já disponível, a mesma regressão verifica SHA256 e orçamento de contexto reais; nenhum download é feito pelo teste. A evidência desta retomada registra `real_tokenizer=True`. A reserva de GPU do teste é privada e simulada, e o transporte retorna respostas hostis controladas. Imagem com instruções foi criada exclusivamente para a regressão, sem tocar o corpus reservado. O runtime/modelo real não foi exercitado.


## Receber revisão e executar qualidade real

A página offline exporta `schema_version`, `rubric`, `manifest_sha256` e os23casos. Export parcial é salvo para continuidade, mas o executor retorna BLOCKED antes de consultar runtime. Rascunho do formulário é um envelope separado, não uma revisão final. Não preencher campos humanos pelo agente. O formulário pode ser reconstruído com `python3 docs/F15-avaliacao-conjunta-de-imagens-e-descricao/build-review-ui.py /caminho/do/pacote`; a saída é impedida de ficar no repositório. Template e fontes de UI não incluem cópias das fotos reais.

Primeiro validar, sem GPU/serviços:

```sh
uv run --directory apps/backend --frozen --no-sync python -m tests.factories.assessment_quality \
  --manifest /caminho/do/pacote/manifest.json \
  --review /caminho/revisoes-finais.json --package /caminho/do/pacote --mode validate
```

Somente após revisão efetiva recebida/validada e splits fechados, selecionar runtime F19 próprio já preparado, `GARIMPEI_ENV=eval`, descartável e alertas desativados. O coordenador preservou pesos/banco na cópia `/home/marce/.cache/garimpei-evaluations/f15-next-wave/gpu-preparation/checkout` com arquivo privado irmão `f15_gpu_20261113.env`; essa prontidão não executou o reservado. Antes de usar a cópia, sincronizar apenas fontes/testes/docs finais auditados e comparar hashes, preservando `.venv`, `.runtime`, env, volumes e lock preparado. Executar o módulo a partir dessa raiz sincronizada, que é a dona do ambiente; o executor não flexibiliza propriedade do checkout.

Iniciar a instância própria por `scripts/init.sh --disposable` com seu arquivo privado; depois usar o mesmo comando de validação acrescido de `--mode real --runtime-env /arquivo/privado-deste-eval.env --output /diretorio-privado/quality-run-novo.json`. O lab também aceita `{"action":"evaluate_corpus","mode":"real","manifest":"...","review":"...","package":"...","runtime_env":"...","output":"..."}`. Não apontar para ambiente principal. Saída existente ou interna ao checkout é recusada. O driver pausa/resume somente o worker verificado e não gerencia o ciclo de vida do serviço selecionado; encerrar pelo `scripts/stop.sh` desse ambiente ao terminar, preservando pesos conforme a política de retenção autorizada.

O executor usa modelos/pins/DI F19 reais, F14 local e política/publicação F15; não oferece bypass fake. Executa somente reserved, registra arquivo privado de entrada com hashes da revisão/manifesto antes da primeira chamada e relatório incremental. Dados corrigidos exigem novo manifesto revisado. Matriz e erros separam ilustração/real e categoria; RAM host/RSS do avaliador não é anunciada como RAM exclusiva do modelo. O primeiro envio após unload confirmado é identificado; load_duration por chamada permite conferir recargas. Se nenhuma foto real for efetivamente enviada, complete permanece false. Casos sem fotos/textuais usam política determinística sem fabricar medidas de inferência. Falha preserva relatório parcial/filas e diagnóstico privado, sem descarregar recursos de terceiros.
