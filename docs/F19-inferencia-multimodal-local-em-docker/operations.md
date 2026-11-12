# F19 — Operação da IA local

A aplicação continua sendo Django/PostgreSQL e worker Procrastinate. IA usa exclusivamente `qwen3.5:4b-q4_K_M`, Ollama oficial 0.40.16 e os digests completos em [model-lock.json](model-lock.json). A tag legível não substitui a conferência do digest. Imagem, manifesto, blobs e tokenizer foram resolvidos em fontes oficiais; as evidências reais ficam em `evidence/`.

## Preparar um ambiente próprio

Use a preparação de segredos da [F02](../F02-fundacao-tecnica-e-ambiente-local/operations.md). Os três segredos permanecem em arquivo privado, nunca em Compose, manifesto, relatório ou contêiner Ollama. Configure nesse arquivo:

```text
GARIMPEI_ENV=eval
GARIMPEI_INSTANCE=<identidade_exclusiva>
GARIMPEI_AI_SERVICE_ENABLED=true
```

A habilitação do serviço é explícita por ambiente; o controle de análise começa habilitado quando a infraestrutura estiver preparada. Sem serviço configurado, web/coleta/alertas continuam independentes. `init` inicia apenas imagens já preparadas e não baixa pesos. Prepare a imagem explicitamente:

```bash
docker pull ollama/ollama:0.40.16@sha256:910d0d8107b538fb0894e63163eb195de0cc7aefcbc666dc62d3b18f71124592
export GARIMPEI_ENV_FILE=<arquivo_privado_deste_ambiente>
./scripts/init.sh --disposable
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py local_ai prepare --download
```

`--disposable` identifica exclusivamente um laboratório sintético; parada normal conserva banco, pesos e resultados. `prepare --download` exige serviço habilitado, baixa explicitamente os pesos/tokenizer fixados, confere cada blob, registra corpus sintético e calibra uma imagem de 512×512. Divergência/incompletude não vira prontidão nem autoriza troca de modelo. Repetir preparo não autoriza ampliar o modelo, usar `latest` ou substituir pins silenciosamente.

Os modelos ficam no volume Docker `ollama_models` do projeto Compose da instância. O tokenizer, originais registrados, derivados, catálogo e reservas de capacidade ficam em `.runtime/<environment_id>/inference/`, com arquivos privados. Originais são conservados; nomes de arquivos são hashes, sem caminhos vindos do anúncio. Requisições, partes, resultados e controle ficam no PostgreSQL próprio. Migração aditiva: `0013_local_inference`, dependente de `0012_opportunity_collection`.

## Foto autorizada e corpus

O corpus reproduzível é `apps/backend/tests/fixtures/inference/{cases.json,image-a.png,image-b.png}`; os desenhos sintéticos são CC0 e têm hashes no manifesto. Para registrar foto adicional, defina `GARIMPEI_AI_PHOTO_MANIFEST` apontando para um manifesto privado legível com `id`, `revision`, `path`, `sha256`, `source`, `authorization` e licença/proveniência aplicáveis. A aplicação confere hash, limites e registro antes de enviar a imagem; HTTP não aceita URL ou caminho arbitrário para o modelo.

