# Contract: F02 — Fundação técnica e ambiente local

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-10T21-15-47Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

*Gerado por spec-writer. Edições manuais serão substituídas na regeneração.*

## Prerequisites

Condições futuras para executar este contrato; produzir runtime, arquivos e estados abaixo é parte da F02. **Ainda não existem como aplicação** nesta especificação. Ausência bloqueia os cenários dependentes; não equivale a sucesso. Nenhuma prova usa conta pessoal, anúncio real ou mensagem WhatsApp.

### Runtime services

| Recurso | Preparação | Verificação / itens |
|---|---|---|
| WSL2/Linux x86_64, Git/Bash/Node, uv/Python 3.13, Docker/Compose | Disponibilizar ferramentas conforme versões exatas documentadas antes da integração; sincronizar dependências pelo lock. | Executáveis/versões e daemon real acessíveis; DOC-PREPARACAO, CLI-INICIO, CLI-QUALIDADE e E2E. Falta não autoriza download no gate. |
| Django/web e worker Python independentes | `./scripts/init.sh` no ambiente configurado, após integração F02. | PIDs próprios e prontidão real da spec; testes negativos podem manter deliberadamente um recurso indisponível. API-SAUDE, WRK-FILA e E2E. |
| PostgreSQL e WAHA | Compose com projeto/labels/volumes próprios, bind loopback, imagens por versão/digest compatíveis e chaves privadas. | Conexão ao banco previsto, migrations completas, health WAHA 200/saudável; conta pareada não necessária. Não substituir contêiner real por mock nos itens de operação. |

### Persistent state

| Estado | Criação | Verificação / itens |
|---|---|---|
| Banco exclusivo `garimpei_<identidade>` e schema Django/fila | Provisionar recurso próprio e aplicar `./scripts/migrate-dev.sh --apply`. | Conferir banco selecionado, migrations aplicadas e metadados de propriedade. CLI-MIGRACAO, E2E e WRK-FILA. |
| RuntimeState/RuntimeProbe técnicos | Factories novas da F02 e comando `runtime_probe --wait`, conforme spec §6; cada cenário tem run_id/UUID próprios. | Consultar registros e fila no banco marcado, sem dados de negócio. WRK-FILA, E2E-TRANSACAO, API-SAUDE. |
| Estado de retenção/isolamento | Factories criam probes manuais concluído/pendente, independentes da cadeia de controle, e marcador sintético de sessão em volume próprio. | Ler IDs/estado e hash do marcador antes/depois; não copiar sessão pessoal. E2E-PRESERVACAO/ISOLAMENTO. |
| Execuções de falha e concorrência | Factory prepara identidades diferentes, lock ativo, processo alheio controlado e transações separadas. | Marcadores de propriedade e referências de processo/recibo conferidas antes de interromper ou limpar recursos. E2E-FALHA/PROPRIEDADE/TRANSACAO e CLI-INICIO. |

### Static inputs

| Entrada | Criação | Verificação / itens |
|---|---|---|
| `docs/PRD.md`, stack, AGENTS, harness, arquitetura e decisão/avaliação F01 | Usar checkout canônico; exigir F01 done/avaliação limpa antes da implementação. | Conferir fontes e decisão explícita; este pedido de especificação não as substitui. Todos os itens. |
| `pyproject.toml`, `uv.lock`, `.python-version`, configuração de gates e manifesto das imagens | Produzir na preparação F02 com versões exatas e compatibilidade da spec §3. | Lock sincronizável sem atualização, imagens/digests/arquitetura registrados em `versions.md`; zero ferramenta implícita. CLI-QUALIDADE, DOC-PREPARACAO, E2E-REPRODUCAO. |
| `tests/conftest.py`, `tests/factories/runtime.py`, `tests/fixtures/foundation/` em `apps/backend/` | Nova convenção F02: criar factories técnicas; fixtures de configuração, marcadores e violações de gate usadas somente em cópia temporária. | Arquivos legíveis, factories geram estado isolado e cada violação é válida para seu teste. Não presumir fixtures preexistentes. |
| `tests/fixtures/foundation/cases.json` | Criar catálogo sem segredos reais: cenário, chave ausente/inválida, erro esperado, tipo de violação e gate esperado; valores privados/canários gerados em runtime. | Formato conferido pelas factories; CLI-INICIO/QUALIDADE e E2E-LOGS. |
| `versions.md`, `environment.md`, `operations.md` junto desta feature | Produzir durante implementação, com comandos reais e resultados sanitizados. | Origem/versões, preparação, diagnóstico, recursos e limpeza reproduzíveis. DOC-PREPARACAO-01–02. |

