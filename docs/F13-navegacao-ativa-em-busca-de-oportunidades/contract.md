# Contrato — F13 Navegação ativa em busca de oportunidades

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-12T19-32-55Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

*Gerado por spec-writer. Edições manuais serão substituídas na regeneração.*

## Prerequisites

As condições abaixo fazem parte da entrega futura. Ausência de um pré-requisito impede verificar os itens dependentes; não constitui aprovação ou implementação concluída.

### Runtime services

- Aplicação Django, worker e PostgreSQL próprios de avaliação iniciados por `./scripts/init.sh`, com banco `garimpei_`, portas e identidade de ambiente verificáveis; nenhuma sessão compartilha o perfil real durante testes controlados.
- uv/Python do lock e `playwright-cli` disponíveis. O procedimento reproduzível de preparo e verificação deve constar de `operations.md`; parada por `./scripts/stop.sh` identifica recursos próprios.

### Persistent state

- **Cenário ativo:** configuração concluída com CEP/taxa, dois interesses ativos, ambas as frentes pendentes, observações e recibos anteriores. Produção por factories/migrations do projeto e verificação por leitura de configuração/acompanhamento e estado confirmado no cenário isolado. Usado por: WRK-PERCURSO-01, WRK-DISTRIBUICAO-01, WRK-RETOMADA-01, WRK-RETOMADA-02, WRK-RETOMADA-03, WRK-ACESSO-01, EVT-PUBLICACAO-01, EVT-PUBLICACAO-02, UI-PROGRESSO-01, UI-PROGRESSO-02, API-RETOMADA-01, SVC-PESQUISA-01, E2E-PERCURSO-01.
- **Cenário de sugestões:** interesse ativo PS5 Slim, relação versionada para PS5 Pro e anúncio de suporte verificável; nenhum interesse PS5 Pro salvo. Criação por factories e catálogo; verificar contagens separadas e configuração antes do exercício. Usado por: WRK-SUGESTOES-01, WRK-SUGESTOES-02, WRK-SUGESTOES-03, UI-SUGESTOES-01, UI-SUGESTOES-02, E2E-ADOCAO-01.

### Static inputs

- `apps/backend/tests/fixtures/navigation/cases.json`, a produzir: páginas/detalhes por identidade e horário, desafio, contexto errado, cursor repetido/vencido, falha/atraso, termos equivalentes e incompatíveis, relações positivas/negativas e instruções hostis como dados. Factories existentes e `tests/factories/navigation.py` devem criar e verificar os cenários, sem credenciais reais. Usado por: WRK-PERCURSO-01, WRK-DISTRIBUICAO-01, WRK-RETOMADA-01, WRK-RETOMADA-02, WRK-RETOMADA-03, WRK-ACESSO-01, WRK-PERIMETRO-01, WRK-SUGESTOES-01, WRK-SUGESTOES-02, WRK-SUGESTOES-03, EVT-PUBLICACAO-01, EVT-PUBLICACAO-02, E2E-ADOCAO-01.
- Catálogo versionado de aliases/relações a produzir em `apps/backend/src/garimpei/infra/gateway/navigation/navigation_catalog.json`; casos positivos e negativos coincidem com a spec. Usado por: WRK-PERIMETRO-01, WRK-SUGESTOES-01, SVC-PESQUISA-01, E2E-PERCURSO-01.

### Configuration

- Parâmetros contratuais: uma operação por perfil; turno de uma página ou detalhe; fatia ativa 120 s/2 páginas/10 detalhes; até 100 páginas/3 termos por interesse/ciclo; timeout 20 s; três falhas consecutivas; recuo 15–300 s respeitando fonte. Sugestões: 45 s/1 página/1 detalhe, uma fatia por 300 s e somente quando timeout/cadência/margem de 5 s couberem antes da próxima unidade ativa. Até 500 detalhes pendentes por interesse e 100 sugestões/10 evidências por sugestão. Primeiro teto vence; tempo falso apenas em avaliação.
- Perfil privado/segredos fora do checkout; relógio controlado e origens fake loopback permitidos apenas em `GARIMPEI_ENV=eval`. O preparo deve rejeitar origens arbitrárias e deixar alertas reais desativados.

