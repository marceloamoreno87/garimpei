# Relatório de implementação — F20

**Estado:** implementação concluída; avaliação canônica **clean**,26/26 itens e8/8 ACs. Relatório: [eval-report-2026-11-12T03-22-50Z.md](eval-report-2026-11-12T03-22-50Z.md).
**Base:** bc1bc84; branch feat/F20-apresentacao-financeira; worktree a9af.
**Escopo:** implementação/avaliação locais, sem novos commits, merge, push, PR, deploy ou mensagem real.

## Comportamento entregue

Cards, detalhes e novas mensagens mostram compra → venda estimada → lucro com rótulos próprios e maior peso/tamanho do lucro. A taxa e os comparáveis usados permanecem nos detalhes; referência de novo fica separada. Valores desconhecidos continuam indisponíveis e compra comprovada permanece legível. Revisões antigas são lidas do mesmo snapshot, sem consultar avaliação corrente.

Novas autorizações validam identidade, observação, evento, referências de avaliação/configuração, moeda, valores finitos e coerência Decimal. Snapshot financial-trio-v1, corpo, destino e tentativa são confirmados pela transação existente. Corpos legados são preservados byte a byte; decisão incompleta sem corpo/tentativa volta à consulta F07 do mesmo evento, conservando a intenção. Tentativa sem corpo necessário vai revisão, sem reconstrução ou POST reparador.

A atualização HTMX conserva DOM, filtros/página e composição antiga na falha; os detalhes também usam requisição assíncrona com seleção de main, permitindo a mesma recuperação. Campos/textos financeiros de logística foram removidos da experiência ativa; texto original do vendedor permanece.

## Fases e pré-requisitos

1. Regressões de rótulo e composição incompatível reproduzidas antes da implementação. Modelo tipado de snapshot e fixture financeira entregues.
2. Persistência aditiva0013 e congelamento no fluxo F09 existente; nenhum ajuste em main/config/worker/lifecycle/compose.
3. Projeção/HTML compartilhados e CSS Mineral; configuração sem logística, atualização e recuperação preservadas.
4. Lab reprodutível com fonte/WAHA/relógio/banco próprios; testes de HTTP, concorrência, rollback, legado, migração e números exatos; evidências de navegador/qualidade. Operação em operations.md.

## Validação observada

- Oito testes unitários F20 passaram após regressões de identidade/revisão/variante, legado, composição ausente e componentes ausentes. Suíte unitária anterior ao último acréscimo:200 pass.
- Autorização concorrente e compatibilidade:1 pass14,67s.
- Mensagens exatas F07→snapshot→fake WAHA:1 pass29,49s, incluindo350/zero/−50, redução1200→1000 apesar de observação900 e fração12,63/18,37.
- Migração real0012→0013 com registros legados:1 pass14,57s.
- Regressões HTTP e adoçãoF12:2 pass19,84s.
- Seis gates Python PASS; Django check, migrationscheck, estáticos, sdist/wheel e tokenscheck exit 0. Wheel inspecionado: template, migration e módulos novos incluídos.
- UI com playwright-cli:360/768/1440; zoom equivalente por metade da largura CSS; rótulos/valores/ordem/fontes/overflow medidos. Configuração concluída no navegador e preservada após reinício. Lista e detalhe conservam A durante503 e aplicam nova revisão mediante clique.
- Suíte integral definitiva:339 PASS, exit 0,1133,04 s, processo novo com fontes/testes congelados. Comparação de333 arquivos, diff e10 arquivos novos confirmou bytes idênticos no início/fim. O ensaio anterior338/1 com imports mistos foi rejeitado e preservado; não é evidência de aprovação.

## Correções e limitações

Revisão independente confirmou perda de valores em publicação pré-F20 e referência de avaliação incompatível aceita. Ambas reproduzidas, corrigidas e cobertas. Teste históricoF12 precisava aplicar folhas atuais antes de consultar ORM com campos0013; falha de coluna ausente reproduzida e corrigida no teste. Expectativa antiga da seta de redução foi adaptada para preço anterior separado do trio, conforme spec.

A prova visual de200% usa viewport CSS equivalente, sem acionamento comprovado do zoom nativo. Imagens indisponíveis são estado da massa sintética/F14 futura; esta etapa não comprova coleta de fotos ou canal real. A folha0013 de F19 e esta folha0013 são paralelas: a integração futura precisa de migration de merge. Não houve integração entre branches.

