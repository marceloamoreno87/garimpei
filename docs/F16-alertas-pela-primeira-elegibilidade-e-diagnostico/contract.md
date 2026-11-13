# Contract — F16 Alertas pela primeira elegibilidade e diagnóstico

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-12T16-16-18Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

*Gerado por spec-writer. Alterações manuais são sobrescritas na regeneração.*

## Prerequisites

As condições abaixo descrevem o ambiente de execução dos itens. Produzi-las faz parte da entrega; condição ausente interrompe a verificação correspondente e não constitui evidência de sucesso.

### Runtime services

- Ambiente próprio descartável F02, com versões travadas, PostgreSQL, web e worker Procrastinate iniciados por `./scripts/init.sh`, migrations aplicadas e prontidão verificada. Registrar ambiente, portas, banco `garimpei_` e processos próprios; encerrar por `./scripts/stop.sh`. Limpeza com `--clean` somente nesse ambiente descartável.
- Fonte HTTP sintética e WAHA programável locais, com registro verificável de POSTs, mensagens e consultas. Reusar factories `apps/backend/tests/factories/{runtime,listing,valuation,alert}.py`; estender o servidor WAHA para grupo sintético. Relógio controlado e barreiras comprovam parada nos pontos de preparação, commit, autorização e resposta; não injetar falhas no runtime do usuário.
- Navegador Chromium e `playwright-cli` para UI/E2E. Capturas e snapshots ficam na pasta de evidência da feature, sem segredos. Não é necessário perfil Facebook real para os cenários sintéticos.

### Persistent state

- **BASE:** configuração concluída com CEP sintético `01001000`, interesse PlayStation 5 Slim disco 1 TB, taxa explícita de 10%, oferta RECENTE com compra R$ 1.000,00, funcionamento declarado sem ressalvas, disponibilidade e interesse confirmados. Publicação confiável `T−2h`, primeira observação `T−90min`, marco de monitoramento `T−1h` e observação enriquecida `T−30min`, com `T=2026-11-12T12:00:00Z`. Cinco outros usados equivalentes ativos, de identidades distintas, por R$ 1.450,00/1.475,00/1.500,00/1.525,00/1.550,00, observados em `T−1h`, produzem venda estimada R$ 1.500,00 e lucro R$ 350,00; a própria oferta é excluída da amostra. Grupos/canais de teste são sintéticos, confirmados e ativados, salvo variação declarada. Usado por: SVC-DIAGNOSTICO-01/02/03, UI-DIAGNOSTICO-01/02/03, WRK-PRIMEIRO-01/02/03, WRK-PRAZO-01/02/03/04/05/06, WRK-MANUAL-01/02/03/04, WRK-CONSISTENCIA-01/02/03/04/05/06/07/08, E2E-PERCURSO-01/02, E2E-GRUPO-01.
- **LEGADO:** banco com observações, decisões e intenções no formato F12 anterior à F16; variantes incluem recibo confirmado de descoberta, recibo de redução, intenção nunca transmitida, tentativa autorizada sem resposta, revisão incerta e múltiplos envios possivelmente transmitidos. Corpos, referências, vínculos e datas têm valores conhecidos antes da migração. Uma variante tem 101 anúncios para ultrapassar um lote de 100. Usado por: WRK-ADOCAO-01/02/03/04/05.
- **QUEDAS:** anúncio BASE com primeiro envio confirmado a R$ 1.000,00 e eventos distintos de queda para R$ 900,00, repetição do evento e alta seguida de nova queda para o mesmo valor. Variante sem confirmação anterior conserva o mesmo anúncio inicialmente sem estimativa; outra tem primeiro alerta autorizado com observação anterior à queda, ainda aguardando confirmação. Usado por: WRK-REDUCAO-01/02/03/04.
- Construção: fornecer `apps/backend/tests/factories/first_eligibility.py`, seguindo o context manager de `alert_scenario`, com criação de BASE/LEGADO/QUEDAS por caso e uso das factories existentes. Para LEGADO, aplicar o estado de migrations anterior e avançar com o executor de migrations em banco próprio, sem inferir que criar linhas no schema final demonstra migração. Verificar o preparo pelas leituras F04/F05/F07, inventário de intenções/recibos e histórico do servidor antes de cada item; publicar o mapeamento dos casos em evidência.

