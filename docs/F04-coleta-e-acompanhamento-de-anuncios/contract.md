# Contract — F04 Coleta e acompanhamento de anúncios

*Gerado por spec-writer. Revisado em 2026-11-11 conforme as decisões de retirada aproximada, envio informado e janela de 48 horas aprovadas pelo usuário.*

## Prerequisites

### Runtime services

- Usar ambiente descartável e isolado da F02 com PostgreSQL, Django e worker Procrastinate. Instalar versões travadas, subir com `./scripts/init.sh` e verificar banco da execução com prefixo `garimpei_`, web/worker e processamento de `runtime_probe --wait` conforme [operações F02](../F02-fundacao-tecnica-e-ambiente-local/operations.md). Aplicar as migrations Django e da fila. Para a jornada web, instalar o Chromium do `playwright-cli` se ausente, usar sessão dedicada e conferir que a URL local abre.
- A aplicação deve poder iniciar com o adaptador de teste, por composição dedicada, apontando para um servidor local com respostas programáveis. Registrar chamadas nesse servidor. Para os itens de recuperação, usar o mesmo banco ao parar e voltar com `./scripts/stop.sh` e `./scripts/init.sh`. Quando a falha exigir término abrupto, usar apenas o PID do worker de teste identificado no manifesto.

### Persistent state

- Preparar banco vazio migrado, rascunho F03 e configuração ativa em execuções independentes. Criar rascunho e ativa pela jornada F03 ou por factory que use os casos de uso. Verificar pela interface de configuração confirmada que o rascunho retorna `configured=false` e a ativa retorna `configured=true` com ID, revisão, CEP e interesses correspondentes.
- Para cenários com histórico, produzir a carga pelo worker com a primeira sequência da fixture e confirmar pelo estado da coleta e pela leitura de anúncios/eventos. Para simular falha de persistência, usar uma composição de teste que falhe antes do commit indicado e verifique o rollback. Para pausar uma tentativa em concorrência, usar o servidor local controlável ou uma barreira de teste no limite de gravação. Confirmar que a pausa ou a falha ocorreu antes de prosseguir. Usar as mesmas migrations e o mesmo caminho de agendamento da aplicação.

### Static inputs

- A implementação deve fornecer fixtures sanitizadas e um driver local reproduzível em `apps/backend/tests/fixtures/listing/` e `apps/backend/tests/factories/`. Usar IDs externos distintos A, B, C, D e E nas asserções, todos com links de detalhe válidos no formato da fonte. Montar busca de `Electronics` com o ID do catálogo F03, subcategoria `cameras` e busca `PlayStation 5`. A aparece em categoria e produto, inclusive em página posterior com URL rastreada. B aparece apenas na subcategoria. C aparece apenas na busca de produto. D, com título `PlayStation 50`, aparece apenas como resultado textual impreciso. E simula republicação de A com título e preço iguais e outro ID. A contém preço BRL 2300, título `PlayStation 5 Slim`, link e texto de condição. Os detalhes das fixtures identificam a origem dos campos. Conferir essa matriz e a ordem das respostas pelo registro de chamadas da fonte local.
- Fornecer variações de preço de A por ciclo, com 2300, 2200, ausência, 2400 e 2200, e de nova publicação recuperável durante a parada. Preparar cenários de vazio confirmado, páginas válidas com campos ausentes, contexto territorial errado, continuação interrompida, sessão inválida, limite da fonte e detalhe indisponível. Cada variante deve ser identificável pelo estado retornado e produzir o erro previsto pelo cenário.
- Fixar na fixture um CEP sintético de oito dígitos como referência e outro como destino distinto. Usar pontos de distância conhecida em São Paulo (SP) a 19,9 km, 20 km e 20,1 km do primeiro, além de ponto em outro município próximo e localização de precisão insuficiente. Calcular a distância esperada independentemente da implementação, com pontos de teste geodésicos e precisão declarada. Incluir entrega confirmada para o CEP configurado, entrega explicitamente recusada, confirmação só para outro CEP e envio genérico com frete observado. Conferir o mapa do adaptador de CEP e o contexto da evidência de entrega.

- Preparar também uma identidade já acompanhada com confirmação explícita de indisponibilidade, uma resposta sem essa confirmação e a volta da oferta com preço menor. Conferir pela leitura a disponibilidade, o histórico, a referência anterior de preço e a distinção em relação à falha técnica.

