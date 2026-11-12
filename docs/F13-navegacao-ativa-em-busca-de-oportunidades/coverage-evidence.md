# Mapa de evidências — F13

Suíte completa: 443 PASS, exit 0, com 440 hashes preservados. A avaliação canônica em eval-report-2026-11-12T15-11-54Z.md registra 19 PASS e um MANUAL. Os probes abaixo detalham cada bullet; fontes fake não substituem a prova real adiada.

## SVC-PESQUISA-01 — Perímetro reutilizável

- **Esperado:** O pedido recebe identidade, contexto e limites consultáveis.
  **Observado:** UUID, contexto, janela, revisão, consumo e referências continuam consultáveis depois do rollover. O limite histórico permanece 100 quando a configuração de leitura muda para 3; UUID inexistente tem erro tipado.

- **Esperado:** Repetição do mesmo pedido referencia o mesmo trabalho.
  **Observado:** Repetir o mesmo request UUID devolve o mesmo work UUID antes e depois da troca de ciclo.

- **Esperado:** Termo injustificado ou revisão antiga tem rejeição explícita.
  **Observado:** Termo genérico, constraints arbitrários, revisão antiga e quarto termo acima do orçamento compartilhado são rejeitados sem criar trabalho.

- **Esperado:** A consulta não altera interesses nem afirma equivalência ou preço por si só.
  **Observado:** A configuração conserva os dois interesses; a leitura não altera estado nem executa I/O externo. O resultado não calcula preço ou declara equivalência nova.

Evidência: `tests/integration/test_navigation.py::test_research_boundary_idempotent_and_restrictive`, `tests/integration/test_navigation.py::test_research_history_remains_readable_by_uuid_after_rollover`, `tests/integration/test_navigation.py::test_research_requested_before_window_binds_context_once`, `tests/integration/test_navigation.py::test_justified_fourth_term_is_rejected_by_shared_effective_budget`, `evidence/probes-navigation-history.txt`, `evidence/probes-limits-fairness-http.txt`.

## API-RETOMADA-01 — Comando confirmado e validado

- **Esperado:** Requisição válida confirma intenção persistida e redireciona ao acompanhamento.
  **Observado:** POST válido retorna 303 para /acompanhamento/, grava phase=pending e reason=resume_requested e acrescenta exatamente um job.

- **Esperado:** Formato inválido retorna 400; CSRF ausente retorna 403; revisão antiga ou acesso suspenso retorna 409.
  **Observado:** UUID inválido retorna 400; ausência de CSRF, 403; revisão antiga e acesso suspenso, 409.

- **Esperado:** Requisição rejeitada conserva estado confirmado e histórico.
  **Observado:** Snapshots de Work, Checkpoint, Receipt, CollectionState e Observation permanecem idênticos em cada rejeição.

- **Esperado:** Falha de gravação apresenta erro recuperável, sem confirmar retomada.
  **Observado:** DatabaseError controlado retorna 503 e Tente novamente; nenhum estado confirmado muda.

Evidência: `tests/integration/test_navigation.py::test_resume_http_persists_intent_and_every_rejection_preserves_history`, `tests/integration/test_navigation.py::test_navigation_http_csrf_resume_and_suggestion_preview`, `evidence/probes-limits-fairness-http.txt`.

## UI-PROGRESSO-01 — Entender o percurso

- **Esperado:** O painel identifica interesse, frente, termo original/alias e revisão/horário.
  **Observado:** Original PlayStation 5 Slim, alias PS5 Slim, versão do catálogo, revisão, horário e frente aparecem identificados.

- **Esperado:** Exibe último avanço útil e pendências conhecidas.
  **Observado:** Páginas, detalhes confirmados, fila conhecida e último avanço útil ficam visíveis.

- **Esperado:** Diferencia espera válida, parcialidade, suspensão e ausência de pendências.
  **Observado:** Capturas distinguem andamento, espera, teto, suspensão e conclusão da frente. A suspensão remove o comando indevido de retomada.

- **Esperado:** Exibe motivo e próxima ação sem inventar completude ou total da fonte.
  **Observado:** Motivos traduzidos e próxima ação/horário são visíveis; nenhum total da fonte é inventado.

Evidência: `evidence/ui-before.txt`, `evidence/ui-source-wait.txt`, `evidence/ui-suspended.txt`, `evidence/progress-desktop.png`, `evidence/progress-360.png`, `evidence/suspended-360.png`, `visual-review.md`.

