# Implementação — F03 Configurações e interesses de monitoramento

Execução de 2026-11-10, branch `master` (checkout sem commit base). F02 concluída. Sem commits, push, PR ou deploy. A avaliação canônica é registrada separadamente em `eval-report-*.md`.

| Fase | Entrega e evidência de implementação |
|---|---|
| 1. Catálogo e cenários | Catálogo estático `infra/gateway/monitoring/facebook_categories.json` com Electronics (`479353692612078`), Cameras, Cell Phones e Computers; rótulos e caminhos originais. [Navegação pública observada](evidence/catalog-verification.md). Factories NOVO/RASCUNHO/ATIVA e falhas controladas em `apps/backend/tests/factories/monitoring.py`; matriz em `apps/backend/tests/fixtures/monitoring/cases.json`. |
| 2. Regras e persistência | `domain/monitoring/` guarda validação, agregado, portas e snapshot imutável. `usecase/monitoring/` coordena gravação, leitura, conclusão e edição. Migrations aditivas `0002_monitoring_configuration.py`, repositório/consultas PostgreSQL e unidade de trabalho. Bloqueio transacional cobre criação sem linha, leitura consistente e revisão. Reenvio equivalente não muda a data, a revisão ou os interesses. |
| 3. Interface | Rotas Django e templates/estáticos `infra/http/{monitoring,templates/monitoring,static/monitoring}/`, sem dependências externas em runtime. Fluxo assistido, edição, erro e destino de acompanhamento. CSRF, HTML escapado, envio comum e HTMX, recuperação de foco e confirmação após commit. Tokens e fontes Mineral locais; licenças incluídas. |
| 4. Verificação e retomada | Ambiente exclusivo `eval_f03_213950` com PostgreSQL/web/worker/WAHA técnico. Navegador real percorreu cadastro, edição, conflito, falha de catálogo, falha de gravação, responsividade, teclado, e as duas retomadas. Snapshot confirmado conserva ID/revisão/data e não cria tarefas de negócio. |

A composição em `apps/backend/src/garimpei/main.py` expõe `build_read_monitoring_configuration().execute()` para o snapshot confirmado. F04 e F07 podem receber a porta de leitura no construtor. A autorização só existe após commit da conclusão. A aplicação informa que coleta ainda não está disponível e não cria job, alerta ou marco de processamento inicial.

A base F02 foi preservada. Os testes da fundação que presumiam uma única migration ou número fixo foram adaptados para operar sobre a última migration aplicada e conferir a criação de um novo arquivo. A regressão de resposta JSON 500 fora das rotas F03 continua exercitada. O formatador registra códigos explícitos de validação e falha sem incluir corpo de formulário ou exceção bruta.

Na verificação de implementação, o primeiro teste HTTP mostrou 404 na rota ainda ausente. Testes focados posteriores comprovaram limites, validação, transações e rollback, concorrência, conflitos, reenvio, escape e retomada. A primeira suíte completa teve 124 aprovações e duas falhas nos testes F02 presos à migration `0001`/`0002`; os dois passaram após a correção focada. Os seis gates passaram no código de implementação; a reexecução final da suíte e o veredito por item pertencem à avaliação. A revisão visual também corrigiu a quebra dos rótulos dos botões em 360 px antes da recaptura.

| Itens do contrato | Fronteira e evidência esperada na avaliação |
|---|---|
| SVC-CONFIGURACAO-01 a 04 | Snapshot em banco real, incluindo ausência, estado publicado, leitura concorrente e erro explícito; `tests/integration/test_monitoring_persistence.py`. |
| API-CONFIGURACAO-01 a 08 | POST/GET Django com persistência real, matriz de entrada, 303/409/422/503, reenvio, CSRF e rollback; mesmo arquivo. |
| UI-PRIMEIRO-USO-01, UI-INTERESSES-01 a 04 | Chromium por `playwright-cli`, capturas, estados selecionados, campos sem defaults, erro focado e fallback de catálogo. |
| UI-EDICAO-01 e 02 | Chromium real com edição confirmada, conflito, último interesse, botão ocupado, erro 503 e recarga independente. |
| E2E-CONFIGURACAO-01 a 03 | Snapshots confirmados e interface após parada/início normais da mesma instância descartável. |

Para reproduzir, siga [cenários e comandos](evidence/reproduction.md). Nenhum dado de preferência é semeado na aplicação. Coleta, geocodificação/entrega, cálculo de lucro e alertas permanecem nas features correspondentes.
