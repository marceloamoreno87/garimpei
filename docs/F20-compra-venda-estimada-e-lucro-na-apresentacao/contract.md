# Contrato — F20: Compra, venda estimada e lucro na apresentação

*Gerado por spec-writer. Edições manuais são substituídas na regeneração.*

## Prerequisites

Estas condições fazem parte da entrega futura. Pré-requisito ausente impede executar os itens afetados; a geração deste documento não comprova que a implementação ou o cenário já existem.

### Runtime services

- F07/F08/F09/F12 integradas; Python 3.13, Django/uv conforme lock, PostgreSQL, web/worker separados e ferramentas do harness disponíveis. Criar instância própria `GARIMPEI_ENV=eval`, com `GARIMPEI_INSTANCE` exclusivo e `GARIMPEI_ENV_FILE` privado; usar `./scripts/init.sh --disposable` pelas factories existentes. Confirmar manifesto/banco `garimpei_` próprios e `/health/ready` 200, conforme operação F02.
- Fonte sintética e fake WAHA nomeado servidos localmente pelas factories; nenhum perfil Facebook, grupo, conta ou credencial pessoal. Confirmar endpoints sintéticos no cenário e captura de mensagens pelo fake. O worker usa a mesma instância/banco da web.
- Lab de apresentação da spec §7 disponível com instrução exata em `operations.md`, criação de diretório privado temporário, publicação de URL/IDs/revisões sintéticas e comandos de alteração/falha/reinício/encerramento. Ele reutiliza as factories atuais; não pressupor comando ou fixture implícita. Encerrar somente processos próprios; limpeza só em instância descartável identificada.

### Persistent state

- **CONFIG**: configuração concluída com CEP sintético `01001000`, interesse por produto suportado e taxa 10%, sem valor logístico obrigatório. A preparação usa o assistente/factories F03 e confirma CEP/interesses/taxa/revisão pela leitura de configuração. O cenário inicial não usa defaults de taxa em produção.
- **A / B**: publicações sintéticas, identificadas por revisão/data, criadas pelo fluxo de coleta/avaliação/publicação existente. Em A, **POSITIVO** tem compra 1000, venda 1500, taxa 10% / 150 e lucro 350; em B, compra 900, venda 1600, taxa 20% / 320 e lucro 380. Confirmar a composição pela leitura de F07 e a associação da publicação/observação em F08, antes de executar os itens.
- **ZERO / NEGATIVO / FRACAO**: compras 1350/1400/70, vendas 1500/1500/101, taxas 10%/10%/12,50%, lucros 0/−50/18,37; FRACAO tem taxa monetária arredondada de 12,63. **SEM_VENDA**, **SEM_COMPRA**, **NOVO_APENAS** e **INCOMPATIVEL** expõem componentes ausentes/incompatíveis e motivos conhecidos. Confirmar os valores e estados pelas leituras de F06/F07 e publicações F08. Contradição/corrupção sintética é produzida só pelo lab isolado.
- **PAGINADO**: 42 ofertas no mesmo recorte, com ZERO/NEGATIVO/SEM_VENDA nas posições 40/41/42; os demais lucros permitem conferir a ordenação vigente. Criar pela factory de exploração adaptada à política F12 e verificar 42 identidades distintas e páginas 20/20/2.
- **REDUCAO**: primeiro envio confirmado com compra 1200, evento de redução para 1000 e observação posterior de 900; a composição do evento tem venda 1500 e taxa 10%. Preparar pela factory de alertas e confirmar observações, evento e recibo pela leitura de estado da instância.
- **LEGADO_AUTORIZADO**: corpo exato do formato anterior, sem venda, com suas referências e estados fila/retry seguro/confirmado/incerto em instâncias ou execuções separadas. **LEGADO_SEM_CORPO**: intenção existente sem corpo/tentativa e decisão antiga incompleta. Preservar cópia de comparação dos corpos/referências antes da adoção aditiva. Criar pelo lab de compatibilidade, exercitando o estado persistido anterior e verificando os registros antes dos itens; nunca alterar dados pessoais para simular legado.