## UI-PROGRESSO-02 — Atualização sem perder leitura

- **Esperado:** Atualização bem-sucedida aplica dados mediante ação explícita.
  **Observado:** O backend passa de duas para três páginas; o DOM permanece em duas antes da ação e muda para três somente após Enter em Atualizar percurso.

- **Esperado:** Falha conserva leitura anterior com indicação de horário/erro recuperável.
  **Observado:** Um 503 controlado preserva os quatro blocos anteriores e apresenta erro recuperável junto da leitura datada.

- **Esperado:** Rota e filtros da jornada continuam preservados.
  **Observado:** A URL /acompanhamento/?pagina=2&q=slim permanece igual antes e depois do sucesso e da falha.

Evidência: `evidence/ui-before.txt`, `evidence/ui-backend-change.txt`, `evidence/ui-before-action.txt`, `evidence/ui-after-action.txt`, `evidence/ui-refresh-failure.txt`.

## UI-SUGESTOES-01 — Evidência antes de adotar

- **Esperado:** Sugestão aparece separada das ofertas monitoradas.
  **Observado:** A rota Sugestões apresenta relações separadas das ofertas monitoradas; testes de banco confirmam persistência isolada.

- **Esperado:** Exibe interesse de origem, relação, anúncio/link, data e limitações.
  **Observado:** Origem Slim, relação Pro, links, data e limitações aparecem; dez links persistidos continuam acessíveis no teto.

- **Esperado:** Outro modelo é identificado como produto diferente, sem lucro/liquidez fabricados.
  **Observado:** O texto identifica outro modelo e não promete lucro ou liquidez.

- **Esperado:** Controles funcionam por teclado e a 360 px sem ocultar evidência ou ação.
  **Observado:** Controles funcionam por teclado. A 360 px, o DOM registra overflow=false e as imagens examinadas preservam evidência e ação por rolagem.

Evidência: `evidence/ui-source-wait.txt`, `evidence/ui-caps.txt`, `evidence/suggestions-wait-360.png`, `evidence/suggestions-caps-360.png`, `visual-review.md`.

## UI-SUGESTOES-02 — Prévia não é adoção

- **Esperado:** Formulário apresenta a proposta editável.
  **Observado:** GET /configuracoes/?sugestao preenche PS5 Pro em campo editável.

- **Esperado:** Configuração continua sem o interesse até gravação explícita bem-sucedida.
  **Observado:** A configuração mantém dois interesses durante a prévia e passa a três somente depois do save confirmado com 303.

- **Esperado:** Cancelar ou falhar ao salvar não confirma adoção.
  **Observado:** Cancelar ou somente abrir não grava. Falha SQL conserva os dois interesses e a proposta editável, sem confirmação indevida.

Evidência: `evidence/ui-adoption-failure.txt`, `evidence/ui-adoption-before.txt`, `evidence/ui-adoption-after-failure.txt`, `evidence/ui-adoption-after-save.txt`, `tests/integration/test_navigation.py::test_navigation_http_csrf_resume_and_suggestion_preview`.

## WRK-PERCURSO-01 — Busca, continuação e detalhe

- **Esperado:** Percorre contexto de busca verificado, continuação e detalhe.
  **Observado:** A fonte HTTP controlada percorre busca, página seguinte e detalhe. Um adapter novo reconstrói o cursor nativo validando o contexto.

- **Esperado:** Publica evidência do primeiro detalhe antes de terminar a exploração.
  **Observado:** Uma ListingObservation é confirmada enquanto a descoberta ainda está incompleta; falha no recibo reverte a publicação.

- **Esperado:** Preserva identidade/link, origem do interesse e contexto solicitado/observado.
  **Observado:** O recibo guarda observation_ids, os anúncios conservam fonte/ID e matches válidos e o adapter verifica o contexto da resposta.

- **Esperado:** Página inesperada não é registrada como busca vazia verificada.
  **Observado:** wrong_search_query produz checkpoint com zero páginas e estado partial, sem registrar busca vazia verificada.

Evidência: `tests/integration/test_navigation.py::test_incremental_publication_and_alias_identity`, `tests/unit/test_navigation_continuation.py::test_safe_cursor_can_reconstruct_in_a_new_adapter`, `tests/integration/test_navigation.py::test_cursor_repeat_wrong_context_and_limits_are_partial`, `evidence/probes-navigation-history.txt`.

