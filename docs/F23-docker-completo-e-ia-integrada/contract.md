# Contrato — F23 Docker completo e IA integrada ao fluxo

*Gerado por spec-writer. Alterações manuais são sobrescritas na regeneração.*

## Prerequisites

Condições a materializar na implementação; ausência mantém o item pendente, sem aprovação por inspeção documental ou simulação. F23 está `pending`; ver [spec](spec.md).

### Runtime services

- **DOCKER:** Compose próprio com postgres/waha/ollama/web/worker e imagens manage/quality. Criar via `./scripts/init.sh` com configuração eval privada e banco `garimpei_`; verificar manifesto, labels, pins, portas, `/health/ready` e heartbeats. Parar por `./scripts/stop.sh`; limpeza somente de instância descartável identificada/autorizada. Usado por CLI-DOCKER-01/02/03/04/05 e todos os E2E.
- Fonte, mídia, WAHA e inferência programáveis em contêineres eval, com histórico de chamadas/barreiras. Entregar composição em `apps/backend/tests/factories/assistance.py`, reutilizando factories listing/media/assessment/inference/valuation/gold/robot existentes; conferir ausência de conta/destinatário real. Fakes não comprovam E2E-GPU-01.
- GPU NVIDIA reservada, modelo/tokenizer íntegros pelo lock F19 e saída externa Ollama bloqueada após preparo explícito. Verificar digests/capacidades e inferência. `playwright-cli` no quality para UI; WSLg/X11 opt-in para login pontual com perfil sintético. Conferir janela/sandbox no host alvo antes de E2E-LOGIN-01.

### Persistent state

- **OFERTAS:** observações por interesse ativo com revisão/preço/datas conhecidos, fotos autorizadas, produto suportado, atributo ausente, correção manual e conflito, além de fotos ausentes e parciais. Criar pelas migrations/factory assistance com factories listing/media/assessment/valuation; conferir IDs e resultados no detalhe público. Usado por API-REVISAO-01/02/03, UI-EVIDENCIA-01, WRK-IDENTIDADE-01/02, WRK-CONDICAO-01, WRK-RECURSO-02 e E2E-FLUXO-01.
- **COMPARAVEIS/INVESTIGACAO:** alvo e cinco identidades equivalentes elegíveis, variantes inválidas, acessório, preço parcial, defeito, amostra vencida/insuficiente/dispersa; interesse com aliases, região e orçamento conhecidos. Criar pelas factories de pesquisa/valoração e conferir contexto/IDs e decisões F06. Usado por WRK-COMPARAVEIS-01/02, WRK-APOIO-01 e E2E-FLUXO-01.
- **REVISOES/COBERTURA:** resultados pendentes, atuais, cacheados e gerações antigas com referências e consumidores conhecidos; dois interesses, um sem dados, com recorte e denominador esperados. Criar pela factory assistance e verificar consulta/registro de consumo. Usado por API-LEITURA-01, UI-COBERTURA-01 e WRK-RASTRO-01/02.
- **OPERACAO:** snapshots atual/ultrapassado, códigos, contagens e sentinelas privadas sintéticas. Criar pela factory operations/assistance e conferir sanitização, whitelist e data. Usado por API-EXPLICACAO-01, UI-DIAGNOSTICO-01 e WRK-APOIO-02.
- **CONTROLE/ENVIO:** pausas específicas/globais, unidade já admitida, oferta que vence durante pausa, intenção congelada e envio incerto no canal sintético. Criar por factories robot/gold/alert e verificar relógio/barreira/recibos. Usado por WRK-CONTROLE-01/02 e WRK-ALERTA-01/02.
- **PERSISTENCIA:** instalação anterior preenchida com banco, perfis/sessões, mídia, pesos, configurações, análises, fila e recibos inventariados. Criar por migrations anteriores/factories e gerar backup F17; restaurar em segunda base descartável própria e comparar inventário antes da adoção. Usado por CLI-DOCKER-03 e E2E-PERSISTENCIA-01.

### Static inputs