### Static inputs

- `apps/backend/tests/fixtures/valuation/financial_presentation.json`: catálogo determinístico dos casos acima, valores decimais em BRL, texto do produto suportado, identidades, observações, referências/revisões, disponibilidade e resultados esperados. Entregável da implementação; validar leitura e associação das entradas antes dos itens.
- `apps/backend/tests/factories/financial_presentation_lab.py`: cenário reproduzível conforme spec §7, com fonte/fake WAHA, relógio controlado, revisões, estados legados e falhas de leitura/retomada. Operação documentada em `operations.md`. Usado por todos os itens; o dado visual é sintético e não comprova cobertura de fonte real.
- Amostras de usados suportam a venda por F06 com cinco identidades distintas funcionais e observações válidas; referência de novo de 2400 fica separada. Verificar retenção/mediana e validade, sem inserir apenas uma venda arbitrária desvinculada da avaliação.

### Configuration

- Instantes UTC controlados e consistentes; o primeiro evento novo a alertar é posterior ao marco persistente exigido pela F12, com interesse e condição elegíveis. F16 não é exigida. Recebimento de comparáveis e mudança de taxa não fabricam descoberta.
- Fakes fornecem confirmação, timeout/incerteza e histórico consultável nos cenários indicados. Verificar número de POSTs, corpo capturado, referência, destino sintético e recibo; logs/relatórios não contêm segredos ou dados pessoais.
- Navegador local em 360/768/1440 px, zoom 200% e teclado. Confirmar a aplicação servida e os estáticos antes das capturas. Prova de canal real não é pré-requisito desta fronteira sintética e só ocorre com autorização específica de envio/destino/mensagem, registrada separadamente.

## Quality gates

Cada gate deve passar para considerar a implementação pronta. Pré-requisito ausente, gate falho ou jornada não executada conserva a pendência; este contrato não registra resultados de execução.

