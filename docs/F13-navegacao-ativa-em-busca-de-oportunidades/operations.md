# Operação — F13 Navegação ativa

Esta feature usa Python/Django, templates/HTMX, PostgreSQL e Procrastinate. Não há serviço de IA, processamento de fotos F14 ou política F16 nesta entrega. A configuração central continua em `garimpei.config.env` e a composição explícita em `garimpei.main`.

## Ambiente isolado

Na raiz da worktree, prepare um arquivo privado com os parâmetros e segredos novos descritos na operação F02. Não reutilize cookies, credenciais ou arquivos de perfil de outro ambiente. O arquivo fica fora de versionamento, com permissão 600. Nesta execução, a identidade foi `GARIMPEI_ENV=eval`, `GARIMPEI_INSTANCE=wave11b_f13`, `GARIMPEI_AI_SERVICE_ENABLED=false`; a aplicação própria ficou na porta 15087. Portas, banco `garimpei_`, volumes e perfil são resolvidos pelo lifecycle e confirmados pelo manifesto privado.

```bash
GARIMPEI_ENV_FILE=/caminho/privado/f13.env ./scripts/init.sh --disposable
GARIMPEI_ENV_FILE=/caminho/privado/f13.env ./scripts/resolve-env.sh
GARIMPEI_ENV_FILE=/caminho/privado/f13.env ./scripts/migrate-dev.sh --check
```

`--disposable` é somente para ambiente próprio descartável autorizado. O runtime de avaliação emparelhado desta execução deve ser preservado: seus dados, perfil e sessão de integração não podem ser removidos com `--clean`. Alertas foram explicitamente desativados; a checagem final de schema confirmou `whatsapp_configured=true`, `alerts_enabled=false`, zero configurações, anúncios e trabalhos de navegação, e colunas `limits/context` existentes. Não houve envio real nesta frente.

## Processamento e recuperação

O worker reconcilia coleta e navegação, verificando configuração e conexão F11. Um lock de perfil e a posse persistente impedem operações concorrentes. Cada unidade confirma checkpoint e recibo na mesma transação curta da publicação F04/F12; nenhum I/O externo ocorre sob essa transação. Geração, revisão e hash de contexto impedem publicação de resposta ultrapassada.

Uma fatia ativa termina no primeiro limite: 120 s, duas páginas ou dez detalhes. Reconstrução nativa de continuação custa duas páginas e reserva dois timeouts/cadências antes de I/O. Até 100 páginas e três termos são compartilhados por interesse/ciclo. O teto de 500 detalhes ativos mantém excedentes em buffer persistente, sem nova busca para drená-los. Cursores opacos ficam no checkpoint; recibos usam hash e não devem expô-los em logs ou relatórios.

Falha de alvo isolado deixa outros alvos aptos avançarem. Três falhas consecutivas encerram a tentativa parcial. Pendências confirmadas são transportadas atomicamente para a janela seguinte de 60 s; o contexto da nova janela exige reconstrução explícita da busca. Login/desafio/perda de acesso suspendem o perfil e exigem recuperação F11. Recuo de fonte, inclusive 429, grava `source_not_before`; reconciliação e tarefas já enfileiradas respeitam esse prazo. A interface apresenta motivos e próximos passos legíveis.

Sugestões usam orçamento separado: 45 s, uma página, um detalhe, intervalo persistente mínimo de 300 s, até 100 registros e dez evidências por sugestão. Só são admitidas quando timeout, cadência e margem de cinco segundos cabem antes do próximo trabalho ativo. A projeção pública e a admissão usam a mesma política pura. Evidência sem relação demonstrada permanece inconclusiva; atingir teto conserva a evidência existente. Nenhuma sugestão produz oferta monitorada, avaliação ou alerta por si só.

## API de pesquisa reutilizável

`RequestResearchUseCase(repository).execute(request_id, scope_revision, origin_interest, canonical_term, constraints, purpose)` devolve a identidade estável do trabalho. `constraints` deve coincidir com o hash do escopo aprovado vigente; não aceita recorte geográfico inventado pelo caller. Relação/alias precisam estar no catálogo versionado. Revisão antiga, contexto divergente ou quarto termo compartilhado são rejeitados explicitamente.

`ReadResearchUseCase(queries).execute(work_id)` consulta identidade, contexto, janela, limites efetivamente usados, consumo, progresso e referências de observações, inclusive depois da troca de ciclo. UUID inexistente produz `MissingNavigation`. Esta consulta não navega, não altera dados e não expõe cursor/payload. Não requer F18 nem adiciona comando HTTP de pesquisa.

## Provas controladas e gates

Factories criam ambientes próprios com fontes fake loopback e canal fake, permitidos somente em `eval`. Cada fixture F13 inicia por `init.sh --disposable`, confirma sua identidade e encerra seus próprios processos/banco. Os testes novos de PostgreSQL não usam o banco session compartilhado. Para a suíte, o cwd do backend é necessário para carregar o `pyproject.toml` e as configurações Django:

```bash
node scripts/run-gates.mjs
DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check --settings=garimpei.config.test_settings
DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py makemigrations --check --dry-run --settings=garimpei.config.test_settings
uv build --project apps/backend
cd apps/backend
uv run --frozen --no-sync pytest
```

Probes úteis: `tests/integration/test_navigation.py`, `tests/integration/test_navigation_events.py`, `tests/unit/test_navigation_timing.py`. O cenário integrado valida a sequência sugestão → prévia → gravação → coleta normal, queda PostgreSQL antes do commit, retomada, recibos confirmados/incertos anteriores, escolhas manuais e uma publicação por identidade em canal fake. O catálogo do produto é `src/garimpei/infra/gateway/navigation/navigation_catalog.json`, incluído no wheel.

O laboratório visual pode ser iniciado, a partir de `apps/backend`, com `uv run --frozen --no-sync python -m tests.factories.navigation_lab /caminho/privado/lab`. O controlador imprime apenas a URL e mantém worker próprio pausado para capturas determinísticas. Seu tratamento de SIGTERM retoma esse worker e executa `stop.sh --clean` somente para os recursos sintéticos do laboratório. A navegação usa sessão própria do `playwright-cli`.

## Prova real e parada

Por instrução explícita do usuário, a prova real de Facebook será feita posteriormente no sistema principal já autenticado. `E2E-PERCURSO-01` permanece MANUAL nesta avaliação; fontes controladas não a substituem. Não acessar o perfil principal, copiar cookies ou solicitar novo login na instância 15087 nesta etapa.

Para parar um runtime preservando perfil, banco e pareamento:

```bash
GARIMPEI_ENV_FILE=/caminho/privado/f13.env ./scripts/stop.sh
```

`stop.sh --clean` fica restrito aos ambientes sintéticos próprios descartáveis. Antes de encerrar, feche somente sessões Playwright próprias, confirme propriedade dos processos pelo cwd/manifesto e libere somente o lock da execução. Artefatos públicos ficam nesta pasta; segredos, perfis e diagnósticos privados permanecem fora do versionamento.