## WRK-DISTRIBUICAO-01 — Ambas as frentes e interesses avançam

- **Esperado:** Cada par interesse/frente recebe oportunidade em até 2N turnos, com N interesses aptos.
  **Observado:** Com N=2, os quatro primeiros recibos aptos cobrem os quatro pares interesse/frente; pesquisas extras compartilham o turno do grupo.

- **Esperado:** Timeout de um item não impede turno de trabalho independente.
  **Observado:** O detalhe Slim demora 1,3 s sob timeout de 1 s; o primeiro recibo registra source_transport e o iPhone saudável publica no terceiro turno.

- **Esperado:** Cada turno respeita unidade e orçamento aplicáveis.
  **Observado:** O primeiro teto encerra a fatia: duas páginas, dez detalhes ou 120 s. Reconstrução reserva duas operações; atraso de banco não autoriza I/O tardio.

- **Esperado:** Espera obrigatória da fonte não é contornada por nova fila ou outro navegador.
  **Observado:** 429 grava o prazo compartilhado; reconciliação e tarefa já enfileirada recusam requests antes desse prazo.

- **Esperado:** Registro informa ordem, consumo de orçamento, último progresso e razão da seleção.
  **Observado:** Recibos persistem ordem, consumo e razão. O trabalho saudável recebe last_progress_at confirmado.

Evidência: `tests/integration/test_navigation.py::test_two_interest_fronts_receive_turns_despite_real_controlled_timeout`, `tests/integration/test_navigation.py::test_research_shares_fairness_budgets_and_rejects_cycle_old_revision`, `tests/integration/test_navigation.py::test_suggestion_rate_limit_survives_collection_reconcile`, `tests/unit/test_navigation_timing.py`, `evidence/probes-limits-fairness-http.txt`, `evidence/green-temporal-budget.txt`.

## WRK-RETOMADA-01 — Queda na fronteira de confirmação

- **Esperado:** Retoma unidades pendentes da última fronteira confirmada.
  **Observado:** Outro processo lê checkpoint com uma página e um recibo; falha antes do commit deixa zero páginas e candidatos. O restart retoma os IDs pendentes 220–224.

- **Esperado:** Página e continuação confirmadas não perdem candidatos.
  **Observado:** A página com 499+200 candidatos mantém 500 ativos e 199 no buffer; outro store drena para 197 sem nova busca nem perda de IDs. A cópia entre ciclos é atômica.

- **Esperado:** Repetição de unidade não duplica observação/evento.
  **Observado:** Repetir detalhe não duplica observação. Uma falha SQL real antes do recibo e retomada após a lease produzem uma observação e um evento por ID.

- **Esperado:** Histórico, escolhas manuais, marco e recibos prévios permanecem preservados.
  **Observado:** O mesmo cenário preserva escolha manual, histórico manual, marco, observações e intents/attempts confirmados ou incertos. O teste histórico compara integralmente os 20 registros anteriores.

Evidência: `tests/integration/test_navigation.py::test_checkpoint_survives_restart_and_atomic_rollback`, `tests/integration/test_navigation.py::test_page_buffer_preserves_excess_without_exceeding_500`, `tests/integration/test_navigation.py::test_partial_finish_and_carry_are_atomic_across_new_cycle`, `tests/integration/test_navigation_events.py::test_alias_events_hostile_content_adoption_and_prior_receipts_survive_f13_retry`, `tests/integration/test_collection.py::test_rollback_and_restart_after_first_batch`, `evidence/probes-navigation-history.txt`, `evidence/probe-events-adoption-history.txt`.

## WRK-RETOMADA-02 — Cursor inválido ou teto

- **Esperado:** Resultado informa parcialidade e razão específica.
  **Observado:** Contexto errado, repetição e teto produzem partial com motivo específico; 99 páginas mais reconstrução de custo 2 não inicia I/O.

- **Esperado:** Reconstrução de busca informa retrabalho e preserva deduplicação.
  **Observado:** A continuação nativa reconstruída preserva deduplicação e registra cursor_rebuilt. Cursor opaco com 480 caracteres usa hash de unidade e não excede campos do banco.