- `apps/backend/tests/fixtures/assistance/cases.json` — entregar casos com IDs, revisão, finalidade, relógio/barreira, entrada/expectativa e variantes de HTTP, cache e falha. Handles **CASOS_HTTP**, **CASOS_CACHE**, **FALHAS** e **RESPOSTAS** selecionam conjuntos desse arquivo; schema/expectativas são conferidos pela factory. Usado por API-REVISAO-02/03, API-EXPLICACAO-01, WRK-VALIDACAO-01/02, WRK-RASTRO-01 e WRK-RECURSO-01.
- `apps/backend/tests/fixtures/assistance/corpus.json` — entregar **CORPUS** com fonte/direitos, IDs/hashes, família/atributos, condição/equivalência/conflitos, rótulos humanos e suporte citado, casos críticos e revisão da base comparada. Reutilizar fotos autorizadas F15; verificar direitos/hashes e revisor antes de executar. Usado por E2E-QUALIDADE-01/GPU-01/FLUXO-01. Falta de material/rótulo bloqueia o item.
- `docs/F23-docker-completo-e-ia-integrada/runtime-lock.json` — entregar pins reais das bases/ferramentas; preservar lock de modelo F19. Verificar imagens/artefatos contra digests, sem hashes inventados. Usado por CLI-DOCKER-01/05 e E2E-GPU-01.

### Configuration

- Arquivo privado `GARIMPEI_ENV_FILE`, `GARIMPEI_ENV=eval`, banco/portas/diretórios e IDs próprios conforme F02; resolução sanitizada conferida no inventário. Credenciais sintéticas são geradas pela factory; CSRF permanece habilitado.
- Limites e nomes internos conforme spec §3; relógio UTC controlável nos testes; `OLLAMA_NO_CLOUD=1`; coordenação GPU de host identifica proprietário de cada ambiente e aguarda liberação, sem encerrar processo alheio.

### External dependencies

- Downloads de imagens/pesos/tokenizer são preparo explícito de fontes oficiais. Conta/sessão real para login depende de ação humana própria; cenário usa perfil sintético. Nenhum item autoriza envio ao canal real do usuário.
- Aceite completo F21 é pré-requisito da conclusão integrada F23; a prova positiva real permanece pendente no progresso. Simulador WAHA prova encadeamento e não substitui essa dimensão.

## Quality gates

Cada gate deve passar para considerar a implementação pronta. Ferramentas executam no contêiner quality, com revisão/ambiente/código de retorno registrados. Comandos Python abaixo partem de `apps/backend/`; pytest não parte da raiz.