### External dependencies

- Fonte controlada nomeada, servida pelo laboratório de factories, registra navegação e efeitos sem usar Facebook/WAHA reais; criação e verificação via testes/operations.md. Usada nos itens controlados.
- Para E2E-PERCURSO-01, acesso Facebook dedicado confirmado em F11 e uso exclusivo do perfil. Login/desafio depende de recuperação manual; sem esse acesso a prova real fica pendente. Não é necessário envio real de WhatsApp.

## Quality gates

Cada gate deve passar para a feature ser considerada pronta; comandos abaixo serão executados na implementação, não nesta especificação.

- **Seis grupos Python** — `node scripts/run-gates.mjs` — tipos, lint/templates, limites, arquitetura, ciclos e código/dependências não utilizados.
- **Suíte** — `uv run --project apps/backend --frozen --no-sync pytest` — regras, HTTP e integração isolada sem regressões.
- **Django** — `uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check --settings=garimpei.config.test_settings` — configuração importável; migrations também exercitadas em PostgreSQL real isolado.
- **Build** — `uv build --project apps/backend` — pacote contém entradas e catálogo necessários.
- **Jornadas** — `playwright-cli` — navegação/teclado/reflow, screenshots e evidências dos itens UI/E2E; avaliação visual por frontend-ui-design.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F13-AC01**: a jornada automática percorre busca, continuação e detalhe dentro do perímetro aprovado, produzindo anúncios e evidências persistentes antes de concluir toda a exploração. | `WRK-PERCURSO-01`, `EVT-PUBLICACAO-01`, `E2E-PERCURSO-01`, `SVC-PESQUISA-01` |
| **F13-AC02**: retomada de navegação não duplica anúncio/evento; contexto errado ou orçamento esgotado mantém cobertura parcial e ponto de continuação explícitos. | `WRK-RETOMADA-01`, `WRK-RETOMADA-02`, `WRK-RETOMADA-03`, `EVT-PUBLICACAO-01`, `EVT-PUBLICACAO-02` |
| **F13-AC03**: login, desafio ou perda de acesso suspendem navegação com recuperação manual; instrução encontrada numa página não altera interesses nem autoriza contato/compra. | `WRK-ACESSO-01`, `WRK-PERIMETRO-01`, `API-RETOMADA-01` |
| **F13-AC04**: o usuário consulta escopo, progresso e razão da pausa. Novos nichos relacionados aos interesses atuais são sugestões separadas, com anúncios reais, explicação da relação e limitações; adotá-los exige alteração explícita de interesse. Ignorar uma sugestão não inicia monitoramento nem produz alertas de suas ofertas. | `UI-PROGRESSO-01`, `UI-PROGRESSO-02`, `UI-SUGESTOES-01`, `UI-SUGESTOES-02`, `E2E-ADOCAO-01` |
| **F13-AC05**: em cenário controlado com descoberta e investigação pendentes para mais de um interesse, ambas as frentes e os interesses aptos avançam dentro dos limites definidos no contrato. Um catálogo extenso, candidato sem resolução ou exploração de sugestões não monopoliza a navegação. Registrar ordem, consumo de orçamento, último progresso e razão da escolha; não exigir proporção numérica ainda não aprovada. | `WRK-DISTRIBUICAO-01`, `WRK-SUGESTOES-02` |
| **F13-AC06**: abreviação/nome equivalente validado gera pesquisa automaticamente, conservando o interesse e suas restrições. Alias não validado ou outro modelo não amplia a busca ativa; resultado incompatível não recebe identidade pelo termo pesquisado. O mesmo anúncio encontrado por termos diferentes conserva fonte/ID e não duplica evento nem primeiro alerta; variações compartilham orçamento do interesse. | `WRK-PERIMETRO-01`, `EVT-PUBLICACAO-01` |
| **F13-AC07**: orçamento próprio de sugestões é limitado e verificável; cenário com sugestão relacionada e sustentada por anúncios reais informa origem, data, relação e incertezas. Candidato sem relação demonstrada não é apresentado como sugestão válida. Sem adoção explícita não há novo interesse ou envio por essa sugestão; sugestão não é prova de lucro ou liquidez. | `WRK-SUGESTOES-01`, `WRK-SUGESTOES-02`, `WRK-SUGESTOES-03`, `UI-SUGESTOES-01`, `UI-SUGESTOES-02`, `E2E-ADOCAO-01` |

