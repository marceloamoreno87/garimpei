# F10 — Plano

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-11T21-54-20Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

1. Registrar escopo no PRD/progresso, preservar IDs e contratos anteriores. Verificar protocolo WAHA na documentação e imagem local; manter design existente.
2. Criar política de importação de cookies, portas, casos de uso, migração e persistência privada versionada. Testar rejeição sem vazamento e rollback/retomada de coleta.
3. Integrar status de acesso/aviso persistente e resolução dinâmica da sessão no worker. Testar que geração antiga não substitui cookies novos.
4. Criar conexão WAHA/QR/grupos e configuração persistida; estender o destinatário e parser de recibos sem redirecionar intenções antigas. Testar grupo desconhecido, conta alterada, sessão indisponível e GOWS.
5. Adicionar menu, seções e feedback acessíveis. Verificar pelo playwright-cli com fixtures sem segredos reais; manter aplicação dev pronta para o usuário.
6. Executar seis gates, Django/migrations, testes Python/PostgreSQL e regressões afetadas. Persistir implementação/avaliação com pendências reais explícitas; não declarar autenticação/entrega real sem prova.