### Static inputs

- Fornecer `apps/backend/tests/fixtures/alert/first_eligibility_cases.json`, com `now`, identidade externa, observações/proveniência, datas com fuso, condição automática/manual, atributos, comparáveis, canal, histórico, barreira e resultado esperado. Registrar casos BASE, LEGADO, QUEDAS e suas variações citadas; incluir data ausente, futura, duvidosa, limite exato e limite excedido em um microssegundo, lucro zero com compra R$ 1.350,00 e negativo de R$ 50,00 com compra R$ 1.400,00, mantendo venda R$ 1.500,00 e taxa 10%, além de revisões incompatíveis. Os valores são sintéticos, sem definir padrões de configuração. Consumido pelas factories dos itens que usam esses três conjuntos. Validar estrutura, distinção de identidades e expectativas monetárias ao preparar os casos; não usar credenciais reais.

### Configuration

- Arquivo privado `GARIMPEI_ENV_FILE`, `GARIMPEI_ENV=eval`, fontes `GARIMPEI_LISTING_FIXTURE_URL`/`GARIMPEI_VALUATION_FIXTURE_URL` em loopback e `GARIMPEI_LISTING_FIXTURE_CLOCK` apontando ao relógio do caso. Para cenários fake, `GARIMPEI_ALERT_FIXTURE_URL` aponta ao WAHA programável; sessão/conta/grupo sintéticos, com sufixo canônico de grupo `@g.us`, são aceitos pela factory e conferidos em cada POST.
- Alertas ativados no vínculo F10 do caso, sem destinos implícitos. Tick 5 s, timeout 10 s, lease 60 s, retry base 15 s/teto 300 s, janela operacional de reconciliação 86.400 s e lotes de até 100; avanço do relógio e barreiras substituem esperas arbitrárias. Conferir configuração efetiva e isolamento antes de permitir worker com rede. O prazo do primeiro alerta é sempre o de 48 horas da publicação, independente desses parâmetros operacionais.

### External dependencies

- Exclusivamente `E2E-GRUPO-01`: WAHA/GOWS fixado conforme [F02](../F02-fundacao-tecnica-e-ambiente-local/versions.md), em ambiente próprio, conta pareada, sessão `WORKING` e grupo de teste explicitamente autorizado pelo usuário para receber a oferta sintética. Verificar conta/grupo e autorização antes de ativar envio; segredos ficam fora do checkout. Sem esse preparo, o item fica pendente e não é substituído pelo fake. Esta especificação não autoriza envio real.

## Quality gates

Cada gate deve passar para considerar a feature pronta; executá-los da raiz com dependências travadas e recursos de teste próprios. Registrar comandos, saída, código de retorno e revisões verificadas.