- **Esperado:** Trabalho não percorrido permanece pendente ou limitado, sem receber confirmação fictícia.
  **Observado:** Cursores e pendências ficam persistidos; diagnóstico, identidade inválida e continuação parcial não recebem prova fictícia de fronteira.

- **Esperado:** Reinício não repõe orçamento de sugestões da mesma janela.
  **Observado:** Novo SuggestionRepository respeita last_slice_at e recusa antes de 300 s; dois ticks mantêm no máximo um job pendente.

Evidência: `tests/integration/test_navigation.py::test_cursor_repeat_wrong_context_and_limits_are_partial`, `tests/integration/test_navigation.py::test_native_rebuild_reserves_cycle_budget_before_io`, `tests/integration/test_navigation.py::test_opaque_cursor_480_characters_does_not_overflow_unit_identity`, `tests/integration/test_navigation.py::test_suggestions_isolated_persistent_budget_and_tick_backlog`, `tests/unit/test_navigation_continuation.py`, `evidence/probes-navigation-history.txt`.

## WRK-RETOMADA-03 — Trabalho ultrapassado

- **Esperado:** Não publica a resposta como estado atual nem altera o checkpoint da nova revisão.
  **Observado:** Resposta com geração substituída ou revisão antiga lança SupersededAttempt e não publica.

- **Esperado:** Dados previamente confirmados permanecem preservados.
  **Observado:** Observações e recibos confirmados permanecem; mudança somente de custos cria ciclo novo e conserva o marco.

- **Esperado:** Progresso antigo não é atribuído à configuração vigente.
  **Observado:** A consulta vigente filtra revisão e ciclo; a resposta antiga não atribui progresso à configuração nova.

Evidência: `tests/integration/test_navigation.py::test_fair_turns_and_stale_generation_rejected`, `tests/integration/test_navigation.py::test_scope_revision_invalidates_old_results`, `tests/integration/test_collection.py::test_lease_and_new_scope_fence_old_worker`, `evidence/probes-navigation-history.txt`.

## WRK-ACESSO-01 — Recuperação humana de acesso

- **Esperado:** Trabalho dependente do perfil fica suspenso com ação de recuperação manual.
  **Observado:** SourceFailure com access=True marca access_suspended e suspende todas as frentes; a interface indica recuperação manual.

- **Esperado:** Reinício ou comando de retomada não libera acesso sem verificação F11.
  **Observado:** Retomar sem acesso F11 verificado retorna 409; tarefas e restart respeitam a suspensão.

- **Esperado:** Progresso confirmado permanece salvo.
  **Observado:** Checkpoints e últimos avanços confirmados permanecem. A captura inclui a frente anteriormente concluída.

Evidência: `tests/integration/test_navigation.py::test_profile_challenge_cannot_be_resumed`, `tests/integration/test_navigation.py::test_three_detail_failures_pause_attempt_and_queued_task_cannot_bypass`, `evidence/probes-navigation-history.txt`, `evidence/ui-suspended.txt`, `evidence/suspended-360.png`.

## WRK-PERIMETRO-01 — Alias conservador e conteúdo externo

- **Esperado:** Termo equivalente preserva interesse, modelo/restrições e justificativa.
  **Observado:** PS5 Slim é alias de PlayStation 5 Slim por catálogo versionado; a key original permanece e o título próprio precisa corresponder.

- **Esperado:** Modelo/variante diferentes não entram como alias ou interesse novo.
  **Observado:** PS5 Pro é relação para outro produto. iPhone Pro, mini e capacidade distinta são casos negativos e não viram aliases.

- **Esperado:** Identidade do resultado não é inferida apenas pelo termo consultado; variante incompatível não recebe match de identidade presumido.
  **Observado:** O resultado incompatível 1306 não recebe match presumido. As restrições são verificadas no título do próprio resultado.

- **Esperado:** Instrução encontrada na fonte não altera escopo ou acessa credenciais.
  **Observado:** Conteúdo hostil é processado como dado: FileAccessCanary/inotify não registra acesso ao segredo sintético e a configuração conserva o escopo aprovado.

- **Esperado:** Nenhum contato, compra ou envio é executado a pedido do conteúdo externo.
  **Observado:** As chamadas externas pertencem somente a search, detail, cep e new. Não há contato, compra ou envio solicitado pelo conteúdo; POSTs fake seguem apenas decisões normais dos IDs aptos.

