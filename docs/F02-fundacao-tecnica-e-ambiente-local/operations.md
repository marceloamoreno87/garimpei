# F02 — Operação local

Aplicação técnica Django em `apps/backend/`, web Gunicorn e worker Procrastinate separados; PostgreSQL/WAHA em contêineres próprios. Sem coletor, conta de marketplace, pareamento WhatsApp ou tela de produto nesta etapa. A primeira fonte aprovada para F04 é Facebook Marketplace.

## Preparação

Linux/WSL2 x86_64, Git/Bash/Node, Docker com Compose e uv **0.11.24** disponíveis. Consulte [versions.md](versions.md) para as versões/digests resolvidos e [environment.md](environment.md) para resultados. O início não instala ferramentas de sistema. Os gates não sincronizam nem baixam dependências.

Na raiz:

```bash
uv python install 3.13.14
uv sync --project apps/backend --locked --all-groups
docker pull postgres:17.11@sha256:ff87138949ad9a46f32ff23bd6852b52ce024a13dffe9b4087be98292cdd3b4f
docker pull devlikeapro/waha:gows-2026.10.1@sha256:1f7faeb0227ad5edb5711f7058bfce807ea65e5f92234af0778e4db140f6eb46
```

Prepare segredos privados uma vez, sem imprimir seu conteúdo. O exemplo recusa sobrescrever arquivo existente:

```bash
uv run --project apps/backend --frozen --no-sync python - <<'PYTHON'
import os
import secrets
from pathlib import Path
folder = Path('.runtime')
folder.mkdir(exist_ok=True, mode=0o700)
file = folder / 'development.env'
fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as output:
    for key in ('DJANGO_SECRET_KEY', 'POSTGRES_PASSWORD', 'WAHA_API_KEY'):
        output.write(key + '=' + secrets.token_urlsafe(40) + '\n')
PYTHON
export GARIMPEI_ENV_FILE="$PWD/.runtime/development.env"
./scripts/init.sh
```

Não executar `source` nesse arquivo: ele é dado `KEY=value`, não shell. Ambiente explícito prevalece sobre arquivo privado; chaves extras não são regravadas. Segredos não são aceitos como defaults fixos nem gravados no manifesto. `.runtime/` e `.venv/` estão ignorados. Não versionar cookies, QR codes ou arquivos privados.

## Início, prontidão e configuração

`init.sh` sincroniza o lock, reserva a operação da instância, usa imagens já preparadas, aplica migrations e inicia os dois grupos de processo. Exit 0/`Ready` exige banco autenticado, schema atualizado, recibo recente do worker e WAHA `/health` saudável/autenticado. Uma porta aberta ou PID vivo não basta. Repetir init saudável conserva run_id, processos e dados. Falha retorna 1; configuração/ferramenta/scaffold ausente retorna 64. Logs privados ficam em `.runtime/<environment_id>/{web,worker}.log`.

`./scripts/resolve-env.sh` mostra apenas identidade, banco e portas. Dev deriva nome de checkout canônico e branch com hash; o checkout atual sem commit também é suportado. Cada início após parada recebe run_id UUID novo. Portas automáticas evitam a faixa efêmera do Windows/WSL e preservam a seleção no manifesto. Porta explícita ocupada é erro, sem encerrar seu proprietário ou trocar de porta silenciosamente. Todos os binds são loopback.