## Service

**Verification mode:** invocar a fronteira pública de pesquisa complementar, consumível por F18, com cliente de teste e consultar resultado/progresso; não exige F18 implementada.

### Pesquisa complementar

#### `SVC-PESQUISA-01` — Perímetro reutilizável
- given: cenário ativo, catálogo versionado e pedido de pesquisa vinculado a interesse/revisão vigentes.
- when: solicitar pesquisa complementar pela fronteira pública.
- then:
  - O pedido recebe identidade, contexto e limites consultáveis.
  - Repetição do mesmo pedido referencia o mesmo trabalho.
  - Termo injustificado ou revisão antiga tem rejeição explícita.
  - A consulta não altera interesses nem afirma equivalência ou preço por si só.

## HTTP API

**Verification mode:** enviar requisições HTTP e observar status, redirecionamento e efeitos persistidos diretos do comando.

### Retomada

#### `API-RETOMADA-01` — Comando confirmado e validado
- given: cenário ativo com unidade suspensa, revisão atual e acesso verificado; variantes de corpo inválido, revisão antiga e CSRF ausente.
- when: enviar o comando de retomada da unidade.
- then:
  - Requisição válida confirma intenção persistida e redireciona ao acompanhamento.
  - Formato inválido retorna 400; CSRF ausente retorna 403; revisão antiga ou acesso suspenso retorna 409.
  - Requisição rejeitada conserva estado confirmado e histórico.
  - Falha de gravação apresenta erro recuperável, sem confirmar retomada.

## UI

**Verification mode:** navegar na aplicação isolada via playwright-cli; observar DOM, texto, foco, navegação e screenshots.

### Progresso

#### `UI-PROGRESSO-01` — Entender o percurso
- given: cenário ativo com unidades executando, aguardando horário/fonte e parciais por teto.
- when: abrir Acompanhamento.
- then:
  - O painel identifica interesse, frente, termo original/alias e revisão/horário.
  - Exibe último avanço útil e pendências conhecidas.
  - Diferencia espera válida, parcialidade, suspensão e ausência de pendências.
  - Exibe motivo e próxima ação sem inventar completude ou total da fonte.

#### `UI-PROGRESSO-02` — Atualização sem perder leitura
- given: cenário ativo já carregado, com novos dados ou falha na leitura seguinte.
- when: solicitar atualização do painel.
- then:
  - Atualização bem-sucedida aplica dados mediante ação explícita.
  - Falha conserva leitura anterior com indicação de horário/erro recuperável.
  - Rota e filtros da jornada continuam preservados.

### Sugestões relacionadas

#### `UI-SUGESTOES-01` — Evidência antes de adotar
- given: cenário de sugestões com anúncio de suporte e relação comprovados.
- when: abrir Sugestões.
- then:
  - Sugestão aparece separada das ofertas monitoradas.
  - Exibe interesse de origem, relação, anúncio/link, data e limitações.
  - Outro modelo é identificado como produto diferente, sem lucro/liquidez fabricados.
  - Controles funcionam por teclado e a 360 px sem ocultar evidência ou ação.

#### `UI-SUGESTOES-02` — Prévia não é adoção
- given: cenário de sugestões, sem interesse sugerido salvo.
- when: abrir a ação de adicionar uma sugestão à configuração.
- then:
  - Formulário apresenta a proposta editável.
  - Configuração continua sem o interesse até gravação explícita bem-sucedida.
  - Cancelar ou falhar ao salvar não confirma adoção.