- **Seis gates Python** — `node scripts/run-gates.mjs` da raiz montada — tipos, lint/templates, limites, arquitetura, ciclos e código/dependências não usados.
- **Testes Python/PostgreSQL** — `uv run --frozen --no-sync pytest` — regras, integração e regressões com serviços próprios.
- **Django** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --frozen --no-sync python manage.py check` — configuração válida.
- **Migrations** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --frozen --no-sync python manage.py makemigrations --check --dry-run` — schema versionado; ensaio preenchido comprova aplicação.
- **Build** — `uv build --wheel` no backend e `docker compose --profile tools build web worker manage quality` da raiz — pacote, templates, imagens e pins válidos.
- **Harness** — `node --test scripts/test/harness.test.mjs` e `node scripts/check-harness.mjs` da raiz — lifecycle e estrutura preservados.
- **UI/E2E** — jornadas por `playwright-cli`, desktop/largura estreita, corpus humano e GPU reais — cada dimensão exige evidência própria; fixture de resposta não aprova modelo real.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F23-AC01**: Web, worker, navegador dedicado, PostgreSQL, WAHA e Ollama executam em Docker por ambiente, com preparo/migrations em contêiner, imagens fixadas, prontidão efetiva, portas locais e dados isolados; operar não exige Python/uv/Node no host. | CLI-DOCKER-01, CLI-DOCKER-02, CLI-DOCKER-05, E2E-LOGIN-01 |
| **F23-AC02**: Identificação usa revisão de IA local consumida pelo normalizador, com modelo/atributos sustentados por evidências da mesma observação; atributo ausente ou conflito permanece explícito e correção manual válida é preservada. | WRK-IDENTIDADE-01, WRK-IDENTIDADE-02 |
| **F23-AC03**: Condição consome análise local de título/descrição/fotos de F15/F19, com cobertura e limitações; foto ausente, evidência insuficiente ou análise incompatível não confirma funcionamento nem libera nova qualificação. | WRK-CONDICAO-01 |
| **F23-AC04**: Comparáveis retidos na nova política têm revisão local aplicável de equivalência e de indícios de preço parcial/acessório/defeito; F06 mantém seus critérios de amostra, validade, dispersão e mediana, sem completar preço ou variante pela IA. | WRK-COMPARAVEIS-01, WRK-COMPARAVEIS-02 |
| **F23-AC05**: Investigação recebe apoio de IA para lacunas e termos derivados dos interesses/aliases validados, respeitando orçamento, geografia e suspensão; nenhuma sugestão adiciona interesse, fonte ou ação autônoma não autorizada. | WRK-APOIO-01 |
| **F23-AC06**: Diagnóstico assistido explica snapshot sanitizado por códigos e fatos verificáveis, com origem, data e próxima ação; ausência/falha de IA conserva diagnóstico determinístico e nenhuma sugestão executa comando ou altera configuração. | API-EXPLICACAO-01, WRK-APOIO-02, UI-DIAGNOSTICO-01 |
| **F23-AC07**: Inferência usa somente o modelo local fixado, GPU e schemas/referências validados, sem fallback remoto; saída inválida, fato sem suporte, prompt injection ou tool call não é aplicado como confirmação e não expõe segredos. | CLI-DOCKER-05, WRK-VALIDACAO-01, WRK-VALIDACAO-02, E2E-GPU-01 |
| **F23-AC08**: Toda decisão assistida liga entrada, revisões/hashes, finalidade, modelo/prompt/schema/política, resultado e consumidor; cache é compatível com o contexto completo e resultado atrasado não substitui decisão atual. | API-REVISAO-01, API-REVISAO-02, API-REVISAO-03, API-LEITURA-01, WRK-RASTRO-01, WRK-RASTRO-02 |
| **F23-AC09**: Corpus autorizado com rótulos humanos independentes compara base atual e F23 por frente, incluindo casos insuficientes/contraditórios; nenhum caso crítico autoriza incorretamente oferta nem caso antes correto vira confirmação incorreta, com contagens e limites publicados. | E2E-QUALIDADE-01 |
| **F23-AC10**: IA pausada, indisponível, sem GPU/VRAM ou com timeout tem estado e recuperação explícitos, limites finitos e filas independentes; preserva consulta, coleta independente e resultados ainda aplicáveis, sem CPU ou redução de critérios silenciosas. | CLI-DOCKER-02, CLI-DOCKER-04, WRK-RECURSO-01, WRK-RECURSO-02 |
| **F23-AC11**: Pausa global F22 e pausa específica impedem novas chamadas nos pontos de admissão; retomada conserva escolhas, revalida revisões/prazos e não duplica eventos, mensagens ou pesquisa idêntica. | WRK-CONTROLE-01, WRK-CONTROLE-02, WRK-ALERTA-02 |
| **F23-AC12**: Adoção do runtime Docker e reinícios preservam banco, perfis/sessões, mídia, pesos, fila, configurações, análises e recibos, com inventário, backup restaurado e rollback verificado; parada normal não limpa dados e envio incerto não é repetido. | CLI-DOCKER-03, WRK-ALERTA-02, E2E-PERSISTENCIA-01 |
| **F23-AC13**: Detalhes, integração IA e acompanhamento exibem evidências, estado, cobertura por interesse/finalidade com denominador/data e próxima ação pelo mesmo recorte; valores financeiros e corpos autorizados continuam congelados e calculados pelo domínio. | UI-EVIDENCIA-01, UI-COBERTURA-01, UI-DIAGNOSTICO-01, WRK-ALERTA-01, WRK-ALERTA-02 |
| **F23-AC14**: Prova integrada em ambiente isolado demonstra cada perfil com modelo real na GPU e cadeia observação–análises–comparáveis–cálculo–qualificação–mensagem capturada em WAHA controlado, com repetição sem duplicação e falhas cobertas; simulação não substitui GPU, revisão humana ou pendência real de F21. | E2E-GPU-01, E2E-FLUXO-01, E2E-QUALIDADE-01, WRK-RECURSO-01, E2E-PERSISTENCIA-01 |

