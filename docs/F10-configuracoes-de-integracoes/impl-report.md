# F10 — Relatório de implementação

Escopo autorizado: cookies Facebook na interface, aviso e renovação de acesso, conexão WhatsApp e seleção de grupo no menu. Requisito registrado como F10, preservando IDs e histórico anteriores. A nova instrução amplia o destino direto da F09 para grupos escolhidos na conta conectada. F09 continua `implemented`, com suas provas reais adiadas conforme decisão anterior do usuário.

Implementação no checkout `master`, sem commits existentes; alterações anteriores preservadas. Nenhum commit, push, PR ou deploy foi realizado. A instância de desenvolvimento permanece em http://localhost:18351. O ciclo F09 não foi reaprovado por esta extensão.

## Entregas por fase

| Plano | Implementação |
|---|---|
| 1 — Escopo e protocolo | PRD/progresso e documentos F10; protocolo de sessões, QR e grupos conferido na documentação WAHA e no engine GOWS da imagem fixada. Identidade Mineral existente preservada. |
| 2 — Cookies privados | Política aceita header/JSON/estado Playwright, valida autenticação/domínio/expiração e não ecoa segredos. Diretório externo privado, arquivos 0600 por revisão, metadata PostgreSQL e migrations aditivas 0009/0010. |
| 3 — Renovação | Resolução por tarefa no worker, revisão própria, geração antiga invalidada sob lock de publicação e aviso persistente. Marco inicial/histórico preservados. Baseline do ciclo impede confundir sucesso antigo com verificação da nova revisão em relógio congelado. |
| 4 — WhatsApp | Criação/início da sessão, QR servido pelo backend, estado com polling, paginação de grupos e validação contra conta atual. Destino persistido dinamicamente, desativação e recibos GOWS/grupo com vínculo fixo da intenção. |
| 5 — UI | Menu Integrações, formulários CSRF, instruções, feedback e recuperação. Jornadas Chromium em desktop 1440×1000 e celular 390×844, somente fixtures sintéticas. |
| 6 — Verificação | Seis gates, Django/migrations e suíte ampla aprovados; testes direcionados complementam as mudanças posteriores. Evidências e limites no relatório canônico. |

## Arquivos e composição

- `apps/backend/src/garimpei/domain/integration/` e `usecase/integration/`: valores, portas e casos de uso sem dependências de HTTP/ORM.
- `infra/repository/integration/`, `infra/persistence/integration_models.py` e migrations `0009`/`0010`: arquivos privados e estado durável, retomada e baseline.
- `infra/gateway/integration/waha_session.py` e alteração em `infra/gateway/alert/waha_gateway.py`: conexão/grupos e confirmação de saída no grupo/conta corretos.
- `infra/http/integration/`, templates/estáticos de integração, layout, rotas e tratamento central de erros: UI, polling, no-store, proteção de formulários e feedback.
- `config/{env,settings,test_settings}.py` e `main.py`: configuração central, contexto e composição explícita; precedência da configuração UI com compatibilidade das variáveis anteriores.
- `tests/{unit/test_integration_policy.py,integration/test_integrations.py,factories/integration.py,factories/integration_lab.py}`: políticas, fixtures HTTP, UI reproduzível e integração real entre processos locais.
- `tests/integration/test_alert_consumers.py`: restaura o schema atual antes de retomar o worker após a prova histórica da migration F09. A prova anterior permanece.
- `quality/{entrypoints.json,vulture_whitelist.py}`: descobertas exatas de serialização/templates/ORM.

## Resultados e correções verificadas

- Suíte ampla: **238 passed**, exit 0, 894,73 s. Foi coletada antes dos dois novos casos de limite de expiração e dos dois novos testes de integração descritos abaixo.
- Políticas + três testes HTTP/worker de integração, após endurecimento de cookies/diretório: **13 passed**, exit 0, 25,48 s.
- Fluxo F03/F04/F05/F07/F09 com grupo salvo na UI: **1 passed**, exit 0, 34,16 s; novo evento no grupo 1, troca de grupo, próximo evento no grupo 2 e intenção anterior conservada.
- Renovação com coleta bloqueada em I/O: **1 passed**, exit 0, 13,26 s; ciclo antigo superseded, nova revisão resolvida, coleta nova concluída antes de liberar a antiga, nenhum preço antigo publicado, marco inicial preservado.
- Seis gates finais: tipos, lint/templates, limites, arquitetura, ciclos e não utilizados, exit 0. Django check e makemigrations --check: exit 0. Harness: 10 features válidas.

As execuções são complementares; não se afirma uma execução única da suíte inteira com 242 testes. Os 15 casos F10 foram exercitados, incluindo os adicionados após a coleta da suíte ampla. Logs e hashes da árvore final estão em `evidence/`.

O navegador reproduziu POST nativo com `Origin: null` e HTTP 403 quando a política era `no-referrer`; a política agora é `same-origin`, mantendo CSRF ativo, e o mesmo formulário salvou com HTTP 303. Os casos de `expires=0` e valor finito fora da faixa de timestamp falharam antes da correção e passaram depois; o erro permanece seguro e a revisão anterior é preservada. O diretório existente não tem permissões alteradas implicitamente. O aviso de expiração usa o token âmbar existente, com contraste observado 6,19:1.

## Pendências

`HTTP-WHATSAPP-01` e `WRK-GRUPOS-01`: comportamento local verificado com HTTP programável; falta parear e confirmar operação/recibos na conta real pelo usuário. O QR sintético usado na prova tem 1 px e só demonstra entrega/carregamento da imagem. Autenticação Facebook real também não é afirmada. A aplicação está pronta para esse teste, sem credenciais reais em artefatos. F10 permanece `implemented`, sem `completed_at`, enquanto houver validação externa pendente.

## Reavaliação 2026-11-11T21-54-20Z

Reavaliação: formato de recibo SenderAlt coberto em grupo/destino direto, com negativos de conta/chat/participante. A transição WhatsApp agora usa HX-Refresh=true, evitando estado antigo quando o navegador já está na mesma URL #whatsapp. Polling com estado estável não força refresh. Grupo de operação/ativação preservados; API real confirmou pertencimento, e efeitos de grupo foram testados conforme o contrato em HTTP sintético. Apenas o contato explicitamente autorizado recebeu teste externo.

Validação ampla: 253 passed; após último patch HTTP, caso afetado repetido (1 passed), duas transições de navegador verificadas e seis gates finais aprovados. Relatório canônico novo registrado em prd_progress.json. Sem commit/push/PR.