A avaliação usou **PlayStation 5 and DualSense**, de **Osh33m**, [Wikimedia Commons, revisão 1216350292](https://commons.wikimedia.org/w/index.php?title=File:PlayStation_5_and_DualSense.jpg&oldid=1216350292), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). O usuário escolheu explicitamente a foto pública livre. Original conservado: SHA256 `08905d5f2bbb73fd08c4f1e21463052d9c2f7d260d083eb2114a47247a2943db`; derivado PNG redimensionado, sem ampliação: `2a7f38a5129e7b44e975057e53842e929771683b828b55f61a1fe6dfb3ce2a5e`. O arquivo e manifesto ficam fora do versionamento; o relatório preserva atribuição, transformação e hashes.

## Operar e conferir

- `GET /integracoes/ia/`: tela com modo, pausa, chamada ativa/fila, residência, motivo e horário da última conferência.
- Pausar/retomar usa POST com CSRF e revisão de controle. A mesma intenção é idempotente; revisão concorrente rejeitada com 409, formato com 400, CSRF com 403 e falha de banco com 503. Nenhuma ação rejeitada é anunciada como concluída.
- A pausa bloqueia novas partes, conserva a fila e permite terminar somente a chamada já em curso dentro do prazo. Memória só é anunciada como não residente depois de confirmação. Pausa manual persiste após reinício e exige retomada explícita.
- Após 300 segundos sem uso, o modelo é descarregado. Novo trabalho válido carrega os mesmos pesos sem download. Repetição idêntica pode reutilizar resultado e, nesse caso, dispensa recarga.

```bash
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py local_ai status
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py local_ai smoke --fixture text
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py local_ai smoke --fixture unicode
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py local_ai smoke --fixture image-a
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py local_ai smoke --fixture image-b
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py local_ai smoke --fixture authorized-photo
```

O smoke é restrito ao ambiente `eval`, usa observação sintética própria, agenda trabalho persistente e espera até 240 segundos pelo resultado. Não cria eventos de descoberta, classificação manual, intenções ou envios reais. `status` lê o último diagnóstico persistido, com data; o reconciliador verifica a infraestrutura a cada cinco segundos, com orçamento de diagnóstico de três segundos. Código 0 indica operação verificável; 2 identifica pré-requisito/contexto ausente ou preparo incompleto; 1 indica falha de validação/inferência. Não confundir servidor vivo, modelo disponível, residência e análise efetiva.

## Limites e execução

Perfil: contexto4096, saída512, texto recebido16KiB e orçamento textual2048 tokens incluindo instruções/schema, até4 imagens por requisição e uma por chamada. PNG/JPEG até10MiB/20MP, derivado até512×512. Prazo total180s por chamada, resposta64KiB, lease240s, fila100, no máximo três tentativas técnicas com recuos15/30s. Os valores efetivos e faixas estão em `config/env.py`; redução de limites continua explícita. Material sem orçamento comprovado é recusado com `context_unverified`, sem truncamento silencioso.

`GARIMPEI_AI_DISK_LIMIT` limita a área de inferência a até1GiB. A admissão reserva conservadoramente2MiB por assinatura para as respostas/telemetria/overhead PostgreSQL das cinco partes possíveis; arquivos privados são contabilizados adicionalmente sob o mesmo lock. Essa reserva pode impedir admissão antes de atingir exatamente1GiB físico. Dados confirmados não são podados automaticamente. Reserva órfã após falha de banco é conservadora; só pode ser reparada depois de conferir ausência da requisição correspondente no banco próprio.

Uma única chamada de inferência pode ser autorizada por vez, por geração e revisão. O worker consome também `inference`, com pelo menos quatro slots totais, deixando pelo menos três disponíveis para o restante quando a IA está ocupada. Não se iniciam dois consumidores `call_command` concorrentes do mesmo app Procrastinate, pois compartilham o conector global. O reconciliador da IA tem thread independente e não aguarda a inferência.

Assinatura inclui identidade/revisão, conteúdo ordenado, modelo/digests, tokenizer, prompt/schema, transformação e opções. Métricas/timestamps de preparo não invalidam resultado compatível. O decoder só pode escolher referências anotadas pela aplicação; a aplicação ainda valida JSON, campos adicionais, conclusão, offsets/quotes e IDs examinados antes do commit. O resultado não altera condição ou dinheiro; esses consumidores pertencem a F15/F07.

## Transporte e isolamento medidos

No Docker Desktop desta instalação, a porta publicada ficou inacessível ao host quando o contêiner tinha somente uma rede `internal: true`; conectar a rede de preparo restabelecia o acesso. Manter rede externa para inferência não foi adotado. O worker usa REST no loopback do contêiner através de um único canal `docker exec` persistente por execução. O script bash é estático; tamanho validado e bytes HTTP/JSON seguem por stdin, sem interpolar texto/foto em shell.

Criar cada `docker exec` custou aproximadamente3,07s até para `true`. O canal é aquecido em segundo plano e indica indisponibilidade antes de estar pronto; não despacha análise nesse intervalo. O diagnóstico aquecido medido foi aproximadamente47ms, sem ampliar o limite3s. Framing inválido ou transporte perdido após possível envio aborta o canal e conserva execução incerta; antes de novo despacho é necessário comprovar o encerramento da chamada, inclusive reiniciando apenas o contêiner próprio. EOF, `/api/ps` e expiração do lease isoladamente não provam término da chamada.

O lifecycle confere labels de checkout/ambiente e registra a referência imutável do contêiner no manifesto por run. Manifests antigos sem esse campo continuam aceitos. A porta adicional é distinta e persistida sem invalidar as três portas anteriores. O contêiner recebe somente volume de pesos, reserva NVIDIA e configuração Ollama; não recebe checkout, socket Docker, sessão Facebook/WAHA ou segredos. A rede externa é conectada somente durante o preparo explícito e desconectada ao finalizar; inferência roda em rede interna com `OLLAMA_NO_CLOUD=1`. A publicação de porta é em127.0.0.1.

GPU é reservada entre ambientes Garimpei por proprietário no host; não tome uma reserva alheia nem encerre outros programas para liberar VRAM. Outro ambiente precisa aguardar liberação pelo proprietário. CPU/offload parcial, OOM e indisponibilidade são causas explícitas, sem fallback remoto ou troca de modelo. `evidence/container-locality.json` registra rede/mounts/flags e offload CUDA; métricas durante as chamadas complementam a mera visibilidade de `nvidia-smi`.

## Encerrar e recuperar

```bash
./scripts/stop.sh
```

Parada normal encerra somente recursos verificados da instância e conserva pesos, banco, fila e resultados. Não use `stop --clean` em instalação real. O laboratório descartável pode usar `./scripts/stop.sh --clean` somente com o marcador sintético próprio; isso remove seus dados/volumes. Na UI, execução incerta conserva o motivo (inclusive timeout) e mostra encerramento/residência ainda não confirmados; posse persistida não equivale a uma análise comprovadamente em curso. Em execução incerta, preserve diagnóstico e aguarde a confirmação de encerramento; não envie outra chamada ao mesmo modelo por fora da fila.

Serviço ausente pede conferência do contêiner próprio; pesos ausentes/corrompidos pedem preparo explícito; pin diferente exige conferir a referência aprovada; memória/GPU indisponível exige aguardar recurso; saída inválida conserva o resultado anterior e pede revisão da entrada. Não apague volume, perfil ou recibos para tentar recuperar a IA.

## Verificar a entrega

Na raiz, com o ambiente de teste explícito para que pytest configure Django mesmo fora do diretório do backend:

```bash
node scripts/run-gates.mjs
DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync pytest -q
DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check
uv build --project apps/backend
```

Migrations também são aplicadas em PostgreSQL real pelos testes/`init`. Use `playwright-cli` e sessão própria para os controles. A evidência final identifica hash das fontes antes/depois da suíte; alteração de fonte exige nova validação afetada. Fotos reais e pesos permanecem privados; relatórios não devem conter cookies, credenciais, base64 ou respostas com material pessoal.