Os itens também verificam a contribuição F23 para INT-32/INT-33/INT-34.

## HTTP API

**Verification mode:** Enviar requisição local e conferir status, HTML, headers e efeitos diretos de admissão.

### Revisao

#### `API-REVISAO-01` — Admissão assíncrona
- given: OFERTAS tem revisão atual e CSRF válido.
- when: POST /ofertas/<id>/ia/reavaliar/ com finalidade, expected_revision e command_id válidos.
- then:
  - 202 HTML identifica finalidade e referência do trabalho.
  - A resposta informa espera assíncrona, sem declarar análise concluída.

#### `API-REVISAO-02` — Idempotência e conflito
- given: OFERTAS contém comando já admitido.
- when: Repetir POST conforme o caso de CASOS_HTTP.
- then:
  - Mesmo command_id e corpo retornam a mesma referência.
  - Mesmo command_id com corpo diferente retorna 409.
  - Revisão ultrapassada retorna 409 com opção de recarregar.

#### `API-REVISAO-03` — Validação e proteção
- given: OFERTAS está disponível nos casos CASOS_HTTP.
- when: Enviar a variante inválida de requisição indicada no caso.
- then:
  - Formato inválido retorna 400; finalidade válida sem entrada utilizável retorna 422.
  - CSRF ausente retorna 403; alvo inexistente retorna 404; método incompatível retorna 405.
  - Falha de persistência retorna 503 sem confirmação falsa.

### Leitura

#### `API-LEITURA-01` — Consulta sem efeitos
- given: REVISOES e COBERTURA estão persistidas.
- when: GET da página de evidência ou cobertura correspondente.
- then:
  - 200 HTML mostra finalidade, estado e data/revisão aplicáveis.
  - A leitura não cria trabalho nem confirma uma análise nova.

### Explicacao

#### `API-EXPLICACAO-01` — Explicação idempotente do recorte
- given: OPERACAO contém snapshot atual ou ultrapassado, conforme CASOS_HTTP.
- when: POST /acompanhamento/ia/explicar/ com snapshot_id e command_id do caso.
- then:
  - Snapshot atual retorna 202 HTML com referência do trabalho.
  - Repetição idêntica conserva referência; reutilização conflitante retorna 409.
  - Snapshot ultrapassado retorna 409 sem explicar o estado atual por dados antigos.

## CLI

**Verification mode:** Executar wrapper no host com Docker CLI e conferir saída, código, manifesto, inventário e recursos próprios.

### Docker

#### `CLI-DOCKER-01` — Runtime completo
- given: DOCKER possui imagens fixadas e arquivo privado.
- when: Executar ./scripts/init.sh.
- then:
  - Código zero apresenta URL local e identificação do ambiente.
  - Prontidão comprova web, banco e heartbeats dos grupos reservados em contêineres.
  - Operação funciona sem Python/uv/Node no PATH do host.
  - Inventário identifica aplicação/navegador em contêineres e pins resolvidos.

#### `CLI-DOCKER-02` — Dependências parciais
- given: DOCKER tem banco saudável, modelo ausente ou WAHA não pareado.
- when: Executar ./scripts/init.sh.
- then:
  - Base permanece consultável com dependência parcial explicitada.
  - IA ausente não é reportada como pronta.
  - Nenhum peso é baixado implicitamente.

#### `CLI-DOCKER-03` — Parada normal
- given: DOCKER ativo com PERSISTENCIA inventariada.
- when: Executar ./scripts/stop.sh.
- then:
  - Encerramento reconhece somente recursos próprios.
  - Volumes e diretórios persistentes permanecem disponíveis.
  - Não há confirmação de limpeza ou descarregamento não comprovado.

#### `CLI-DOCKER-04` — Recuperação incerta
- given: DOCKER tem chamada de término incerto e reserva GPU mantida.
- when: Executar ./scripts/init.sh --recover-ai.
- then:
  - Wrapper verifica labels e ID do Ollama próprio.
  - Nova execução aguarda confirmação do término anterior.
  - Propriedade ou término não comprovados conservam bloqueio e motivo.
  - Nenhum recurso de outro ambiente é alterado.