## Adendos finais de integridade

Snapshot inclui schema_version1; revisão/identidade/produto/venda da avaliação imutável e referência de configuração são conferidos antes de corpo novo. Referência de revisão999 foi reproduzida como falha e corrigida com regressão PostgreSQL. Três integrações atuais PASS58,59 s e seis regressõesF09 atuais PASS217,37 s; seis gates atuais214 módulos PASS.

E2E da mesma oferta confirmou1000/1500/350 em card/detalhe/corpoA e900/1600/380+taxa20%/320 em B após reinício e clique, preservando corpo/snapshot/reciboA e uma tentativa. Navegador também abriu separadamente incompatibilidade de identidade, avaliação, variante e composição ausente.

Labs próprios, browsers f20/f20setup e baseline eval_wave11_f20 encerrados; dados descartáveis removidos pelos scripts. Nenhum recursoF19 ou de outro checkout foi alterado.

## Arquivos

- `apps/backend/src/garimpei/domain/alert/alert.py`
- `apps/backend/src/garimpei/domain/alert/eligibility.py`
- `apps/backend/src/garimpei/domain/alert/financial_snapshot.py`
- `apps/backend/src/garimpei/domain/listing/exploration.py`
- `apps/backend/src/garimpei/infra/http/listing/exploration_handler.py`
- `apps/backend/src/garimpei/infra/http/listing/exploration_presentation.py`
- `apps/backend/src/garimpei/infra/http/static/listing/exploration.css`
- `apps/backend/src/garimpei/infra/http/static/listing/exploration.js`
- `apps/backend/src/garimpei/infra/http/templates/listing/financial_values.html`
- `apps/backend/src/garimpei/infra/http/templates/listing/offer_detail.html`
- `apps/backend/src/garimpei/infra/http/templates/listing/results.html`
- `apps/backend/src/garimpei/infra/http/templates/monitoring/cost_fields.html`
- `apps/backend/src/garimpei/infra/http/templates/monitoring/form.html`
- `apps/backend/src/garimpei/infra/http/templates/monitoring/region_fields.html`
- `apps/backend/src/garimpei/infra/persistence/alert_models.py`
- `apps/backend/src/garimpei/infra/persistence/migrations/0013_alert_message_snapshot.py`
- `apps/backend/src/garimpei/infra/queries/listing/exploration_mapper.py`
- `apps/backend/src/garimpei/infra/queries/listing/exploration_source.py`
- `apps/backend/src/garimpei/infra/repository/alert/delivery_state.py`
- `apps/backend/src/garimpei/infra/repository/alert/financial.py`
- `apps/backend/src/garimpei/infra/repository/alert/message_authorization.py`
- `apps/backend/tests/factories/financial_presentation_lab.py`
- `apps/backend/tests/fixtures/valuation/financial_presentation.json`
- `apps/backend/tests/http/test_financial_presentation.py`
- `apps/backend/tests/integration/test_alert_consumers.py`
- `apps/backend/tests/integration/test_collection.py`
- `apps/backend/tests/integration/test_exploration.py`
- `apps/backend/tests/integration/test_financial_messages.py`
- `apps/backend/tests/unit/test_financial_presentation.py`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/authorization-integration.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/browser-layout-journey.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/browser-layout-observed.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/browser-states-journey.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/configuration-360.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/configuration-after-restart.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/configuration-saved-browser.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-1440-zoom200.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-1440.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-360-zoom-before.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-360-zoom200.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-360.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-768-zoom200.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-768.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-before-update.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-failed-update.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/detail-failed-update.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/exact-monetary-worker.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/fraction-browser-observed.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/fraction-detail.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/gates-python.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/http-collection-regressions.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/list-1440-zoom200.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/list-1440.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/list-360-zoom200.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/list-360.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/list-768-zoom-before.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/list-768-zoom200.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/list-768.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/migration-legacy.txt`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/missing-purchase-360.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/update-failure-360.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/update-recovered-360.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/evidence/zero-negative-unavailable-360.png`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/operations.md`
- `docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/orchestration-2026-11-12T02-10-44Z.md`

Progresso: alterada somente entradaF20. Contrato/spec/plano e avaliações históricas preservados.

Arquivo adicional de integridade: `apps/backend/src/garimpei/infra/repository/alert/financial_references.py`.
