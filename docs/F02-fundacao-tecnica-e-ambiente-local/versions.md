# F02 — Versões e compatibilidade

Preparação executada em 2026-11-10, antes da integração do scaffold. Origem: Django `django-admin startproject` em diretório temporário próprio, Python/uv e registros oficiais. A aplicação final adapta seletivamente essa base à arquitetura do projeto.

| Componente | Versão / artefato validado |
|---|---|
| Python | 3.13.14, CPython instalado pelo uv no espaço do usuário |
| uv | 0.11.24 |
| PostgreSQL | `postgres:17.11@sha256:ff87138949ad9a46f32ff23bd6852b52ce024a13dffe9b4087be98292cdd3b4f` |
| WAHA | `devlikeapro/waha:gows-2026.10.1@sha256:1f7faeb0227ad5edb5711f7058bfce807ea65e5f92234af0778e4db140f6eb46`, linux/amd64, GOWS |
| django | 5.2.19 |
| procrastinate | 3.10.0 |
| psycopg | 3.3.8 |
| psycopg-pool | 3.3.3 |
| gunicorn | 23.0.0 |
| psutil | 7.2.2 |
| django-stubs | 5.2.9 |
| mypy | 1.19.1 |
| ruff | 0.17.4 |
| djlint | 1.49.10 |
| import-linter | 2.16 |
| grimp | 3.19 |
| vulture | 2.16 |
| deptry | 0.25.1 |
| pytest | 9.2.0 |
| pytest-django | 4.14.0 |
| hatchling | 1.33.0 |
| HTMX | 2.0.11, [origem](https://github.com/bigskysoftware/htmx/tree/v2.0.11), SHA-256 `d6fdc75f204e6bdefa99b69bf1e6d4ac69b8a364f77929f45c13476b4000f717`; licença do mesmo tag incluída no vendor |

## Prova anterior à integração

Django migrations oficiais da fila aplicadas em PostgreSQL vazio. Duas conexões demonstraram invisibilidade de estado/job não confirmados e visibilidade conjunta após commit; rollback removeu ambos. Worker invocado pelo comando Django oficial consumiu probe confirmado e encerrou com exit 0. Resultado sanitizado em `evidence/queue-poc.json`. Um erro inicial de argumento `--log-format` não aceito pelo wrapper Django foi corrigido na prova; o comando oficial final usa sua interface válida.

WAHA próprio respondeu HTTP 200 e `status: ok` em `/health` autenticado, sem sessão/QR/envio. A primeira tentativa de resolver tag com ordem incorreta `2026.10.1-gows` retornou not found; API oficial do Docker Hub identificou `gows-2026.10.1` e seu digest. Não houve substituição de engine ou imagem móvel. Health de serviço não comprova autenticação/entrega WhatsApp.

## Integração seletiva

Aceitar da preparação temporária: `pyproject.toml`, `uv.lock`, `.python-version`; adaptar entrada `manage.py` e organização/configuração Django conforme spec. Rejeitar `bootstrap/settings.py`, urls/ASGI/WSGI padrão, SQLite e instruções genéricas geradas. Criar módulos de fundação em `src/garimpei/`; não copiar pasta temporária inteira nem seu venv, segredos, banco ou script de PoC.

Baseline: 467 arquivos preexistentes com SHA-256 em temporário privado antes das alterações. `AGENTS.md`, `.agents/`, `.codex/`, arquitetura e design são preservados. Mesclas intencionais: scripts de ambiente/gates/testes, README, gitignore, harness e artefatos F01/F02/progresso. Não há commit base e não foi criado commit para usar worktree.

## Fontes e limites

[Django 5.2](https://docs.djangoproject.com/en/5.2/), [Procrastinate 3.10.0](https://github.com/procrastinate-org/procrastinate/tree/3.10.0), [Docker Hub WAHA](https://hub.docker.com/r/devlikeapro/waha/tags?name=2026.10.1), [PostgreSQL](https://hub.docker.com/_/postgres), [uv](https://docs.astral.sh/uv/). Licenças das bibliotecas permanecem nas distribuições travadas; HTMX inclui a licença original junto do asset. Combinação inicial testada não é benchmark de capacidade nem prova de todas as condições do contrato.
