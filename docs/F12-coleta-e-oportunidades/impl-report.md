# Implementação — F12 Coleta e oportunidades

Implementação autorizada pelo pedido de melhoria da coleta e pelas escolhas na conversa. Extensão de intervalo solicitada explicitamente pelo usuário em 2026-11-11 local / 2026-11-12 UTC. Não houve commit, push, PR ou deploy. O repositório já estava sem commit inicial e com o produto não rastreado; trabalhos anteriores foram preservados.

## Resultado implementado

- Uma busca por interesse, sem busca adicional contendo “envio”; chave de escopo versionada.
- Detalhamento intercalado a cada página, publicação a cada dez detalhes e preservação do cursor ao abrir detalhes. Matches posteriores são unidos sem duplicar descoberta/observação.
- Marco persistente de monitoramento e descoberta emitida: anúncios comprovadamente publicados após o marco podem alertar com carga parcial. Adoção em instalação existente começa no instante da migration, sem transformar o estoque anterior em alertas.
- Lucro potencial = revenda estimada − compra − taxa, antes de frete/transporte. Configuração dispensa frete; exploração e alertas dispensam modalidade. Mensagens/revisões antigas conservam seu significado e recibos congelados.
- Eventos sem amostra suficiente/dispersa/vencida aguardam referências por até 48 horas desde a observação, sem intenção prematura; exclusões anteriores permanecem fechadas.
- Categorias selecionáveis: eletrônicos, câmeras, computadores, videogames/consoles, fones e TVs. A rota antiga de celulares permanece identificável e indisponível; novos grupos são filtros independentes, sem inventar hierarquia nativa.
- Identidade conservadora ampliada: iPhones 11–16 por edição/capacidade, Xbox Series S/X em configurações explícitas, Switch por variante/capacidade, corpos avulsos de câmeras selecionadas, GPUs RTX com VRAM e distinção GDDR quando necessária, SKUs completos de TVs e modelos selecionados de fones. As matrizes oficiais e limitações estão na pesquisa.
- Descrições naturais com afirmação de funcionamento são reconhecidas; ressalvas, perguntas, defeitos e acessórios continuam protegidos. Entrada, parcela e somente troca não geram lucro fabricado.

## Correção operacional solicitada durante a validação

A instalação real acumulou oito ciclos classificados como falha, apesar de 557 observações publicadas. O próximo horário foi deslocado em uma hora, sem `Retry-After` da fonte. A nova política usa 60 segundos entre ciclos com progresso, inclusive parcial. Falha geral sem progresso começa em 15 segundos e limita o recuo técnico a 300 segundos; prazo maior pedido pela fonte prevalece. O reconciliador corrige esperas antigas. Os valores foram aplicados também no ambiente de desenvolvimento, sem expor ou substituir os segredos.

Três erros consecutivos de detalhe pausam a tentativa e publicam antes o progresso confirmado. Browser fechado suspende acesso; HTTP 401/403/429, timeout, falha de rede e mudança de contexto possuem diagnósticos seguros. Logs de exceção conservam tipo e localização, sem texto bruto, argumentos, valores locais ou credenciais.

O banco real registrou 146 cancelamentos por timeout ao esperar a trava de publicação. A avaliação de preços fazia correspondência repetida e todas as requisições dentro dessa trava. Agora identifica cada anúncio uma vez, indexa equivalentes por produto, ignora entradas inalteradas e prepara assinaturas fora da trava. Grava requisições em lotes de dez, verificando um marco de observações para descartar preparação ultrapassada por nova coleta. Preserva versionamento e proteção contra publicação fora de ordem.

## Arquivos por responsabilidade

| Área | Arquivos principais |
|---|---|
| Coleta/domínio | `domain/listing/{scope,ports,condition,discovery,scheduling,read_models}.py`; `usecase/listing/collect_listings_usecase.py` |
| Valoração/domínio | `domain/valuation/{identity,electronics_identity,component_identity,consumer_identity,offer_quality,policy,profit}.py` |
| Alertas/configuração | `domain/alert/{alert,eligibility}.py`; `domain/monitoring/configuration.py` |
| Navegador/catálogo | `infra/gateway/listing/{marketplace_browser,facebook_marketplace}.py`; `infra/gateway/monitoring/facebook_categories.json` |
| Persistência | `infra/persistence/{listing_models,monitoring_models}.py`; migration `0012_opportunity_collection.py` |
| Repositórios | `infra/repository/listing/postgres_repository.py`; `infra/repository/valuation/postgres_repository.py`; `infra/repository/alert/{financial,delivery_state}.py` |
| Consultas/apresentação | `infra/queries/listing/{postgres_queries,exploration_source,exploration_mapper,exploration_queries}.py`; `infra/queries/alert/event_source.py`; apresentação de exploração e templates de configuração/lista/detalhe/acompanhamento |
| Diagnóstico | `infra/runtime/logging.py` |
| Regressões | Novo `tests/unit/test_opportunity_improvements.py`; testes existentes de coleta, navegador, configuração, lucro, valoração, exploração, alertas e integrações; fixtures sintéticas correspondentes |
| Documentação | PRD, progresso, CONTEXT e artefatos desta pasta |

Todos os caminhos de código acima partem de `apps/backend/src/garimpei/`.

## Pré-requisitos produzidos

Migration aditiva com marco seguro, preservação de histórico/recibos e atualização do constraint de configuração. Fixtures exercitam novos datados, histórico parcial, adoção de schema, recibo confirmado, preço parcial, variantes, espera por amostra, retomada, limitação de requisições e cadência. Nenhuma credencial nova foi necessária.

## Evidências

- `adapter-category-validation.json`: seis categorias verificadas pelo adaptador real autenticado, com detalhe entre páginas e progresso de IDs; somente contagens/metadados públicos.
- `category-validation.json`: investigação inicial, incluindo rotas rejeitadas e opções sem continuação comprovada.
- `ui-validation.json` e screenshots: formulário sem frete, categorias, lucro único e reflow em desktop/celular, com dados sintéticos identificados.
- Avaliação final: ver relatório timestampado desta pasta para comandos, códigos de saída e resultado por item. Resultados anteriores com falhas foram mantidos em diagnóstico temporário e não tratados como aprovação.

## Limites

A mudança não comprova cobertura integral do Marketplace, aplicação de todos os filtros geográficos nem estabilidade indefinida de acesso. Ordenação solicitada não é tratada como prova de ordenação aplicada. Resultados parciais e amostra insuficiente continuam explícitos. O intervalo é a espera entre ciclos; duração de navegação/enriquecimento depende da fonte. Não há promessa de consulta completa ou alerta a cada 60 segundos. Estimativas usam preços pedidos e não garantem revenda ou lucro realizado.
