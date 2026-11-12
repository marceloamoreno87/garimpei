# Relatório de implementação — F04 Coleta e acompanhamento de anúncios

## Escopo

A F03 estava aprovada e disponível neste checkout. A implementação foi integrada à árvore de trabalho existente. O repositório estava em `master` sem commit base.

| Etapa do plano | Resultado |
|---|---|
| 1 · Viabilidade e perfil da fonte | Acesso autenticado, busca de categoria/produto, continuação e detalhe reais comprovados com a sessão renovada fornecida pelo usuário em 2026-11-11. Na revisão aprovada, retirada aproximada e envio informado foram comprovados; a avaliação de 40 páginas ficou em 23 PASS e 1 FAIL por janela insuficiente para a retomada real. |
| 2 · Dados e regras | Implementados e verificados com a fonte local e PostgreSQL. Migração aditiva, chaves por fonte/ID, preparação por consulta, observações, vínculos de interesse, preços em BRL, cobertura e eventos paginados. |
| 3 · Worker e recuperação | Implementados e verificados com a fonte local. Reconciliação a cada dois segundos, agendamento junto do commit PostgreSQL, lease com geração, retomada da passagem e bloqueio compartilhado com a publicação F03. O processo continua atendendo a fila `runtime` da F02. |
| 4 · Acompanhamento | Implementado e verificado com Django e Chromium em instância descartável. A rota lê o estado local, mantém o acesso a configurações e informa carga inicial, conclusão, parcialidade ou indisponibilidade. |