- **Seis gates backend** — `node scripts/run-gates.mjs` — tipos, lint/templates, limites, arquitetura, ciclos e código/dependências sem uso, sobre o escopo Python real.
- **Regressões Python/PostgreSQL** — `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests` — regras, integração, HTTP, migração e falhas controladas, inclusive regressões de F09/F12.
- **Django** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check` — configuração e registro válidos.
- **Drift de migrations** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py makemigrations --check --dry-run` — schema versionado; aplicação em base preenchida também é verificada nos itens de adoção.
- **Build** — `uv build --project apps/backend --wheel` — pacote construído com entradas necessárias.
- **Harness** — `node --test scripts/test/harness.test.mjs` e `node scripts/check-harness.mjs` — regressões e estrutura preservadas; não substituem os gates Python.
- **Navegador** — jornadas UI/E2E com `playwright-cli`, conforme skill do projeto — evidência de estados e recuperação no navegador, incluindo largura estreita, sem inferir envio pela aparência da tela.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F16-AC01**: uma oferta coletada antes, inicialmente incerta ou sem estimativa, gera um único primeiro alerta quando se torna automaticamente elegível dentro das 48 horas da publicação confiável, independentemente de o marco de monitoramento ser posterior à publicação. | WRK-PRIMEIRO-01, WRK-PRIMEIRO-02, WRK-PRIMEIRO-03, WRK-MANUAL-02, WRK-CONSISTENCIA-01, WRK-CONSISTENCIA-04 |
| **F16-AC02**: sem data confiável, com data futura ou idade superior à janela, não autorizar primeiro envio; confirmação de data válida permite reavaliar. A idade é conferida também na autorização do envio, sem usar primeira coleta como data de publicação. | WRK-PRAZO-01, WRK-PRAZO-02, WRK-PRAZO-03, WRK-PRAZO-04, WRK-PRAZO-05, WRK-PRAZO-06 |
| **F16-AC03**: adoção e retomada consideram estoque recente elegível sem envio confirmado e preservam recibos/intentos anteriores; reinício, oscilação de classificação e troca de versão não duplicam o primeiro alerta. Transmissão incerta continua em reconciliação. | WRK-ADOCAO-01, WRK-ADOCAO-02, WRK-ADOCAO-03, WRK-ADOCAO-04, WRK-ADOCAO-05, WRK-CONSISTENCIA-02, WRK-CONSISTENCIA-03, WRK-CONSISTENCIA-05, WRK-CONSISTENCIA-06, WRK-CONSISTENCIA-07, WRK-CONSISTENCIA-08, E2E-PERCURSO-02 |
| **F16-AC04**: detalhes exibem estado, motivo legível e data da avaliação para espera, exclusão, fila, falha, incerteza e confirmação; cadastro de grupo ativo não é confundido com mensagem enviada ou lida. | SVC-DIAGNOSTICO-01, SVC-DIAGNOSTICO-02, SVC-DIAGNOSTICO-03, UI-DIAGNOSTICO-01, UI-DIAGNOSTICO-02, UI-DIAGNOSTICO-03, E2E-PERCURSO-01 |
| **F16-AC05**: reduções elegíveis conservam identidade de evento e exigência de envio anterior confirmado. Gravar ou corrigir classificação manual muda a aba após sucesso e não gera alerta nem intenção adiada para a retomada; entradas automáticas independentes continuam sujeitas à política vigente e à precedência manual. Vencimento de janela não altera recibos existentes. | WRK-MANUAL-01, WRK-MANUAL-02, WRK-MANUAL-03, WRK-MANUAL-04, WRK-REDUCAO-01, WRK-REDUCAO-02, WRK-REDUCAO-03, WRK-REDUCAO-04, WRK-PRAZO-06, WRK-CONSISTENCIA-06 |
| **F16-AC06**: teste de ponta a ponta comprova anúncio inicialmente inelegível → enriquecimento → primeira elegibilidade → envio ao grupo correto → recibo persistido → retomada sem duplicação. Prova real autorizada é distinguida dos testes com canal fake. | E2E-PERCURSO-01, E2E-PERCURSO-02, E2E-GRUPO-01 |

Os itens também verificam a contribuição F16 para INT-18 e INT-21. Integração futura com F15/F17/F18 não é pré-requisito; as entradas equivalentes já fornecidas pelas dependências bastam para o contrato.

## Service

**Verification mode:** Invocar a consulta pública de diagnóstico consumida por F08; observar DTO, erro tipado e ausência de efeitos de envio, com estado persistido do caso.

### Diagnóstico

#### `SVC-DIAGNOSTICO-01` — Motivos por identidade e revisão
- given: BASE nas variações de espera por data, condição, identificação, amostra, configuração, análise, fila, exclusão e falha recuperável, cada uma com decisão conhecida.
- when: consultar o diagnóstico da identidade e observação exibidas.
- then:
  - O resultado contém estado, motivo legível e horário da última avaliação ou indicação de que ela ainda não ocorreu.
  - As referências da observação, condição e composição correspondem à decisão aplicável, sem afirmar variante divergente quando a identidade está ausente.
  - Nenhuma intenção ou tentativa é criada pela leitura.

