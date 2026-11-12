# Harness do Garimpei

O harness do Garimpei organiza o desenvolvimento no Codex: requisitos → especificação/plano/contrato → implementação → avaliação → correção. Skills, scripts, templates e validadores estão contidos no projeto. O PRD define F01–F09. A base Python/Django e o lifecycle real são entregáveis da F02; os comandos atuais estão no guia de operação da feature.

A [stack aprovada](stack.md) é Python/Django, templates/HTMX, PostgreSQL e worker separado com tarefas persistentes, sem Redis inicialmente. O suporte executável descrito abaixo ainda é o harness TypeScript/npm/Prisma preservado. F02 deve adaptá-lo e verificar o suporte a Python antes de concluir a fundação; a decisão documental não torna esses scripts compatíveis.

Para o passo a passo de planejamento e desenvolvimento em projetos novos ou existentes, consulte o [guia de desenvolvimento](guia-desenvolvimento.md).

## Configuração

| Local | Responsabilidade |
|---|---|
| `AGENTS.md` | Regras e fontes canônicas do Garimpei |
| `.codex/config.toml` | Habilitação dos quatro plugins neste projeto |
| `.agents/skills/` | Workflows adaptados e recursos reutilizáveis |
| `.codex/agents/` | Papéis de implementação, avaliação e correção, disponíveis quando houver delegação autorizada |
| `scripts/` | Ambiente, gates, instalação e verificação do harness |
| `.playwright/cli.config.json` | Chromium headless e sessão de navegador isolada |
| `docs/prd_progress.json` | Estado e histórico das features do PRD |
| `.codex/harness-sources.json` | Origem, revisão e versões dos plugins Full Cycle |

Modelo, esforço de raciocínio, permissões, MCPs e hooks ai-memory são herdados da configuração pessoal existente. O projeto já está marcado como confiável no Codex local. Em outra máquina, a confiança é uma escolha local do usuário; o instalador não muda permissões.

O Codex descobre skills de projeto em `.agents/skills/`. Os pacotes Full Cycle são instalados pelo CLI; as quatro skills adaptadoras neste repositório traduzem os comandos/agentes originalmente escritos para Claude. As adaptações não dependem do binário `claude` ou de seu `Task` tool.

## Começar a definir etapas

1. Descreva produto, público, problema e limites. Use `$prd-writer` para elaborar `docs/PRD.md` com IDs, dependências, critérios de aceite e ondas.
2. Use `$spec-writer F01` para produzir `docs/F01-slug/spec.md`, `plan.md` e `contract.md`.
3. Na etapa de fundação, integre a base Django conforme a stack aprovada. Os templates preservados incluem TypeScript/Fastify, Next.js e PostgreSQL/Prisma; sua presença não os torna a escolha do produto. A adaptação dos scripts, skills e validadores faz parte de F02.
4. Use `$implement-feature F01` para apenas implementar ou `$implement-and-evaluate F01` para o ciclo completo. Use `$evaluator F01` e `$fix-runner` separadamente quando necessário.
5. Peça `$implement-and-evaluate-tmux wave N` somente quando quiser executar uma onda em paralelo. Fundações com arquivos comuns permanecem sequenciais.

O PRD e a direção de stack estão definidos. F01 deve esclarecer a viabilidade das integrações antes da execução de F02; o escopo da investigação prática ainda precisa ser definido.

## Ambiente e gates atuais

A F02 adapta `init.sh`, `stop.sh`, `resolve-env.sh`, `migrate-dev.sh` e a entrada `node scripts/run-gates.mjs` à base Python. Preparação, segredos privados, imagens fixadas, instâncias, prontidão, retenção e comandos executáveis: [operação F02](F02-fundacao-tecnica-e-ambiente-local/operations.md). Sem scaffold/lock ou ferramenta, as entradas atuais retornam 64; não anunciam ambiente pronto. Os parágrafos abaixo sobre npm/Prisma e o runner da skill descrevem o suporte TypeScript preservado, que não é executado pelo lifecycle/gates Python.

## Referência histórica do ambiente e gates TypeScript

```bash
./scripts/init.sh
./scripts/stop.sh
node scripts/run-gates.mjs
./scripts/migrate-dev.sh -- --name <mudanca>
```

Antes do scaffold, `init.sh` informa que apenas o harness está pronto, sem gerar estado de aplicação. O runner de gates retorna erro de pré-requisito (código 64) enquanto o backend/dependências não existirem. Isso não representa uma avaliação da aplicação.

Na implementação atual, os scripts esperam workspaces npm em `apps/backend` e, opcionalmente, `apps/web`. A presença de `apps/backend/prisma/schema.prisma` habilita o ciclo de banco; a presença do package da web habilita o frontend. Esse suporte precisa ser substituído/adaptado em F02 para web/worker Python e migrations Django/fila. As exigências atuais de `dev`, `/health`, `prisma:generate` e workspaces descrevem o harness preservado, não um scaffold Python pronto.

O ambiente usa banco `garimpei_<branch-normalizada>` e procura portas livres a partir de 4000/3000 com offset por branch. Portas, logs e PIDs ficam sob controle dos scripts; variáveis adicionais existentes são preservadas. PostgreSQL já ativo ou Docker Compose podem ser usados pelos scripts de ambiente. Os scripts de banco usam credenciais locais de desenvolvimento e pressupõem ambiente descartável.

