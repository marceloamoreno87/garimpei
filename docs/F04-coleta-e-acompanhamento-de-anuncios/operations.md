# Operação do coletor Facebook Marketplace

## Preparação

As dependências Playwright 1.65.0 e playwright-stealth 2.0.3 estão fixadas em `apps/backend/uv.lock`. O navegador verificado é Chromium 158.0.8127.18, revisão Playwright 1254.

```bash
uv sync --project apps/backend --frozen
uv run --project apps/backend --frozen --no-sync playwright install chromium
```

A sessão fornecida pelo usuário fica em `/home/marce/.config/garimpei/facebook-storage-state.json`, modo 0600, fora do checkout. O importador de ambiente verifica essa privacidade. Usar a referência no ambiente privado da instância, junto dos segredos de Django, PostgreSQL e WAHA preparados conforme F02.

```bash
export GARIMPEI_FACEBOOK_STATE_FILE=/home/marce/.config/garimpei/facebook-storage-state.json
./scripts/init.sh
```

A configuração F03 confirmada libera a coleta. A avaliação usa nome próprio e `init.sh --disposable`; a limpeza é `stop.sh --clean`, somente na instância de avaliação identificada.

## Navegação e estado privado

O navegador usa playwright-stealth na criação dos contextos para alinhar JavaScript, User-Agent e client hints, com idioma pt-BR, fuso America/Sao_Paulo e viewport 1357 × 1271. Plataforma e renderer WebGL preservam os valores do sistema. A aplicação usa uma aba e uma thread próprias por tarefa, navegação cadenciada e contexto reutilizado.

Um lock no diretório privado serializa o arquivo de sessão. A aquisição aguarda por até o timeout configurado para permitir a transferência entre tentativas; se continuar ocupado, a tarefa registra indisponibilidade de sessão sem abrir outro navegador. O navegador grava a sessão renovada atomicamente com modo 0600. Sessão expirada ou desafio interrompem novas navegações da tarefa. Falhas aparecem por códigos fixos, sem cookies, tokens ou dados de perfil nos logs. Esses ajustes não garantem que a fonte aceite uma execução futura.

## Consulta e contexto efetivo

A busca abre a rota do interesse e lê o modelo da consulta Relay entregue pela própria página. A execução da consulta acontece no contexto autenticado do navegador, pela mesma origem, mantendo nome, documento e variáveis atuais da página. O documento não é um ID fixo no código. A chamada lê os tokens no próprio navegador e não os devolve no resultado da consulta. A aplicação seleciona campos de anúncios; metadados temporários de página e de sessão não são gravados como anúncios nem incluídos nos logs.

A consulta de leitura informa centro obtido pela BrasilAPI CEP v2, raio de referência, ordenação descendente de publicação e filtro nativo por dias. `__comet_req=15` conserva o contexto Comet e os IDs usados nas rotas de detalhe. Sem esse contexto, a fonte forneceu IDs alternativos em um ensaio; eles não servem como prova de identidade canônica.

As URLs sozinhas não comprovam os filtros: a conta testada conservava raio de 6 km apesar de `radius=20`. A implementação verifica os parâmetros efetivamente transmitidos. Retirada usa 20 km; candidatos com envio usam busca ampliada de 500 km e termo adicional `envio`. Essa busca permite origens brasileiras além do município de São Paulo, mas não comprova cobertura exaustiva de todos os anúncios do Brasil. O coletor só projeta envio quando houver evidência explícita no anúncio.

As categorias usam ID ou rota do catálogo F03. Electronics usa o ID 479353692612078 e o rótulo pt-BR observado. Produtos usam o texto configurado. Títulos sem a sequência de tokens do produto são descartados pela correspondência; resultados de categoria e identidades já acompanhadas conservam sua revisita.

A continuação usa o cursor retornado pelo servidor. O primeiro detalhe abre a página e fornece o modelo atual `MarketplacePDPContainerQuery`; os seguintes usam a mesma consulta de leitura com o ID solicitado, mantendo a cadência. Se a consulta não devolver essa identidade com preço, o navegador relê a página completa para renovar o contexto antes de registrar detalhe indisponível. A projeção exige identidade correspondente, lê o preço atual em BRL e ignora recomendações de outros anúncios, preço riscado e parcelas. Só campos do anúncio necessários ao produto são persistidos.

## Janela de publicação

Cada ciclo fixa os limites inclusivos UTC `[início - 48 horas, início]` no PostgreSQL. Uma nova tentativa do mesmo ciclo conserva esses limites. O filtro nativo por dias recebe um conjunto de dias que contém toda a janela; a aplicação aplica o recorte exato pelos timestamps de publicação. O filtro de calendário isolado não prova as 48 horas.

O fim da janela exige esgotamento verificável do resultado ou ordenação nativa descendente, sequência observada sem inversões e uma página inteira anterior ao limite inferior. Uma página que mistura publicações dentro e fora da janela continua a busca, mesmo se o anúncio antigo estiver no final. Data ausente e inversão desabilitam a parada antecipada por ordem. Resultado antigo isolado não encerra uma sequência fora de ordem. Página repetida, falha ou teto de segurança mantêm a parcialidade.

Os logs JSON de páginas registram interesse/modalidade, número de página, quantidade, primeiro/último timestamp, continuação, ordenação, raio e prova de fronteira. O ciclo conserva a prova por consulta em `window_evidence`. Esses registros permitem auditar o perfil efetivamente percorrido sem expor a sessão.