#### `SVC-DIAGNOSTICO-02` — Recibo anterior e situação atual
- given: BASE em variações com primeiro alerta confirmado e condição atual inelegível, ou primeiro confirmado e uma redução posterior com transmissão incerta.
- when: consultar o diagnóstico.
- then:
  - O primeiro envio permanece confirmado com referência e horário sustentados pelo recibo.
  - O impedimento da avaliação atual aparece separado do motivo histórico de envio.
  - Redução incerta permanece identificada como incerta sem apagar a confirmação do primeiro alerta.
  - O resultado não declara entrega ou leitura no grupo.

#### `SVC-DIAGNOSTICO-03` — Ausência e falha de leitura
- given: BASE, identidade inexistente e falha de leitura de diagnóstico controlada como cenários separados.
- when: consultar a identidade de cada cenário.
- then:
  - Identidade inexistente retorna ausência identificável.
  - Falha técnica retorna erro distinto de ausência e de nunca enviado.
  - Nenhuma consulta chama envio ou reconciliação no canal.

## UI

**Verification mode:** Abrir lista/detalhe no navegador e observar texto, acessibilidade, navegação e parâmetros preservados. Usar o estado público e o registro de chamadas do ambiente para conferir ausência de envio por leitura.

### Diagnóstico

#### `UI-DIAGNOSTICO-01` — Estado compreensível por oferta
- given: BASE em cada estado declarado em SVC-DIAGNOSTICO-01, além de envio incerto e confirmação no servidor; grupo configurado inclusive no cenário sem intenção.
- when: abrir o detalhe da oferta a partir da lista.
- then:
  - A lista identifica o estado resumido e o detalhe apresenta estado, motivo e data da avaliação legíveis.
  - Configuração ativa sem recibo não aparece como mensagem enviada.
  - Envio incerto e confirmação no servidor têm rótulos distintos, sem promessa de entrega/leitura.
  - O bloco permanece legível por teclado e em largura estreita sem ocultar motivo ou data.

#### `UI-DIAGNOSTICO-02` — Oferta antiga e diagnóstico atual
- given: BASE com lista/detalhe fixados em uma revisão e decisão de alerta baseada em observação posterior, com mensagem histórica congelada.
- when: abrir o detalhe nessa revisão preservando os parâmetros da lista.
- then:
  - A divergência de observação é indicada explicitamente no diagnóstico.
  - Valores exibidos da oferta e da mensagem autorizada conservam suas referências e datas.
  - A leitura não aplica revisão nova nem altera filtros, página ou ordenação sem a ação existente de atualização.

#### `UI-DIAGNOSTICO-03` — Falha parcial e recuperação na jornada
- given: BASE legível, filtros e página definidos, com falha exclusiva na consulta de diagnóstico.
- when: abrir o detalhe da oferta.
- then:
  - Os dados disponíveis da oferta continuam visíveis.
  - O bloco identifica que o estado do alerta não pôde ser consultado.
  - A ação de tentar novamente aponta para a mesma jornada, preservando rota, filtros e revisão, sem representar falha como primeira instalação.

## Worker

**Verification mode:** Executar estágios agendados com PostgreSQL e dependências programáveis; conferir decisões, intenções, recibos, mensagens e contagem de POSTs após processamento. Barreiras/relógio definem os pontos de queda e os prazos; cada item começa com o conjunto e a variação declarados.

### Primeiro alerta

#### `WRK-PRIMEIRO-01` — Enriquecimento tardio
- given: BASE, RECENTE coletada antes do marco de monitoramento, inicialmente incerta ou sem amostra, sem alerta confirmado; detalhe/comparáveis suficientes acabam de chegar como entrada automática relevante.
- when: processar a reavaliação pendente.
- then:
  - Um único primeiro alerta é enviado para o grupo configurado quando todas as condições estiverem satisfeitas.
  - A decisão referencia observação, condição e composição aplicáveis ao anúncio.
  - O sistema não cria novo evento de descoberta para obter esse envio.

