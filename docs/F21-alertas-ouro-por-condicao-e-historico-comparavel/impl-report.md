# F21 — Implementação e verificação em andamento

Esta execução acrescenta `gold-alert-v1`: conjunção pura de condição textual/visual aplicável, identidade normalizada, histórico F06 válido e composição F07 com lucro positivo. A autorização final revalida as evidências após a consulta do canal, preservando mensagens congeladas e reconciliação.

A migration 0027 mantém decisões imutáveis, referência na intenção, assinatura automática própria para a exceção manual e adoção persistente. Um trigger impede nova autorização por consumidores incompatíveis após ativação. A adoção é explícita pelo comando `adopt_gold_alerts --activate`; o estado inicial pending não declara a política já adotada. Reinício não desativa uma política ativa. Backup inclui decisões/vínculos/barreira, com rejeição de downgrade.

O lab `python -m tests.factories.gold_lab` prepara casos declarados em `tests/fixtures/alert/gold_cases.json`. Fontes, análise e WAHA controlados são identificados como sintéticos; PostgreSQL, regras de identidade/mediana/lucro, persistência e autorização são reais. A primeira bateria tem 19 PASS; relatório canônico e verificações adicionais serão anexados antes do encerramento.

A prova real é independente: consultas autorizadas ao perfil dedicado, contexto São Paulo/20 km, detalhes e fotos com origem/hash. A referência assistida por IA não substitui a revisão humana exigida pela F21. A feature permanece em implementação até a avaliação por item; nenhuma pendência autoriza `done`.
