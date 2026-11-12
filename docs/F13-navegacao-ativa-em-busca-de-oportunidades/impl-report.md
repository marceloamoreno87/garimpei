# Implementação — F13 Navegação ativa em busca de oportunidades

**Branch:** `feat/F13-navegacao-ativa` · **Base:** `c8ca8ae79d5a9760a251e14931db4cbc2549b594` · **Execução:** `2026-11-12T12-10-45Z`.

A implementação entrega navegação incremental persistente, justiça entre descoberta/investigação e interesses, aliases conservadores e sugestões separadas com adoção explícita. A avaliação final é pending: 19 itens PASS, um MANUAL; seis critérios de aceite verificados e um indeterminado. Todos os gates locais passaram, e a prova real Facebook foi adiada pelo usuário. A falha inicial e a correção permanecem documentadas. Não houve commit, push, merge, PR ou acesso ao sistema principal.

## Escopo entregue

- Domínio puro em `domain/navigation`: catálogo versionado de equivalências e relações dirigidas, orçamento, elegibilidade compartilhada, turnos e contratos de leitura/escrita.
- Casos de uso `RunSliceUseCase`, `RunSuggestionsUseCase`, leitura de progresso/sugestões, retomada, pedido e consulta histórica de pesquisa complementar por UUID.
- Cinco modelos próprios: NavigationWork, NavigationCheckpoint, NavigationUnitReceipt, NicheSuggestion e SuggestionEvidence. Migration `0015_navigation` depende exclusivamente de `0014_merge_inference_and_financial_snapshot`; inclui `CollectionState.source_not_before` e snapshots de contexto/limites.
- Repositórios curtos com transações de checkpoint/recibo/publicação, controle por revisão e geração, buffer persistente no teto de 500, limites por interesse e transporte atômico de pendências entre janelas.
- Adapter Facebook continua somente leitura. A continuação nativa reconstrói contexto autenticado e só restaura cursor seguro; o cursor permanece privado. Reconstrução reserva duas páginas e dois timeouts/cadências antes de I/O.
- Painéis HTMX e templates de acompanhamento/sugestões, motivos legíveis, atualização por ação, prévia editável na configuração e falhas que conservam a leitura/estado confirmado.
- Composição principal, registro de modelos, configuração central, worker, rotas e entradas legítimas dos gates aplicados pelo coordenador nos arquivos comuns. O coletor anterior sem consumidores reais foi removido conforme a decomposição prevista em F13.

A publicação usa o store existente F04/F12 e preserva deduplicação, condição, marco de monitoramento, avaliação e recibos. F19 e F20 continuam na base integrada. Não foram implementadas IA, fotos F14 ou política F16. Apenas a decoração de escopo e o matching por aliases aprovados mudaram em scope/consolidation; Evidence e proveniência pertencem à frente F16.

## Verificações e evidências

`coverage-evidence.md` relaciona cada bullet dos 20 itens aos testes e logs. A auditoria focal independente fechou os grupos de limites, retomada, fairness, eventos, adoção e interface após examinar as novas asserções e capturas.

| Verificação | Resultado registrado |
|---|---|
| Probes persistência/contexto/histórico | 32 PASS em 18,48 s |
| RED temporal e pós-claim | quatro falhas comportamentais reproduzidas antes da correção |
| GREEN temporal + orçamento público | sete PASS em 7,05 s |
| Limites 100/10, 300 s exatos, quarto termo, timeout/fairness e efeitos HTTP | cinco PASS em 13,64 s |
| Evento/alias/adoção/conteúdo hostil/recibos prévios no mesmo cenário integrado | um PASS em 71,80 s |
| F04/F12 parciais/descoberta nova/três falhas sem alterar os originais | três PASS em 43,68 s |
| GUI desktop/360 px/teclado/erro/suspensão/tetos | capturas e logs em evidence; avaliação em visual-review.md |
| Seis grupos Python, Django, migrations e build antes do primeiro full | exit 0 |
| Primeira suíte ampla final | 2 FAIL / 29 PASS, 457,67 s, exit 2 após SIGINT próprio |
| Freeze durante a primeira suíte | 440 arquivos, conjunto e hashes idênticos |

