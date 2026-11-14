# Harness do Garimpei

O harness organiza requisitos → especificação/plano/contrato → implementação → avaliação → correção. O PRD contém F01–F23; o [estado atual](status-atual.md) identifica os aceites e as pendências de F21/F23.

A aplicação usa Python/Django, templates/HTMX, PostgreSQL e worker separado com Procrastinate, sem Redis. O lifecycle e os seis grupos de gates foram implementados em F02. Os templates/helpers TypeScript preservados nas skills são referências históricas, não o runtime do produto.

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

O PRD, a stack e os artefatos de F01/F02 já existem. Para evolução, consulte o estado atual e a feature alvo antes de reutilizar um exemplo de início do zero.

## Ambiente e gates atuais

O lifecycle padrão usa Docker/Compose e ferramentas Unix no host. Pré-requisitos, imagens, segredos e procedimentos atuais estão em [operação F23](F23-docker-completo-e-ia-integrada/operations.md); a [operação F02](F02-fundacao-tecnica-e-ambiente-local/operations.md) preserva a fundação anterior. A configuração autoral é centralizada em `apps/backend/src/garimpei/config/env.py`; o arquivo privado indicado por `GARIMPEI_ENV_FILE` não deve ser versionado. Use caminho absoluto, pois os processos são iniciados de `apps/backend/`.

```bash
export GARIMPEI_ENV_FILE=/caminho/privado/garimpei.env
./scripts/resolve-env.sh
./scripts/init.sh
./scripts/migrate-dev.sh --check
./scripts/stop.sh
```

`init.sh` prepara dependências, migrations e processos próprios, valida prontidão e anuncia a URL resolvida. `stop.sh` conserva dados/volumes/sessões. `--clean` só é permitido para uma instância de avaliação criada como descartável e autorizada; não é uma limpeza genérica de banco de desenvolvimento. Portas, nomes `garimpei_`, manifestos e ownership separam os ambientes. O controle global F22 pausa o trabalho de negócio pela interface; não substitui a parada dos processos.

A entrada do gate continua `node scripts/run-gates.mjs`, executada no contêiner de ferramentas por `./scripts/quality.sh node /app/scripts/run-gates.mjs`. Ela chama as ferramentas Python em `apps/backend/`, sem instalar ferramentas silenciosamente:

| Grupo | Ferramentas efetivas |
|---|---|
| Tipos | mypy estrito em `src`, `tests`, verificadores e `manage.py` |
| Lint e templates | Ruff check/format e djlint para templates Django |
| Limites | import-linter com `.importlinter` |
| Arquitetura | `scripts/quality/check_architecture.py` |
| Ciclos | `scripts/quality/check_cycles.py` |
| Não utilizados | Vulture com whitelist pontual registrada e deptry |

Entradas dinâmicas legítimas de Django ficam documentadas em `quality/entrypoints.json`; a whitelist não autoriza excluir módulos inteiros. Falha, ferramenta ausente ou teste não executado não vira aprovação.

Execute a suíte a partir de `apps/backend/` dentro do contêiner para preservar a resolução dos módulos usados pelos subprocessos:

```bash
./scripts/quality.sh sh -c 'cd /app/apps/backend && uv run --frozen --no-sync pytest'
```

Python, uv, Node e Chromium ficam nas imagens; o host não precisa desses runtimes para operar o caminho padrão. `GARIMPEI_RUNTIME=host` conserva o lifecycle anterior somente quando explicitamente escolhido para compatibilidade das regressões; esse modo exige as ferramentas Python/uv no ambiente que o executa. Os testes de lifecycle antigos rodam nesse modo dentro de `quality`, com serviços próprios, sem tornar o host o runtime padrão do produto.

Testes de integração usam PostgreSQL/serviços próprios em Docker. Temporários privados devem ficar fora do checkout e ter espaço disponível; os backups exigem reserva mínima de 1 GiB. `TMPDIR` ou `--basetemp` podem selecionar outro disco privado, preservando essa proteção. Navegador usa `playwright-cli` com sessão própria; não crie outro projeto E2E para substituir esse fluxo.

## Referências históricas TypeScript

O helper `.agents/skills/clean-arch/scripts/run-gates.mjs` e o gerador abaixo preservam exemplos TypeScript/Fastify/Prisma. Eles não são a entrada canônica de validação ou inicialização do Garimpei Python. Não executar comandos antigos de workspace npm/Prisma como se operassem o banco Django.

## Scaffold sem substituir o harness

O gerador TypeScript preservado está em `.agents/skills/clean-arch/scripts/scaffold.mjs`. Ele protege arquivos existentes; `--force` não é um mecanismo de integração do harness. O comando abaixo demonstra a prévia desse gerador, não a criação da base Django aprovada. A fundação Django já foi integrada pela F02; o comando a seguir apenas demonstra o gerador histórico:

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

Navegação usa `playwright-cli` e Chromium headless isolado, configurado em `.playwright/cli.config.json`. Em nova máquina, instale o CLI e execute `playwright-cli install-browser chromium`. Consulte a skill local para snapshots e screenshots. Node/npm e Git atendem as ferramentas; uv/Python e Docker/Compose atendem a aplicação e os testes que os exigem. tmux é opcional; PostgreSQL e WAHA são dependências operacionais, e Ollama/GPU pertence ao perfil local de inferência.

Skills e plugins locais ficam disponíveis na próxima atualização de descoberta do Codex; se a sessão atual mantiver o catálogo antigo, abra uma nova sessão em `~/dev/garimpei`.

## Validação e proveniência

```bash
node scripts/check-harness.mjs
node --test scripts/test/harness.test.mjs
node --test .agents/skills/clean-arch/scripts/scaffold/test/*.test.mjs
codex plugin list --marketplace fullcycle-claude-marketplace --json
```

Essas verificações cobrem recursos, scripts e instalação local. Para validar a configuração pelo CLI sem iniciar uma sessão, use `codex --strict-config app-server --print-startup-config` e mantenha a saída privada, pois pode conter detalhes locais. Os testes, gates e jornadas da aplicação existem e devem ser executados conforme o contrato e a mudança atual. Execução paralela continua exigindo autorização, especificações e ambientes próprios; os checks do harness não substituem a suíte do produto.

Fontes: [Full Cycle Claude Marketplace](https://github.com/devfullcycle/claude-mkt-place), revisão registrada em `.codex/harness-sources.json`; documentação oficial de [configuração do Codex](https://learn.chatgpt.com/docs/config-file/config-basic), [skills](https://learn.chatgpt.com/docs/extend/skills) e [plugins](https://developers.openai.com/plugins/build).