## Worker

**Verification mode:** acionar trabalho persistente com PostgreSQL e fonte controlada; observar chamadas externas registradas, checkpoints e efeitos confirmados, incluindo queda/reinício.

### Percurso incremental

#### `WRK-PERCURSO-01` — Busca, continuação e detalhe
- given: cenário ativo e fixture de duas páginas, com detalhe válido na primeira.
- when: executar a navegação automática.
- then:
  - Percorre contexto de busca verificado, continuação e detalhe.
  - Publica evidência do primeiro detalhe antes de terminar a exploração.
  - Preserva identidade/link, origem do interesse e contexto solicitado/observado.
  - Página inesperada não é registrada como busca vazia verificada.

### Distribuição de esforço

#### `WRK-DISTRIBUICAO-01` — Ambas as frentes e interesses avançam
- given: cenário ativo, dois interesses com ambas as frentes pendentes, consulta extensa e detalhe lento/falho, sem suspensão de acesso global.
- when: processar uma rodada de turnos aptos.
- then:
  - Cada par interesse/frente recebe oportunidade em até 2N turnos, com N interesses aptos.
  - Timeout de um item não impede turno de trabalho independente.
  - Cada turno respeita unidade e orçamento aplicáveis.
  - Espera obrigatória da fonte não é contornada por nova fila ou outro navegador.
  - Registro informa ordem, consumo de orçamento, último progresso e razão da seleção.

### Retomada

#### `WRK-RETOMADA-01` — Queda na fronteira de confirmação
- given: cenário ativo e interrupção controlada imediatamente antes ou depois do commit de página/detalhe.
- when: reiniciar o processamento.
- then:
  - Retoma unidades pendentes da última fronteira confirmada.
  - Página e continuação confirmadas não perdem candidatos.
  - Repetição de unidade não duplica observação/evento.
  - Histórico, escolhas manuais, marco e recibos prévios permanecem preservados.

#### `WRK-RETOMADA-02` — Cursor inválido ou teto
- given: cenário ativo e variante de cursor vencido/repetido, contexto errado ou orçamento esgotado.
- when: processar a próxima unidade.
- then:
  - Resultado informa parcialidade e razão específica.
  - Reconstrução de busca informa retrabalho e preserva deduplicação.
  - Trabalho não percorrido permanece pendente ou limitado, sem receber confirmação fictícia.
  - Reinício não repõe orçamento de sugestões da mesma janela.

#### `WRK-RETOMADA-03` — Trabalho ultrapassado
- given: cenário ativo com resposta ainda em curso e configuração ou geração de posse substituída.
- when: receber a resposta antiga.
- then:
  - Não publica a resposta como estado atual nem altera o checkpoint da nova revisão.
  - Dados previamente confirmados permanecem preservados.
  - Progresso antigo não é atribuído à configuração vigente.

### Acesso e perímetro

#### `WRK-ACESSO-01` — Recuperação humana de acesso
- given: cenário ativo cuja fonte apresenta login, desafio ou perda de acesso.
- when: tentar a próxima navegação.
- then:
  - Trabalho dependente do perfil fica suspenso com ação de recuperação manual.
  - Reinício ou comando de retomada não libera acesso sem verificação F11.
  - Progresso confirmado permanece salvo.

#### `WRK-PERIMETRO-01` — Alias conservador e conteúdo externo
- given: fixture/catálogo com PS5 Slim, alias validado, PS5 Pro, variante com capacidade distinta e instruções hostis de página.
- when: navegar conforme o planejamento aprovado.
- then:
  - Termo equivalente preserva interesse, modelo/restrições e justificativa.
  - Modelo/variante diferentes não entram como alias ou interesse novo.
  - Identidade do resultado não é inferida apenas pelo termo consultado; variante incompatível não recebe match de identidade presumido.
  - Instrução encontrada na fonte não altera escopo ou acessa credenciais.
  - Nenhum contato, compra ou envio é executado a pedido do conteúdo externo.