Evidência: `tests/unit/test_navigation_policy.py::test_alias_keeps_variant_and_requires_listing_evidence`, `tests/unit/test_navigation_policy.py::test_only_explicit_directed_relations_are_researchable`, `tests/integration/test_navigation_events.py::test_alias_events_hostile_content_adoption_and_prior_receipts_survive_f13_retry`, `evidence/probe-events-adoption-history.txt`.

## WRK-SUGESTOES-01 — Exploração automática fundamentada

- **Esperado:** Nicho relacionado recebe justificativa e anúncio de suporte verificado.
  **Observado:** A relação Slim→Pro vem do catálogo; anúncios 1304/9130 sustentam evidência verificada e datada.

- **Esperado:** Relação genérica com eletrônicos não basta para publicar sugestão.
  **Observado:** O catálogo exige relação dirigida explícita; pertencer genericamente a eletrônicos não autoriza sugestão.

- **Esperado:** Falta de evidência mantém investigação inconclusiva.
  **Observado:** Falta de suporte persiste state=inconclusive e reason=evidence_pending; essa investigação não aparece entre sugestões válidas.

- **Esperado:** Anúncios exclusivamente sugeridos ficam fora de ofertas, amostras e eventos monitorados.
  **Observado:** Antes da adoção ou descoberta independente, não há Listing, ListingEvent ou POST por essa origem; evidências ficam em storage separado.

Evidência: `tests/integration/test_navigation.py::test_suggestions_isolated_persistent_budget_and_tick_backlog`, `tests/integration/test_navigation.py::test_exact_300_seconds_and_missing_support_stays_inconclusive`, `tests/integration/test_navigation_events.py::test_alias_events_hostile_content_adoption_and_prior_receipts_survive_f13_retry`, `evidence/probes-limits-fairness-http.txt`, `evidence/probe-events-adoption-history.txt`.

## WRK-SUGESTOES-02 — Trabalho ativo tem precedência

- **Esperado:** Não inicia navegação de sugestão que adie trabalho ativo.
  **Observado:** active_work, active_due_soon e source_wait impedem claim. Atraso após claim não autoriza I/O além de 45 s; detalhe só inicia se couber.

- **Esperado:** Mantém orçamento separado e motivo de espera consultável.
  **Observado:** O DTO público apresenta consumo, 45 s, intervalo de 300 s, tetos e next_at, usando a mesma política de admissão. A query não altera contagens.

- **Esperado:** Não abre outro navegador com o mesmo perfil para executar em paralelo.
  **Observado:** Locks de perfil e queueing_lock impedem concorrência; dois reconcile criam no máximo uma tarefa de sugestão.

Evidência: `tests/unit/test_navigation_policy.py::test_idle_budget_admission_and_no_restart_reset`, `tests/unit/test_navigation_timing.py`, `tests/integration/test_navigation.py::test_suggestion_budget_wait_and_caps_are_public_read_only`, `tests/integration/test_navigation.py::test_suggestions_isolated_persistent_budget_and_tick_backlog`, `evidence/green-temporal-budget.txt`, `evidence/green-public-budget.txt`.

## WRK-SUGESTOES-03 — Sugestão ignorada e limites

- **Esperado:** Ignorar sugestão não adiciona interesse nem produz alerta de suas ofertas por essa origem.
  **Observado:** O ID 9130 apenas sugerido não adiciona PS5 Pro e produz zero POST; ignorar não autoriza monitoramento ou alerta.

- **Esperado:** Teto suspende inclusão/exploração afetada sem apagar evidência confirmada.
  **Observado:** 100 registros impedem o 101º; 99→100 é permitido. Dez evidências ficam preservadas e a 11ª é recusada sem nova request.

- **Esperado:** A descoberta independente pelo interesse ativo mantém sua política vigente.
  **Observado:** O mesmo ID 9130 encontrado depois pela categoria ativa recebe match de categoria, sem match do produto PS5 Pro não adotado, e segue a política vigente.

Evidência: `tests/integration/test_navigation.py::test_suggestion_100_records_and_10_evidences_preserve_every_record`, `tests/integration/test_navigation_events.py::test_alias_events_hostile_content_adoption_and_prior_receipts_survive_f13_retry`, `evidence/probes-limits-fairness-http.txt`, `evidence/probe-events-adoption-history.txt`.

## EVT-PUBLICACAO-01 — Uma descoberta por identidade

