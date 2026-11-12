# Pesquisa de coleta e oportunidades — fontes e limites

Consulta em 2026-11-11. Pesquisa somente em código, documentação pública e fontes primárias; sem navegação autenticada, leitura de perfis ou execução da aplicação. Recomendações para a extensão F12; contratos anteriores permanecem históricos. As propostas abaixo não constituem categorias ou rotas novas validadas.

## Fatos observados

### Coleta e continuidade

- Cada interesse gera duas buscas (`pickup` e `shipping`). A segunda acrescenta “envio” ao termo e amplia o raio de 20 para 500 km. Isso altera simultaneamente expressão e geografia, apesar de `_patch_filters()` habilitar ambas as modalidades. A repetição não equivale a duas páginas da mesma busca. Fontes: [scope.py](../../apps/backend/src/garimpei/domain/listing/scope.py), [facebook_marketplace.py](../../apps/backend/src/garimpei/infra/gateway/listing/facebook_marketplace.py), [marketplace_browser.py](../../apps/backend/src/garimpei/infra/gateway/listing/marketplace_browser.py).
- O browser já usa perfil persistente, exclusão por lock e uma thread para a API síncrona. `_open()` reutiliza a página durante sua vida. O handler fecha o recurso ao terminar a execução quando recebe callback de fechamento; perfil persistido não significa processo continuamente aberto. Playwright documenta que o diretório conserva sessão, impede múltiplas instâncias concorrentes e que fechar o contexto persistente fecha o browser. Fontes: [handler](../../apps/backend/src/garimpei/infra/worker/listing_handler.py), [browser](../../apps/backend/src/garimpei/infra/gateway/listing/marketplace_browser.py), [API oficial](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context).
- `_search()` navega, extrai um template Relay e repete a consulta; `_scroll()` normalmente usa seu cursor, com scroll visual apenas como alternativa sem template. O coletor já detecta páginas/continuações repetidas e distingue limite de paginação de fim real. O parser interrompe nos marcadores de fim dos resultados principais. Preservar essas proteções ao ampliar cobertura. Fontes: [browser](../../apps/backend/src/garimpei/infra/gateway/listing/marketplace_browser.py), [coletor](../../apps/backend/src/garimpei/usecase/listing/collect_listings_usecase.py), [parser](../../apps/backend/src/garimpei/infra/gateway/listing/relay_parser.py).
- Atenção à força da prova: `_search()` injeta um objeto `proof` com filtros que o próprio adapter escreveu. `_context()` lê esses valores para marcar ordenação/geografia. Isso comprova parâmetros enviados, não, isoladamente, sua aplicação pela fonte. A checagem de datas descendentes é evidência adicional, mas não demonstra ausência de anúncios omitidos. Fontes: mesmos arquivos, métodos `_search`, `_context` e `_boundary`.
- Há esperas fixas antes/depois de navegação e requisição. A documentação recomenda sincronização por sinais de rede/elementos em vez de `wait_for_timeout` para prontidão. Cadência de acesso e prontidão devem ser controles separados. Fontes: [browser](../../apps/backend/src/garimpei/infra/gateway/listing/marketplace_browser.py), [Page](https://playwright.dev/python/docs/api/class-page#page-wait-for-timeout), [Network](https://playwright.dev/python/docs/network).

### Categorias e significado dos dados

- O catálogo local contém eletrônicos, câmeras, celulares e computadores. Contudo, a evidência F11 relata que `cell-phones` redirecionou ao browse geral. `selectable: true` e uma URL sintaticamente válida não asseguram funcionamento presente. Não foi validada outra categoria nesta pesquisa. Fontes: [catálogo](../../apps/backend/src/garimpei/infra/gateway/monitoring/facebook_categories.json), [validador](../../apps/backend/src/garimpei/infra/gateway/monitoring/facebook_catalog.py), [limitação registrada](../F11-sessao-facebook-por-navegador/catalog-availability-2026-11-11.md).
- A publicação original da Meta descreve busca, categorias, filtros por localização/preço e preço informado pelo vendedor. É contexto histórico, sem garantir rotas, parâmetros, abrangência ou disponibilidade atuais no Brasil. O adapter lê `listing_price`, descrição, condição e disponibilidade; não captura comprovante de transação nem preço final negociado. Consequentemente, sua mediana estima preços pedidos por equivalentes, não vendas realizadas. Fontes: [Meta](https://about.fb.com/news/2016/10/introducing-marketplace-buy-and-sell-with-your-local-community/), [parser](../../apps/backend/src/garimpei/infra/gateway/listing/relay_parser.py), [política](../../apps/backend/src/garimpei/domain/valuation/policy.py). A interpretação estatística é uma inferência sobre esses campos.

### Identidade, comparáveis e lucro

- A identidade só trata iPhone 12/13 e alguns PS5. A regex de iPhone aceita 64/128/256/512 GB independentemente da edição e omite 1 TB. A Apple documenta iPhone 13 comum com 128/256/512 GB e 13 Pro com 128/256/512 GB/1 TB: há combinações inválidas aceitas e válidas rejeitadas. Fontes: [identity.py](../../apps/backend/src/garimpei/domain/valuation/identity.py), [Apple](https://support.apple.com/en-euro/108044).
- “Slim” não prova capacidade nem presença atual de leitor: o anúncio oficial de 2023 descrevia 1 TB nas duas edições, enquanto o manual CFI-21XX distingue 1 TB no console com leitor e 825 GB na edição digital. O leitor pode ser adicionado a modelos compatíveis. Não generalizar a regra de um CFI validado para toda a família. Fontes: [Sony 2023](https://blog.playstation.com/2023/10/10/new-look-for-ps5-console-this-holiday-season/), [manual Sony CFI-21XX](https://www.playstation.com/content/dam/global_pdc/en/corporate/support/manuals/ps5-docs/2100ab/CFI-21XX_PS5_Instruction_Manual_Web%24en.pdf), [leitor Sony](https://direct.playstation.com/en-us/buy-accessories/disc-drive-for-ps5-digital-edition-consoles).
- Comparáveis vêm apenas dos anúncios já persistidos. Precisam de identidade exata, condição usada, disponibilidade confirmada, declaração explícita de funcionamento e demais filtros; a política aplica mediana, mínimo de amostra e dispersão. A referência de novo tem somente uma entrada PS5 no catálogo. Melhorar busca sem enriquecer detalhes pode continuar sem produzir amostra elegível. Fontes: [repositório](../../apps/backend/src/garimpei/infra/repository/valuation/postgres_repository.py), [política](../../apps/backend/src/garimpei/domain/valuation/policy.py), [varejo](../../apps/backend/src/garimpei/infra/gateway/valuation/retail_catalog.json).
- Lucro e alertas ainda dependem de cobertura por modalidade; envio exige frete. Isso precisa ser alterado para a decisão atual: **lucro potencial antes de frete/transporte = revenda estimada − compra − taxa**. Fontes: [profit.py](../../apps/backend/src/garimpei/domain/valuation/profit.py), [elegibilidade](../../apps/backend/src/garimpei/domain/alert/eligibility.py); fórmula nova autorizada na conversa, não derivada de fonte externa.

## Recomendações priorizadas — propostas, não resultados medidos

1. **Desacoplar aquisição de logística.** Uma busca por interesse e escopo geográfico explícito, sem sufixo “envio”. Preservar modalidade como informação opcional. Recalcular lucro/alertas sem bloquear por ausência de envio/retirada; manter disponibilidade, condição, identidade, amostra e carga inicial como requisitos próprios. Escolher a geografia na especificação, sem presumir que remover modalidades autoriza cobertura nacional.
2. **Validar a coleta pela experiência nativa.** Para cada categoria candidata, registrar vínculo original, destino após redirect, contexto retornado, filtros visíveis, IDs recebidos e continuação. Comparar rotas nativas com consultas compostas. Categoria indisponível produz diagnóstico próprio; busca textual alternativa deve aparecer como busca de produto, sem fingir cobertura da categoria. Distinguir “solicitado”, “observado” e “confirmado”.
3. **Aprofundar paginação e detalhes com diagnóstico.** Correlacionar resposta à busca/cursor, registrar IDs novos/repetidos, datas, motivo de término e campos ausentes. Reutilizar o primeiro feed somente após confirmar equivalência dos filtros. Priorizar detalhe dos candidatos com preço/identidade/condição pendentes. Timeout, cursor sem progresso e desafio permanecem estados incompletos; jamais equivalem a catálogo vazio. Interromper no desafio e usar recuperação humana existente.
4. **Expandir eletrônicos por identidade estruturada.** Catálogo versionado de fabricante/família/modelo/variante/capacidade e aliases, com combinações válidas ancoradas em especificações oficiais. Separar identificador do aparelho de acessórios, lotes, peças e capacidade de expansão. Evidência contraditória permanece indeterminada. Avaliar novas famílias pelo material efetivamente coletado, sem declarar suporte geral a todos os eletrônicos.
5. **Formar amostras próprias de equivalentes.** Depois da descoberta, buscar comparáveis do modelo exato e enriquecer detalhes; deduplicar IDs e preservar proveniência. Mostrar amostra, idade, dispersão, exclusões e motivo de indisponibilidade. Não reduzir critérios apenas para gerar oportunidades. Qualquer novo estimador, faixa ou limiar requer avaliação em corpus rotulado, sem metas inventadas.
6. **Medir continuidade antes de redesenhar processos.** Separar custo de inicialização, busca, página, detalhe e bloqueios de lock. Só considerar browser de vida mais longa se a medição justificar, com proprietário único, desligamento explícito e recuperação de falhas. Persistência já existe; ganho operacional ainda é hipótese.

Uma oportunidade calculável continua sendo estimativa sobre anúncios; não garante revenda, liquidez ou lucro realizado. Essa limitação deve acompanhar a fórmula sem reintroduzir dependência de frete.

## Inventário de impacto da decisão aceita

Levantamento estático; nenhum teste executado. Caminhos abaixo são superfícies a revisar, não mudanças realizadas. A alteração atravessa F03/F04/F07/F08/F09.

- **Busca única/F04:** revisar `Search.modality`, `Search.key`, geração de buscas e versão da chave em [scope.py](../../apps/backend/src/garimpei/domain/listing/scope.py); URL, raio, contexto e `pickup_scope_verified` em [facebook_marketplace.py](../../apps/backend/src/garimpei/infra/gateway/listing/facebook_marketplace.py). [PostgresCollectionRepository](../../apps/backend/src/garimpei/infra/repository/listing/postgres_repository.py) persiste `planned`, `query_key`, `scope_key` e marco inicial. Risco: reutilizar ciclos antigos com novo significado das unidades ou gerar alertas de carga inicial. Versionar a semântica do escopo e definir transição explícita, preservando histórico. Revisar [test_listing_policy.py](../../apps/backend/tests/unit/test_listing_policy.py), [test_marketplace_source.py](../../apps/backend/tests/unit/test_marketplace_source.py), [test_collection.py](../../apps/backend/tests/integration/test_collection.py), [test_marketplace_browser.py](../../apps/backend/tests/integration/test_marketplace_browser.py) e [test_facebook_gateway.py](../../apps/backend/tests/integration/test_facebook_gateway.py).
- **Configuração/F03:** `shipping_estimate` é obrigatório em `next_step`, `save_costs` e `_require_complete` de [configuration.py](../../apps/backend/src/garimpei/domain/monitoring/configuration.py); o constraint `monitoring_completion` também exige frete não nulo em configuração ativa, em [monitoring_models.py](../../apps/backend/src/garimpei/infra/persistence/monitoring_models.py). Revisar DTOs `StepInput`/estado do formulário em [usecase/monitoring](../../apps/backend/src/garimpei/usecase/monitoring), [forms/presentation](../../apps/backend/src/garimpei/infra/http/monitoring), [cost_fields.html](../../apps/backend/src/garimpei/infra/http/templates/monitoring/cost_fields.html) e [form.html](../../apps/backend/src/garimpei/infra/http/templates/monitoring/form.html). Retirar a obrigatoriedade exige migração coerente; taxa continua entrada necessária. Cobertura de regressão: [test_monitoring_configuration.py](../../apps/backend/tests/unit/test_monitoring_configuration.py), [test_monitoring_persistence.py](../../apps/backend/tests/integration/test_monitoring_persistence.py), [test_monitoring.py](../../apps/backend/tests/http/test_monitoring.py), [test_tracking.py](../../apps/backend/tests/http/test_tracking.py).
- **Composição/DTOs F07:** [profit.py](../../apps/backend/src/garimpei/domain/valuation/profit.py) contém `ProfitInput.coverage/applicable_freight`, `ModalityProfit`, `principal`, `modalities`, `shipping_freight`, propriedades `profit/freight`, política e motivos por modalidade. A nova composição precisa expor um lucro próprio, independente desses estados, com fórmula/taxa/arredondamento e exclusões explícitos. Revisar leitura corrente/evento em [profit_queries.py](../../apps/backend/src/garimpei/infra/queries/valuation/profit_queries.py); preservar observação imutável, identidade da avaliação, validade e snapshot consistente. Risco: remover coverage indiscriminadamente também libera eventos de escopo antigo. Atualizar [test_profit.py unitário](../../apps/backend/tests/unit/test_profit.py), [integrado](../../apps/backend/tests/integration/test_profit.py), [fixtures](../../apps/backend/tests/fixtures/valuation/cases.json) e [factory](../../apps/backend/tests/factories/valuation.py).
- **Exploração/F08:** `Criteria.modality`, `Offer.pickup/shipping` e parse em [exploration.py](../../apps/backend/src/garimpei/domain/listing/exploration.py); `visible` ainda depende de coverage em [exploration_source.py](../../apps/backend/src/garimpei/infra/queries/listing/exploration_source.py). [exploration_queries.py](../../apps/backend/src/garimpei/infra/queries/listing/exploration_queries.py) filtra modalidade e ordena pela coluna materializada `profit`; [publisher](../../apps/backend/src/garimpei/infra/repository/listing/exploration_repository.py) e [mapper](../../apps/backend/src/garimpei/infra/queries/listing/exploration_mapper.py) persistem composição. Revisar [presentation](../../apps/backend/src/garimpei/infra/http/listing/exploration_presentation.py), [resultados](../../apps/backend/src/garimpei/infra/http/templates/listing/results.html) e [detalhe](../../apps/backend/src/garimpei/infra/http/templates/listing/offer_detail.html): filtro, URLs, rótulo principal e indisponibilidade por cobertura. Risco: decoder novo quebrar revisões antigas ou interface mostrar fórmula nova com ordenação antiga. Testes: [unitário](../../apps/backend/tests/unit/test_exploration.py), [integrado](../../apps/backend/tests/integration/test_exploration.py), [factory](../../apps/backend/tests/factories/exploration.py) e [casos](../../apps/backend/tests/fixtures/listing/exploration_cases.json).
- **Alertas/F09:** retirar a exigência de coverage em [eligibility.py](../../apps/backend/src/garimpei/domain/alert/eligibility.py), `covered/current_eligibility` em [event_source.py](../../apps/backend/src/garimpei/infra/queries/alert/event_source.py) e ambas as chamadas no [repositório](../../apps/backend/src/garimpei/infra/repository/alert/postgres_repository.py). A revalidação antes de enviar usa `current_eligibility` em [delivery_state.py](../../apps/backend/src/garimpei/infra/repository/alert/delivery_state.py); mudar somente a política deixa esse segundo bloqueio. [financial.py](../../apps/backend/src/garimpei/infra/repository/alert/financial.py) congela lucro e `principal`; incluir semântica da nova fórmula e ajustar mensagem. Preservar silêncio inicial, interesse, condição, disponibilidade, revisão/observação, idempotência e confirmação anterior da redução. Revisar [test_alert_policy.py](../../apps/backend/tests/unit/test_alert_policy.py), [test_alert_consumers.py](../../apps/backend/tests/integration/test_alert_consumers.py), [test_alert_delivery.py](../../apps/backend/tests/integration/test_alert_delivery.py) e [fixtures](../../apps/backend/tests/fixtures/alert/cases.json). Não reabrir automaticamente decisões históricas excluídas nem reenviar intenções já confirmadas.

## Matriz oficial para expansão conservadora de identidade

Consulta pública complementar em 2026-11-11. Capacidades são nominais de fábrica; esta matriz não valida anúncios, categorias Facebook, disponibilidade regional nem equivalência de preço entre variantes.

### Apple: iPhone 11–16

Fonte para todas as células: [Apple — identificar o modelo](https://support.apple.com/en-gb/108044). Valores em GB, exceto `1 TB`; `—` significa variante ausente nesta família. Variantes agrupadas em uma célula compartilham capacidades, mas devem conservar identidades distintas.

| Família | Base | mini | Plus | Pro | Pro Max |
| --- | --- | --- | --- | --- | --- |
| 11 | 64/128/256 | — | — | 64/256/512 | 64/256/512 |
| 12 | 64/128/256 | 64/128/256 | — | 128/256/512 | 128/256/512 |
| 13 | 128/256/512 | 128/256/512 | — | 128/256/512/1 TB | 128/256/512/1 TB |
| 14 | 128/256/512 | — | 128/256/512 | 128/256/512/1 TB | 128/256/512/1 TB |
| 15 | 128/256/512 | — | 128/256/512 | 128/256/512/1 TB | 256/512/1 TB |
| 16 | 128/256/512 | — | 128/256/512 | 128/256/512/1 TB | 256/512/1 TB |

O **16e**, listado separadamente pela Apple, tem 128/256/512 GB; não é alias do 16. Exceções para regressão: 11 Pro 128 GB, 12 Pro 64 GB, 13 base 64 GB e 15/16 Pro Max 128 GB são combinações ausentes da matriz oficial. Para anúncios, capacidade ou variante contraditória deve produzir identidade indeterminada, sem correção silenciosa.

### Microsoft: Xbox Series S/X

| Modelo/edição | SSD de fábrica | Leitor | Fonte primária |
| --- | --- | --- | --- |
| Series S Robot White | 512 GB ou 1 TB | Sem leitor | [Xbox Wire, opções de 2024](https://news.xbox.com/en-us/2024/11/15/xbox-series-xs-every-console-option-available-now/) |
| Series S Carbon Black | 1 TB | Sem leitor | [Xbox Wire, lançamento de 2023](https://news.xbox.com/en-us/2023/06/11/xbox-series-s-1tb-black/) |
| Series X Carbon Black | 1 TB | Com leitor | [Xbox, produto](https://www.xbox.com/en-us/consoles/xbox-series-x) |
| Series X Robot White Digital Edition | 1 TB | Sem leitor | [Xbox Wire, opções de 2024](https://news.xbox.com/en-us/2024/11/15/xbox-series-xs-every-console-option-available-now/) |
| Series X Galaxy Black Special Edition | 2 TB | Com leitor | [Xbox Wire, opções de 2024](https://news.xbox.com/en-us/2024/11/15/xbox-series-xs-every-console-option-available-now/) |
| Series X X25 Limited Edition | 1 TB | Com leitor | [Xbox, produto consultado](https://www.xbox.com/en-us/consoles/xbox-series-x) |

Recomendação: não deduzir capacidade pela cor branca; ela ocorre em duas capacidades do Series S. “Series X 1 TB” sem edição/leitor não resolve a diferença física/digital. Edições Galaxy/X25 permanecem separadas ou fora da estimativa até haver comparáveis próprios. Cartão de expansão e HDD externo não alteram a identidade do SSD de fábrica; a [página Xbox](https://www.xbox.com/en-us/consoles/xbox-series-x) os descreve como expansão separada. “Xbox One S/X” não é alias de “Series S/X”.

### Nintendo: Switch original/LCD, Lite e OLED

| Variante | Memória interna nominal | Fonte primária |
| --- | --- | --- |
| Switch padrão/original LCD | 32 GB | [Nintendo FAQ](https://www.nintendo.com/us/gaming-systems/switch/faq/); [especificação atual HAC-001(-01)](https://www.nintendo.com/us/gaming-systems/switch/tech-specs/) |
| Switch Lite HDH-001 | 32 GB | [Nintendo, especificações](https://www.nintendo.com/us/gaming-systems/switch/tech-specs/) |
| Switch OLED HEG-001 | 64 GB | [Nintendo, comparação oficial](https://www.nintendo.com/us/gaming-systems/switch/compare/) |

A Nintendo separa memória interna de microSD; parte da memória interna é reservada ao sistema. “Switch OLED + cartão 256 GB” não significa OLED de fábrica com 256 GB. Recomendações: exigir variante explícita; “Switch” ou “Switch 32 GB” não distingue LCD de Lite. Não inferir revisão V1/V2 pela capacidade; a especificação pública consultada nomeia HAC-001(-01). Edições temáticas e conjuntos incompletos merecem atributo próprio ou exclusão conservadora da comparação. Esta seção não inclui Switch 2.

## Complemento: câmeras e placas de vídeo

Consulta pública em 2026-11-11. Os nomes abaixo fundamentam identificação técnica; não comprovam equivalência comercial, funcionamento nem presença de todos os itens no anúncio. Nenhum anúncio real foi inspecionado nesta pesquisa.

### Câmeras: modelo do corpo e composição da oferta

| Fabricante | Modelos/aliases oficiais confirmados | Fonte primária |
| --- | --- | --- |
| Canon | EOS Rebel T5i = EOS 700D = Kiss X7i | [Lista oficial de câmeras Canon EDSDK](https://developercommunity.usa.canon.com/resource/1727731595000/CDC_EDSDKRAW_Compat_List) |
| Canon | EOS Rebel T6i = EOS 750D = Kiss X8i | [Canon EDSDK](https://developercommunity.usa.canon.com/resource/1727731595000/CDC_EDSDKRAW_Compat_List) |
| Canon | EOS Rebel T7i = EOS 800D = Kiss X9i | [Canon EDSDK](https://developercommunity.usa.canon.com/resource/1727731595000/CDC_EDSDKRAW_Compat_List) |
| Canon | EOS Rebel SL2 = EOS 200D = Kiss X9 | [Canon EDSDK](https://developercommunity.usa.canon.com/resource/1727731595000/CDC_EDSDKRAW_Compat_List) |
| Canon | EOS Rebel SL3 = EOS 250D = EOS 200D II = Kiss X10 | [Canon EDSDK](https://developercommunity.usa.canon.com/resource/1727731595000/CDC_EDSDKRAW_Compat_List) |
| Canon | EOS 80D; EOS 90D — modelos separados | [Canon EDSDK](https://developercommunity.usa.canon.com/resource/1727731595000/CDC_EDSDKRAW_Compat_List) |
| Nikon | D3300; D3500; D5300; D5600; D7100; D7200; D750 — sete modelos separados | [Lista oficial de corpos DSLR compatíveis](https://imaging.nikon.com/sport-optics/lineup/dsystem/fsa-l2/) |
| Sony | α6000 / a6000 = ILCE-6000; α6300 / a6300 = ILCE-6300 | [Sony, tabela de corpos e lentes](https://www.sony.co.jp/en/Products/diacc/compatibilities/body_case_lens/) |
| Sony | α6400 / a6400 = ILCE-6400 | [Sony, produto](https://electronics.sony.com/imaging/interchangeable-lens-cameras/aps-c/p/ilce6400-b) |

**Corpo, lente avulsa e kit são composições distintas.** A Canon anunciou a EOS 90D em corpo avulso, kit EF-S 18–55 IS STM e kit EF-S 18–135 IS USM. A Sony oferece a a6400 em corpo avulso, corpo + 16–50 e corpo + 18–135. A Nikon lista D3500 Body Only e D3500 + AF-P DX 18–55 VR. São provas diretas de configurações separadas, sem transportar seus preços históricos para o mercado usado. Fontes: [Canon, lançamento](https://www.usa.canon.com/newsroom/2019/20190828-camera), [Sony, opções](https://electronics.sony.com/imaging/interchangeable-lens-cameras/aps-c/p/ilce6400-b), [Nikon, kits](https://www.nikon-asia.com/products/cameras/cameras-dslr/d3500-camera-kits) — a última listagem foi recuperada no índice da busca; abertura direta retornou 403.

Recomendação de identidade: separar `body_model`, `offer_kind` (corpo/kit/lente) e conjunto de lentes identificadas por modelo completo. Exigir declaração positiva de corpo avulso para compará-lo com outro corpo avulso; ausência de menção à lente não prova sua ausência. Para kits, “18–55” sozinho não prova a versão da lente. “Lente para T7i”, “carregador D750” e listas de compatibilidade não identificam a câmera como objeto vendido. T5 não é T5i, T6 não é T6i, T7 não é T7i; 200D não é 200D II; D750 não é D7500. Vários modelos de corpo ou composição desconhecida continuam indeterminados. Esses são critérios conservadores propostos, não conclusões de valor de mercado.

### NVIDIA GeForce: matriz de VRAM para placas desktop

| GPU | VRAM nominal oficial | Tipo de memória | Fonte primária |
| --- | --- | --- | --- |
| RTX 2060 | 6 GB ou 12 GB | GDDR6 | [NVIDIA, comparação série 20](https://www.nvidia.com/en-us/geforce/graphics-cards/compare/) |
| RTX 3060 | 8 GB ou 12 GB | GDDR6 | [NVIDIA, família 3060](https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3060-3060ti/) |
| RTX 3060 Ti | 8 GB | GDDR6 ou GDDR6X | [NVIDIA, família 3060](https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3060-3060ti/) |
| RTX 3070 | 8 GB | GDDR6 | [NVIDIA, família 3070](https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3070-3070ti/) |
| RTX 3080 | 10 GB ou 12 GB | GDDR6X | [NVIDIA, família 3080](https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3080-3080ti/) |
| RTX 4060 | 8 GB | GDDR6 | [NVIDIA, série 40](https://www.nvidia.com/en-au/geforce/graphics-cards/40-series/) |
| RTX 4060 Ti | 8 GB ou 16 GB | GDDR6 | [NVIDIA, série 40](https://www.nvidia.com/en-au/geforce/graphics-cards/40-series/) |
| RTX 4070 | 12 GB | GDDR6 ou GDDR6X | [NVIDIA, família 4070](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4070-family/) |
| RTX 4070 SUPER | 12 GB | GDDR6X | [NVIDIA, família 4070](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4070-family/) |
| RTX 4070 Ti | 12 GB | GDDR6X | [NVIDIA, família 4070](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4070-family/) |
| RTX 4070 Ti SUPER | 16 GB | GDDR6X | [NVIDIA, família 4070](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4070-family/) |

As páginas NVIDIA separam modelos e, na RTX 3080, mostram também diferenças de núcleos/barramento entre versões de 10/12 GB. Portanto, capacidade diferente não é apenas acessório; não agrupar suas amostras automaticamente. RTX 3060 Ti “12 GB” e RTX 4070 Ti “16 GB” não correspondem às combinações da matriz — a última pode estar confundida com Ti SUPER, sem autorização para corrigi-la automaticamente.

Recomendação de matching: preservar sufixos `Ti`/`SUPER` e VRAM, distinguindo também GDDR6/GDDR6X quando aplicável e documentado. Nos modelos com múltiplas capacidades, VRAM omitida impede equivalência completa; a inferência de capacidade única, se adotada, deve ter proveniência de catálogo e não ser apresentada como declaração do vendedor. A matriz é **desktop**: não aplicar a notebooks, GPUs móveis, computadores completos, carcaças, coolers ou placas “para peças”. Fabricante da placa/SKU, refrigeração, garantia e estado podem alterar o preço; compartilhar GPU/VRAM não estabelece equivalência comercial. No caso de GDDR6/GDDR6X indeterminada, manter a lacuna explícita e definir na política se ela impede a estimativa.

## Complemento: televisores brasileiros e fones

Consulta pública em 2026-11-11. As páginas abaixo comprovam códigos/modelos do fabricante; não comprovam identidade ou estado de um anúncio nem validam categorias do Marketplace.

### TVs: tamanho, série e código completo

| Fabricante/família comercial | Tamanho | Código completo publicado no suporte brasileiro | Fonte primária |
| --- | --- | --- | --- |
| Samsung AU7700 | 50” | `UN50AU7700GXZD` | [Samsung Brasil](https://www.samsung.com/br/support/model/UN50AU7700GXZD/) |
| Samsung AU7700 | 55” | `UN55AU7700GXZD` | [Samsung Brasil](https://www.samsung.com/br/support/model/UN55AU7700GXZD/) |
| Samsung CU7700 | 50” | `UN50CU7700GXZD` | [Samsung Brasil](https://www.samsung.com/br/support/model/UN50CU7700GXZD/) |
| Samsung CU7700 | 55” | `UN55CU7700GXZD` | [Samsung Brasil](https://www.samsung.com/br/support/model/UN55CU7700GXZD/) |
| LG UR8750 | 50” | `50UR8750PSA.BWZ` (modelo comercial `50UR8750PSA`) | [LG Brasil](https://www.lg.com/br/suporte/suporte-ao-producto/cs-50UR8750PSA.BWZ/) |
| LG UR8750 | 55” | `55UR8750PSA.BWZ` (modelo comercial `55UR8750PSA`) | [LG Brasil](https://www.lg.com/br/suporte/suporte-ao-producto/cs-55UR8750PSA.BWZ/) |

Recomendação conservadora: manter `model_code`, `screen_inches` e sufixo/revisão declarado, validando coerência entre código e tamanho. `UN50AU7700`, `UN55AU7700`, `UN50CU7700` e `UN55CU7700` são prefixos dos códigos brasileiros acima, **não SKU exato**. Não acrescentar `GXZD` por ser anúncio brasileiro, nem resolver “Samsung 50 4K” para um desses modelos. Na LG, distinguir modelo comercial completo de código de suporte com extensão `.BWZ`; não fabricar essa extensão quando ausente. Identidade parcial pode organizar descoberta, mas não deve satisfazer comparação que exige SKU completo. AU e CU, 50 e 55 polegadas, extensões diferentes ou tamanho contraditório permanecem separados/indeterminados.

Também exigir que o objeto vendido seja a TV inteira: “controle para UN50AU7700GXZD”, “placa principal”, “display”, “pé/base” e “TV para peças” não são comparáveis funcionais de um televisor completo. Suporte de parede e soundbar vendidos junto são composição adicional; não estimar o conjunto como TV avulsa sem política explícita. Essas regras são propostas de matching, sem inferir equivalência de mercado.

### Fones: modelo completo e objeto vendido

| Identidade de modelo | Distinção documental útil | Fonte primária |
| --- | --- | --- |
| Sony `WH-1000XM4` | Especificação própria; driver de 40 mm | [Sony Brasil](https://www.sony.com.br/electronics/support/wireless-headphones-bluetooth-headphones/wh-1000xm4/specifications) |
| Sony `WH-1000XM5` | Especificação própria; driver de 30 mm | [Sony Brasil](https://www.sony.com.br/electronics/support/wireless-headphones-bluetooth-headphones/wh-1000xm5/specifications) |
| JBL `Tune 510BT` | Modelo on-ear; Bluetooth 5.0 | [JBL Brasil](https://www.jbl.com.br/TUNE510BT-.html) |
| JBL `Tune 520BT` | Modelo on-ear; Bluetooth 5.3 | [JBL Brasil](https://www.jbl.com.br/TUNE520BT.html) |
| JBL `Tune 720BT` | Modelo over-ear; Bluetooth 5.3; cabo de áudio destacável | [JBL Brasil](https://www.jbl.com.br/TUNE720BT.html) |

Recomendação: normalizar apenas grafia (caixa, espaços/hífens convencionais), preservando a família `WH`, geração `XM4/XM5` e sufixo inteiro `BT`. “Sony XM4”, “JBL 520”, “JBL Bluetooth” e modelos com outros sufixos não resolvem automaticamente para a tabela. `WF`, `BTNC`, `NC` ou números adicionais não devem ser descartados pelo parser para obter um match. A Sony também documenta `WH-1000XM5SA` no [guia conjunto](https://helpguide.sony.net/mdr/wh1000xm5/v1/pt/index.html); compartilhar manual não autoriza fundi-lo ao XM5 na precificação.

“Almofada/espuma para WH-1000XM4”, “case Tune 720BT”, “cabo”, “arco”, “peça de reposição” e anúncios de réplica não identificam um fone original completo para comparação. Modelo reconhecido continua separado de funcionamento, autenticidade, composição e saúde da bateria. Cor e acessórios podem ser atributos próprios; a decisão de agrupá-los exige política, sem assumir equivalência comercial pela semelhança do nome.