### Configuration

- Preparar pela configuração central a fonte de teste, o perfil de janela, o intervalo, o tempo de resposta, a espera de recuperação e um relógio controlável para cenários determinísticos. Conferir a configuração efetiva e avançar o relógio até a próxima tentativa ou vencimento da lease. A prova real usa perfil medido e documentado com os valores efetivamente executados. Dados de sessão e CEP privado ficam fora de logs, fixtures compartilhadas e versionamento.

- Preparar a janela inclusiva de `início do ciclo - 48 horas` até `início do ciclo`, com relógio controlado. Fornecer anúncios exatamente no limite, imediatamente antes e depois, com data ausente e em ordem misturada. Incluir um anúncio já acompanhado cuja publicação excede 48 horas para verificar sua revisita. Confirmar que uma nova tentativa do mesmo ciclo conserva os limites.
- A prova real precisa identificar a ordenação, a semântica do filtro temporal quando usado e a fronteira efetivamente percorrida. O número de páginas isolado não comprova a janela.

### External dependencies

Atualização autorizada em 2026-11-11. O usuário forneceu e renovou uma sessão própria e solicitou explicitamente scraping com stealth. A execução real passa a iniciar com essa sessão privada. A avaliação verifica o acesso efetivamente observado, a extração e a cobertura do perfil descrito em [operations.md](operations.md). A distinção entre sessão aceita, bloqueio e dados públicos continua explícita.