- **Esperado:** Uma identidade fonte/ID conserva os matches válidos.
  **Observado:** Os IDs 9001 e 9002 preservam fonte/ID e matches de categoria e produto Slim em uma observação cada. As chamadas incluem termo literal e alias.

- **Esperado:** Não duplica descoberta ou primeiro alerta pela multiplicidade de consultas.
  **Observado:** Cada ID apto produz uma descoberta, uma intenção, uma tentativa e um POST fake, apesar das consultas convergentes.

- **Esperado:** IDs diferentes não são fundidos apenas por título ou foto.
  **Observado:** 9001 e 9002 continuam identidades diferentes com observações, eventos e mensagens próprias, mesmo com título e foto iguais.

Evidência: `tests/integration/test_navigation_events.py::test_alias_events_hostile_content_adoption_and_prior_receipts_survive_f13_retry`, `tests/integration/test_navigation.py::test_incremental_publication_and_alias_identity`, `evidence/probe-events-adoption-history.txt`.

## EVT-PUBLICACAO-02 — Política vigente preservada

- **Esperado:** Eventos seguem as mesmas regras do fluxo F04/F12.
  **Observado:** T→T+61 descobre publicação T+30 durante histórico inicial parcial: uma descoberta e um carregamento inicial. A publicação e avaliação usam os caminhos F04/F12.

- **Esperado:** Incerteza não vira elegibilidade por ter vindo da F13.
  **Observado:** 9003, com data desconhecida, não produz descoberta; 9004, com condição incerta, é excluído e não recebe intenção.

- **Esperado:** Recibos anteriores não são reabertos e transmissão incerta não é repetida.
  **Observado:** 9141 confirmado e 9142 incerto/review mantêm uma tentativa e os mesmos corpos, financial, ACKs e intenções após queda e retomada.

Evidência: `tests/integration/test_navigation_events.py::test_alias_events_hostile_content_adoption_and_prior_receipts_survive_f13_retry`, `tests/integration/test_collection.py::test_proven_new_listing_can_alert_with_initial_history_partial`, `tests/integration/test_collection.py::test_repeated_detail_errors_pause_after_three_attempts_and_recover`, `evidence/probe-events-adoption-history.txt`, `evidence/probes-legacy-f04-f12.txt`.

## E2E-PERCURSO-01 — Prova real de leitura e continuidade

- **Esperado:** Evidências públicas sanitizadas comprovam contexto, continuação, detalhe e retomada.
  **Observado:** MANUAL: a prova real foi adiada pelo usuário. Não há evidência Facebook de contexto, continuação, detalhe e retomada nesta execução.

- **Esperado:** Acompanhamento corresponde ao progresso persistido.
  **Observado:** MANUAL: correspondência da interface com progresso da fonte real ainda não verificada.

- **Esperado:** Registro informa tempos, limites e parcialidade observados, sem prometer completude.
  **Observado:** MANUAL: tempos, limites e parcialidade da fonte real não foram afirmados; os probes controlados são evidência distinta.

- **Esperado:** Nenhum contato ou envio real é necessário à prova.
  **Observado:** Esta frente não executou contato ou envio real. Essa ausência, isoladamente, não completa a jornada real.

Evidência: `operations.md`, `orchestration-2026-11-12T12-10-45Z.md`.

## E2E-ADOCAO-01 — Sugestão entra por configuração confirmada

- **Esperado:** Somente após confirmação o interesse integra o escopo ativo.
  **Observado:** A prévia não muda o escopo; POST save com 303 inclui PS5 Pro e nova revisão. Falha de gravação não adota.

- **Esperado:** Nova coleta usa revisão vigente e o caminho normal de observações.
  **Observado:** Após salvar, a próxima coleta cria observação do ID 9130 com revisão vigente e match de produto ps5 pro.

- **Esperado:** Política de avaliação/alerta aplicável continua sendo a vigente, sem alerta causado só pela sugestão.
  **Observado:** Sugestão, prévia e adoção produzem zero POST por si só; descobertas aptas seguem a política vigente.

Evidência: `tests/integration/test_navigation_events.py::test_alias_events_hostile_content_adoption_and_prior_receipts_survive_f13_retry`, `evidence/probe-events-adoption-history.txt`, `evidence/ui-adoption-after-failure.txt`, `evidence/ui-adoption-after-save.txt`.