#### `WRK-PRIMEIRO-02` — Lucro sem corte mínimo
- given: três variações independentes de BASE com lucro positivo, zero e negativo calculáveis e demais condições elegíveis.
- when: processar as reavaliações.
- then:
  - Cada oferta recebe um primeiro alerta individual.
  - A composição e a mensagem preservam o sinal do lucro correspondente.

#### `WRK-PRIMEIRO-03` — Estoque inicial e coleta parcial
- given: BASE com RECENTE pertencente a estoque inicial silencioso, interesse/disponibilidade comprovados, catálogo ainda parcial e nenhum evento de descoberta elegível.
- when: processar a adoção concluída e a reavaliação dessa oferta.
- then:
  - Um primeiro alerta pode ser confirmado para a oferta recente elegível.
  - A carga global continua identificada como parcial.
  - Nenhum evento de descoberta ou prova de completude é fabricado.

### Prazo

#### `WRK-PRAZO-01` — Fronteira inclusiva
- given: BASE em três execuções independentes com idade na autorização de 48 horas exatas, 48 horas mais um microssegundo e publicação no próprio instante da autorização.
- when: despachar cada oferta elegível.
- then:
  - Exatamente 48 horas e publicação no instante atual admitem um primeiro POST.
  - A oferta acima da janela não produz POST e informa vencimento.

#### `WRK-PRAZO-02` — Data ausente, futura ou não confiável
- given: BASE em variações sem publicação, com publicação futura, relativa sem precisão suficiente ou sem fuso inequívoco; primeira coleta e marco têm datas recentes válidas.
- when: processar a reavaliação.
- then:
  - Nenhuma variação autoriza primeiro envio.
  - O motivo distingue ausência, futuro e falta de confiabilidade.
  - Primeira coleta e marco não são usados como substitutos da publicação.

#### `WRK-PRAZO-03` — Confirmação posterior da publicação
- given: BASE aguardando data, com uma observação automática nova que comprova publicação dentro da janela e mantém as demais condições.
- when: processar a nova entrada.
- then:
  - A espera por data é substituída pela decisão atual sustentada pela nova evidência.
  - O primeiro alerta é enviado uma vez, sem reescrever a decisão histórica de data ausente.

#### `WRK-PRAZO-04` — Vencimento enquanto o canal espera
- given: BASE elegível em fila sem tentativa autorizada; o canal ficou indisponível até depois de 48 horas da publicação.
- when: o worker tenta despachar após o canal voltar.
- then:
  - Não há POST do primeiro alerta vencido.
  - O diagnóstico identifica a expiração e conserva o histórico da espera.

#### `WRK-PRAZO-05` — Verificação lenta cruza o limite
- given: BASE preparada antes do limite; a verificação de sessão está retida na barreira e só termina depois de 48 horas da publicação.
- when: liberar a verificação de sessão.
- then:
  - A conferência final recusa a autorização e nenhum POST ocorre.
  - Horário de preparo não é usado como horário de autorização.

#### `WRK-PRAZO-06` — Incerteza depois do prazo
- given: BASE com tentativa autorizada dentro da janela, possivelmente transmitida, sem resposta conclusiva; agora a publicação tem mais de 48 horas.
- when: processar a reconciliação.
- then:
  - O sistema apenas consulta a mesma mensagem/referência no vínculo original.
  - Nenhum novo POST é feito, mesmo se a busca não encontrar resultado.
  - Evidência inequívoca posterior pode confirmar o envio original; sua ausência conserva incerteza.

### Adoção

#### `WRK-ADOCAO-01` — Confirmação legada impede novo primeiro alerta
- given: LEGADO em variantes com recibo confirmado anterior de descoberta ou de redução, mantendo anúncio recente hoje elegível.
- when: executar a adoção F16.
- then:
  - Nenhum novo primeiro alerta é criado para essas identidades.
  - Referências, corpos, vínculos, recibos e datas anteriores permanecem intactos.
  - O diagnóstico reconhece a confirmação anterior sem depender do formato da mensagem antiga.