Anúncios novos com data conhecida fora da janela não geram descoberta. Datas ausentes continuam nulas. Anúncios conhecidos continuam revisitados mesmo depois das 48 horas. A carga inicial termina somente após buscas e gravações completas; seus eventos são silenciosos. A retomada posterior mantém o marco e a identidade.

## Localização e envio

BrasilAPI e Marketplace fornecem coordenadas sem raio de precisão por anúncio. Os pontos estimados dentro de 20 km e no município de São Paulo são candidatos com “localização aproximada”. Sem coordenadas utilizáveis, a distância fica nula; a candidatura exige evidência territorial da busca e retirada informada. O sentinela histórico 0,0 de registros antigos permanece indisponível.

Envio estruturado ou declaração explícita, como “envio para todo o Brasil”, permite candidatura. Sem confirmação para o destino vigente, a leitura informa “entrega no CEP a confirmar”. Uma estimativa de frete não comprova envio nem entrega. Confirmações e recusas do CEP permanecem separadas, assim como o frete observado e seu destino.

## Parâmetros

| Variável | Padrão com sessão real |
|---|---|
| `GARIMPEI_FACEBOOK_STATE_FILE` | Referência explícita ao arquivo privado |
| `GARIMPEI_FACEBOOK_CADENCE_MS` | 1200 ms |
| `GARIMPEI_LISTING_TIMEOUT` | 20 s por operação |
| `GARIMPEI_LISTING_LEASE` | 60 s, renovada nos checkpoints |
| `GARIMPEI_LISTING_INTERVAL` | 600 s após concluir o ciclo |
| `GARIMPEI_LISTING_MAX_PAGES` | 100 páginas de proteção por consulta |
| `GARIMPEI_LISTING_RETRY_BASE` | 900 s |
| `GARIMPEI_LISTING_RETRY_MAX` | 3600 s |

O perfil real de avaliação usa intervalo de 60 s e recuo de 3600 s. Quantidades e duração variam com a fonte. O teto permanece uma proteção e nunca substitui a prova da janela. A conclusão da F04 depende do relatório canônico completo do contrato.

## Histórico de medições

A execução anterior, antes da revisão aprovada em 2026-11-11, gravou 65 anúncios e atingiu o teto de duas páginas, deixando o marco inicial aberto. O relatório anterior permanece preservado. A revisão implementa retirada aproximada, envio informado e descoberta/recuperação nas últimas 48 horas. Os novos resultados são registrados separadamente na avaliação atual.

A avaliação de 40 páginas gravou 444 anúncios, 444 observações e 444 eventos iniciais silenciosos. Somente a consulta ampliada de produto/envio atingiu o teto. O primeiro relatório atual registrou 23 PASS e 1 FAIL; a correção amplia o teto para 100 e mantém o mesmo banco. O agendamento da instância descartável é antecipado uma vez para executar a reavaliação; o relógio UTC e as publicações continuam reais.

## Indisponibilidade confirmada e retomada

O usuário aprovou registrar a indisponibilidade confirmada de anúncio já acompanhado e continuar o ciclo. O redirecionamento nativo `unavailable_product=1`, vinculado ao ID solicitado e com sessão aceita, sustenta esse fato. Uma resposta incompleta, falha HTTP, bloqueio ou ausência na busca continua sendo falha técnica. Para identidade ainda não acompanhada, a confirmação não conclui automaticamente sua primeira leitura.

A observação negativa tem preço atual desconhecido, cobertura excluída e referência histórica preservada. Não gera alteração de preço. Uma posterior volta mantém o UUID e compara preço com a última evidência conhecida anterior à indisponibilidade. JSON anterior continua legível com campos opcionais ausentes.

A fonte pode devolver `has_next_page=true` para recomendações após o fim principal. O parser reconhece `MarketplaceSearchFeedEndOfResults` / `SERP_END_OF_RESULTS` e vazio principal explícito, conserva os resultados anteriores ao marcador e ignora recomendações posteriores. Uma página vazia intermediária com continuação não encerra a janela. A medição complementar percorreu 6 páginas na retirada de Electronics, 4 no envio da categoria, 11 na retirada do produto e 43 no envio do produto.

Na prova de retomada, o worker é encerrado pelo lifecycle. Uma leitura independente e sem persistência identifica uma publicação feita durante a parada; só então o worker é reiniciado e deve recuperar a oferta pelo caminho normal. Esse observador não cria publicações nem grava identidades/eventos na aplicação.

## Avaliação concluída

A execução final concluiu o marco inicial em 2026-11-11T14:03:37.360907+00:00. O worker ficou parado de 14:03:40 até 14:15:22 UTC e retomou no mesmo banco. A retomada concluiu com duas publicações recuperadas desse intervalo, 15 anúncios mais antigos revisitados e zero duplicações. Ver [eval-report-2026-11-11T14-50-42Z.md](eval-report-2026-11-11T14-50-42Z.md) para evidência por item.

O campo nativo `serp_landing_settings.virtual_category_id` conserva o contexto Electronics. A Meta pode incluir ofertas relacionadas nessa categoria virtual; isso não equivale a uma taxonomia estrita de cada oferta. Para produtos, a aplicação verifica a sequência textual configurada. A recuperação de uma identidade não confirma retirada, entrega ou elegibilidade para alerta.
