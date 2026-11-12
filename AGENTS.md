# Garimpei

## Escopo e fontes

Este repositório está no planejamento do MVP, com requisitos em `docs/PRD.md` e features em `docs/prd_progress.json`. Preserve IDs, dependências e histórico; aprovação documental não altera o estado de implementação das features.

O harness do projeto está em `.agents/skills/`, `.codex/` e `scripts/`. Consulte [docs/harness.md](docs/harness.md) para operação e configuração.

Antes de especificar arquitetura, ambiente, backend ou interface, leia a [stack aprovada](docs/stack.md): Python/Django, templates/HTMX, PostgreSQL e worker separado com tarefas persistentes, sem Redis inicialmente. Os scripts, templates e validadores TypeScript preservados ainda precisam de adaptação em F02; sua presença não define a stack do produto.

Requisitos e instruções atuais do usuário prevalecem sobre templates. Use ai-memory conforme as instruções globais para histórico e handoffs; confirme fatos nos arquivos atuais. Aprovação e fonte canônica de requisitos ficam no repositório e na conversa.

## Fluxo de desenvolvimento

- PRD e etapas: use `prd-writer`; preserve IDs `F01`, dependências, prioridades e ondas.
- Especificar uma feature: use `spec-writer`; produza `docs/FXX-slug/{spec,plan,contract}.md`.
- Implementar uma etapa definida: use `implement-feature`. Para o ciclo completo solicitado, use `implement-and-evaluate`, `evaluator` e `fix-runner`.
- Contratos descrevem comportamento observável. Avaliação registra evidências por item; marque `done` somente após avaliação completa e gates aprovados.
- Use `implement-and-evaluate-tmux` somente quando o usuário pedir execução paralela de uma onda. Cada feature usa worktree e ambiente próprios; fundações que alteram arquivos comuns são sequenciais.
- Commit, push, PR, merge e deploy dependem do escopo autorizado na conversa; a instalação deste harness não os autoriza automaticamente.

## Ambiente

Execute `./scripts/init.sh` antes de trabalho que precise da aplicação; use `./scripts/stop.sh` para encerrar seus processos. Antes do scaffold, `init.sh` apenas informa o estado de preparação. `stop.sh --clean` também remove o banco de desenvolvimento da branch quando Prisma estiver habilitado; use apenas em ambiente descartável autorizado.

A referência do projeto Python é `apps/backend/`; templates e estáticos serão definidos na arquitetura/F02, com interface servida pelo Django. Inicie web e worker pelos scripts de ambiente após sua adaptação; preserve o isolamento de portas e o prefixo de banco `garimpei_`.

## Backend

Leia a skill `clean-arch` antes de alterações no backend. Preserve dependências voltadas às regras de negócio (`domain/` ← `usecase/` ← `infra/`), DI por construtor, composição explícita e configuração central. A arquitetura e F02 devem mapear esses princípios para Python/Django e seus processos web/worker; caminhos e exemplos TypeScript das skills/templates são referências a adaptar. Handlers validam entrada, chamam casos de uso e delegam erros ao tratamento central.

Mantenha módulos pequenos, tipos explícitos e retornos antecipados. Evite `any`, lógica duplicada e mais de dois níveis de indentação. Comente motivos. Mensagens de erro devem informar valor problemático e formato esperado, sem expor segredos.

Cubra regras de negócio e defeitos com testes significativos; use fakes nomeados para I/O externo. Logs de aplicação são JSON estruturado; saída de CLI é texto legível.

F02 deve definir e implementar comandos de validação Python para tipos, lint, limites de dependências, arquitetura, ciclos e código/dependências não utilizados, além dos testes aplicáveis. Execute todos os gates definidos no contrato antes de concluir backend. O runner atual `node scripts/run-gates.mjs` executa ferramentas TypeScript e permanece pendente de adaptação; não comprova validação Python. Falha de gate é falha; verificação ausente ou não executada permanece pendente e impede concluir a fundação.

## Frontend

Use `playwright-cli` para navegação e verificação no navegador; leia a skill correspondente. Priorize jornadas críticas e regras de negócio. Quando o design do Garimpei for definido, salve-o em `docs/design/` e use `frontend-ui-design` para avaliar telas com evidências visuais.

## Arquivos e verificação

Mantenha artefatos de feature junto de sua especificação. Temporários ficam em diretório temporário do sistema ou pasta de execução ignorada, fora da raiz. Segredos ficam no ambiente; nunca em relatórios ou versionamento.

Para verificar o harness sem aplicação: `node --test scripts/test/harness.test.mjs` e `node scripts/check-harness.mjs`. Isso não substitui os gates nem os testes de uma aplicação futura.
