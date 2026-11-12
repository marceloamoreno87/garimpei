# F02 — Relatório de implementação

**Run:** `2026-11-10T19-52-16Z`. **Estado:** `implemented`, pronto para avaliação integral. Fases 5/5 executadas nesta sessão, sem delegação. Nenhum commit, push ou PR. Spec/plano/contrato preservados; autorização atual de implementação substitui o limite histórico da geração da especificação.

## Entrega e propósito

Base Django 5.2/Python 3.13 integrada em `apps/backend/`, com PostgreSQL 17, fila Procrastinate 3.10 e worker separado. Configuração central tipada, composição explícita, contratos/caso de uso puro de prontidão, modelos/migrations técnicos, health HTTP, logs JSON e HTMX local com hash/licença. Não há coleta, anúncios/interesses, tela de produto, conta de marketplace ou envio WhatsApp.

O lifecycle Python dos scripts canônicos verifica prontidão real, mantém instância/run, identifica grupos de processo/contêineres/volumes e preserva dados na parada normal. Início parcial desfaz apenas a tentativa; limpeza depende de propriedade, descarte e ausência de sessão real/desconhecida. Migrações têm check/apply/make distintos. Nenhum source/eval de arquivo .env ou fallback npm/Prisma.

## Fases

| Fase | Resultado / evidência |
|---|---|
| 1 — compatibilidade | PoC real anterior à integração; versions.md, queue-poc.json, digests x86_64 e WAHA 200/status ok. |
| 2 — aplicação e persistência | src/garimpei, manage.py, configuração, composição, models/migration com dependência da fila, comandos runworker/runtime_probe, templates/asset local. |
| 3 — operação | Scripts Python/Compose; propriedade/PID reutilizado, isolamento, timeout, rollback, retenção, marcador sintético e retomada testados. |
| 4 — qualidade | Entrada node scripts/run-gates.mjs executa seis grupos Python reais, sem instalar ferramentas; testes negativos com diagnóstico e cópias próprias. |
| 5 — passagem | versions.md, environment.md, operations.md, README/harness e este relatório; avaliação integral seguinte registra veredito canônico. |

## Pré-requisitos produzidos

`pyproject.toml`, `uv.lock`, `.python-version`, `compose.yaml`, package src, migrations oficiais/aplicação, settings de teste sem banco externo no carregamento, tests/conftest.py, factories/runtime.py e fixtures/foundation/cases.json. Fixtures geram segredos/marcadores próprios em runtime e não deixam Python deliberadamente inválido na árvore canônica.

Seis gates: mypy/django-stubs; Ruff/djLint; Import Linter; AST/registro; Grimp; Vulture/deptry. Entrypoints e exceções de framework são explícitos. Conexão psycopg do ORM fornecida ao conector síncrono de enqueue mantém atomicidade inclusive no worker oficial; não usa callback pós-commit em outra conexão.

## Verificação disponível e avaliação pendente

Resultados preliminares e amostra de recursos em environment.md. A avaliação seguinte deve executar gates, suíte completa atual, check/migrations/estáticos/build, regressões do harness e todos os 32 itens do contrato, com evidência por then. Nenhum item é dispensado por falta de serviço ou ferramenta. Progresso `implemented` não é PASS nem done.

## Arquivos alterados e limites

Novos: apps/backend (aplicação, testes, gates/configuração/vendor), compose.yaml e artefatos F02. Mesclas: scripts/init/stop/resolve-env/migrate-dev, runner de gates, testes do harness, README, gitignore e docs/harness. Apenas F01/F02 têm atualizações de progresso nesta sessão: F01 pela reavaliação prévia da dependência, F02 pelo ciclo solicitado; F03–F09 preservadas.

Sem commit base, foi usado o checkout autorizado com baseline de hashes; nenhuma worktree/commit foi criado artificialmente. Faltas de geografia/frete, identidade/histórico, comparáveis e estratégia de coleta continuam nos escopos F03/F04/F06/F09. A fundação não assume cookies nem reduz requisitos do MVP.

## Correção após avaliação inicial — ciclo 1

A avaliação inicial executou 72 testes/gates com sucesso, mas a inspeção suplementar revelou 28 redes Compose órfãs e esgotamento de pools, reprovando E2E-LIMPEZA-01/E2E-ISOLAMENTO-01. O fix-runner reproduziu com teste público --clean que falhou antes da correção. Redes agora têm labels de instância/checkout e seus endpoints/propriedade são verificados antes da remoção; limpeza descarta a rede exclusiva e conserva redes alheias. Fixtures negativos também encerram suas redes. A correção não altera spec/plano/contrato. Reavaliação integral necessária.
