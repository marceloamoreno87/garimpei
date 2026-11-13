# Plano de implementação: F03 — Configurações e interesses de monitoramento

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-10T22-12-38Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

Estado: plano de entrega futura, sem implementação iniciada. Executar sequencialmente após F02, preservando o escopo de F03 e o progresso `pending` até avaliação completa.

## Pré-requisitos

- F02 avaliada e configuração/versões de [operations.md](../F02-fundacao-tecnica-e-ambiente-local/operations.md) e [versions.md](../F02-fundacao-tecnica-e-ambiente-local/versions.md): Python 3.13, Django 5.2, uv/lock e imagens preparadas.
- Instância de avaliação isolada, segredos privados, banco `garimpei_`, web/worker/PostgreSQL/WAHA prontos via `./scripts/init.sh`; preservar dados de desenvolvimento.
- Catálogo Facebook com proveniência verificável, conforme spec §3; categorias do laboratório não satisfazem este pré-requisito. Sua obtenção faz parte da entrega de F03.
- [PRD](../PRD.md), [spec](spec.md), [contrato](contract.md), design canônico e skills `implement-feature`, `clean-arch`, `playwright-cli` e `frontend-ui-design` nos trabalhos correspondentes.
- Factories e cenários descritos na spec §7 ainda precisam ser criados; não pressupor seeds, credenciais de marketplace ou endpoints de falha já existentes.

## Fase 1 — Confirmar o catálogo e preparar os cenários

**1. Categorias verificadas** — Obter e documentar as categorias selecionáveis do recorte de eletrônicos e sua hierarquia real, preparando o catálogo versionado da spec §3. Se a fonte impedir a verificação, registrar o impedimento e manter o aceite de categorias pendente, sem substituição por dados do protótipo.

**2. Cenários reproduzíveis** — Preparar os estados de primeiro uso, rascunho, configuração concluída e falha controlada no ambiente isolado da F02. Entregar instruções de criação/verificação dos cenários e separar dados sintéticos da evidência do catálogo real.

**Verificação da fase:** confrontar catálogo, URLs e prova datada; reproduzir os cenários sem dados pessoais e sem modificar a instância contínua. Satisfazer os pré-requisitos do contrato antes de executar seus itens.

## Fase 2 — Persistir rascunho e publicar configuração

**3. Regras e persistência** — Entregar o modelo de configuração e interesses, com validação, armazenamento independente da execução e migração aditiva, conforme spec §§3/6. Preservar a fundação técnica e impedir preferências fictícias no primeiro uso.

**4. Publicação e consulta** — Entregar os casos de uso, composição e consultas públicas de F03, garantindo confirmação atômica, revisão e reenvio seguro. Tornar os dados confirmados disponíveis aos futuros consumidores F04/F07, distinguindo ausência, falha e rascunho.

**Verificação da fase:** demonstrar os itens SVC do contrato, rollback/conflito em PostgreSQL e preservação dos dados F02. Executar a entrada dos seis gates após alterações estruturais de backend; nenhuma fila de negócio deve ser criada.

## Fase 3 — Entregar configuração guiada e edição

**5. Primeiro uso** — Entregar as três etapas e a página de destino, usando os componentes e a direção visual aprovados. Preservar entradas, comunicar erros e só confirmar conclusão após a publicação válida, sem simular coleta.

**6. Revisão das preferências** — Entregar edição posterior de CEP, custos e interesses com confirmação, conflito recuperável e preservação do estado anterior quando a gravação falhar. Manter a navegação inicial e a retomada coerentes com a configuração persistida.

**Verificação da fase:** exercitar os itens HTTP/UI com e sem JavaScript, incluindo CSRF e respostas HTMX de erro; verificar teclado, foco e layout com `playwright-cli`. Avaliar visualmente com `frontend-ui-design`, sem reutilizar evidência do protótipo como teste da aplicação.

## Fase 4 — Comprovar retomada e preparar avaliação

**7. Evidências da entrega** — Executar as jornadas completas do contrato, incluindo parada/reinício normal e falha de confirmação, e registrar evidências sanitizadas junto à feature. Preparar `impl-report.md` com cobertura por item, limitações e instruções para reproduzir cada estado, sem declarar F04/F07 implementadas.

**Verificação da fase:** executar todos os comandos de Quality gates do contrato, preservar os resultados reais e conferir o Coverage Manifest contra os cinco critérios F03 do PRD. Verificação ausente é pendência; conclusão documental não autoriza `done`, commit, push, PR ou deploy.