O usuário solicitou explicitamente scraping real com stealth e forneceu uma sessão própria. As condições e o perfil executado estão registrados na operação da feature. Fontes da decisão anterior de acesso e do alcance da prova amostral. [Política da Meta](https://about.fb.com/news/2021/04/how-we-combat-scraping/) · [Decisão da F01](../F01-discovery-e-viabilidade-de-integracoes/decisions.md)

## Arquivos e fronteiras

- `apps/backend/src/garimpei/domain/listing/` e `usecase/listing/` contêm correspondência, consolidação, cobertura, transições e interfaces para coleta, agenda e leitura.
- `infra/persistence/listing_models.py` e `migrations/0003_listing_collection.py` registram entidades e restrições. O repositório publica lote e eventos juntos. A edição F03 e a publicação de coleta usam o mesmo bloqueio PostgreSQL.
- `infra/repository/listing/` e `infra/queries/listing/` mantêm gravação e projeções. Os consumidores podem compor `build_read_listing`, `build_read_listing_changes` e `build_read_collection_status`.
- `main.py`, `config/env.py`, `runworker.py` e `infra/worker/listing_handler.py` integram a coleta ao lifecycle F02. `infra/gateway/listing/` contém o adaptador da fixture e o estado de indisponibilidade da fonte real.
- `infra/http/monitoring/monitoring_handler.py` e os templates `monitoring/tracking.html` e `monitoring/form.html` ligam o estado persistido à jornada F03.
- `apps/backend/tests/fixtures/listing/` e `tests/factories/listing.py` fornecem a matriz sanitizada, servidor programável, relógio controlável e criação de instância própria. Os testes unitários, PostgreSQL e Chromium exercitam a implementação.

## Perfil verificável

A composição local usa `GARIMPEI_ENV=eval` e `GARIMPEI_LISTING_FIXTURE_URL` com origem HTTP em `127.0.0.1`. O teste usa `GARIMPEI_LISTING_FIXTURE_CLOCK` apontando para arquivo privado com instante ISO 8601 e fuso. `tests/factories/listing.py` configura intervalo de 60 s, timeout de 15 s, lease de 20 s, até cinco páginas por consulta e recuo de 5 a 900 s. Os tempos lógicos são controlados pelo teste. A espera mínima informada pela fonte pode exceder o teto do recuo calculado.

A fixture representa buscas independentes de categoria, subcategoria e produto, com páginas programáveis e contextos de retirada e envio. O mapa sintético de CEP inclui dois destinos, precisão declarada e posições de teste na fronteira dos 20 km. A recuperação do histórico e a entrega vinculada ao destino foram verificadas nesse perfil local.

A configuração `GARIMPEI_FACEBOOK_STATE_FILE` habilita o coletor autenticado real. O contexto aplica playwright-stealth, idioma pt-BR, fuso de São Paulo, navegação cadenciada e gravação atômica da sessão privada. A composição de teste continua disponível. Sem arquivo de sessão ou fonte de teste, a aplicação registra `source_profile_unavailable`. [Operação e parâmetros](operations.md)

## Verificação da implementação

- `node scripts/run-gates.mjs` aprovou os seis grupos Python.
- `pytest` da suíte focada registrou 8 aprovações, incluindo migração sobre F03, worker real, retomada e falha antes do commit. Os três testes unitários iniciais de política também passaram.
- `manage.py check`, `makemigrations --check --dry-run` e `collectstatic --noinput` foram executados com `garimpei.config.test_settings` e retornaram 0.
- `node --test scripts/test/harness.test.mjs` e `node scripts/check-harness.mjs` retornaram 0.

## Pendências históricas da avaliação anterior

A integração real de categoria/produto, detalhe e continuação é exercitada nesta continuação. `WRK-FONTE-02` e `WRK-FONTE-03` continuam exigindo retirada e entrega com evidência para o CEP e retomada de publicação real dentro da janela adotada. O relatório canônico da execução registra o veredito por item.

## Continuação real em 2026-11-11

O adaptador passou a ler os documentos Relay da página e as respostas de continuação do feed. A projeção seleciona a identidade solicitada e seu preço atual, descartando preço riscado e recomendações de outros anúncios. Os campos disponíveis de descrição, condição, publicação e localização seguem para a observação.

A prova direta encontrou continuação real tanto na categoria Electronics quanto no produto PlayStation 5. A primeira sessão enviada foi removida pelo serviço. A sessão renovada manteve autenticação e permitiu a extração. O arquivo privado e os cookies renovados ficam fora do repositório.

A integração revelou `SynchronousOnlyOperation` quando o event loop da fachada síncrona do Playwright coexistia com o Django na mesma thread. O navegador agora executa em uma thread própria. O teste de regressão reproduziu a falha e passou após a correção. Os seis gates Python passaram com o adaptador real.

Os arquivos adicionais são `marketplace_browser.py`, `relay_parser.py` e `identity.py` no gateway de anúncios, a integração BrasilAPI no gateway de CEP e uma declaração de tipos local da API usada de playwright-stealth. A referência a essa declaração fica na configuração do mypy.

## Resultado da execução autenticada

A instância descartável confirmou 65 anúncios únicos, 65 observações e 65 eventos `initial_load` silenciosos. A execução foi de 2026-11-11T01:55:59.079980+00:00 até 2026-11-11 02:02:07.128935+00:00, incluindo inicialização e leitura dos detalhes. Prontidão e acompanhamento retornaram HTTP 200. O ciclo registrou parcialidade por janela limitada e envio nacional sem comprovação.

A suíte integral teve 143 testes aprovados. Após o ajuste final dos cabeçalhos, os quatro testes dirigidos de navegador e parser/source passaram, assim como a prova direta na fonte real e os seis gates. [Avaliação canônica](eval-report-2026-11-11T02-04-22Z.md)

## Implementação da política aprovada de 48 horas

A revisão acrescenta `PublicationWindow`, campos persistidos de início/fim e evidência por consulta na migração aditiva `0004_listing_publication_window`. Os limites são criados uma vez por ciclo lógico. Descobertas com data conhecida fora da janela são descartadas; revisitas do histórico continuam. A migração e as leituras conservam observações anteriores com campos opcionais ausentes, incluindo o antigo sentinela de localização 0,0.

A cobertura passa a expor candidatura, precisão e os textos “localização aproximada” e “entrega no CEP a confirmar”. Os estados de confirmação de retirada/entrega continuam distintos. Evidência territorial positiva de uma busca não entra em conflito com ausência dessa verificação na busca de envio. A elegibilidade e o envio de alertas seguem os contratos posteriores.

O navegador usa as consultas de leitura e os modelos Relay da página atual, mantendo contexto Comet, filtros geográficos efetivos, cursor do servidor e cadência. O filtro nativo de dias é um conjunto maior que a janela exata; término por ordem requer ordenação nativa e sequência monotônica observada. Ausência ou inversão impede esse atalho. Os detalhes conservam correspondência de identidade e reutilizam o modelo da primeira página para evitar recarregar a interface completa para cada anúncio.

Regressões cobrem limites inclusivos de 48 horas, datas ausentes e futuras, resultado antigo fora de ordem, filtros realmente transmitidos, cursor, contexto dos IDs, união das modalidades e dados históricos. A interface de acompanhamento expõe os limites da janela persistida. O perfil atual e a separação entre candidatura e confirmação estão em [operations.md](operations.md).

### Correção dirigida após a avaliação de 40 páginas

O relatório `eval-report-2026-11-11T13-01-03Z.md` aprovou 23 itens e reprovou somente WRK-FONTE-03. Os 444 anúncios/observações iniciais eram silenciosos; houve 23 candidatos com envio informado. A correção ampliou a proteção para 100 páginas e conservou o banco para a reavaliação.

Foram reproduzidos e corrigidos dois limites adicionais relevantes à retomada: a aquisição imediata do lock rejeitava uma transferência breve da sessão, e um anúncio antigo no fim de uma página mista podia antecipar a fronteira. As regressões exigem espera limitada pelo lock e página inteira antiga com ordenação nativa e observada válidas. A consulta de detalhe reutilizada também relê o documento completo quando sua resposta não contém a identidade pedida. Os testes do navegador passaram após cada reprodução; os seis gates foram aprovados novamente.

### Decisão de indisponibilidade e verificação final local

O usuário aprovou “Registrar indisponibilidade e continuar” para anúncios já acompanhados quando a Meta confirmar a indisponibilidade. A evidência real redirecionou o ID 1532605772041551 para `unavailable_product=1`. O driver agora distingue esse fato de erro técnico, e o caso de uso só o aceita como observação conclusiva para identidade já persistida. Evidências opcionais `source_available` e `availability_evidence` preservam leitura de JSON antigo.

Uma confirmação negativa conserva UUID, vínculos, histórico e último preço conhecido, registra preço atual nulo e cobertura excluída, sem evento de alteração de preço. A leitura oferece a última observação válida. O teste PostgreSQL passou por carga inicial parcial, indisponibilidade de dois anúncios (inclusive produto sem categoria), conclusão do marco e volta com redução de 2300 para 2200. Erros técnicos continuam parciais.

O parser reconhece o marcador nativo `MarketplaceSearchFeedEndOfResults` / `SERP_END_OF_RESULTS`, além de vazio principal explícito, e separa recomendações posteriores. Página vazia intermediária com continuação não comprova término. O ensaio direto confirmou as quatro buscas com limites fixos da janela: 6, 4, 11 e 43 páginas, respectivamente, com fronteira cronológica ou fim explícito do resultado principal.

A suíte integral atual passou com 152 testes em 328,89 s. Os testes dirigidos de navegador/parser/consolidação passaram com 13 aprovações; a regressão de indisponibilidade e volta passou individualmente. Seis gates Python aprovados. A avaliação real final continua no mesmo banco para confirmar marco e retomada; a implementação está pronta para esse veredito.

## Resultado final

F04 aprovada em [eval-report-2026-11-11T14-50-42Z.md](eval-report-2026-11-11T14-50-42Z.md): 24/24 itens e 5/5 critérios verificados. A carga inicial real completou a janela e o marco; a retomada preservou o marco, UUIDs e eventos, recuperou duas publicações feitas durante a parada e revisitou 15 anúncios anteriores à nova janela. Não houve duplicação. A confirmação de indisponibilidade foi persistida preservando a referência de 3800,00 e o histórico.

A suíte integral teve 152 aprovações. Depois dos últimos ajustes de precedência da confirmação e de transporte de proveniência pelo adaptador, os 13 testes dirigidos e a regressão PostgreSQL passaram novamente, junto dos seis gates. O contexto virtual da categoria foi auditado na consulta nativa; ele pode incluir resultados relacionados. Produtos usam correspondência textual de nome/modelo. As instâncias de avaliação foram removidas; a sessão privada externa foi preservada. Não foram feitos commits ou operações de publicação.