#### `CLI-DOCKER-05` — Preparo e restrições
- given: DOCKER tem artefatos incompletos e rede privada definida.
- when: Executar ./scripts/init.sh --prepare-ai.
- then:
  - Preparo verifica imagem, modelo, tokenizer e digests.
  - Ollama retorna à rede interna sem saída externa ao concluir.
  - Inventário comprova portas somente loopback e ausência de socket Docker na aplicação.
  - Imagem e relatórios não contêm os segredos sentinela.

## UI

**Verification mode:** Navegar por ações de usuário e conferir DOM/acessibilidade, conteúdo, foco e navegação.

### Evidencia

#### `UI-EVIDENCIA-01` — Origem e limites
- given: OFERTAS tem REVISOES atuais, anteriores e conflitantes.
- when: Abrir detalhes da oferta correspondente.
- then:
  - Estado distingue analisado, pendente, parcial, conflito e falha.
  - Referências, finalidade, modelo, data e revisão permitem conferir a origem.
  - Conflito mostra evidências e preserva a correção manual.
  - Análise parcial ou antiga não aparece como confirmação de funcionamento atual.

### Cobertura

#### `UI-COBERTURA-01` — Contagens por frente
- given: COBERTURA inclui interesses com e sem dados.
- when: Abrir cobertura na integração IA.
- then:
  - Contagens por interesse/finalidade mostram denominador e data do recorte.
  - Sem dados é distinto de zero resultados aprovados.
  - Decisões assistidas apontam resultado consumido; cache é distinto de nova chamada.
  - Limitações e próxima ação são legíveis em desktop e largura estreita.

### Diagnostico

#### `UI-DIAGNOSTICO-01` — Falha conserva consulta
- given: OPERACAO está visível com filtros e recorte conhecidos.
- when: Solicitar explicação no caso de falha assistida.
- then:
  - Diagnóstico determinístico continua disponível.
  - Erro ou pendência pertence à ação de explicação.
  - Filtros e leitura anterior aplicável são preservados.
  - Sugestão não é apresentada como ação executada.

## Worker

**Verification mode:** Despachar unidade persistente e observar resultado, chamadas registradas e efeitos após processamento.

### Identidade

#### `WRK-IDENTIDADE-01` — Identificação sustentada
- given: OFERTAS tem produto suportado e resposta local com referências válidas.
- when: Processar revisão de identidade.
- then:
  - Normalização registra somente atributos admitidos e sustentados.
  - Decisão referencia o resultado local consumido.
  - Modelo não cria alias/família automaticamente.

#### `WRK-IDENTIDADE-02` — Lacunas, conflito e manual
- given: OFERTAS tem atributo ausente ou correção manual e divergência explícita.
- when: Processar revisão correspondente.
- then:
  - Atributo ausente permanece desconhecido.
  - Correção manual não é sobrescrita.
  - Conflito sustentado conserva ambas as evidências e exige revisão.
  - Nova qualificação dependente da identidade fica bloqueada.

### Condicao

#### `WRK-CONDICAO-01` — Texto e fotos
- given: OFERTAS tem caso completo ou caso de omissão/defeito.
- when: Processar avaliação de condição F15.
- then:
  - Resultado registra texto e fotos efetivamente examinados.
  - Foto ausente, omissão ou defeito relevante não libera qualificação indevida.
  - Aparência não comprova funcionamento interno.
  - Precedência e histórico manual F15 são preservados.

### Comparaveis

#### `WRK-COMPARAVEIS-01` — Revisão e retenção
- given: COMPARAVEIS tem alvo e candidatos equivalentes versionados.
- when: Processar investigação e avaliação pendentes.
- then:
  - Cada candidato retido tem revisão local aplicável ligada ao alvo correto.
  - F06 calcula mediana pela amostra persistida sob política vigente.
  - Retenção não depende do lucro desejado.