#### `WRK-ADOCAO-02` — Intenção legada não transmitida
- given: LEGADO com intenção em fila antes da autorização, ainda elegível, e entradas repetidas para a mesma identidade.
- when: processar adoção e despacho dessa identidade.
- then:
  - No máximo um primeiro POST ocorre para o anúncio.
  - Intenção incorporada conserva sua referência; qualquer intenção não aproveitada tem encerramento comprovadamente sem transmissão e motivo identificável.
  - O histórico da descoberta não é recriado nem apagado.

#### `WRK-ADOCAO-03` — Histórico incerto ou conflitante
- given: LEGADO em variantes com tentativa autorizada sem resposta, revisão incerta e múltiplas transmissões possíveis da mesma identidade.
- when: processar a adoção.
- then:
  - Nenhuma variante libera novo primeiro POST.
  - As tentativas anteriores continuam disponíveis para reconciliação no vínculo original.
  - Conflito ou integridade desconhecida aparece como revisão necessária, sem declarar nunca enviado.

#### `WRK-ADOCAO-04` — Migração e retomada entre lotes
- given: LEGADO com 101 anúncios e recibos conhecidos, schema migrado e adoção interrompida após um lote confirmado do inventário.
- when: reiniciar o processamento da adoção.
- then:
  - O inventário retoma da fronteira confirmada e cobre todas as identidades sem duplicar efeitos.
  - Nenhum envio ocorre antes da conclusão consistente do inventário legado.
  - Observações, escolhas manuais, corpos e recibos mantêm seu conteúdo anterior.
  - A migração em si não acessa WAHA ou Facebook.

#### `WRK-ADOCAO-05` — Schema novo sobre banco preenchido
- given: LEGADO no schema F12, com escolhas manuais, observações e recibos inventariados, sem worker despachando.
- when: aplicar as migrations F16 ao banco próprio.
- then:
  - Dados, UUIDs, referências, corpos, vínculos e recibos anteriores permanecem íntegros.
  - O estado permite executar a adoção retomável antes de liberar despacho F16.
  - A aplicação da migration não consulta nem envia mensagens ao canal.

### Escolha manual

#### `WRK-MANUAL-01` — Sem alerta imediato ou adiado
- given: BASE inicialmente incerta, com amostra pronta, alterada manualmente para boa; nenhuma entrada automática relevante mudou desde a ação.
- when: reiniciar o worker e processar os ticks/reconciliações pendentes.
- then:
  - A escolha permanece boa e a oferta continua na aba correspondente.
  - Nenhuma intenção de primeiro envio é criada por essa escolha, antes ou depois da retomada.
  - Nova coleta com conteúdo semanticamente idêntico mantém essa proteção.

#### `WRK-MANUAL-02` — Entrada independente após a escolha
- given: BASE com escolha manual boa preservada e marco consumido; comparáveis ou detalhe útil posteriores mudaram efetivamente a entrada automática, completando a elegibilidade.
- when: processar a entrada independente.
- then:
  - A condição manual continua prevalecendo.
  - Um primeiro alerta pode ser confirmado dentro da janela.
  - A causa registrada é a entrada automática, sem intenção atribuída à ação manual.

#### `WRK-MANUAL-03` — Escolha ruim prevalece
- given: BASE com escolha manual ruim, enquanto uma entrada automática posterior indica condição boa e composição calculável.
- when: processar a entrada automática.
- then:
  - Nenhum primeiro alerta é enviado.
  - O diagnóstico informa o impedimento da condição efetiva e preserva a escolha manual.

#### `WRK-MANUAL-04` — Avaliação concorrente com correção manual
- given: BASE incerta com avaliação preparada antes de uma escolha manual boa, retida antes da publicação; não há outra entrada automática independente.
- when: liberar a publicação após a escolha manual confirmada.
- then:
  - O resultado preparado não cria intenção por combinar a nova escolha com a entrada antiga.
  - O marco de proteção permanece após reinício.