A invocação literal de pytest a partir da raiz retornou exit 2 por descoberta de configuração; ela não foi contada como prova de implementação. A execução correta usa cwd `apps/backend` e `uv run --frozen --no-sync pytest`, carregando o mesmo lock e `pyproject.toml`.

## Ciclo de correção 1

O histórico da janela de 48 horas mostrou perda da prova `source_exhausted` quando o adapter confirma a fronteira sem prova textual explícita. A correção restaura essa normalização somente no término verificado, sem diagnóstico ou identidade inválida. O teste histórico original passou em 10,55 s.

O histórico de restart exigia repetir buscas e proibia detalhes, estratégia substituída pela retomada durável de F13. Com autorização do coordenador, passou a verificar os 20 IDs anteriores e snapshots integrais de observações/eventos, cinco detalhes pendentes 220–224 e total final de 25, sem duplicação ou busca repetida. Nenhuma garantia de negócio foi removida.

O coordenador autorizou adaptar a sincronização de publicação para exigir conteúdo útil antes de liberar a segunda categoria, preservando silêncio, quatro observações finais e unicidade/matches. Autorizou também usar o modelo histórico project_state na leitura do schema 0012; as garantias de cutover e recibos permanecem. O módulo inteiro é executado novamente antes dos gates da correção.

## Ambiente, segurança e limites

Instância principal própria de avaliação: `eval_wave11b_f13`, aplicação em 15087, IA desativada. O schema final foi alinhado e checado preservando pareamento/perfil: zero configurações, anúncios e trabalhos; colunas limits/context presentes; WhatsApp configurado e alertas desativados. O laboratório visual e os testes usam bancos/portas/volumes próprios e fontes/canal fake loopback; não há POST real nesta frente.

A instrução do usuário para realizar a prova real posteriormente no principal prevalece sobre o preparo inicial. A janela F11 própria foi encerrada verificando propriedade, sem copiar perfil ou cookies. `E2E-PERCURSO-01` continua MANUAL; não há afirmação de completude ou validação real do Facebook. A feature não pode receber `done` ou avaliação `clean` enquanto esse item estiver pendente.

Limpeza e comandos reproduzíveis constam de `operations.md`; o diário conserva interrupções, freezes e ciclos. O relatório canônico posterior deve consolidar o resultado real dos gates e a pendência externa, sem converter probes em aprovação da suíte.

## Resultado final do ciclo 1

Suíte completa: **443 PASS em 1425,39 s (23:45), exit 0**. Os mesmos **440 arquivos** conservaram todos os hashes, sem adição ou remoção durante o full. Seis grupos Python, Django/check, migrations/check e build retornaram exit 0 antes do congelamento e permanecem válidos para os mesmos bytes. [Relatório canônico](eval-report-2026-11-12T15-11-54Z.md); [comparação final](evidence/freeze-cycle1-after.json); [log completo](evidence/full-suite-cycle1.txt).

O módulo histórico completo passou com 13 testes tanto no probe quanto no full. Foram usados um ciclo de correção de até três; nenhum commit/push/merge foi criado. A única pendência é E2E-PERCURSO-01, por instrução explícita do usuário. F13 permanece implemented e a orquestração termina manual-pending, sem done/clean.

O laboratório visual e as fixtures descartáveis foram limpos; sessões Playwright próprias encerradas. A instância15087 foi parada normalmente com exit0, preservando banco, perfil e pareamento; a última leitura confirmou alertas desativados. O único manifesto restante é o ambiente próprio preservado em estado stopped. A liberação do lock desta execução consta de evidence/cleanup.json. Nenhum recurso principal foi tocado.
