# Implementação F17 — em execução

Branch isolada `feat/F17-resiliencia-operacional`, base `3ce35d5`. Este relatório parcial não declara aceite nem altera a feature para `done`.

O primeiro incremento contém modelos aditivos, progresso durável com deduplicação de fronteiras, instrumentação transacional de publicação, consumidores por fila, leitura de contagens por snapshot, comandos de backup/exportação/restauração, arquivo privado versionado por allowlist e barreira de recuperação persistente em arquivo e banco. A habilitação automática permanece desativada até a calibração e avaliação finais.

A captura usa `REPEATABLE READ READ ONLY`, registra schema, migrations, hash do código, perfil e cursor coberto. A exportação conserva exatamente os bytes do arquivo selecionado. URLs temporárias de mídia perdem query/fragment por schema, com exclusão declarada; campos arbitrários de credenciais em JSON são rejeitados. A restauração exige destino eval próprio, descartável e vazio; não importa autenticação nem jobs técnicos e conserva o despacho bloqueado.

Evidências do primeiro incremento: `evidence/calibration-initial.json`, `evidence/increment-gates.txt` e `evidence/increment-tests.txt`. Cinco percursos saudáveis usaram PostgreSQL/fonte/canal fake, com um recibo por percurso e nenhum envio real. Seis grupos Python passaram; onze testes unitários e um percurso integrado de backup/exportação/restauração passaram.

Pendentes nesta revisão parcial: integrar a mídia protegida F14; completar os cenários adversos, reconciliação comprovada da restauração, limites e calibração do incremento; verificar UI/E2E com navegador; executar regressões completas e avaliação canônica por item. `spec.md`, `plan.md` e `contract.md` preservam a condição preliminar enquanto esses ensaios faltarem.