### Redução de preço

#### `WRK-REDUCAO-01` — Queda após confirmação anterior
- given: QUEDAS com primeiro envio confirmado antes do evento de queda, publicação há mais de 48 horas e nova queda elegível dentro da política vigente de F09/F12.
- when: processar o evento de queda.
- then:
  - Uma mensagem de redução usa o preço anterior, preço novo e composição da observação desse evento.
  - A janela de publicação do primeiro alerta não é aplicada à redução.
  - O recibo do primeiro alerta continua preservado.

#### `WRK-REDUCAO-02` — Queda que cria primeira elegibilidade
- given: QUEDAS sem confirmação anterior, com uma queda que completa a primeira elegibilidade dentro da janela de publicação.
- when: processar essa entrada e sua conclusão.
- then:
  - Há no máximo uma mensagem de primeiro alerta.
  - A confirmação desse primeiro alerta não produz também mensagem de redução para o mesmo evento que a precedeu.

#### `WRK-REDUCAO-03` — Repetição e queda distinta
- given: QUEDAS com redução confirmada, repetição técnica do evento e alta seguida de nova queda ao mesmo valor.
- when: processar o feed.
- then:
  - A repetição não envia novamente a mesma redução.
  - A alta não produz alerta.
  - A nova queda elegível tem mensagem e identidade de evento próprias.

#### `WRK-REDUCAO-04` — Aguardar confirmação de intenção anterior
- given: QUEDAS com primeiro alerta já autorizado para observação anterior ao evento de redução, confirmação em espera e nenhum uso desse evento na composição do primeiro alerta.
- when: processar a confirmação do primeiro alerta e o trabalho dependente já aguardando.
- then:
  - A redução distinta pode ser enviada uma vez conforme a janela de espera vigente de F09/F12.
  - A mensagem de redução usa a própria observação/preço e preserva a identidade do evento.
  - O sistema não substitui a mensagem de primeiro alerta já autorizada pela composição nova.

### Consistência e recuperação

#### `WRK-CONSISTENCIA-01` — Resultado de revisão ultrapassada
- given: BASE com composição pronta para observação anterior, enquanto a observação vigente mudou preço/variante antes da publicação da decisão.
- when: processar a avaliação preparada.
- then:
  - Nenhum envio combina a observação nova com identidade ou valores da antiga.
  - O diagnóstico informa pendência de avaliação aplicável ou resultado desatualizado.
  - Nova entrada confirmada pode retomar o trabalho sem apagar o histórico.

#### `WRK-CONSISTENCIA-02` — Concorrência pela mesma identidade
- given: BASE elegível, dois workers aptos a reclamar o mesmo primeiro alerta e entradas duplicadas de reavaliação.
- when: processar as reclamações concorrentes.
- then:
  - O canal observa um único primeiro POST.
  - A identidade durável aponta para o mesmo efeito e seu recibo.
  - Entrada duplicada de reavaliação mantém a mesma identidade de primeiro envio.

#### `WRK-CONSISTENCIA-03` — Queda após possível transmissão
- given: BASE com WAHA programável que registra a mensagem e perde a resposta, ou worker interrompido após autorizar e antes de confirmar.
- when: retomar o processamento.
- then:
  - Não ocorre repetição automática do POST possivelmente efetuado.
  - A reconciliação usa a referência original e pode persistir o recibo inequívoco.
  - Histórico vazio ou ambíguo conserva incerteza e não libera nova tentativa de envio.

#### `WRK-CONSISTENCIA-04` — Falha isolada de dependência
- given: duas identidades BASE, uma com falha persistente na consulta financeira e outra pronta para avaliação/envio.
- when: processar um lote de reavaliação.
- then:
  - A primeira identidade conserva espera/falha recuperável e próxima ação limitada.
  - A segunda avança até confirmação sem depender da recuperação da primeira.
  - Progresso confirmado e invalidações de nova geração sobrevivem à retomada.