### Sugestões relacionadas

#### `WRK-SUGESTOES-01` — Exploração automática fundamentada
- given: cenário de sugestões, tempo livre admissível e fonte controlada com evidência de nicho relacionado e outro sem relação demonstrada.
- when: executar a fatia automática de sugestões.
- then:
  - Nicho relacionado recebe justificativa e anúncio de suporte verificado.
  - Relação genérica com eletrônicos não basta para publicar sugestão.
  - Falta de evidência mantém investigação inconclusiva.
  - Anúncios exclusivamente sugeridos ficam fora de ofertas, amostras e eventos monitorados.

#### `WRK-SUGESTOES-02` — Trabalho ativo tem precedência
- given: cenário de sugestões com trabalho ativo apto ou prazo próximo que não comporta outra operação.
- when: o agendador considera explorar sugestões.
- then:
  - Não inicia navegação de sugestão que adie trabalho ativo.
  - Mantém orçamento separado e motivo de espera consultável.
  - Não abre outro navegador com o mesmo perfil para executar em paralelo.

#### `WRK-SUGESTOES-03` — Sugestão ignorada e limites
- given: cenário de sugestões ignoradas, com limite de tempo/quantidade atingido e uma oferta também encontrada independentemente por interesse ativo.
- when: processar a próxima rodada automática.
- then:
  - Ignorar sugestão não adiciona interesse nem produz alerta de suas ofertas por essa origem.
  - Teto suspende inclusão/exploração afetada sem apagar evidência confirmada.
  - A descoberta independente pelo interesse ativo mantém sua política vigente.

## Event

**Verification mode:** observar publicações, matches e intenções/recibos com consumidores existentes e canal fake, sem envio real.

### Publicação e deduplicação

#### `EVT-PUBLICACAO-01` — Uma descoberta por identidade
- given: cenário ativo e mesma oferta encontrada por termo literal, alias e dois interesses, com consumidor/canal fake.
- when: confirmar os resultados convergentes.
- then:
  - Uma identidade fonte/ID conserva os matches válidos.
  - Não duplica descoberta ou primeiro alerta pela multiplicidade de consultas.
  - IDs diferentes não são fundidos apenas por título ou foto.

#### `EVT-PUBLICACAO-02` — Política vigente preservada
- given: cenário ativo com recibos anteriores, data desconhecida, condição incerta e oferta nova apta conforme a política atualmente implementada.
- when: publicar o lote confirmado da navegação.
- then:
  - Eventos seguem as mesmas regras do fluxo F04/F12.
  - Incerteza não vira elegibilidade por ter vindo da F13.
  - Recibos anteriores não são reabertos e transmissão incerta não é repetida.

## E2E

**Verification mode:** executar aplicação, banco e worker isolados; dirigir o navegador e conferir efeitos integrados. Prova real usa perfil dedicado exclusivo e somente leitura.

### Navegação integrada

#### `E2E-PERCURSO-01` — Prova real de leitura e continuidade
- given: cenário ativo, catálogo e acesso real confirmado/exclusivo; rota selecionada com continuação e detalhes disponíveis.
- when: executar percurso automático com pausa e retomada.
- then:
  - Evidências públicas sanitizadas comprovam contexto, continuação, detalhe e retomada.
  - Acompanhamento corresponde ao progresso persistido.
  - Registro informa tempos, limites e parcialidade observados, sem prometer completude.
  - Nenhum contato ou envio real é necessário à prova.

### Adoção explícita

#### `E2E-ADOCAO-01` — Sugestão entra por configuração confirmada
- given: cenário de sugestões na fonte controlada e configuração sem o nicho sugerido.
- when: concluir a gravação explícita do interesse sugerido no formulário existente.
- then:
  - Somente após confirmação o interesse integra o escopo ativo.
  - Nova coleta usa revisão vigente e o caminho normal de observações.
  - Política de avaliação/alerta aplicável continua sendo a vigente, sem alerta causado só pela sugestão.