#### `WRK-COMPARAVEIS-02` — Exclusões e amostra
- given: COMPARAVEIS inclui incompatíveis, acessórios, preço parcial, defeitos e amostras inválidas.
- when: Processar o caso correspondente.
- then:
  - Candidato incompatível não é retido como equivalente.
  - Modelo não completa preço ou atributo desconhecido.
  - F06 conserva cinco identidades, janela de 14 dias, corte 50–150% e razão máxima/mínima até 1,5.
  - Referência de novo segue separada com validade de sete dias.
  - Amostra insuficiente não produz venda/lucro fictícios.

### Apoio

#### `WRK-APOIO-01` — Investigação limitada
- given: INVESTIGACAO tem interesse ativo, lacuna e aliases permitidos.
- when: Processar apoio à investigação.
- then:
  - Termos utilizados derivam de interesses/aliases validados.
  - Geografia, orçamento e suspensão permanecem autorizados.
  - Nenhum interesse/fonte é adicionado automaticamente.
  - Termo fora da whitelist não provoca navegação.

#### `WRK-APOIO-02` — Explicação sanitizada
- given: OPERACAO tem códigos/contagens e sentinelas privadas.
- when: Processar explicação local do snapshot.
- then:
  - Entrada da IA contém somente fatos sanitizados permitidos.
  - Resultado mostra origem/data e ação de catálogo.
  - Sugestão não executa comando, envio, login ou mudança de configuração.
  - Leitura repetida do mesmo recorte não cria nova análise.
  - A análise referencia o snapshot operacional real, sem criar anúncio artificial.

### Validacao

#### `WRK-VALIDACAO-01` — Schema e suporte
- given: RESPOSTAS contém JSON inválido, referência inventada ou fato/preço sem suporte.
- when: Processar a resposta correspondente.
- then:
  - Resposta é recusada com motivo verificável.
  - Não é aplicada como confirmação ou ausência de conflito.
  - Decisão anterior ainda aplicável é conservada com revisão.

#### `WRK-VALIDACAO-02` — Conteúdo hostil
- given: RESPOSTAS tem prompt injection em texto/foto ou tool call.
- when: Processar o caso correspondente.
- then:
  - Conteúdo não altera política/configuração/destino.
  - Nenhum comando ou tool sugerido é executado.
  - Sentinelas privadas não aparecem na entrada da IA, resultado público ou logs.

### Rastro

#### `WRK-RASTRO-01` — Cache contextual
- given: REVISOES tem resultado válido e variação de contexto segundo CASOS_CACHE.
- when: Processar solicitação do caso.
- then:
  - Assinatura idêntica reutiliza somente resultado válido compatível.
  - Mudança de finalidade, alvo/candidato, revisão/hash, correção, modelo, prompt/schema/opções ou política impede cache incompatível.
  - Consumidor conserva vínculo ao resultado usado.

#### `WRK-RASTRO-02` — Conclusão atrasada
- given: REVISOES tem geração antiga em execução e entrada atual alterada.
- when: Concluir geração antiga.
- then:
  - Resultado permanece histórico ultrapassado.
  - Decisões atuais não são sobrescritas.
  - Resultado não habilita alerta para revisão nova.

### Recurso

#### `WRK-RECURSO-01` — Falhas e orçamento
- given: FALHAS inclui GPU ausente/OOM, timeout, contexto excedido e fila cheia.
- when: Processar unidade afetada.
- then:
  - Estado diferencia recurso, término incerto, entrada incompatível e fila cheia.
  - Tentativas e orçamento são finitos conforme perfil.
  - Não há CPU/remoto silencioso nem truncamento.
  - Consulta e trabalho independente continuam progredindo.

#### `WRK-RECURSO-02` — Revisão obrigatória
- given: OFERTAS tem revisão obrigatória pendente/falha ou somente falha narrativa.
- when: Processar qualificação correspondente.
- then:
  - Falta de revisão obrigatória aplicável bloqueia nova autorização.
  - Análise antiga incompatível permanece histórica.
  - Falha apenas narrativa não bloqueia oferta com requisitos suficientes.

### Controle

#### `WRK-CONTROLE-01` — Pausa por unidade
- given: CONTROLE tem pausa global ou específica confirmada e job antigo.
- when: Reclamar próxima unidade assistida.
- then:
  - Nenhuma nova inferência é admitida.
  - Fila e decisões confirmadas são preservadas.
  - Unidade já admitida conclui somente nos limites F22.