#### `WRK-CONSISTENCIA-05` — Histórico indisponível
- given: BASE em fila, com falha de leitura do histórico ou evidência de intervalo restaurado sem recibos reconciliados.
- when: tentar despachar.
- then:
  - Nenhum POST é autorizado enquanto a integridade estiver indeterminada.
  - O diagnóstico registra falha/suspensão recuperável, sem afirmar nunca enviado ou apagar recibos conhecidos.

#### `WRK-CONSISTENCIA-06` — Vínculo e corpo congelados
- given: BASE com intenção autorizada/incerta no grupo original, seguida de alteração de grupo, taxa ou avaliação.
- when: processar a retomada/reconciliação dessa intenção.
- then:
  - Nenhum POST redireciona a mensagem ao grupo novo.
  - Corpo, valores, referência e vínculo autorizados permanecem originais.
  - Troca de grupo ou versão não cria outro primeiro alerta para a mesma identidade.

#### `WRK-CONSISTENCIA-07` — Resposta atrasada
- given: BASE com geração de envio/reconciliação ultrapassada e uma resposta tardia da chamada anterior para a mesma referência.
- when: registrar a resposta tardia.
- then:
  - A resposta não sobrescreve indevidamente o estado de geração mais recente.
  - Evidência da tentativa original permanece disponível para reconciliação.
  - Nenhum segundo primeiro POST é liberado por esse conflito de geração.

#### `WRK-CONSISTENCIA-08` — Oscilação sem segundo primeiro alerta
- given: BASE já confirmada, com fila de entradas automáticas que alternam elegível/incerta/elegível e uma reavaliação após troca de versão da política, sem nova identidade F04.
- when: processar a fila de reavaliações.
- then:
  - O histórico conserva o primeiro envio confirmado.
  - Nenhum novo primeiro POST é criado por oscilação ou mudança de versão.

## E2E

**Verification mode:** Executar web, worker, PostgreSQL e canal declarado; usar a jornada pública e conferir a mensagem no grupo, o recibo persistido, a UI e a retomada. Distinguir prova determinística local da prova real autorizada.

### Percurso integrado

#### `E2E-PERCURSO-01` — Enriquecer, confirmar e retomar
- given: BASE inicialmente sem amostra e com detalhe incompleto, grupo sintético configurado/ativado pela F10 e fonte programável que passa a fornecer os dados suficientes.
- when: disponibilizar os dados suficientes na fonte sintética para processamento normal.
- then:
  - A oferta passa de espera com motivo explícito para primeiro alerta no grupo sintético correto.
  - A mensagem usa título/link e valores da mesma observação/composição autorizada.
  - O recibo persiste associado à referência original.
  - O detalhe mostra confirmação no servidor com data, distinguindo-a de leitura no grupo.
  - Evidências não expõem segredos nem identificadores privados do usuário.

#### `E2E-PERCURSO-02` — Retomada do percurso confirmado
- given: BASE completou E2E-PERCURSO-01, com mensagem e recibo persistidos e ambiente preservado.
- when: reiniciar normalmente o worker.
- then:
  - O recibo continua associado à mesma referência e ao mesmo grupo.
  - O canal não recebe outro primeiro POST.
  - O detalhe continua identificando a confirmação histórica e sua data.

### Grupo real

#### `E2E-GRUPO-01` — Prova externa autorizada
- given: BASE sintética, pré-requisito externo de grupo real explicitamente autorizado satisfeito, ambiente próprio e canal efetivo conferido antes da ativação.
- when: processar a primeira elegibilidade dessa oferta de teste.
- then:
  - Uma mensagem chega ao grupo autorizado com a referência esperada.
  - A confirmação inequívoca do WAHA é persistida e vinculada à mesma mensagem/grupo.
  - O diagnóstico usa o recibo real, sem chamar aceitação no servidor de prova de leitura.
  - A prova registra separadamente observação no grupo e confirmação técnica, com dados privados redigidos.
- notes: Sem autorização, conta, grupo ou evidência, este item permanece pendente e impede declarar avaliação completa de F16.