- Para `WRK-FONTE-01` a `WRK-FONTE-03`, verificar as condições de automação da Meta, preparar o driver e navegador confirmados e comprovar acesso conforme o perfil operacional. Usar a sessão privada fornecida e autorizada pelo usuário em arquivo externo ao repositório. Verificar sua aceitação com evidência sanitizada. A sessão é uma condição de autenticação. As condições de automação seguem a política da fonte. [Política publicada pela Meta](https://about.fb.com/br/news/2021/04/como-combatemos-a-raspagem-de-dados/).
- Preparar a base ou provedor de CEP validado e um destino de teste em São Paulo, mantendo o CEP fora da evidência pública quando privado. Conferir origem e versão dos dados, município e a precisão declarada. Identificar amostras reais com retirada aproximada e envio informado pelo canal permitido. Registrar evidências de campo, consulta, destino consultado de forma redigida, data, fronteira da janela e resultados. A integração real fica pendente quando acesso, dados ou amostra obrigatória estiverem indisponíveis. A prova PlayStation 5 da F01 e as fixtures locais sustentam apenas seus respectivos cenários.

## Quality gates

Cada gate precisa passar para a feature ser considerada pronta. Executar da raiz, com dependências preparadas e ambiente de teste isolado.

- **Seis gates backend** — `node scripts/run-gates.mjs` — tipos, lint Python/templates, limites de dependência, arquitetura, ciclos e código/dependências sem uso.
- **Testes Python e PostgreSQL** — `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests` — persistência, worker, falhas e regressões F02/F03, com os serviços obrigatórios disponíveis.
- **Django** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check` — registro e configuração consistentes.
- **Migrations** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py makemigrations --check --dry-run` — modelos versionados. A aplicação real da migração é verificada no PostgreSQL.
- **Estáticos** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py collectstatic --noinput` — assets da interface empacotáveis.

## Coverage Manifest

| Critério de aceite do PRD §9 | Itens |
|---|---|
| **F04-AC01**: a integração da primeira plataforma obtém anúncios associados às categorias e nomes/modelos configurados, conservando identidade, origem, link e preço disponíveis. | SVC-ANUNCIOS-01, WRK-COLETA-01, WRK-FONTE-01 |
| **F04-AC02**: a coleta contempla retirada em São Paulo (SP), com 20 km do CEP como referência aproximada e indicação de incerteza, e candidatos de origens no Brasil com envio informado; sem confirmação específica, a entrega aparece como “entrega no CEP a confirmar”. Frete estimado não serve como prova de entrega. | SVC-COBERTURA-01, SVC-COBERTURA-02, WRK-FONTE-02 |
| **F04-AC03**: carga inicial, anúncio novo e redução de preço são distinguíveis; após reinício, o acompanhamento preserva o marco inicial e as identidades já conhecidas. | WRK-COLETA-02, WRK-COLETA-03, WRK-COLETA-04, WRK-COLETA-08, WRK-COLETA-09, EVT-HISTORICO-01, EVT-HISTORICO-02 |
| **F04-AC04**: a retomada atualiza os anúncios acompanhados e recupera publicações disponíveis na fonte dentro da janela das últimas 48 horas; a execução comprova o término dessa janela e preserva identidades e eventos. Falhas de acesso ou paginação permanecem explícitas; preço, data e entrega desconhecidos conservam sua incerteza. | SVC-ANUNCIOS-02, SVC-COBERTURA-02, WRK-COLETA-04, WRK-COLETA-05, WRK-COLETA-06, WRK-COLETA-07, WRK-COLETA-08, WRK-COLETA-09, WRK-FONTE-03, UI-ACOMPANHAMENTO-02 |
| **F04-AC05**: a primeira coleta aguarda a conclusão da configuração de F03, percorre a janela das últimas 48 horas e é silenciosa; seu marco termina após a conclusão verificável das buscas e gravações, admitindo candidatos com localização aproximada ou entrega a confirmar. Os reinícios retomam o acompanhamento salvo sem recriar a instalação inicial. | WRK-COLETA-02, WRK-COLETA-03, WRK-COLETA-04, WRK-COLETA-10, UI-ACOMPANHAMENTO-01, E2E-CONFIGURACAO-01, E2E-CONFIGURACAO-02, E2E-CONFIGURACAO-03 |

A fronteira da F04 em INT-01 e INT-09 é coberta pela ingestão de interesses e pelo início condicionado à configuração confirmada. As saídas para INT-02, INT-03, INT-04, INT-05 e INT-11 são verificadas em `Service`, `Worker` e `Event`. Para INT-07 e INT-08, o contrato verifica histórico, conteúdo, retomada e silêncio dos eventos que alimentam F09. Elegibilidade, envio e apresentação das listas têm contratos próprios.

## Service

**Verification mode:** Consultar as interfaces de leitura publicadas para F05, F06, F07, F08 e F09 sobre estado persistido pelo worker.

### Anúncios

#### `SVC-ANUNCIOS-01` — Campos disponíveis na origem
- given: A foi coletado com a evidência de preço, texto de condição e link da fixture.
- when: consultar A pelo UUID local.
- then:
  - A leitura conserva UUID, ID externo, origem Facebook Marketplace e link canônico.
  - A leitura retorna 2300,00 BRL, título e texto de condição observados.
  - A identificação e a publicação têm campos distintos. A publicação é nula quando a fonte omite sua data.

#### `SVC-ANUNCIOS-02` — Informação ausente permanece desconhecida
- given: A última observação válida de um anúncio tem identidade verificável, sem preço ou frete informado e sem evidência de condição.
- when: consultar o anúncio.
- then:
  - Preço e frete observados são nulos, inclusive com frete estimado cadastrado.
  - O campo de evidência de condição é indisponível.
  - Para anúncio já acompanhado cuja indisponibilidade a fonte confirmou explicitamente, a leitura expõe esse estado, preço atual nulo, cobertura excluída e a última observação válida. Identidade, histórico e referência de preço são preservados.

### Cobertura

#### `SVC-COBERTURA-01` — Retirada no raio aproximado de referência
- given: anúncios com retirada explícita nos pontos de teste, inclusive posições aproximadas e localização insuficiente.
- when: consultar cada anúncio da matriz de retirada.
- then:
  - Os pontos estimados de 19,9 km e 20 km em São Paulo (SP) são candidatos ao recorte de referência e expõem a indicação de localização aproximada quando aplicável.
  - O ponto estimado de 20,1 km e o ponto de outro município são identificados como fora do recorte de referência, conservando a proveniência da estimativa.
  - Sem coordenadas utilizáveis, a distância numérica é nula. Um filtro aproximado comprovadamente aplicado pela fonte pode sustentar a candidatura, com o grau de precisão explícito.

#### `SVC-COBERTURA-02` — Envio informado e confirmação do destino
- given: anúncios de envio da matriz, inclusive origem fora de São Paulo, envio genérico e configuração com frete estimado.
- when: consultar cada anúncio da matriz de entrega.
- then:
  - Envio explicitamente informado permite ler o candidato. Sem confirmação específica do CEP vigente, a projeção informa “entrega no CEP a confirmar”.
  - Respostas positiva e negativa para o CEP vigente permanecem distintas. Confirmação para outro CEP conserva a entrega no destino vigente como desconhecida.
  - O frete observado conserva sua origem e escopo. O frete aplicável ao CEP é nulo sem vínculo verificável. Frete ou estimativa de frete isolados não comprovam envio ou entrega.

## UI

**Verification mode:** Abrir ou recarregar a rota local pelo navegador. Verificar conteúdo, navegação e as chamadas registradas pelo servidor da fonte de teste.

### Acompanhamento

#### `UI-ACOMPANHAMENTO-01` — Primeira coleta real
- given: F03 confirmada e primeira coleta em execução.
- when: abrir `/acompanhamento/`.
- then:
  - A página apresenta a coleta inicial em andamento e oferece acesso às configurações.
  - A leitura da página não dispara consulta externa.

#### `UI-ACOMPANHAMENTO-02` — Falha visível e histórico preservado
- given: houve uma coleta completa e a tentativa mais recente terminou parcial ou indisponível.
- when: abrir `/acompanhamento/`.
- then:
  - A página comunica a falha ou parcialidade e distingue o último sucesso da tentativa atual.
  - A configuração continua acessível.

## Worker

**Verification mode:** Executar o worker pelo lifecycle normal e observar chamadas da fonte, estado de coleta e dados nas interfaces publicadas. Usar as sequências locais controladas em `WRK-COLETA-*` e a fonte real em `WRK-FONTE-*`.

### Coleta

#### `WRK-COLETA-01` — União de interesses e identidade estável
- given: configuração com categoria, subcategoria e produto da fixture principal.
- when: executar um ciclo completo.
- then:
  - Há buscas separadas para os interesses configurados e a continuação prevista é consultada.
  - A, B, C e E ficam disponíveis. D não é associado ao produto da fixture.
  - A tem uma identidade e uma observação no ciclo, vinculadas aos interesses correspondentes.
  - A e a republicação E têm identidades distintas.

#### `WRK-COLETA-02` — Término silencioso da carga inicial
- given: configuração confirmada, sem marco inicial, e todas as consultas previstas disponíveis.
- when: completar o primeiro ciclo.
- then:
  - O estado passa a acompanhamento ativo após comprovar e gravar a janela de publicação das últimas 48 horas do ciclo, admitindo candidatos com localização aproximada ou entrega no CEP a confirmar.
  - Cada anúncio identificado pela primeira vez tem evento `initial_load` marcado como silencioso.
  - O histórico desse ciclo não contém eventos candidatos a alerta. O marco registra os limites UTC da janela confirmada.
  - A confirmação explícita de indisponibilidade de uma identidade já acompanhada é registrada sem impedir o marco; erro técnico ou detalhe sem confirmação continua impedindo a conclusão.

#### `WRK-COLETA-03` — Reinício antes do marco inicial
- given: a primeira passagem foi interrompida entre dois lotes de gravação, com a varredura consolidada e o marco ainda aberto.
- when: reiniciar o worker no mesmo banco com a fonte novamente disponível.
- then:
  - A passagem retoma o escopo confirmado e os limites de janela persistidos do mesmo ciclo, terminando o marco após a cobertura requerida.
  - Identidades e eventos iniciais gravados permanecem únicos.
  - Os anúncios ainda não observados antes da interrupção são registrados como carga inicial silenciosa.

#### `WRK-COLETA-04` — Retomada depois do marco
- given: o worker parou após a carga inicial, A continua acessível com preço reduzido e há publicação nova recuperável pela busca durante a interrupção.
- when: reiniciar o worker no mesmo banco.
- then:
  - A mantém identidade e é revisitado, inclusive se acessível só por detalhe.
  - Seu preço atualizado gera uma redução com preço anterior e novo.
  - A publicação recuperada, disponível nas últimas 48 horas do novo ciclo, gera `discovered` e o marco inicial permanece o mesmo. Uma publicação imediatamente anterior à janela não é apresentada como recuperada por essa busca.

  - Na matriz determinística da fonte local, o limite exato de 48 horas é inclusivo, publicações anteriores ficam fora da descoberta e um resultado antigo fora de ordem não encerra a busca sem prova de ordenação. Os limites de uma tentativa retomada do mesmo ciclo permanecem os persistidos.

#### `WRK-COLETA-05` — Falha parcial de acesso
- given: uma consulta produz resultados válidos e outra termina com bloqueio, sessão inválida, continuação interrompida ou contexto incorreto.
- when: executar o ciclo previsto.
- then:
  - O estado registra resultado parcial ou indisponível com motivo verificável.
  - O último sucesso integral permanece intacto. Se a carga inicial estiver aberta, seu marco continua aberto.
  - Observações válidas já confirmadas permanecem consultáveis. A falta de leitura não substitui o preço anterior por um valor inventado.
  - Confirmação explícita de indisponibilidade de um anúncio já acompanhado preserva seu histórico e último preço conhecido, exclui a candidatura atual e permite concluir o ciclo quando o restante estiver completo. Uma posterior volta usa a mesma identidade e a referência de preço anterior à indisponibilidade.

#### `WRK-COLETA-06` — Vazio verificável
- given: a fonte devolve vazio confirmado para todas as buscas no contexto pretendido e não há detalhes conhecidos pendentes.
- when: executar um ciclo completo.
- then:
  - O estado registra uma passagem bem-sucedida com zero novos anúncios.
  - O término da carga inicial é permitido nessa janela vazia confirmada.

#### `WRK-COLETA-07` — Rollback e tentativa recuperável
- given: uma gravação de observação e evento falha antes do commit.
- when: executar a tentativa agendada.
- then:
  - O progresso dessa gravação e o evento não ficam visíveis.
  - O estado permite nova tentativa durável. Um ciclo incompleto não atualiza o último sucesso integral.

#### `WRK-COLETA-08` — Nova tentativa após expiração
- given: a execução anterior perdeu a lease e uma nova geração processou a mesma janela.
- when: liberar a execução antiga para tentar gravar.
- then:
  - O estado, os dados e os eventos publicados pela nova geração permanecem íntegros.
  - O mesmo resultado de negócio não é duplicado.

#### `WRK-COLETA-09` — Escopo atualizado após edição
- given: o marco está concluído, há coleta antiga pausada e uma nova revisão F03 altera CEP ou interesses.
- when: executar o próximo ciclo do escopo vigente.
- then:
  - O ciclo consulta somente os interesses e CEP do escopo vigente.
  - Confirmação atribuída ao CEP anterior não aparece como confirmação atual.
  - O marco e as identidades anteriores são preservados. Uma identidade desconhecida no novo escopo é registrada como descoberta.
  - Uma tentativa antiga que prossiga não publica sob o escopo novo.

#### `WRK-COLETA-10` — Escopo atualizado antes do marco
- given: uma carga inicial incompleta contém observações silenciosas e a configuração confirmada passa a ter um escopo diferente.
- when: completar a primeira passagem bem-sucedida do escopo atualizado.
- then:
  - O marco registra a conclusão da janela do escopo atualizado.
  - O histórico silencioso anterior é preservado. As identidades obtidas pela primeira vez na passagem atual permanecem silenciosas.

### Fonte

#### `WRK-FONTE-01` — Busca, detalhe e continuação reais
- given: ambiente autorizado, configuração com categoria real do catálogo e nome/modelo, amostra recuperável para ambos.
- when: executar a passagem autorizada no perfil documentado.
- then:
  - Resultados das duas formas de busca são identificáveis por origem e contexto.
  - A evidência associa identidade externa, link e preço disponível às observações persistidas.
  - Uma continuação comprovada dentro da janela produz resultados ou término verificável.

#### `WRK-FONTE-02` — Evidência real de retirada aproximada e envio informado
- given: CEP de referência em São Paulo (SP), amostra com retirada e oferta de origem brasileira com envio informado.
- when: executar as buscas reais no perfil documentado e consultar suas projeções.
- then:
  - O centro, o raio de referência de 20 km e o município efetivamente aplicados à busca de retirada são verificáveis. A localização aproximada do anúncio aparece com indicação de incerteza.
  - A oferta com envio informado fica disponível com “entrega no CEP a confirmar” quando faltar confirmação específica. Seu contexto territorial e evidência de envio estão registrados.
  - A evidência identifica a origem dos dados, a precisão disponível e eventuais confirmações ou recusas de entrega para o CEP, sem promover informação genérica a confirmação.

#### `WRK-FONTE-03` — Janela de 48 horas e retomada na fonte real
- given: carga inicial real concluída na janela de 48 horas, marco ativo, intervalo de parada registrado e publicação desse intervalo disponível na janela do ciclo retomado.
- when: retomar a coleta no mesmo banco com os filtros e a fronteira temporal documentados.
- then:
  - A carga inicial conserva os eventos silenciosos e seu marco. A publicação recuperada dentro da janela gera descoberta posterior à carga inicial, com identidade estável.
  - A execução registra os limites UTC da janela e comprova seu término por filtro temporal validado, ordenação e paginação verificadas ou esgotamento do resultado. Um limite de segurança atingido antes dessa fronteira conserva parcialidade.
  - Anúncios já conhecidos, inclusive os publicados há mais de 48 horas, são revisitados quando acessíveis. Data ausente permanece nula e sua associação à janela exige evidência da fonte.
  - A evidência real identifica os timestamps e a continuação observados que sustentam a fronteira escolhida. Repetir a leitura mantém identidades e eventos únicos.
  - Uma confirmação explícita de indisponibilidade de identidade conhecida fica registrada e preserva o histórico; esse fato não é confundido com falha técnica de acesso ou extração.

## Event

**Verification mode:** Produzir observações pelo worker e ler o histórico durável pela interface de mudanças usada por F09, avançando o cursor retornado a cada página.

### Histórico

#### `EVT-HISTORICO-01` — Repetição sem novo evento de preço
- given: A já possui uma redução registrada de 2300,00 para 2200,00 BRL.
- when: completar outro ciclo com o mesmo preço de A.
- then:
  - A leitura após o cursor anterior não contém outra redução de A.
  - O evento anterior continua recuperável pelo mesmo identificador.

#### `EVT-HISTORICO-02` — Nova redução depois de aumento
- given: o preço de A chegou a 2200,00 BRL, ficou desconhecido e depois subiu para 2400,00 BRL.
- when: completar um ciclo em que A volta a 2200,00 BRL.
- then:
  - O histórico contém uma redução distinta com os valores 2400,00 e 2200,00 BRL.
  - A observação sem preço não gerou alteração de preço.
  - O aumento está registrado separadamente da redução e a leitura paginada os recupera em ordem.

## E2E

**Verification mode:** Concluir ou tentar concluir a jornada guiada no web com worker ativo. Observar a rota da F03, o servidor da fonte de teste e o estado durável da coleta.

### Configuração

#### `E2E-CONFIGURACAO-01` — Rascunho não libera a coleta
- given: instalação nova com worker ativo e etapa intermediária da F03 pronta para salvar.
- when: salvar a etapa intermediária.
- then:
  - A configuração permanece em rascunho.
  - A fonte permanece sem consultas nos ticks observados após o salvamento.

#### `E2E-CONFIGURACAO-02` — Falha na conclusão não libera coleta
- given: rascunho válido e falha programada antes do commit da conclusão F03.
- when: confirmar a conclusão no assistente.
- then:
  - A interface informa falha e a configuração continua incompleta.
  - A fonte permanece sem consultas nos ticks observados após a falha.

#### `E2E-CONFIGURACAO-03` — Confirmação libera o worker
- given: rascunho válido, worker ativo e fonte local disponível.
- when: concluir com sucesso a configuração guiada.
- then:
  - A navegação segue para o acompanhamento.
  - O worker encontra a configuração confirmada e executa a primeira coleta com as duas formas de interesse cadastradas.
  - As primeiras observações publicam somente eventos silenciosos.

## Decisão adicional do usuário

Em 2026-11-11, após uma oferta real anteriormente acompanhada passar a redirecionar para `unavailable_product=1`, o usuário escolheu “Registrar indisponibilidade e continuar”. Os IDs e o Coverage Manifest foram preservados. A distinção entre fato de indisponibilidade confirmado e falha técnica passa a ser exigida em SVC-ANUNCIOS-02, WRK-COLETA-02/05 e WRK-FONTE-03.