### Configuration

| Entrada | Preparação | Verificação / consequência |
|---|---|---|
| Identidade e diretório privado | `GARIMPEI_ENV=eval`, `GARIMPEI_INSTANCE` exclusivo e manifesto/lock próprios em cenário descartável; dev usa identidade estável da spec. | Bancos/labels/volumes/PIDs do cenário conferidos antes de ações; nomes/bind devem obedecer à spec. |
| Segredos técnicos | Gerar/exportar privadamente `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `WAHA_API_KEY`; arquivo opcional privado é lido somente pelo bootstrap central. | Presença e formato, sem revelar valor. Cenários de ausência removem uma chave deliberadamente; nenhum default secreto fictício. |
| Portas, tempos e logs | Preparar valores válidos da spec §3, porta explícita ocupada e valores inválidos pelos fixtures controlados. | Defaults técnicos e precedência comprovados; saída não altera chaves extras ou segredos. |
| Configuração de testes | Settings próprios sem I/O no carregamento; banco de testes `garimpei_test_<hash>`, diretórios e volumes marcados. | Antes de pytest, confirmar destino e propriedade. Não permitir testes/limpeza no banco contínuo. |
| Limpeza descartável | Identidade eval, marcador de descartável e autorização para recursos do cenário atual. | Ausência de qualquer condição faz `--clean` recusar; parada comum preserva recursos persistidos. |

### External dependencies

- Registro de pacotes/imagens acessível na preparação explícita; indisponibilidade ou digest/arquitetura incompatível fica registrada e bloqueia a instalação dependente. Não se assume internet necessária durante gates com dependências já preparadas.
- WAHA local real para prontidão e retenção; sessão autenticada, conta e destinatário não são pré-requisitos F02. Saúde do serviço não significa envio comprovado.
- Testes isolados de diagnóstico podem usar `UnavailableDatabaseProbe` e `UnavailableWahaProbe`, fakes nomeados. Eles não substituem PostgreSQL, fila, worker ou WAHA reais nos itens que os exigem.

## Quality gates

Todos os grupos precisam passar, com comandos, escopo e códigos explícitos. As interfaces abaixo devem ser implementadas pela F02; escrevê-las não é evidência de execução. `node scripts/run-gates.mjs` é a única entrada canônica dos seis grupos de backend da spec §7; não executar validadores TypeScript como aprovação Python.

- **Seis gates Python** — `node scripts/run-gates.mjs` — tipos/mypy, lint/Ruff+djLint, limites/Import Linter, arquitetura, ciclos/Grimp e código/dependências não usados/Vulture+deptry; nenhum grupo vazio, ausente ou com sucesso fixo. Comandos exatos da spec §7, na ordem, sem instalação implícita.
- **Testes Python** — `uv run --frozen --no-sync pytest` em `apps/backend/` — unitários, PostgreSQL/fila/HTTP, lifecycle e controles negativos com pré-requisitos preparados; nenhum cenário obrigatório omitido por skip de serviço ausente.
- **Registro Django** — `uv run --frozen --no-sync python manage.py check` em backend — configuração e registro corretos.
- **Migrations versionadas** — `uv run --frozen --no-sync python manage.py makemigrations --check --dry-run` em backend — nenhuma diferença ORM sem migration.
- **Schema instalado** — `./scripts/migrate-dev.sh --check` na raiz — nenhuma migration pendente no banco próprio preparado.
- **Estáticos** — `uv run --frozen --no-sync python manage.py collectstatic --noinput` em backend — assets locais preparados; teste verifica origem/hash/licença do HTMX.
- **Build** — `uv build --no-build-isolation` em backend — wheel/sdist com backend de build já provisionado e travado; erro não é convertido em sucesso.
- **Regressão do harness** — `node --test scripts/test/harness.test.mjs` — intenção das regressões preservada e expectativas Python adaptadas.
- **Estrutura do harness** — `node scripts/check-harness.mjs` — fontes/recursos/configuração/sintaxe/progresso válidos, sem substituir gates do produto.

Antes de comandos de integração, preparar explicitamente o ambiente descartável do contrato. Falta de configuração/runtime/driver bloqueia a execução; erro de pré-requisito 64 nunca equivale a gate aprovado. Nenhum valor secreto entra na evidência dos comandos.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F02-AC01**: stack, persistência, requisitos locais e comandos de preparação estão documentados com base nas decisões registradas; instalação e inicialização podem ser reproduzidas no ambiente definido. | DOC-PREPARACAO-01, DOC-PREPARACAO-02, E2E-REPRODUCAO-01, CLI-MIGRACAO-01, CLI-MIGRACAO-02, CLI-MIGRACAO-03, WRK-FILA-01 |
| **F02-AC02**: `init.sh` inicia web e worker, verifica sua prontidão e as dependências previstas na etapa; `stop.sh` encerra seus processos, respeitando isolamento de portas e prefixo `garimpei_`, preservando dados e sessão WAHA na parada normal. | CLI-INICIO-01, CLI-PARADA-01, CLI-PARADA-02, CLI-PARADA-03, API-SAUDE-02, API-SAUDE-03, WRK-FILA-01, WRK-FILA-02, WRK-FILA-03, E2E-REPRODUCAO-01, E2E-ISOLAMENTO-01, E2E-PRESERVACAO-01, E2E-PROPRIEDADE-01, E2E-LIMPEZA-01 |
| **F02-AC03**: arquitetura, configuração central, DI e logs seguem `AGENTS.md`; a entrada de gates definida no contrato executa e aprova as verificações de tipos, lint, limites de dependências, arquitetura, ciclos e código/dependências não utilizados adequadas a Python, além dos testes aplicáveis. Os comandos e suas evidências são explícitos; verificações ausentes ou não executadas permanecem pendentes. | CLI-QUALIDADE-01, CLI-QUALIDADE-02, CLI-QUALIDADE-03, E2E-COMPOSICAO-01, E2E-LOGS-01, E2E-TRANSACAO-01, E2E-TRANSACAO-02, DOC-PREPARACAO-01 |
| **F02-AC04**: configuração obrigatória ausente ou recurso indisponível impede declarar inicialização bem-sucedida e produz diagnóstico sem expor segredos. | CLI-INICIO-02, CLI-INICIO-03, CLI-INICIO-04, API-SAUDE-01, API-SAUDE-03, API-SAUDE-04, E2E-FALHA-01, E2E-LOGS-01 |

## HTTP API

**Verification mode:** Enviar requisições HTTP reais ao web da instância própria e conferir status, headers e corpo; falhas de dependência são preparadas antes de cada ação. Sem consulta ou mutação de dados pelo GET.

### Saúde e prontidão

#### `API-SAUDE-01` — Vida sem falsa prontidão

- given: web vivo e banco ou WAHA indisponível em ambiente próprio.
- when: enviar GET `/health`.
- then:
  - HTTP 200 com body `{"status":"alive"}`.
  - Content-Type é application/json.
  - Cache-Control é no-store.
  - O corpo não declara prontidão das dependências.

#### `API-SAUDE-02` — Execução integralmente pronta

- given: schema atualizado, worker próprio consumindo probes recentes do run ativo e WAHA saudável.
- when: enviar GET `/health/ready`.
- then:
  - HTTP 200 e body.status é `ready`.
  - body.environment_id e body.run_id correspondem à execução atual.
  - body.checks contém database, migrations, worker e waha em `ready`.
  - Cache-Control é no-store.

#### `API-SAUDE-03` — Dependência obrigatória degradada

- given: uma variante do cenário: banco inacessível; migration pendente; worker parado/probe expirado há mais de 15 s; ou WAHA indisponível, mantendo web vivo.
- when: enviar GET `/health/ready`.
- then:
  - HTTP 503 e body.status é `not_ready` em até 10 s.
  - O check afetado é `unavailable`, inclusive checks dependentes do banco quando ele falha.
  - body.error.code é `DEPENDENCY_UNAVAILABLE`.
  - O corpo não contém DSN, senha, chave ou exceção bruta.
- notes: Executar as quatro variantes; sessão WhatsApp não pareada não constitui esta falha de serviço.

#### `API-SAUDE-04` — Fronteira local e método

- given: web disponível e nenhuma ação mutável necessária.
- when: enviar uma variante: GET `/health` com Host não permitido, ou OPTIONS `/health/ready` com Host permitido.
- then:
  - Host não permitido responde HTTP 400.
  - OPTIONS ao health responde HTTP 405.
  - Nenhuma variante confirma prontidão ou expõe detalhes privados.
- notes: Executar cada variante separadamente; o status depende da variante.

## CLI

**Verification mode:** Executar os comandos públicos no ambiente próprio e verificar stdout/stderr, código de saída e prazo; efeitos que exigem inspeção de banco/processos/volumes estão nos itens E2E/Worker.

### Inicialização

#### `CLI-INICIO-01` — Confirmação de ambiente pronto

- given: dependência F01 encerrada e configuração/ferramentas/serviços da F02 válidos.
- when: executar `./scripts/init.sh`.
- then:
  - Exit 0 dentro do timeout de início configurado.
  - Saída legível identifica web/worker prontos e identidade da instância.
  - URLs anunciadas usam loopback.
  - Nenhum segredo ou DSN com senha aparece na saída.

#### `CLI-INICIO-02` — Configuração obrigatória inválida

- given: uma chave obrigatória ausente ou valor não secreto fora do formato, com canários privados nas demais entradas; casos da spec §3 preparados separadamente.
- when: executar `./scripts/init.sh`.
- then:
  - Exit 64.
  - Diagnóstico indica chave e formato esperado.
  - Valor inválido não secreto é identificável quando disponível.
  - Valores secretos/canários não aparecem.
  - Não há mensagem Ready.

#### `CLI-INICIO-03` — Ferramenta ou instalação ausente

- given: uma ferramenta obrigatória indisponível ou scaffold/lock ausente em cópia de avaliação.
- when: executar `./scripts/init.sh`.
- then:
  - Exit 64 e nome do pré-requisito ausente.
  - Não há fallback npm/Prisma ou declaração de ambiente pronto.
  - Não há instalação silenciosa de ferramenta de sistema.

#### `CLI-INICIO-04` — Recurso indisponível

- given: uma variante: porta explícita ocupada por processo alheio; PostgreSQL sem prontidão; WAHA sem prontidão; imagem/digest incompatível; ou lock da mesma instância ativo.
- when: executar `./scripts/init.sh`.
- then:
  - Exit 1, dentro do timeout quando aplicável.
  - Diagnóstico identifica recurso/classe da falha sem segredo.
  - Não há mensagem Ready.
- notes: Executar todas as variantes, sem contornar a falha por recurso alternativo implícito.

### Parada e limpeza

#### `CLI-PARADA-01` — Parada normal

- given: ambiente próprio iniciado e tarefas técnicas de curta duração.
- when: executar `./scripts/stop.sh`.
- then:
  - Exit 0 no prazo de parada configurado quando os recursos encerram normalmente.
  - Saída identifica processos e serviços próprios encerrados.
  - Não declara remoção de banco, volumes ou sessão.

#### `CLI-PARADA-02` — Parada repetida ou encerramento incompleto

- given: uma variante: ambiente já parado, ou processo próprio controlado excede o prazo de parada.
- when: executar `./scripts/stop.sh`.
- then:
  - Ambiente já parado retorna exit 0.
  - Prazo excedido retorna exit 1 com diagnóstico de encerramento incompleto.
  - Nenhuma tarefa interrompida é anunciada como concluída.
- notes: Executar cada variante; não exigir falha simulada de processo pessoal.

#### `CLI-PARADA-03` — Negação de limpeza indevida

- given: uma variante: ambiente dev, propriedade desconhecida, ausência de marcador descartável ou sessão real/desconhecida.
- when: executar `./scripts/stop.sh --clean`.
- then:
  - Exit 64 antes de qualquer remoção.
  - Saída informa condição de limpeza não satisfeita.
  - Não anuncia limpeza concluída.
- notes: A autorização de limpeza do próprio cenário eval não se estende a outros recursos.

### Migrations

#### `CLI-MIGRACAO-01` — Verificação sem aplicação implícita

- given: banco próprio conectado com uma variante: migrations pendentes ou schema atualizado.
- when: executar `./scripts/migrate-dev.sh --check`.
- then:
  - Exit 1 e diagnóstico de pendência na primeira variante.
  - Exit 0 e diagnóstico de schema atualizado na segunda variante.
  - A saída não declara aplicação/criação de migration.

#### `CLI-MIGRACAO-02` — Aplicação repetível e uso inválido

- given: banco próprio e migrations versionadas, ou uma variante de argumentos inválidos.
- when: executar a variante de `./scripts/migrate-dev.sh --apply`, ou argumento inválido.
- then:
  - Aplicação válida retorna exit 0 após schema atualizado.
  - Reaplicação ao schema atualizado retorna exit 0 sem conflito.
  - Argumento inválido retorna exit 64 com uso correto.
  - Diagnóstico não expõe credenciais.

#### `CLI-MIGRACAO-03` — Criação de migration sem aplicar banco

- given: cópia própria com alteração ORM técnica válida, banco identificado e nome de migration válido.
- when: executar `./scripts/migrate-dev.sh --make <nome>`.
- then:
  - Exit 0 com identificação da migration local criada.
  - Nenhuma aplicação de migration ao banco é anunciada.
  - Nome inválido em variante separada retorna exit 64 com formato esperado.
- notes: Confrontar o schema inalterado no teste de integração; a árvore canônica não é modificada para gerar fixtures.

### Qualidade

#### `CLI-QUALIDADE-01` — Seis grupos reais

- given: implementação válida com ferramentas travadas e entradas não vazias preparadas.
- when: executar `node scripts/run-gates.mjs`.
- then:
  - Exit 0.
  - Saída identifica os seis grupos Python da spec §7 e comandos executados.
  - Cada grupo informa aprovação e escopo analisado não vazio.
  - Saída não atribui aprovação Python aos validadores TypeScript.

#### `CLI-QUALIDADE-02` — Rejeição de violações representativas

- given: cópia temporária válida alterada com exatamente uma violação do catálogo abaixo, sem mudar a árvore original.
- when: executar o comando do gate afetado e sua entrada canônica no cenário correspondente.
- then:
  - O comando afetado retorna código não zero pela violação esperada.
  - A entrada canônica retorna código não zero e não anuncia seis grupos aprovados.
  - O diagnóstico identifica o grupo/arquivo ou dependência responsável.
  - A violação não é ocultada por ignore/exclusão ampla.
- notes: Cada linha/variante do catálogo é obrigatória; comandos isolados evitam que falha anterior mascare a verificação de outro grupo.

| Gate | Violações preparadas separadamente |
|---|---|
| Tipos | Retorno incompatível com anotação explícita em módulo autoral alcançado. |
| Lint | Import não usado; template Django com violação do linter escolhido. |
| Limites | Import de infraestrutura/I/O em domínio; cadeia indireta proibida. |
| Arquitetura | Leitura de ambiente fora do bootstrap; adapter concreto construído em caso de uso; módulo em posição proibida. |
| Ciclos | Dois módulos autorais da mesma camada importam um ao outro. |
| Não utilizados | Função órfã não referenciada; dependência runtime declarada sem consumidor. |

#### `CLI-QUALIDADE-03` — Validação ausente continua pendente

- given: source, ferramenta ou configuração de um dos seis grupos ausente em cópia própria.
- when: executar `node scripts/run-gates.mjs`.
- then:
  - Exit 64 com pré-requisito/grupo identificado.
  - Nenhum download é iniciado.
  - Grupo ausente não aparece aprovado.
  - Não há fallback silencioso para tsc/ESLint/Prisma.

## Worker

**Verification mode:** Preparar probes reais na fila PostgreSQL própria, iniciar/observar consumidores separados e consultar recibos persistidos; usar limite de início da spec, sem rede externa de marketplace/WhatsApp.

### Fila técnica persistente

#### `WRK-FILA-01` — Consumo independente do web

- given: tarefa técnica confirmada no banco, worker próprio disponível e web parado.
- when: liberar o consumo da tarefa técnica.
- then:
  - Há recibo concluído para o probe/run_id esperado dentro do timeout configurado.
  - A conclusão não depende de requisição ou aba web aberta.
  - Nenhuma tarefa de coleta ou mensagem externa é disparada.

#### `WRK-FILA-02` — Retomada de tarefa ainda não iniciada

- given: probe manual confirmado e pendente no PostgreSQL, com worker parado após parada normal.
- when: iniciar novamente o worker dessa instância.
- then:
  - O probe pendente continua disponível para consumo.
  - O recibo correspondente é concluído no prazo configurado.
  - Estado concluído de probe anterior não é apagado para simular instalação nova.
- notes: Não presume recuperação automática de job já em execução após SIGKILL; esse procedimento é documentado separadamente.

#### `WRK-FILA-03` — Duplicata ou execução antiga

- given: duas entregas do mesmo probe/seq e dois consumidores próprios, ou tarefa de controle de run_id antigo com execução atual distinta.
- when: liberar o processamento da variante.
- then:
  - A duplicata produz no máximo um recibo concluído e uma cadeia sucessora de controle.
  - Tarefa antiga não atualiza a prontidão da execução atual.
  - Nenhum estado de alerta WhatsApp é criado ou declarado entregue.
- notes: Executar as duas variantes; a garantia é de efeito técnico local, não de entrega externa exatamente uma vez.

## E2E

**Verification mode:** Operar instâncias descartáveis reais, seguir os comandos documentados e observar HTTP, processos, PostgreSQL, fila, contêineres/volumes e logs sanitizados. Não reutilizar sessão pessoal. Inspecionar apenas recursos marcados do cenário.

### Reprodução e isolamento

#### `E2E-REPRODUCAO-01` — Instalação, prontidão e reinício idempotente

- given: checkout com base integrada, lock/imagens registrados, configuração privada válida e ambiente próprio sem processos/dados anteriores.
- when: seguir o procedimento de preparação e início de `operations.md`.
- then:
  - Web e worker têm processos/grupos próprios distintos, com prontidão real do run ativo.
  - Banco e schema Django/fila estão preparados e identificados por `garimpei_`.
  - WAHA próprio responde saudável sem exigir conta pareada ou envio.
  - Repetir init no estado saudável conserva a instância e não duplica recursos.
  - Nenhum arquivo preexistente de harness/requisitos é substituído pelo scaffold; mesclas necessárias têm evidência de diff/hash.

#### `E2E-ISOLAMENTO-01` — Duas instâncias

- given: duas instâncias descartáveis próprias, inclusive nomes de branch que normalizam igual ou checkouts sem commit.
- when: iniciar ambas conforme documentação.
- then:
  - Identidades, portas, bancos e volumes são distintos.
  - Web/PostgreSQL/WAHA publicam apenas em loopback.
  - Probes/dados/marcadores de uma instância não aparecem na outra.
  - Parar uma instância conserva prontidão e dados da outra.

### Falha e preservação

#### `E2E-FALHA-01` — Início parcial não destrutivo

- given: estado persistente próprio e recurso alheio controlado, com falha induzida durante o início da instância.
- when: executar `./scripts/init.sh`.
- then:
  - O comando falha sem anunciar Ready.
  - Processos/contêineres criados pela tentativa malsucedida são encerrados.
  - Recursos já ativos antes da tentativa não são encerrados por esse rollback.
  - Dados/volumes persistentes e recurso alheio mantêm conteúdo/propriedade.

#### `E2E-PRESERVACAO-01` — Parada e nova execução conservam persistência

- given: probes manuais concluído/pendente e marcador sintético com hash conhecido no volume de sessão próprio.
- when: realizar parada normal e iniciar de novo a mesma instância.
- then:
  - Os processos web/worker anteriores encerraram e a nova execução tem run_id distinto.
  - Banco, volumes, probe concluído e hash do marcador foram preservados.
  - Probe confirmado ainda pendente pode ser retomado pelo worker.
  - Nenhuma sessão real precisou ser copiada, pareada ou desconectada.

#### `E2E-PROPRIEDADE-01` — Proteção de recursos alheios

- given: manifesto com PID reutilizado/alheio ou marcador de propriedade inconsistente, preparado sobre processo controlado do teste.
- when: solicitar parada ou limpeza da instância com esse manifesto.
- then:
  - O comando recusa a ação insegura com diagnóstico e código não zero.
  - O processo/contêiner/banco alheio continua intacto.
  - Nenhuma remoção é autorizada apenas pelo nome do processo ou pela porta.

#### `E2E-LIMPEZA-01` — Limpeza de avaliação própria autorizada

- given: instância eval descartável parada, explicitamente autorizada, com marcadores de propriedade e sessão sintética, mais uma segunda instância própria preservável.
- when: executar `./scripts/stop.sh --clean` para a instância descartável.
- then:
  - Somente banco/volumes e marcadores descartáveis dessa instância são removidos.
  - A segunda instância mantém recursos e conteúdo.
  - A saída confirma a identidade limpa sem credenciais.
  - Nenhuma sessão real é removida ou usada neste cenário.

### Composição, transação e logs

#### `E2E-COMPOSICAO-01` — Bootstrap e configuração coerentes

- given: base instalada e banco inicialmente sem tabelas, com configuração extra privada e canários conhecidos.
- when: preparar schema e iniciar web/worker pelas entradas documentadas.
- then:
  - Registro e descoberta de migrations funcionam antes de existirem tabelas técnicas.
  - Web/worker usam a mesma configuração central e adapters compostos explicitamente.
  - Configuração extra/segredos preexistentes não são sobrescritos pelo resolver.
  - Não ocorre coleta, envio ou processo adicional por importação/AppConfig.ready.
- notes: Complementar observação runtime com os gates de arquitetura e provas com fakes nomeados; não basta existir um arquivo chamado main.py.

#### `E2E-TRANSACAO-01` — Commit conjunto de estado e tarefa

- given: transação PostgreSQL real cria probe e enqueue, ainda não confirmados; worker próprio e conexão de observação independentes.
- when: confirmar a transação.
- then:
  - Probe e job ficam visíveis conjuntamente após commit.
  - Worker conclui o recibo do probe confirmado dentro do prazo.
  - Nenhum job é consumido antes de seu estado ser confirmado.

#### `E2E-TRANSACAO-02` — Rollback sem tarefa órfã

- given: mesma preparação transacional, com probe e enqueue ainda não confirmados.
- when: reverter a transação.
- then:
  - Probe e job correspondentes não existem na conexão de observação após rollback.
  - Não há recibo de conclusão para o UUID revertido após um ciclo técnico de observação.
  - Nenhuma chamada externa é executada para compensar a falha.
- notes: Observar por pelo menos 15 s com worker pronto; não substituir enqueue transacional por callback pós-commit em conexão independente.

#### `E2E-LOGS-01` — Diagnóstico sem exposição

- given: execução própria com canários distintos em senha, chave, DSN e cabeçalho; sucesso, falha de dependência e erro inesperado controlado preparados separadamente.
- when: exercer cada cenário técnico e coletar sua saída pública/logs da aplicação.
- then:
  - Linhas de log autorais da aplicação são JSON parseável com timestamp UTC, level, logger, event, environment_id e run_id.
  - Erros têm código/classe estável e correlação com a execução.
  - Canários, credenciais e exceções externas brutas não aparecem em CLI, HTTP ou logs.
  - A saída de CLI permanece texto legível com recurso/chave/formato pertinente.

## Documentação

**Verification mode:** Abrir os documentos da entrega, conferir fontes/versões/comandos e confrontar evidências reais dos itens acima; documento sozinho não prova instalação/prontidão. Código de superfície: DOC.

### Preparação e passagem

#### `DOC-PREPARACAO-01` — Operação reproduzível documentada

- given: base implementada com versões, ambiente e evidências disponíveis.
- when: consultar `versions.md`, `environment.md`, `operations.md` e README/harness adaptados.
- then:
  - Séries/patches, Python/uv/lock, imagens/digests/engine e organização correspondem ao que foi executado.
  - Pré-requisitos/segredos são referências com preparação/verificação explícitas, sem valores privados.
  - Comandos reais de instalação, início, migrations, seis gates, testes/build e parada estão documentados com seus resultados.
  - Limites locais e capacidade medida da base são distinguidos da carga de coletor ainda não implementado.
  - Falta de ferramenta/cenário não aparece como aprovação ou compatibilidade testada.

#### `DOC-PREPARACAO-02` — Limites e recuperação

- given: operação e validação consolidadas, sem implementação das features seguintes.
- when: consultar as instruções de parada, preservação e retomada.
- then:
  - Parada normal e limpeza descartável têm condições e efeitos distintos.
  - Recuperação de tarefas pendentes é distinguida de tarefa interrompida em execução e de entrega externa incerta.
  - Pareamento/envio WAHA, fonte/coleta e decisões de negócio futuras permanecem nos escopos responsáveis.
  - Nenhuma aprovação de F01 ou da fundação é inferida somente destes documentos.