`stop.sh` encerra processos identificados deste checkout. `stop.sh --clean` também apaga o banco de desenvolvimento da branch quando habilitado; não o use em bancos compartilhados ou fora do escopo autorizado.

O runner TypeScript preservado em `clean-arch/scripts/run-gates.mjs` executa TypeScript, ESLint, Dependency Cruiser, Architecture, Madge e Knip. O wrapper da raiz valida pré-requisitos e direciona para o backend. F02 deve definir e implementar cobertura equivalente adequada a Python, conforme [stack.md](stack.md), incluindo testes e inicialização real. Até essa adaptação e execução, os gates da aplicação Python permanecem pendentes.

## Scaffold sem substituir o harness

O gerador TypeScript preservado está em `.agents/skills/clean-arch/scripts/scaffold.mjs`. Ele protege arquivos existentes; `--force` não é um mecanismo de integração do harness. O comando abaixo demonstra a prévia desse gerador, não a criação da base Django aprovada. Para o produto, gerar a base apropriada em temporário e integrá-la seletivamente é trabalho de F02:

```bash
node .agents/skills/clean-arch/scripts/scaffold.mjs Garimpei --yes --shape backend --no-db --no-install --no-gates --no-git --dry-run
```

Escolha `backend-n-nextjs`/`--db` somente conforme a fundação definida. Preserve `AGENTS.md`, README, `.gitignore`, `.codex/`, `.agents/` e os scripts já adaptados ao integrar. Os templates também mantêm uma opção de compatibilidade `CLAUDE.md` para outros consumidores; o arquivo canônico do projeto é `AGENTS.md`.

## Progresso

`docs/prd_progress.json` usa `schema_version: 1`. O schema detalhado está em `.agents/skills/prd-writer/references/prd-format.md`. O PRD é a fonte de nomes, prioridades, dependências e ondas; o JSON registra execução.

| Status | Significado |
|---|---|
| `pending` | Etapa definida, ainda não iniciada |
| `implementing` | Implementação em andamento |
| `implemented` | Pronta para avaliação |
| `done` | Contrato completo aprovado pelo avaliador |
| `fail` | Falha terminal com motivo registrado |
| `pr-blocked` | Avaliação limpa; integração de PR autorizada bloqueada |
| `removed` | Etapa retirada do PRD, mantendo histórico |

Escreva apenas a entrada da feature em execução, preservando as demais e os campos de origem do PRD. Faça escrita atômica com temporário e rename; em uma mesma worktree, serialize o read-modify-write inteiro. Em paralelo, cada worktree mantém seu JSON e o coordenador consolida as entradas individuais, evitando perda de atualizações.

Datas usam UTC/RFC 3339. `cycles` conta correções; `failure_reason` descreve falha/bloqueio em até 200 caracteres. Ao concluir, grave `completed_at`, `report_path` e limpe `failure_reason`; ao reabrir uma etapa, limpe `completed_at`. Nunca use uma aprovação antiga como evidência da execução atual.

O avaliador gera `eval-report-<timestamp>.md`; o ciclo completo gera `orchestration-<timestamp>.md`. PASS exige evidência; BLOCKED/MANUAL/SKIPPED não equivalem a aprovação. Contratos e relatórios anteriores permanecem preservados.

## Plugins e ferramentas

Os quatro plugins e exemplos de uso estão em [plugins.md](../plugins.md). Para repetir a instalação autorizada em outro ambiente com Codex CLI compatível:

```bash
./scripts/setup-codex.sh
```

O script registra o marketplace na revisão de referência e instala os pacotes no perfil local do Codex. Em marketplace previamente registrado, o CLI pode reutilizar o registro existente; confira a origem/revisão antes de atualizar. A instalação não altera MCPs nem conexões externas.

Navegação usa `playwright-cli` e Chromium headless isolado, configurado em `.playwright/cli.config.json`. Em nova máquina, instale o CLI e execute `playwright-cli install-browser chromium`. Consulte a skill local para snapshots e screenshots. Node, npm e Git atendem o harness; `lsof`/`curl` atendem o lifecycle. tmux é opcional. PostgreSQL/Docker e renderizadores de diagramas serão necessários apenas nas etapas que os utilizarem.

Skills e plugins locais ficam disponíveis na próxima atualização de descoberta do Codex; se a sessão atual mantiver o catálogo antigo, abra uma nova sessão em `~/dev/garimpei`.

## Validação e proveniência

```bash
node scripts/check-harness.mjs
node --test scripts/test/harness.test.mjs
node --test .agents/skills/clean-arch/scripts/scaffold/test/*.test.mjs
codex plugin list --marketplace fullcycle-claude-marketplace --json
```

Essas verificações cobrem recursos, scripts e instalação local. Para validar a configuração pelo CLI sem iniciar uma sessão, use `codex --strict-config app-server --print-startup-config` e mantenha a saída privada, pois pode conter detalhes locais. Testes/gates/jornadas da aplicação serão executados após sua criação. O fluxo paralelo completo precisa de features especificadas, um commit base e ambientes reais; não há execução de produto nesta preparação.

Fontes: [Full Cycle Claude Marketplace](https://github.com/devfullcycle/claude-mkt-place), revisão registrada em `.codex/harness-sources.json`; documentação oficial de [configuração do Codex](https://learn.chatgpt.com/docs/config-file/config-basic), [skills](https://learn.chatgpt.com/docs/extend/skills) e [plugins](https://developers.openai.com/plugins/build).
