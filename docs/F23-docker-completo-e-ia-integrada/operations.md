# Operação F23 — runtime Docker

Os wrappers usam Bash, ferramentas Unix e Docker/Compose. Python, uv, Node, Gunicorn, Playwright e as ferramentas de qualidade ficam nas imagens. A imagem runtime não contém Docker CLI nem recebe seu socket. O serviço `quality` é uma ferramenta administrativa opt-in: contém Docker CLI, usa rede do host e recebe o socket para executar os testes de lifecycle já existentes. Não publicar esse serviço como aplicação.

## Instância própria

Criar arquivo externo privado, modo 0600, com `GARIMPEI_ENV=eval`, `GARIMPEI_INSTANCE=<identificador [a-z0-9_]{1,40}>`, `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` e `WAHA_API_KEY`. O parser do host trata esse arquivo como dados; não executa seu conteúdo. Para desenvolvimento, usar `GARIMPEI_ENV=dev`; eval exige identificador explícito. Portas podem ser definidas por `GARIMPEI_WEB_PORT`, `GARIMPEI_PG_PORT` e `GARIMPEI_WAHA_PORT`.

```bash
export GARIMPEI_ENV_FILE=/caminho/privado/garimpei.env
./scripts/resolve-env.sh
./scripts/init.sh --disposable  # somente instância eval criada como descartável
./scripts/migrate-dev.sh --check
./scripts/stop.sh
```

`init` constrói a imagem, aguarda PostgreSQL saudável, aplica migrations/collectstatic sob advisory lock PostgreSQL e inicia dois processos em contêineres separados. O preparo registra um novo run ID e a cadeia persistente de heartbeat. A prontidão exige banco, migrations, heartbeat e API WAHA. O pareamento WAHA e a prontidão da IA são dimensões separadas: falta de sessão/modelo não autoriza automação, mas conserva leitura da base. Uma instância já pronta é reutilizada. Web/worker existentes e sem prontidão exigem parada explícita antes de outra tentativa.

Publicações são loopback. PostgreSQL usa rede privada de dados; worker e manage alcançam Ollama por `http://ollama:11434`, em rede interna sem gateway. Ollama não publica porta, não recebe checkout, credenciais, sessão ou perfil. Web recebe mídia em leitura e configuração de integração; o perfil Facebook é montado separadamente em worker/manage em `/facebook-profile`.

Dados de estado ficam em `.runtime/<environment_id>`; mídia, integrações, perfil e backups ficam por padrão em `~/.local/share/garimpei/docker/<environment_id>`. `GARIMPEI_PRIVATE_DIR` permite escolher outro diretório próprio. Banco, WAHA e pesos usam volumes Compose com labels de ambiente/checkout. O manifesto de aplicação registra a raiz imutável `/app`; o inventário Docker registra separadamente os labels com o caminho do checkout do host.

A parada normal verifica labels, registra parada da cadeia de heartbeat e para inclusive Ollama, preservando diretórios e volumes. A reserva global da GPU só é liberada após confirmar o Ollama próprio parado. `--clean` é recusado neste runtime enquanto não existir verificação suficiente de sessão sintética e inventário da migração; isso conserva dados em vez de remover volumes por suposição.

## IA local

```bash
./scripts/init.sh --prepare-ai
./scripts/init.sh --recover-ai
```

A construção da imagem baixa explicitamente o tokenizer público da revisão F19 e verifica SHA-256. O preparo local copia esse artefato verificado para o estado, sem baixar pesos em um início normal. `--prepare-ai` reserva a GPU no mesmo arquivo global F19, inicia somente Ollama próprio e conecta saída externa temporária para o download oficial. Confere imagem, hashes de todas as camadas, tokenizer e API version/tags/show contra o lock; remove a saída externa mesmo em falha. Não há fallback cloud/CPU ou socket Docker na aplicação.

`--recover-ai` exige labels/ID e proprietário da reserva global. Para o Ollama, confirma `Running=false`, reinicia a mesma instância e só então registra recuperação das chamadas incertas. Timeout, lease vencido ou ausência em `/api/ps` não constituem essa confirmação. A aplicação mantém o bloqueio e indica recuperação pelo operador.

## Login humano em contêiner

```bash
./scripts/facebook-login.sh --test-display
./scripts/facebook-login.sh
```

Requer WSLg/X11 já disponível (`DISPLAY` e socket gráfico); ausência mantém login requerido. O comando para o worker antes de montar o mesmo perfil no manage e o retoma ao encerrar. A pessoa solicita e confirma login na página de integrações, seguindo F11. A janela pertence ao contêiner; não há CDP/VNC publicado, `xhost +` ou perfil pessoal. Chromium usa sandbox, usuário não root, seccomp oficial versionado e somente a capability `SYS_CHROOT` adicional necessária à namespace sandbox. O teste gráfico abre apenas HTML sintético e não acessa conta externa.

## Ferramentas e regressões

```bash
./scripts/quality.sh node /app/scripts/run-gates.mjs
./scripts/quality.sh sh -c 'cd /app/apps/backend && uv run --frozen --no-sync pytest'
./scripts/quality.sh sh -c 'cd /app/apps/backend && DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --frozen --no-sync python manage.py check'
```

A imagem `quality` inclui os arquivos do checkout e usa `uv.lock`; não monta o código do host. Rebuild após alteração de fontes para avaliar o código novo. O runner canônico continua `node scripts/run-gates.mjs` dentro da ferramenta. O socket de Docker dessa ferramenta permite aos testes criar apenas os ambientes marcados que eles próprios administram.

As regressões F02–F22 que verificam sinais/PIDs do processo legado usam exclusivamente `GARIMPEI_RUNTIME=host` nas factories, `scripts/legacy/` e `compose.host.yaml`. Esse caminho explícito preserva os testes anteriores; a operação padrão usa Docker. Ele não comprova o lifecycle novo, que tem ensaios próprios de init/stop/readiness, GUI, rede, GPU e preservação.

## Adoção de instalação preenchida

O helper `scripts/docker-adoption.sh` e o [runbook de migração](migration-runbook.md) materializam snapshot frio, checksums e restauração em alvo vazio próprio. O ensaio mecânico e seus limites têm evidência separada; devem ser lidos antes da adoção.

Não ocorre migração automática de volumes ou perfis existentes. Antes de adotar: desligar admissão F22, drenar unidades, inventariar IDs/revisões/filas/intenção/tentativas/recibos e caminhos privados; gerar backup F17; restaurá-lo em uma segunda instância eval própria; comparar os inventários e comprovar a barreira de envio incerto. Copiar perfil/mídia/sessão somente com seus processos parados, checksum e ownership comprovados. Conservar a instalação anterior até validar rollback. Havendo atividade após backup, preservar/reconciliar também o inventário mais recente de tentativas/recibos antes de permitir novos envios.

O ensaio da adoção e rollback completos permanece evidência própria do contrato; iniciar contêineres ou conservar um volume não o substitui. Não executar no ambiente real sem backup restaurado e prova de rollback. A pendência real F21 e corpus humano independente também impedem declarar aceite integrado F23.

Fontes operacionais consultadas: [startup e saúde Compose](https://docs.docker.com/compose/how-tos/startup-order/), [Playwright Docker e sandbox](https://playwright.dev/python/docs/docker). Pins e proveniência estão em `runtime-lock.json`.