- **Seis gates Python** — `node scripts/run-gates.mjs` — tipos, lint/templates, limites, arquitetura, ciclos e código/dependências não utilizados.
- **Testes Python e PostgreSQL** — `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests` — cenários monetários, HTML, snapshot, migração/compatibilidade e retomada sem regressões.
- **Django** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check` — configuração válida.
- **Migrations** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py makemigrations --check --dry-run` — schema corresponde às migrations entregues.
- **Estáticos** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py collectstatic --noinput` — templates e ativos usados são coletáveis.
- **Build Python** — `uv build --directory apps/backend --no-build-isolation` — distribuição inclui templates, ativos e migration utilizados.
- **Tokens** — `python3 docs/design/generate_tokens.py --check` — tokens e CSS gerados permanecem sincronizados.
- **Jornadas e acabamento** — executar itens UI/E2E com `playwright-cli` e avaliar com `frontend-ui-design` — evidência de desktop/largura estreita/zoom, rótulos, destaque, sinais, paginação, contexto e recuperação. Registrar relatório junto da feature.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F20-AC01**: cada card, detalhe e mensagem autorizada após a adoção de F20 mostra conjuntamente, nessa ordem, Preço de compra, Preço de venda estimado e Lucro estimado, em BRL com centavos e derivados da mesma composição aplicável. Referência de novo não preenche venda de usado. Mensagens de primeiro alerta e redução preservam título, data e link. | API-FINANCEIRO-01, API-FINANCEIRO-02, WRK-MENSAGEM-01, WRK-MENSAGEM-02, WRK-MENSAGEM-06, E2E-COMPOSICAO-01 |
| **F20-AC02**: configuração, filtros, cards, detalhes e novas mensagens não exibem campos, títulos ou explicações geradas de frete/transporte, nem exigem custo logístico. Salvar, reabrir a configuração e reiniciar conservam CEP, interesses e percentual da taxa; evidências originais, dados históricos, recibos e corpos autorizados permanecem intactos. | UI-CONFIGURACAO-01, UI-CONFIGURACAO-02, UI-CONFIGURACAO-03, WRK-MENSAGEM-01, E2E-MENSAGEM-02 |
| **F20-AC03**: no cenário sintético compra R$ 1.000,00, venda estimada R$ 1.500,00 e taxa configurada de 10%, exibir lucro estimado R$ 350,00 e, nos detalhes, taxa de 10% e R$ 150,00. Com a mesma venda/taxa, compra de R$ 1.350,00 produz lucro R$ 0,00 e compra de R$ 1.400,00 produz lucro negativo de R$ 50,00, com sinal visível e sem ocultar a oferta. Esses números são teste, não padrões de configuração; aplicar o arredondamento vigente também a casos com fração de centavo. | API-FINANCEIRO-02, UI-FINANCEIRO-02, API-FINANCEIRO-03, WRK-MENSAGEM-08 |
| **F20-AC04**: sem venda estimada válida, manter compra conhecida e indicar venda/lucro indisponíveis, com motivo nos detalhes. Sem compra, indicá-la como indisponível e não calcular lucro. Nenhum caso usa zero substituto, outra variante, referência de novo ou preço criado por IA. A oferta continua visível e não ganha elegibilidade por preencher apenas rótulos. | UI-FINANCEIRO-03, UI-FINANCEIRO-04, WRK-MENSAGEM-03 |
| **F20-AC05**: nova mensagem congela compra, venda, percentual/valor da taxa e lucro da mesma revisão/observação; recálculo posterior, mudança de taxa, alteração visual e reinício não modificam corpo autorizado nem geram reenvio. Conferir valores com a composição congelada, mesmo quando a lista já apresenta uma revisão posterior. | WRK-MENSAGEM-01, WRK-MENSAGEM-04, E2E-COMPOSICAO-02, E2E-MENSAGEM-01, E2E-MENSAGEM-02 |
| **F20-AC06**: navegador comprova o trio completo e legível na lista/detalhes em desktop e largura estreita, na ordem compra → venda estimada → lucro, com maior destaque tipográfico para o lucro e compra/venda próximas no mesmo grupo. Rótulos e sinais permanecem acessíveis, sem depender apenas de cor ou causar overflow, mantendo ordenação, filtros, páginas de 20 e atualização mediante clique. Novas mensagens preservam a mesma ordem e destacam rótulo/valor do lucro em negrito; conteúdo é verificado pelo mesmo snapshot financeiro, com prova de canal real separada quando autorizada. | UI-FINANCEIRO-01, API-FINANCEIRO-03, UI-ATUALIZACAO-01, UI-ATUALIZACAO-02, WRK-MENSAGEM-01, WRK-MENSAGEM-02, WRK-MENSAGEM-08 |
| **F20-AC07**: intenção anterior à adoção de F20, já com corpo autorizado, mantém seu texto/valores originais em fila, retomada, confirmação ou reconciliação, ainda que não contenha venda estimada. A atualização de formato não completa esse dado com a avaliação atual, não cria intenção duplicada nem repete POST possivelmente transmitido; recibos anteriores continuam associados ao mesmo evento e destino. | WRK-MENSAGEM-05, WRK-MENSAGEM-07, E2E-MENSAGEM-02 |
| **F20-AC08**: composição ausente ou incompatível informa indisponibilidade sem misturar revisões ou autorizar mensagem com valores inconsistentes. Falha de atualização conserva a leitura anterior aplicável com revisão/data, erro visível e opção de tentar novamente, preservando filtros/página; a falha não confirma atualização nem libera alerta. | UI-FINANCEIRO-04, UI-ATUALIZACAO-03, API-FINANCEIRO-04, WRK-MENSAGEM-03 |

## HTTP API

**Verification mode:** Solicitar as rotas HTML completas e parciais na instância isolada; conferir código, corpo e links de contexto. Efeitos assíncronos são verificados em Worker/E2E.

### Apresentação financeira

#### `API-FINANCEIRO-01` — Trio da publicação selecionada
- given: revisão A publicada, revisão B posterior disponível e lista fixada em A.
- when: GET `/ofertas/` com filtros, página 2, revisão A e, em execução equivalente, cabeçalho HTMX.
- then:
  - Responder 200 com o trio completo por card na ordem compra, venda estimada e lucro.
  - Os valores correspondem à composição A de cada oferta, sem componentes da revisão B.
  - Links de detalhe e paginação conservam filtros e revisão A.

#### `API-FINANCEIRO-02` — Detalhe e taxa da mesma composição
- given: POSITIVO na revisão A e referência independente de novo de R$ 2.400,00.
- when: GET do detalhe de POSITIVO com revisão A.
- then:
  - Mostrar compra R$ 1.000,00, venda estimada R$ 1.500,00 e lucro estimado R$ 350,00 nessa ordem.
  - Mostrar taxa de 10% equivalente a R$ 150,00 na composição detalhada.
  - A referência de novo R$ 2.400,00 permanece separada da venda estimada de usado.
  - Metadados permitem identificar a publicação e a composição consultadas.

#### `API-FINANCEIRO-03` — Paginação preserva zero, negativo e indisponível
- given: 42 ofertas filtradas publicadas, com ZERO, NEGATIVO e SEM_VENDA nas posições 40, 41 e 42 e lucro ordenado pelas regras vigentes.
- when: consultar cada página do mesmo recorte, em execuções independentes.
- then:
  - As páginas apresentam respectivamente 20, 20 e 2 identidades sem repetição.
  - ZERO e NEGATIVO continuam no conjunto, com R$ 0,00 e sinal negativo de R$ 50,00; SEM_VENDA permanece sem lucro numérico.
  - O trio não altera a ordem global nem cria filtro de lucro mínimo.

#### `API-FINANCEIRO-04` — Erros preservam seus significados
- given: entradas malformadas, oferta inexistente, publicação expirada e falha controlada de leitura, em cenários separados.
- when: solicitar a lista ou o detalhe correspondente a cada cenário.
- then:
  - Retornar respectivamente 400, 404, 410 e 503, sem apresentar falha como lista vazia válida.
  - A recuperação oferecida para versão expirada ou falha conserva o recorte válido solicitado.

## UI

**Verification mode:** Navegar pela aplicação local com `playwright-cli`, conferir conteúdo, ordem de leitura, contexto e estilos computados e capturar evidência visual das telas. Avaliar acabamento com `frontend-ui-design`.

### Apresentação financeira

#### `UI-FINANCEIRO-01` — Grupo financeiro legível e lucro em destaque
- given: POSITIVO disponível na lista e nos detalhes.
- when: abrir cada superfície em 360, 768 e 1440 px e com zoom de 200%, em execuções independentes.
- then:
  - O grupo mostra integralmente “Preço de compra”, “Preço de venda estimado” e “Lucro estimado”, nessa ordem visual e de leitura.
  - Compra e venda permanecem próximas e legíveis no mesmo grupo do lucro.
  - O lucro tem maior destaque tipográfico que compra/venda, preservando a qualificação de estimativa.
  - Não há overflow da página nem corte de rótulos/valores/sinais; estados permanecem compreensíveis sem depender de cor.

#### `UI-FINANCEIRO-02` — Zero, negativo e arredondamento
- given: ZERO, NEGATIVO e FRACAO publicados com as entradas da fixture.
- when: abrir o detalhe de cada caso, em execuções independentes.
- then:
  - ZERO apresenta lucro R$ 0,00; NEGATIVO apresenta lucro negativo de R$ 50,00 com sinal visível.
  - FRACAO apresenta compra R$ 70,00, venda R$ 101,00, taxa 12,50% / R$ 12,63 e lucro R$ 18,37.
  - Os valores conservam centavos e rótulos; as ofertas não são ocultadas pelo resultado financeiro.

#### `UI-FINANCEIRO-03` — Componentes ausentes não fabricam valores
- given: SEM_VENDA, SEM_COMPRA e NOVO_APENAS publicados, com respectivos motivos e componentes conhecidos.
- when: abrir lista/detalhe de cada caso, em execuções independentes.
- then:
  - SEM_VENDA conserva compra conhecida e exibe venda/lucro indisponíveis.
  - SEM_COMPRA identifica compra indisponível e não mostra lucro calculado.
  - NOVO_APENAS conserva a referência independente de novo, sem usá-la como venda estimada.
  - O motivo do componente indisponível é acessível nos detalhes; nenhum caso usa zero ou valor deduzido para preencher lacuna.

#### `UI-FINANCEIRO-04` — Composição incompatível é explícita
- given: INCOMPATIVEL com oferta legível e composição ausente ou de outra identidade/observação/variante, em cenários separados.
- when: abrir seus detalhes.
- then:
  - Mostrar “Composição indisponível para esta revisão”.
  - Preservar apenas os componentes cuja associação à oferta e à observação esteja comprovada.
  - Venda/lucro incompatíveis permanecem indisponíveis, sem combinar revisão antiga com compra atual.

### Configuração sem logística

#### `UI-CONFIGURACAO-01` — Configurar sem campos logísticos
- given: instalação sintética sem configuração concluída, com CEP e interesses de teste preparados nas etapas anteriores.
- when: concluir o assistente com taxa de 10% e sem enviar campo logístico.
- then:
  - A configuração é concluída com sucesso e conduz ao acompanhamento existente.
  - O formulário apresenta somente os campos pertinentes ao fluxo atual, com a taxa preservada e sem custo logístico obrigatório.
  - Campos, títulos e explicações gerados de frete/transporte não aparecem no fluxo financeiro ativo.

#### `UI-CONFIGURACAO-02` — Reabrir configuração preservada
- given: CONFIG salva sem campos logísticos e aplicação reiniciada pela preparação do cenário.
- when: abrir `/configuracoes/`.
- then:
  - CEP, interesses e taxa de 10% correspondem ao estado confirmado antes do reinício.
  - O formulário continua sem campo logístico ou exigência de valor de frete/transporte.

#### `UI-CONFIGURACAO-03` — Textos financeiros e evidência original
- given: oferta com descrição original contendo “frete” e snapshot histórico preservado.
- when: abrir lista/detalhes e configuração financeira.
- then:
  - Rótulos, filtros, subtítulos e explicações financeiros gerados pelo produto não incluem frete/transporte.
  - A descrição original continua legível e não é apagada por mencionar frete.
  - A taxa percentual e seu valor continuam explicados nos detalhes.

### Atualização explícita e recuperação

#### `UI-ATUALIZACAO-01` — Aviso mantém composição anterior
- given: lista na revisão A com filtros, página e foco conhecidos; revisão B publicada.
- when: a consulta de novidades informa a atualização.
- then:
  - Exibir o aviso e a ação de atualizar sem substituir o trio da revisão A.
  - Preservar identidades, ordem, página, filtros e foco até o clique.

#### `UI-ATUALIZACAO-02` — Clique aplica nova composição
- given: lista na revisão A com aviso da revisão B e página ainda existente no novo recorte.
- when: acionar “Atualizar lista”.
- then:
  - O trio passa integralmente à composição B aplicável, com revisão/data identificáveis.
  - Aba, busca, categoria e página válida são preservadas.
  - A revisão aplicada é confirmada e o foco segue a convenção existente da exploração.

#### `UI-ATUALIZACAO-03` — Falha conserva leitura e recuperação
- given: lista ou detalhe da revisão A já carregado, com atualização B disponível e falha controlada da leitura de B.
- when: acionar a atualização.
- then:
  - Mostrar “Não foi possível atualizar os valores. Tente novamente” com ação de recuperação no mesmo contexto.
  - Conservar os valores de A com sua revisão/data; não confirmar aplicação de B.
  - Preservar filtros e página, com resultados anteriores acessíveis.

## Worker

**Verification mode:** Executar o fluxo normal de decisões, autorização, envio e reconciliação na instância isolada; observar mensagens capturadas pelo fake WAHA e estado persistente de intenções/tentativas/recibos. Não chamar helpers internos como superfície contratual.

### Mensagens financeiras

#### `WRK-MENSAGEM-01` — Primeiro alerta com trio completo
- given: POSITIVO elegível pelas regras F12, evento novo posterior ao marco de monitoramento, canal sintético ativo e intenção ainda sem autorização.
- when: processar a primeira autorização/envio da intenção.
- then:
  - O corpo capturado apresenta compra R$ 1.000,00, venda estimada R$ 1.500,00 e lucro estimado R$ 350,00, nessa ordem e com os rótulos completos.
  - Rótulo e valor do lucro estão em negrito no corpo, com qualificação de estimativa preservada.
  - Título, origem, data, link e referência persistente permanecem presentes, sem explicação gerada de frete/transporte.
  - O snapshot autorizado identifica os mesmos evento/observação/composição e conserva taxa de 10% / R$ 150,00 junto dos três valores.

#### `WRK-MENSAGEM-02` — Redução usa composição do evento
- given: REDUCAO com primeiro envio confirmado a R$ 1.200,00, evento de redução a R$ 1.000,00 elegível e observação posterior a R$ 900,00; composição do evento usa venda R$ 1.500,00 e taxa 10%.
- when: processar a autorização/envio desse evento de redução.
- then:
  - O corpo “Preço reduzido” apresenta compra R$ 1.000,00, venda R$ 1.500,00 e lucro R$ 350,00 da observação do evento.
  - A compra posterior de R$ 900,00 não substitui a compra autorizada de R$ 1.000,00.
  - O corpo conserva título, data, link e lucro em negrito; eventual preço anterior fica separado do trio.

#### `WRK-MENSAGEM-03` — Dados ausentes ou incompatíveis não autorizam corpo novo
- given: intenção ainda sem corpo/tentativa com composição ausente, incompleta ou incompatível, incluindo casos SEM_VENDA e INCOMPATIVEL.
- when: processar a próxima avaliação/autorização dessa intenção, em execuções independentes.
- then:
  - Nenhuma mensagem com componentes inventados ou misturados é autorizada ou enviada.
  - O motivo persistido distingue espera por dados de incompatibilidade, conforme o fluxo vigente.
  - O sistema não recupera venda/taxa por diferença entre valores nem usa referência de novo ou IA para completá-las.

#### `WRK-MENSAGEM-04` — Corpo congelado sobrevive a mudanças
- given: mensagem A já autorizada com snapshot completo; composição B e taxa nova foram publicadas e o canal ainda precisa concluir o passo permitido pela F09.
- when: retomar o processamento da intenção A.
- then:
  - O corpo e o snapshot A permanecem idênticos aos autorizados antes da mudança.
  - Evento, destino e referência persistente continuam vinculados à mesma intenção.
  - A mudança de formato/configuração não cria evento, intenção retroativa ou envio adicional; transmissão incerta segue reconciliação.

#### `WRK-MENSAGEM-05` — Corpo legado autorizado conserva seu formato
- given: LEGADO_AUTORIZADO em fila, retry seguro, confirmação ou reconciliação, em cenários separados, com corpo anterior que não contém venda estimada.
- when: processar o próximo passo permitido pela F09 para a intenção correspondente.
- then:
  - O corpo permanece byte a byte igual ao registro original, sem venda/taxa preenchidas a partir da oferta atual.
  - Evento, destinatário vinculado, tentativas e recibos mantêm sua associação.
  - Um envio incerto ou confirmado não provoca novo POST por causa da adoção de F20.

#### `WRK-MENSAGEM-06` — Intenção antiga ainda não autorizada
- given: LEGADO_SEM_CORPO sem tentativas e com decisão financeira antiga incompleta; F07 possui composição completa aplicável ao mesmo evento/observação.
- when: processar a primeira autorização da intenção após adoção de F20.
- then:
  - O corpo novo contém o trio completo da composição validada para o evento.
  - Snapshot e corpo ficam associados à intenção original; nenhum evento ou intenção adicional é criado.
  - Não há preenchimento por dados de observação incompatível ou dedução de venda a partir do lucro.

#### `WRK-MENSAGEM-07` — Falta de corpo com tentativa prévia exige revisão
- given: tentativa persistente possivelmente transmitida cujo corpo necessário à reconciliação está ausente.
- when: retomar o processamento da intenção.
- then:
  - A inconsistência permanece identificada para revisão, com a tentativa preservada.
  - Nenhum corpo substituto é fabricado e nenhum POST é repetido para reparar a lacuna.

#### `WRK-MENSAGEM-08` — Zero, sinal negativo e centavos nas mensagens
- given: ZERO, NEGATIVO e FRACAO elegíveis e sem autorização prévia, com composições válidas, em cenários separados.
- when: processar a primeira autorização/envio de cada intenção.
- then:
  - O corpo mantém o trio na ordem aprovada e lucro respectivamente R$ 0,00, negativo de R$ 50,00 e R$ 18,37.
  - Rótulo e valor do lucro ficam em negrito, preservando sinal e centavos.
  - O snapshot de FRACAO conserva taxa 12,50% e R$ 12,63 da composição, sem novo arredondamento divergente na mensagem.

## E2E

**Verification mode:** Exercitar web, banco e worker da mesma instância, usando fonte e WAHA sintéticos. Comparar composição publicada, conteúdo HTML e corpo autorizado/capturado, incluindo retomada. A prova em canal real é separada e requer autorização explícita de envio.

### Composição entre superfícies

#### `E2E-COMPOSICAO-01` — Uma composição sustenta cada superfície
- given: POSITIVO da revisão A publicado a partir de F07/F08/F12 e sua intenção elegível F09 ainda não autorizada.
- when: concluir o processamento dessa intenção com a web aberta na revisão A.
- then:
  - Card, detalhe, snapshot e mensagem usam compra R$ 1.000,00, venda R$ 1.500,00 e lucro R$ 350,00 da mesma composição aplicável.
  - A taxa do snapshot corresponde aos 10% / R$ 150,00 explicados nos detalhes.
  - Nenhuma etapa usa referência de novo para completar o trio.

#### `E2E-COMPOSICAO-02` — Revisões diferentes permanecem identificáveis
- given: mensagem A autorizada e lista ainda aberta em A; revisão B com compra R$ 900,00, venda R$ 1.600,00, taxa 20% / R$ 320,00 e lucro R$ 380,00 publicada.
- when: aplicar B na lista pela ação de atualização.
- then:
  - Lista/detalhes de B exibem o trio B e permitem identificar essa revisão.
  - O corpo/snapshot A conservam seus valores e referências, mesmo após a atualização da interface.
  - A publicação/aplicação de B não reenvia a mensagem A.

### Mensagens e retomada

#### `E2E-MENSAGEM-01` — Reinício e concorrência preservam autorização
- given: autorização A confirmada no armazenamento e interrupção controlada antes de concluir o envio, com revisão/taxa posteriores disponíveis.
- when: reiniciar os processos próprios e retomar a intenção com concorrência controlada.
- then:
  - Existe somente um corpo/snapshot autorizado para a intenção e ele continua sendo A.
  - A criação de tentativas e o destino respeitam a exclusão/idempotência da F09; não ocorre POST adicional por concorrência ou mudança de formato.
  - Situação possivelmente transmitida continua em reconciliação, sem reenvio automático.

#### `E2E-MENSAGEM-02` — Adoção aditiva conserva histórico
- given: banco isolado com corpos legados autorizados, eventos, tentativas e recibos registrados antes da migração, e nova oferta sem intenção.
- when: adotar o formato F20 pelo lifecycle próprio, sem novos eventos de negócio.
- then:
  - Corpos, tentativas e recibos anteriores mantêm seus dados e vínculos.
  - Não surgem mensagens, intenções ou descobertas retroativas apenas por aplicar a migração/formato.
  - CEP, interesses e taxa configurados permanecem intactos.