As chaves e limites completos estão na [spec §3](spec.md#configuração-central). Para execução descartável, definir `GARIMPEI_ENV=eval`, `GARIMPEI_INSTANCE=<nome_exclusivo>` e iniciar com `./scripts/init.sh --disposable`; usar segredos próprios. Não reutilizar sessão ou banco pessoal em avaliação. Fila e banco não são compartilhados entre instâncias.

- `GET /health`: vida, HTTP 200, sem consultar dependências.
- `GET /health/ready`: 200 somente com os quatro checks prontos; 503 com código `DEPENDENCY_UNAVAILABLE` na degradação. Corpo inclui instância/run e não inclui segredos.
- Host desconhecido: 400; OPTIONS: 405. Não há login do Garimpei ou endpoint de negócio.

Os logs web/worker são JSON com correlação e códigos estáveis; texto de exceção, DSN, cabeçalhos e mensagem externa bruta não são serializados. CLI escreve diagnóstico legível. O adaptador do worker normaliza inclusive os avisos textuais do CLI oficial. Diagnosticar pelo código/classe/recurso; não publicar arquivos privados completos.

## Migrations e tarefa técnica

Na raiz, com a mesma configuração privada:

```bash
./scripts/migrate-dev.sh --check
./scripts/migrate-dev.sh --apply
./scripts/migrate-dev.sh --make nome_em_snake_case
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py runtime_probe --wait
```

`--check` não aplica; `--make` cria migration local e não altera o banco; `--apply` é repetível. O wrapper exige propriedade/instância conhecida e nunca direciona para um banco externo pela simples existência de uma porta.

`runworker` delega ao worker Django oficial depois do registro explícito de tarefas. Controle técnico a cada 5 s, validade de 15 s e timeout local não definem frequência de coleta/alerta. Probe manual é independente do controle e pode retomar com run_id antigo. Tarefa de controle antiga não renova prontidão; duplicata não abre segunda cadeia sucessora.

Estado e enqueue usam a conexão psycopg da transação ORM. O DjangoConnector padrão não aceita conexão externa explícita: a composição usa SyncPsycopgConnector dedicado no enqueue, mantendo o worker oficial. Não substituir por `on_commit` com outra conexão: o teste real observa invisibilidade/commit/rollback nas duas conexões.

## Parada, retenção e recuperação

```bash
./scripts/stop.sh
```

Parada normal marca o run encerrado, aguarda grupos próprios e para contêineres, preservando banco, volumes e sessão. Repetir parada retorna 0. PID, criação, grupo, comando, cwd, labels e checkout são conferidos antes de sinalizar; divergência recusa a ação. Timeout encerra apenas grupo próprio e retorna falha, sem declarar tarefa interrompida concluída. Início parcial desfaz apenas recursos iniciados pela tentativa, preservando os que já estavam ativos.

Tarefa confirmada ainda não iniciada continua no PostgreSQL e foi testada após reinício. Job em execução após SIGKILL é situação diferente: não há recuperação automática universal prometida. Conservar ID/estado e diagnosticar com as ferramentas oficiais do Procrastinate antes de decidir retry; política para tarefas de negócio fica em F04/F09. Nada nesta fundação confirma entrega WhatsApp ou efeito externo exatamente uma vez.

`./scripts/stop.sh --clean` exige instância **eval**, descarte explicitamente marcado, propriedade íntegra e sessão sintética. Recusa dev, marcador ausente, sessão real/desconhecida e arquivos ou metadados de sessão que não correspondam ao cenário sintético. A inspeção privada usa os metadados SQLite do próprio WAHA, não substitui PostgreSQL da aplicação. Limpeza remove somente contêineres, volumes e redes próprias depois das verificações. Redes também recebem labels de instância/checkout; endpoints alheios impedem remoção. A parada normal conserva a rede para a mesma instância, e --clean a remove. Não executar prune global. Não usar em ambiente contínuo; parada normal nunca remove volumes.

## Qualidade, testes e build

Na raiz:

```bash
node scripts/run-gates.mjs
node --test scripts/test/harness.test.mjs
node scripts/check-harness.mjs
```

Em `apps/backend/`:

```bash
uv run --frozen --no-sync pytest
DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --frozen --no-sync python manage.py check
DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --frozen --no-sync python manage.py makemigrations --check --dry-run
DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --frozen --no-sync python manage.py collectstatic --noinput
uv build --no-build-isolation
```

Pytest prepara instâncias PostgreSQL/WAHA reais próprias e exige Docker/imagens; ausência é falha, sem skip. Apenas os cenários explicitamente negativos usam cópias/recursos defeituosos. Gates executam tipos, lint/templates, limites, arquitetura, ciclos e não utilizados; lista exata na spec §7 e saída por grupo na entrada canônica. Asset HTMX local tem hash e licença testados. Templates/estáticos são fundação; servir as telas e suas jornadas pertence às features de interface.

Não executar os validadores TypeScript preservados para declarar Python aprovado. `scripts/spawn-detached.mjs` e o acervo TypeScript permanecem disponíveis para o harness, mas o lifecycle Python usa seu supervisor próprio e não chama npm/Prisma.
