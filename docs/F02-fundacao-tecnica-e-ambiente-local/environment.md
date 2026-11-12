# F02 — Ambiente e resultados observados

Execução `2026-11-10T19-52-16Z`, nesta sessão, sem agentes separados. Autorização: implementar e avaliar F02, com até três ciclos de correção por padrão. Nenhum commit, push, PR, merge, deploy, pareamento ou envio. A F01 foi reavaliada antes da implementação: 14 PASS e quatro ACs verificados; Facebook aprovado, coleta fora desta etapa.

## Preparação efetivamente executada

WSL2/Linux x86_64, Git 2.53.0, Bash 5.3.9, Node v26.3.1, Docker 29.9.3 e Compose v5.7.0 disponíveis. Python inicial do sistema era 3.14.4; foi instalado CPython 3.13.14 no espaço do usuário por uv 0.11.24, sem substituir o Python do sistema. Registro completo de dependências/digests em [versions.md](versions.md). A escolha django-stubs foi ajustada à série 5.2 antes da integração; mypy travado em 1.19.1.

Scaffold Django gerado em temporário. Somente pyproject/lock/pin foram copiados inicialmente; entradas e módulos foram adaptados seletivamente. Inventário e testes reais de fila/WAHA precederam a cópia. Nenhum PostgreSQL, sessão ou serviço pessoal foi reutilizado.

## Medição pontual da base

Amostra UTC **2026-11-10T20:52:12.027760+00:00**, instância descartável própria `eval_final_eval_195216`. Web, worker, PostgreSQL e WAHA estavam ativos; `/health` e `/health/ready` responderam 200 com JSON e no-store, run/identidade corretos. Banco `garimpei_eval_final_eval_195216`; banco de testes configurado separadamente `garimpei_test_d9a5f365dbf87e81`. Portas web/PG/WAHA: {'web': 18862, 'pg': 18962, 'waha': 19062}. Dados estruturados: [foundation-snapshot.json](evidence/foundation-snapshot.json).

RSS somado de cada grupo, incluindo filhos: [93880320, 65175552] bytes. Esse somatório pode contar páginas compartilhadas mais de uma vez e não representa memória física exclusiva. Docker stats da mesma amostra: [('garimpei-eval_final_eval_195216-postgres-1', '38.24MiB / 31.34GiB', '0.94%'), ('garimpei-eval_final_eval_195216-waha-1', '269.6MiB / 31.34GiB', '0.07%')]. Limites de memória do daemon não são capacidade adicional à WSL. É uma amostra de base ociosa/controle técnico, sem benchmark, coletor, conta WhatsApp ou carga de negócios. Sem SLA, intervalo de coleta ou custo total demonstrados.

## Verificações e regressões

- Prova inicial real de migrations/fila: estado e enqueue invisíveis antes do commit, visíveis conjuntamente após commit, rollback sem ambos e worker oficial consumindo recibo. [queue-poc.json](evidence/queue-poc.json).
- Seis gates Python passaram na árvore integrada. Cenários negativos rejeitaram tipos, lint/template, import direto/transitivo, montagem/ambiente/caminho/I/O em import, ciclo, função órfã e dependência sem uso. A avaliação final repete os checks no estado entregue e registra comandos/diagnósticos.
- Suíte preliminar completa: 59 PASS, sem skip, em 126,42 s. Novos cenários obrigatórios e verificações mais estritas foram acrescentados depois; o total final pertence ao relatório de avaliação, não a essa execução preliminar.
- Rodadas dirigidas: 25 cenários de operação passaram; cinco falhas reais de serviço/imagem/ferramenta passaram; dois consumidores/execução antiga e cópia própria com migration/erro HTTP passaram. Não confundir resultado de rodada parcial com avaliação completa.
- `uv build --no-build-isolation`, check Django, makemigrations --check e collectstatic passaram na preparação. Harness: quatro testes e estrutura aprovados, sem atribuir a eles a validação Python.

Defeitos corrigidos durante a implementação inicial: ordem de tag WAHA; argumento de CLI não aceito; porta efêmera recusada pelo host; falso ocupado por TIME_WAIT; configuração de logging Gunicorn; conector Django que não aceita conexão externa explícita; herança indevida de settings nos subprocessos de teste; observação prematura de PostgreSQL reiniciado. Regressões pertinentes ficaram nos testes. Nada foi marcado aprovado mediante alteração do contrato.

## Preservação e propriedade

Baseline SHA-256 de 467 arquivos preexistentes. Alterações esperadas: `.gitignore`, `README.md`, `scripts/run-gates.mjs`, `scripts/migrate-dev.sh`, `scripts/stop.sh`, `scripts/init.sh`, `scripts/resolve-env.sh`, `scripts/test/harness.test.mjs`, `docs/F01-discovery-e-viabilidade-de-integracoes/decisions.md`, `docs/harness.md`, `docs/prd_progress.json`. AGENTS, .agents, .codex, arquitetura/design e spec/plano/contrato F02 preservados. O relatório final inclui comparação de hashes e progresso das demais features. Scripts antigos de scaffold/TypeScript permanecem no acervo, sem execução no produto.

Instâncias de prova usam IDs/bancos/volumes/PIDs próprios, configuração privada e marcadores descartáveis. Os testes encerram seus recursos e removem apenas volumes autorizados; uma falha anterior de fixture deixou um PostgreSQL temporário, depois encerrado pelo comando público com verificação de propriedade. As instâncias da PoC inicial também foram removidas após registro da evidência. A instância final será encerrada ao terminar a avaliação; resultado de limpeza fica no relatório.

Conta, cookies e scraping do Facebook ficam em F04. Pareamento e entrega WAHA pertencem a F09. Probes técnicos, asset HTMX e endpoints de saúde não são implementação das jornadas do produto.

## Descoberta e correção de limpeza — ciclo 1

Após os gates e 72 testes da avaliação inicial, a prova suplementar identificou redes Compose retidas por --clean. O esgotamento de pools impediu outra instância. Foram removidas 28 redes órfãs **desta execução**, conferindo nomes exatos dos geradores de testes, projeto Compose, criação posterior ao lock F02 e ausência de endpoints. Evidência em evidence/evaluation-2026-11-10T20-54-37Z/legacy-owned-network-cleanup.json; nenhum prune global.

A correção acrescenta labels de instância/checkout a redes, verificação de endpoints próprios e remoção da rede na limpeza descartável. Uma rede estrangeira controlada deve permanecer intacta. O teste de regressão falhou no código anterior (network inspect ainda retornava 0 depois de --clean). Nova avaliação deve comprovar correção e ausência de regressões; a avaliação inicial permanece preservada.
