# F11 — Relatório de implementação

Decisão aplicada: janela própria com login manual e coleta automática, aprovada na resposta do usuário à comparação com coleta assistida. O diagnóstico e as hipóteses estão em [diagnosis.md](diagnosis.md). O pedido foi registrado como extensão F11, preservando PRD, IDs, dependências e avaliações anteriores; F09/F10 seguem com provas externas pendentes.

## Entregas

- Configuração central resolve o tipo de sessão antes dos defaults de timeout/retry/intervalo. A sessão gerenciada recebe padrões reais de acesso, com overrides explícitos mantidos.
- Migration aditiva `0011_facebook_browser_profile` persiste modo, pedido, estado e horário de login. Portas e casos de uso de abrir/confirmar separados de HTTP/ORM.
- Worker mantém a janela interativa, com pedido idempotente, prazo de 15 minutos, detecção de fechamento/interrupção e recuperação explícita. Geração de coleta invalidada sob o lock de publicação; uma confirmação antiga não substitui um pedido/modo novo.
- `MarketplaceBrowser` usa contexto persistente visível no modo perfil, diretório privado 0700 e lock exclusivo. Login é verificado no Marketplace com estado autenticado; perfil fechado/gravado antes de liberar coleta. Não utiliza o hook stealth nem flags de ocultação do caminho legado nesse novo modo.
- Coletas reutilizam o diretório do perfil. Falha de acesso suspende execução; reinício não libera a suspensão no modo perfil. Ofertas, marco inicial e recibos conservados.
- Integrações oferece Abrir navegador / Já entrei, verificar acesso, status por polling e recuperação. Cookies ficam como opção avançada. Layout Mineral e configuração WhatsApp preservados.

## Arquivos principais

- `domain/integration/facebook_login.py`, `usecase/integration/{request,confirm}_facebook_login_usecase.py`: portas e orquestração de comandos.
- `infra/repository/integration/facebook_profile_repository.py`, `postgres_repository.py`, `private_session.py`; modelos e migration `0011`: estado, retomada e exclusividade.
- `infra/worker/facebook_login_handler.py`, comando `runworker.py`, `main.py`: dono da janela, lifecycle e composição explícita.
- `infra/gateway/listing/marketplace_browser.py`, `config/env.py`: contexto persistente e configuração central.
- Handler, apresentação, templates e CSS de Integrações: operação pela aplicação.
- `tests/unit/test_facebook_browser.py`, `tests/integration/test_facebook_profile.py` e factories `facebook_login.py`/`facebook_login_lab.py`: políticas, Chromium real e laboratório local sem Facebook.

## Verificação

- Red da regressão de configuração: 1 failed antes da implementação (`defaults-before.log`).
- Casos finais da feature: **7 passed**, exit 0, 23,71 s. Chromium real preserva cookies e localStorage ao fechar/reabrir; segundo dono é recusado pelo lock. Requisição HTTP/CSRF, confirmação inválida/válida, fechamento/timeout, suspensão, reinício e baseline preservado exercitados.
- Regressões afetadas: **30 passed**, exit 0, 177,03 s: configuração, políticas de integração, fonte Marketplace, fluxos F10 e coleta F04. A suíte inteira não foi repetida nesta extensão.
- Seis gates: tipos, lint/templates, limites, arquitetura, ciclos e não utilizados — exit 0. Django check sem problemas; makemigrations --check sem mudanças. Harness com 11 features válido.
- Chromium visível abriu pelo WSLg contra site sintético local e foi encerrado, exit 0. UI verificada com playwright-cli em 1440×1000 e 390×844: login pendente, verificação inválida, verificação bem-sucedida, desafio e opção avançada por teclado, sem overflow horizontal.

Logs, screenshots sintéticos e hashes finais em `evidence/`. O laboratório e a sessão CLI foram encerrados; o ambiente dev permanece rodando em http://localhost:18351. O processo dev já carregava o fluxo funcional antes do último ajuste de texto de apresentação; a janela real aguardando confirmação do usuário foi preservada, sem novo restart que interrompesse o login. Esse delta é apenas a remoção de “pela coleta” do texto de sessão verificada; o próximo início carregará a redação atual.

## Limites

O bloqueio remoto relatado não foi reproduzido nesta execução, e sua causa interna não foi atribuída ao Facebook como fato. `session_expired` e defaults incorretos foram observados localmente. O novo perfil elimina a transferência manual incompleta como fluxo principal; não promete tornar a automação indetectável nem garantir estabilidade futura.

`MANUAL-FACEBOOK-01` permanece pendente: usuário autenticar na janela, confirmar e observar coleta/reabertura na fonte real. O estado real aguardando confirmação não equivale a sucesso. Sem senha/cookies/QR reais nos artefatos; nenhuma ação no navegador pessoal. Sem commit, push, PR ou deploy.

## Reavaliação 2026-11-11T21-54-20Z

Reavaliação real: perfil autenticado pelo usuário reaberto, busca nativa com 24 anúncios e detalhe válido, e 141 ofertas observadas no banco. Composição de URL corrigida para usar /marketplace/category/<slug>/ sem prefixo indevido de cidade. Login/cookies e desafios verificados também em fixture/Chromium real. Os contratos passaram; a completude do catálogo F04 continua limitada pela categoria cell-phones, conforme catalog-availability-2026-11-11.md. Nenhuma escolha do operador foi apagada nem o marco inicial foi liberado manualmente.

Validação ampla: 253 passed; após último patch HTTP, caso afetado repetido (1 passed), duas transições de navegador verificadas e seis gates finais aprovados. Relatório canônico novo registrado em prd_progress.json. Sem commit/push/PR.
