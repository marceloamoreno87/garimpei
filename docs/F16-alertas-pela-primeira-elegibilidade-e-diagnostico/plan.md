# Plano de implementação — F16 Alertas pela primeira elegibilidade e diagnóstico

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-12T16-16-18Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

## Pré-requisitos

- Dependências F04/F05/F07/F08/F09/F10/F12 avaliadas, com seus artefatos históricos preservados; stack e versões travadas em `apps/backend/uv.lock` e na F02.
- Ambiente isolado da F02, PostgreSQL, web/worker e servidor WAHA programável; iniciar somente quando houver trabalho de aplicação, usando `./scripts/init.sh`. Parada normal preserva dados; limpeza apenas no ambiente descartável próprio.
- Ler `spec.md`, `contract.md`, PRD atual e clean-arch antes das alterações. Coordenar mudanças nos módulos de coleta, valoração, projeções, composição e alertas compartilhados com outras features.
- Fixtures/factories, relógio controlável e barreiras declarados no contrato são entregáveis da implementação. Grupo/sessão reais exigem autorização específica para o item externo; sua ausência não é suprida pelo fake.

## Fase 1 — Base verificável e regras

**1. Cenários e fronteiras** — Preparar os cenários determinísticos de primeira elegibilidade, datas, histórico e escolha manual descritos no contrato. Consolidar o mapeamento das entradas atuais F04/F05/F07/F10/F12 e das regras F09 substituídas pela F16.

**2. Política de primeiro alerta** — Definir a identidade lógica, os motivos, a janela inclusiva e o marco de entrada automática consumida, conforme spec §3. Manter reduções e reconciliação sob as regras preservadas.

**Verificação da fase:** matriz de casos e invariantes da spec §7, incluindo exatamente 48 horas, data futura e repetição automática após escolha manual; nenhuma consulta externa ou mensagem real.

## Fase 2 — Persistência e adoção

**3. Estado durável e migração** — Acrescentar o histórico de elegibilidade e o trabalho de reavaliação sem substituir decisões ou recibos existentes. Adaptar a origem das intenções para comportar o primeiro alerta corrente e as reduções por evento.

**4. Inventário do legado** — Implementar a adoção retomável e o vínculo de intenções/recibos anteriores antes de liberar despacho F16. Conservar a suspensão quando houver histórico indeterminado e preservar o marco manual nos anúncios antigos.

**Verificação da fase:** migrations em base nova e preenchida, retomada entre lotes, inventário idempotente e ausência de POST durante adoção; cenários de legado do contrato.

## Fase 3 — Reavaliação e despacho

**5. Entradas automáticas persistentes** — Integrar as invalidações confirmadas e a varredura de reparo aos estágios separados do worker. Retomar enriquecimento e estoque recente sem fabricar eventos de descoberta ou tratar reinício como nova evidência.

**6. Autorização e reconciliação** — Conectar a composição corrente à primeira elegibilidade e revalidar prazo/versões na fronteira do envio. Preservar corpo e vínculo autorizados, bloquear segundo primeiro alerta e manter quedas independentes após confirmação anterior.

**Verificação da fase:** itens Worker/Event do contrato, concorrência e quedas nas fronteiras de commit/autorização/POST, avanço de outro anúncio durante falha e regressões de F09/F12.

## Fase 4 — Diagnóstico na exploração

**7. Leitura e apresentação do estado** — Expor a consulta tipada e integrar estado, motivos, datas e histórico à lista e ao detalhe F08. Distinguir revisão visual, avaliação atual e recibo, com recuperação na mesma jornada.

**Verificação da fase:** itens Service/UI, leitura sem efeitos de envio, revisões divergentes, falha parcial, navegação via `playwright-cli` e evidências sanitizadas.

## Fase 5 — Validação integrada e entrega

**8. Percurso e evidências finais** — Consolidar o percurso inicialmente inelegível até confirmação e retomada, além da prova real no grupo autorizado quando seu pré-requisito estiver disponível. Documentar operação, adoção, diagnóstico, pendências externas e resultados por item junto da feature.

**Verificação da fase:** executar todos os quality gates do contrato e conferir o Coverage Manifest contra o PRD vigente. Evidência ausente permanece pendente; preparar os artefatos para avaliação sem marcar `done` antes do veredito completo. Este plano não autoriza commit, push, PR, merge ou deploy.