#### `WRK-CONTROLE-02` — Retomada
- given: CONTROLE tem pausas específicas e oferta vencida durante pausa global.
- when: Retomar robô.
- then:
  - Pausas específicas permanecem.
  - Revisões e idade de publicação são revalidadas.
  - Oferta fora do prazo não recebe novo primeiro alerta.
  - Pesquisa idêntica já válida não é repetida.

### Alerta

#### `WRK-ALERTA-01` — Qualificação e números
- given: ENVIO possui evidências suficientes na política F23.
- when: Processar autorização de alerta.
- then:
  - F21 verifica revisões assistidas aplicáveis, amostra e lucro positivo.
  - Compra/venda/lucro são centavos calculados pelo domínio.
  - Corpo vem do snapshot determinístico, sem enviar texto livre da IA diretamente.
  - Modelo não escolhe destinatário nem autoriza envio por si.

#### `WRK-ALERTA-02` — Corpo e vínculo preservados
- given: ENVIO tem intenção congelada/incerta ou nova evidência incompatível.
- when: Processar retomada/revalidação no caso correspondente.
- then:
  - Corpo, evento e destino já autorizados são preservados.
  - Envio incerto segue reconciliação sem novo POST automático.
  - Nova transmissão dependente de revisão incompatível fica suspensa.

## E2E

**Verification mode:** Exercitar sistema completo e verificar cadeia entre serviços, chamadas, decisões e dados persistentes.

### Qualidade

#### `E2E-QUALIDADE-01` — Referência humana
- given: CORPUS tem rótulos humanos independentes e base atual reproduzível.
- when: Comparar base e F23 no mesmo corpus.
- then:
  - Relatório publica acertos, erros, abstenções, conflitos, falhas, cobertura e custo por tarefa.
  - Nenhum caso crítico permite autorização incorreta.
  - Nenhum caso antes correto vira confirmação incorreta.
  - Revisor humano confirma rótulos/divergências e limites; modelo não é gabarito.

### Gpu

#### `E2E-GPU-01` — Cada perfil real
- given: DOCKER tem GPU reservada, modelo fixado e CORPUS autorizado.
- when: Executar lote nos quatro perfis novos e no perfil F15.
- then:
  - Cada perfil tem inferência real na GPU com resultado validado ou abstenção fundamentada.
  - Rastro liga chamada, modelo, validação e consumidor.
  - Inferência funciona com saída externa do Ollama bloqueada.
  - Métricas registram GPU, tokens e duração; fakes não contam como modelo real.

### Fluxo

#### `E2E-FLUXO-01` — Cadeia e repetição
- given: DOCKER tem fonte/WAHA controlados e OFERTAS com cinco comparáveis retidos.
- when: Executar jornada de coleta até mensagem capturada e repetição do mesmo anúncio.
- then:
  - Cadeia liga observação, mídia, condição, identidade, comparáveis e cálculo.
  - Mensagem corresponde à qualificação e snapshot aplicáveis.
  - Repetição não duplica observação/evento nem primeiro alerta.
  - Prova controlada não encerra dimensão real positiva pendente de F21.

### Persistencia

#### `E2E-PERSISTENCIA-01` — Adoção e rollback
- given: PERSISTENCIA tem instalação anterior inventariada e backup F17 descartável.
- when: Executar ensaio de adoção e rollback.
- then:
  - Inventário comprova conservação de dados, sessões/perfis, mídia, pesos, configurações, análises, filas e recibos.
  - Backup é restaurado e verificado antes da adoção.
  - Reinício preserva pausas/histórico e não repete envio incerto.
  - Rollback usa somente recursos próprios sob barreira de recuperação.

### Login

#### `E2E-LOGIN-01` — Browser em Docker
- given: DOCKER tem display WSLg/X11 autorizado e perfil sintético dedicado.
- when: Executar jornada de login humano pelo contêiner pontual.
- then:
  - Janela acessível comprova encaminhamento gráfico no host alvo.
  - Chromium permanece no contêiner como usuário não root e sandbox comprovado.
  - Login e coleta não abrem perfil simultaneamente.
  - Sem display, login_required orienta preparo sem coletor no host.
