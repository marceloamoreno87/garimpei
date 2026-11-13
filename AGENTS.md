# Garimpei

## Escopo e fontes

Este repositório contém a aplicação Django do MVP, com requisitos em `docs/PRD.md`, execução em `docs/prd_progress.json` e síntese em `docs/status-atual.md`. Preserve IDs, dependências e histórico; aprovação documental não altera o estado de implementação das features.

O harness do projeto está em `.agents/skills/`, `.codex/` e `scripts/`. Consulte [docs/harness.md](docs/harness.md) para operação e configuração.

Antes de especificar arquitetura, ambiente, backend ou interface, leia a [stack aprovada](docs/stack.md): Python/Django, templates/HTMX, PostgreSQL e worker separado com tarefas persistentes, sem Redis inicialmente. O lifecycle e os gates Python foram implementados em F02; templates/helpers TypeScript preservados nas skills não definem a stack nem substituem esses comandos.

Requisitos e instruções atuais do usuário prevalecem sobre templates. Use ai-memory conforme as instruções globais para histórico e handoffs; confirme fatos nos arquivos atuais. Aprovação e fonte canônica de requisitos ficam no repositório e na conversa.

## Fluxo de desenvolvimento

- PRD e etapas: use `prd-writer`; preserve IDs `F01`, dependências, prioridades e ondas.
- Especificar uma feature: use `spec-writer`; produza `docs/FXX-slug/{spec,plan,contract}.md`.
- Implementar uma etapa definida: use `implement-feature`. Para o ciclo completo solicitado, use `implement-and-evaluate`, `evaluator` e `fix-runner`.
- Contratos descrevem comportamento observável. Avaliação registra evidências por item; marque `done` somente após avaliação completa e gates aprovados.
- Use `implement-and-evaluate-tmux` somente quando o usuário pedir execução paralela de uma onda. Cada feature usa worktree e ambiente próprios; fundações que alteram arquivos comuns são sequenciais.
- Commit, push, PR, merge e deploy dependem do escopo autorizado na conversa; a instalação deste harness não os autoriza automaticamente.

## Ambiente

Execute `./scripts/init.sh` antes de trabalho que precise da aplicação; use `./scripts/stop.sh` para encerrar seus processos. `stop.sh --clean` remove recursos/dados da instância de avaliação criada como descartável; use apenas nesse ambiente identificado e autorizado.

A aplicação Python está em `apps/backend/`; templates e estáticos ficam em `src/garimpei/infra/http/`, com interface servida pelo Django. Inicie web e worker pelos scripts canônicos; preserve o isolamento de portas e o prefixo de banco `garimpei_`.

## Backend

Leia a skill `clean-arch` antes de alterações no backend. Preserve dependências voltadas às regras de negócio (`domain/` ← `usecase/` ← `infra/`), DI por construtor, composição explícita e configuração central. A arquitetura/F02 mapeiam esses princípios para Python/Django e seus processos web/worker; caminhos e exemplos TypeScript das skills/templates são referências a adaptar. Handlers validam entrada, chamam casos de uso e delegam erros ao tratamento central.

Mantenha módulos pequenos, tipos explícitos e retornos antecipados. Evite `any`, lógica duplicada e mais de dois níveis de indentação. Comente motivos. Mensagens de erro devem informar valor problemático e formato esperado, sem expor segredos.

Cubra regras de negócio e defeitos com testes significativos; use fakes nomeados para I/O externo. Logs de aplicação são JSON estruturado; saída de CLI é texto legível.

F02 implementou comandos Python para tipos, lint/templates, limites de dependências, arquitetura, ciclos e código/dependências não utilizados, além dos testes aplicáveis. Execute todos os gates definidos no contrato antes de concluir backend. A entrada `node scripts/run-gates.mjs` executa os seis grupos Python. O helper TypeScript preservado nas skills não substitui essa entrada. Execute pytest de `apps/backend/` para preservar os imports nos subprocessos. Falha de gate é falha; verificação ausente ou não executada permanece pendente e impede concluir a fundação.

## Frontend

Use `playwright-cli` para navegação e verificação no navegador; leia a skill correspondente. Priorize jornadas críticas e regras de negócio. A direção e as convenções do Garimpei estão em `docs/design/MASTER.md` e `docs/design/implementation.md`; use `frontend-ui-design` para avaliar telas com evidências visuais.

## Arquivos e verificação

Mantenha artefatos de feature junto de sua especificação. Temporários ficam em diretório temporário do sistema ou pasta de execução ignorada, fora da raiz. Segredos ficam no ambiente; nunca em relatórios ou versionamento.

Para verificar o harness sem aplicação: `node --test scripts/test/harness.test.mjs` e `node scripts/check-harness.mjs`. Isso não substitui os gates nem os testes de uma aplicação futura.
