# Contract — F22 Controle global de ligar e desligar o robô

*Gerado por spec-writer. Alterações manuais são sobrescritas na regeneração.*

## Prerequisites

Estas condições são entregáveis da implementação para executar os itens. Sua ausência deixa a verificação correspondente pendente; não constitui evidência de aprovação.

### Runtime services

- Versão integrada com F02/F03/F08/F13/F14/F15/F16/F19 avaliadas, PostgreSQL, Django e worker Procrastinate próprios. Preparar ambiente `eval` descartável pelas factories F02 e `./scripts/init.sh`; verificar manifesto, banco `garimpei_`, portas e prontidão. Encerrar por `./scripts/stop.sh`; limpeza restrita à instância descartável autorizada.
- Servidores programáveis de fonte, mídia, inferência e WAHA em loopback, com registro de chamadas e barreiras antes/depois das autorizações. Reusar `tests/factories/{runtime,listing,media,inference,assessment,first_eligibility,alert}.py` e seus servidores. Comprovar os pontos de bloqueio antes de cada interrupção; falhas/queda usam somente recursos de teste.
- Chromium e `playwright-cli` para itens UI/E2E. Registrar snapshots e capturas sanitizados na pasta de evidências da F22; não usar fonte, sessão ou grupo reais.

### Persistent state

- **CONTROLE:** instalação de teste configurada, controle inicialmente ligado/revisão conhecida, dois comandos UUID distintos e duas abas com a mesma revisão. Variações incluem desligado, drenando, operação de término indeterminado, worker indisponível e banco/controle em falha. Criar pelas migrations e factory F22; conferir estado pela leitura pública antes dos itens. Usado por: SVC-ADMISSAO-01/02/03/04, API-CONTROLE-01/02/03/04/05/06/07/08, UI-CONTROLE-01/02/03, WRK-PAUSA-01/02/03/04/05/06/07/08/09/10/11, E2E-ROBO-01/02/03.
- **TRABALHO:** interesses/CEP/taxa salvos, anúncios e amostra suficientes pelo fluxo das dependências, etapas pendentes e jobs anteriores ao comando de pausa. Há uma página seguida de outra, dois detalhes, duas fotos, avaliação preparada, inferência com duas partes e uma intenção F16 elegível sem autorização; cada unidade tem identidade conhecida. Criar usando as factories existentes e conferir observação, condição, revisão, composição e fila pelo estado público/persistido. Usado por: SVC-ADMISSAO-01/03/04, WRK-PAUSA-01/02/03/04/05/07/08/09/10, E2E-ROBO-01/02/03.
- **ENVIO:** uma intenção já autorizada com referência/corpo/vínculo congelados, em variantes com resposta retida, confirmação positiva, transmissão possivelmente realizada e falha comprovadamente não transmitida. WAHA programável conserva histórico de POSTs e mensagens; nenhum destinatário real é configurado. Criar pelo fluxo F16 e barreira, não por envio ao usuário. Usado por: WRK-PAUSA-05/06, E2E-ROBO-01/02/03.
- **LEGADO:** base com configuração concluída e filas/recibos conhecidos anterior ao schema F22, sem escolha global, incluindo preferências específicas IA pausada e alertas desativados. Preparar pelo executor de migrations no banco próprio até a revisão anterior, registrar inventário e avançar migrations F22; comparar os dados depois. Usado por: WRK-PAUSA-11.

### Static inputs

- Fornecer `apps/backend/tests/fixtures/robot/control_cases.json` com intenção/revisão, UUIDs dos comandos, etapas/unidades, gerações, timestamps UTC, barreira, estado das preferências e resultado esperado dos conjuntos acima. Fornecer `apps/backend/tests/factories/robot.py` para materializar cada caso com as factories existentes, controlar relógio e consultar mensagens/chamadas. Usado pelos itens que referenciam CONTROLE, TRABALHO, ENVIO ou LEGADO; verificar estrutura, identidades e expectativas antes de ativar o worker.
- Reusar `apps/backend/tests/fixtures/alert/first_eligibility_cases.json` para oferta recente/elegível e vencimento do primeiro envio, e `apps/backend/tests/fixtures/inference/cases.json` para partes da inferência. A factory deve registrar os casos/revisões selecionados e preservar expectativas dos contratos atuais. Usado por: WRK-PAUSA-03/05/06/08 e E2E-ROBO-01/03.

### Configuration

- Arquivo privado `GARIMPEI_ENV_FILE`, `GARIMPEI_ENV=eval`, diretórios e banco próprios. Endereços de fixtures `GARIMPEI_LISTING_FIXTURE_URL`, `GARIMPEI_VALUATION_FIXTURE_URL` e `GARIMPEI_ALERT_FIXTURE_URL` apontam para servidores locais autorizados pelo ambiente de teste. Injetar o gateway de inferência programável na composição de teste conforme F19; não depender da GPU compartilhada para a verificação de controle.
- Relógio e timeouts são os dos casos/etapas existentes; a pausa não altera o relógio nem zera orçamento. Sessão/conta/grupo do canal são sintéticos e conferidos em cada chamada. Confirmar configuração efetiva para impedir tráfego a fonte ou canal reais. CSRF permanece habilitado para verificações HTTP/UI.

## Quality gates

Todos os gates devem passar para considerar a implementação pronta. Executar da raiz e registrar saída/código de retorno, revisão e ambiente verificados.

- **Seis gates Python** — `node scripts/run-gates.mjs` — tipos, lint/templates, limites, arquitetura, ciclos e código/dependências sem uso.
- **Testes Python/PostgreSQL** — `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests` — regras, HTTP, migração, concorrência e regressões das dependências.
- **Django** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check` — configuração e registros válidos.
- **Migrations** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py makemigrations --check --dry-run` — schema versionado; WRK-PAUSA-11 verifica aplicação real em base preenchida.
- **Build** — `uv build --project apps/backend --wheel` — pacote com entradas e templates necessários.
- **Harness** — `node --test scripts/test/harness.test.mjs` e `node scripts/check-harness.mjs` — estrutura e regressões do lifecycle preservadas.
- **Navegador** — jornadas UI/E2E via `playwright-cli` com desktop e largura estreita — evidência do controle, estados, erros e continuidade da consulta, sem inferir ausência de trabalho só pela tela.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F22-AC01**: O usuário liga e desliga o robô por ações explícitas em Acompanhamento; estado global fica visível também nas ofertas, e desligar mantém interface, configuração, dados e histórico consultáveis. | API-CONTROLE-01, API-CONTROLE-02, UI-CONTROLE-01, UI-CONTROLE-02 |
| **F22-AC02**: Após confirmar a pausa, nenhuma nova unidade de coleta/pesquisa, mídia, identificação/valoração, avaliação/inferência ou envio é autorizada, inclusive por tarefa já enfileirada e por workers concorrentes; verificar a barreira antes da operação, sem depender apenas do agendador. | SVC-ADMISSAO-01, WRK-PAUSA-01, WRK-PAUSA-02, WRK-PAUSA-03, WRK-PAUSA-04, WRK-PAUSA-05 |
| **F22-AC03**: Unidades já autorizadas podem concluir e persistir resultado/checkpoint aplicável sem iniciar a próxima unidade; mostrar desligando enquanto houver operação em curso e não declarar desligado quando sua conclusão for indeterminada. | SVC-ADMISSAO-03, UI-CONTROLE-01, WRK-PAUSA-02, WRK-PAUSA-03, WRK-PAUSA-11 |
| **F22-AC04**: Pausa, reinício e retomada preservam filas, escolhas, configurações, sessão, pesos, intenções e recibos. Mensagem já autorizada pode concluir; envio incerto continua em reconciliação no vínculo original sem novo POST automático. | WRK-PAUSA-05, WRK-PAUSA-06, WRK-PAUSA-09, E2E-ROBO-01, E2E-ROBO-02 |
| **F22-AC05**: A intenção global salva sobrevive ao fechamento da aba, reinício e edição de configuração. Comando repetido é idempotente; comando conflitante de outra aba não sobrescreve decisão mais recente. Adoção sem escolha global preserva o comportamento anterior de configuração/início. | API-CONTROLE-03, API-CONTROLE-04, WRK-PAUSA-09, WRK-PAUSA-11 |
| **F22-AC06**: Ligar retoma apenas trabalho aplicável, sem duplicar coleta/evento/primeiro alerta, sem remover suspensão de acesso, barreira de recuperação ou pausas específicas da IA/alertas. Validade das referências e idade de publicação são conferidas novamente; oferta vencida durante a pausa não recebe primeiro envio. | SVC-ADMISSAO-04, WRK-PAUSA-07, WRK-PAUSA-08, WRK-PAUSA-10, E2E-ROBO-03 |
| **F22-AC07**: Falha ao ler ou gravar o controle mostra erro recuperável sem confirmação falsa nem mudança silenciosa da decisão persistida; novas operações ficam bloqueadas quando o estado não puder ser verificado. Worker ausente ou conclusão incerta aparece distinto de desligado confirmado. | SVC-ADMISSAO-02, API-CONTROLE-05, API-CONTROLE-06, API-CONTROLE-07, UI-CONTROLE-01, UI-CONTROLE-03 |
| **F22-AC08**: Jornada em ambiente isolado comprova desligar durante atividade, preservar consulta de ofertas, bloquear novos trabalhos/envios, reiniciar mantendo a pausa e ligar retomando trabalho válido sem mensagens duplicadas; testes não alteram recursos reais do usuário. | E2E-ROBO-01, E2E-ROBO-02, E2E-ROBO-03 |

Os itens verificam também a contribuição F22 para INT-29/INT-30/INT-31. F17/F18 não são necessárias; a integração futura usa a mesma barreira sem simular essas features.

## Service

**Verification mode:** Invocar as portas públicas de controle/admissão consumidas por F13/F14/F15/F16/F19; observar decisão, permissão, leitura tipada e efeitos persistidos na unidade fornecida.

### Admissão

#### `SVC-ADMISSAO-01` — Barreira comum entre estágios
- given: CONTROLE desligado e TRABALHO pendente em cada estágio de coleta/pesquisa, mídia, identificação/valoração, avaliação/inferência e envio.
- when: solicitar autorização para cada unidade em casos independentes.
- then:
  - Toda solicitação é negada como pausa, sem permissão de iniciar trabalho.
  - Os pedidos e checkpoints permanecem disponíveis para retomada.
  - A negativa não consome orçamento de falhas/tentativas do estágio.

#### `SVC-ADMISSAO-02` — Controle ilegível
- given: CONTROLE com falha de leitura persistente.
- when: solicitar uma nova autorização operacional.
- then:
  - Nenhuma permissão é concedida por fallback em memória ou valor padrão.
  - O erro é identificável como indisponibilidade do controle, distinto de pausa confirmada.

#### `SVC-ADMISSAO-03` — Finalizar autorização anterior
- given: TRABALHO com unidade autorizada antes do desligamento, resultado aplicável e CONTROLE agora desligado.
- when: finalizar a unidade previamente autorizada.
- then:
  - O resultado/checkpoint é conservado conforme a posse e a revisão válidas.
  - A finalização não cria autorização para a unidade seguinte.
  - Uma conclusão repetida não duplica a observação ou o efeito já confirmado.

#### `SVC-ADMISSAO-04` — Preferência individual conservada
- given: CONTROLE global ligado e TRABALHO em variantes com IA pausada, alertas desativados ou recurso específico bloqueado.
- when: consultar a possibilidade efetiva de execução de cada estágio.
- then:
  - A habilitação global não é apresentada como liberação do estágio bloqueado.
  - Preferências e motivos individuais continuam disponíveis sem alteração.

## HTTP API

**Verification mode:** Enviar requisições HTTP à instância própria; verificar status, headers, HTML e a decisão de controle persistida, sem observar conclusão assíncrona por esse meio.

### Controle global

#### `API-CONTROLE-01` — Salvar desligamento
- given: CONTROLE ligado, revisão e comando novos válidos, token CSRF válido.
- when: enviar POST para `/acompanhamento/robo/desligar/`.
- then:
  - Resposta 303 redireciona para Acompanhamento após a gravação.
  - A intenção persistida fica desligada com revisão atualizada.
  - A resposta não afirma que uma chamada ativa já terminou.

#### `API-CONTROLE-02` — Salvar habilitação
- given: CONTROLE desligado com revisão/comando novos válidos e token CSRF válido.
- when: enviar POST para `/acompanhamento/robo/ligar/`.
- then:
  - Resposta 303 redireciona para Acompanhamento após commit.
  - Somente a intenção global passa a ligada; configurações e preferências individuais permanecem iguais.

#### `API-CONTROLE-03` — Replay não reaplica intenção antiga
- given: um comando de CONTROLE já foi confirmado e outro comando legítimo posterior mudou a intenção.
- when: repetir o POST original com o mesmo UUID e payload.
- then:
  - A requisição é reconhecida sem reexecutar o comando nem incrementar a revisão.
  - A intenção posterior permanece preservada.
  - O destino do redirecionamento apresenta o estado atual confirmado, sem fingir uma nova aplicação do comando antigo.

#### `API-CONTROLE-04` — Revisão ou UUID conflitantes
- given: CONTROLE em variantes com outra aba usando revisão antiga ou UUID já registrado para payload diferente.
- when: enviar o comando conflitante.
- then:
  - A resposta é 409 com motivo legível e recuperação por recarga do estado.
  - Nenhuma intenção confirmada mais recente é sobrescrita.

#### `API-CONTROLE-05` — Forma inválida
- given: CONTROLE e CSRF válido, em casos com revisão ausente/negativa/não inteira ou UUID ausente/malformado.
- when: enviar POST de controle.
- then:
  - A resposta é 400 e informa o formato esperado.
  - O controle persistido permanece inalterado.

#### `API-CONTROLE-06` — Método e CSRF
- given: CONTROLE, em cenários independentes de GET numa ação POST ou POST sem CSRF válido.
- when: enviar a requisição inválida.
- then:
  - Método inválido retorna 405 com `Allow`; CSRF inválido retorna 403.
  - Nenhuma das requisições modifica a intenção.

#### `API-CONTROLE-07` — Falha de gravação
- given: CONTROLE ligado, comando válido e falha de commit controlada.
- when: enviar o comando de desligar.
- then:
  - A resposta é 503 com erro recuperável, sem confirmação de pausa salva.
  - A última decisão confirmada permanece preservada.
  - Nenhuma execução usa um estado apenas otimista como autorização ou confirmação de término.

#### `API-CONTROLE-08` — Leitura sem efeitos
- given: CONTROLE em um estado conhecido.
- when: enviar GET para `/acompanhamento/robo/`.
- then:
  - O fragmento apresenta intenção e estado efetivo com revisão/data aplicáveis.
  - A resposta tem `Cache-Control: no-store`.
  - A leitura não altera decisão, revisão ou fila de trabalho.

## UI

**Verification mode:** Navegar por Acompanhamento e ofertas com `playwright-cli`; acionar controles e observar textos, acessibilidade, erros e preservação da leitura. Conferir execução separadamente nos itens Worker/E2E.

### Controle global

#### `UI-CONTROLE-01` — Intenção e execução distintas
- given: CONTROLE em casos ligado, desligando com operação ativa, desligado sem operação, término indeterminado e worker ausente.
- when: abrir Acompanhamento.
- then:
  - A intenção confirmada e o estado efetivo são distinguíveis, com ação explícita apropriada.
  - Operação ativa mostra desligando e término indeterminado não aparece como desligado confirmado.
  - Worker ausente não é anunciado como operação saudável nem como prova de término.
  - Controles e mensagens funcionam por teclado, têm rótulos legíveis e não dependem só de cor.

#### `UI-CONTROLE-02` — Consulta durante pausa
- given: CONTROLE desligado e TRABALHO com ofertas já publicadas, filtros/página/revisão conhecidos.
- when: abrir a lista e o detalhe da oferta pela jornada existente.
- then:
  - Ofertas e histórico continuam consultáveis com o estado global visível.
  - Filtros, paginação e valores da revisão exibida permanecem coerentes.
  - A leitura não exige ligar o robô nem é apresentada como nova coleta/análise.

#### `UI-CONTROLE-03` — Erro sem confirmação otimista
- given: CONTROLE ligado e formulário válido, com falha de persistência do comando.
- when: clicar em “Desligar robô”.
- then:
  - A tela informa a falha e conserva a última decisão confirmada como tal.
  - A interface não troca para desligado confirmado só porque o botão foi clicado.
  - A recuperação mantém a jornada de Acompanhamento sem pedir para refazer configuração.

## Worker

**Verification mode:** Executar jobs/reconciliadores na instância própria, com servidores locais e barreiras; conferir chamadas, resultados persistidos, checkpoints e mensagens. Relógio e pausas são controlados sem depender de atraso arbitrário.

### Pausa e retomada

#### `WRK-PAUSA-01` — Jobs enfileirados antes da pausa
- given: TRABALHO em todas as etapas já possui jobs na fila e CONTROLE desligou antes de qualquer autorização operacional.
- when: consumir esses jobs antigos.
- then:
  - Nenhuma nova chamada/unidade operacional é iniciada em qualquer etapa.
  - Pedidos/checkpoints são conservados sem registrar conclusão fictícia ou multiplicar jobs por repetição.

#### `WRK-PAUSA-02` — Página autorizada termina sem próxima página
- given: TRABALHO com página/detalhe já autorizado e retido em resposta; CONTROLE desligou depois da autorização.
- when: liberar a resposta da unidade em curso.
- then:
  - A evidência aplicável e seu checkpoint são persistidos uma vez.
  - A próxima página/detalhe não é requisitada, ainda que pertença ao mesmo job.
  - O estado deixa desligando somente após confirmar o término da unidade.

#### `WRK-PAUSA-03` — Parte da IA e próxima imagem
- given: TRABALHO em cenários independentes com uma imagem ou parte de inferência autorizada e outra pendente, seguido de pausa global.
- when: concluir a unidade já autorizada.
- then:
  - A cópia/resultado aplicável da unidade é conservado.
  - A próxima imagem ou parte de inferência não começa.
  - A preferência específica de pausa da IA permanece inalterada.

#### `WRK-PAUSA-04` — Preparação não é autorização
- given: TRABALHO com valoração/avaliação preparada ou job reclamado, retido antes da fronteira operacional; CONTROLE desligou durante a barreira.
- when: liberar a tarefa preparada.
- then:
  - Ela não inicia a unidade por ter passado antes apenas pelo agendador ou pela preparação.
  - O pedido permanece retomável sem ser contado como falha ou avanço útil.

#### `WRK-PAUSA-05` — Pausa e autorização de mensagem concorrentes
- given: ENVIO em casos com pausa confirmada antes da autorização e autorização confirmada antes da pausa, inclusive sob workers concorrentes.
- when: processar a disputa na fronteira da transmissão.
- then:
  - Quando a pausa precede a autorização, nenhum POST ocorre.
  - Quando a autorização precede a pausa, somente a mensagem dessa autorização pode concluir, com recibo persistido.
  - Concluir a mensagem não autoriza outra mensagem encadeada com o robô desligado.

#### `WRK-PAUSA-06` — Incerteza e retry seguro durante pausa
- given: ENVIO em variantes possivelmente transmitida e comprovadamente não transmitida, com CONTROLE desligado.
- when: executar a recuperação/reconciliação.
- then:
  - A transmissão possível usa apenas consulta no vínculo original, sem novo POST.
  - Evidência inequívoca pode confirmar o envio original; histórico vazio conserva a incerteza.
  - A tentativa seguramente não transmitida também aguarda ligar para autorizar outro POST.

#### `WRK-PAUSA-07` — Ligar preserva preferências e barreiras
- given: TRABALHO pausado globalmente com IA pausada especificamente, alertas desativados, desafio de acesso ou barreira de recuperação, em variações independentes.
- when: processar a habilitação global.
- then:
  - O robô não altera as preferências nem remove qualquer barreira específica.
  - Trabalho independente permitido pode avançar, mas cada etapa bloqueada mantém seu motivo.
  - Nenhum acesso, inferência ou POST ocorre contornando o impedimento do estágio.

#### `WRK-PAUSA-08` — Tempo de pausa não prorroga validade
- given: TRABALHO em variantes com primeiro alerta que venceu as 48 horas de publicação ou referências que venceram enquanto desligado.
- when: retomar o processamento após ligar.
- then:
  - O primeiro alerta vencido não gera POST de compensação.
  - A referência vencida não é usada como estimativa válida para novo efeito.
  - Motivo e pendência de dados atuais ficam explícitos sem apagar a avaliação histórica.

#### `WRK-PAUSA-09` — Reinício e edição não ligam sozinhos
- given: CONTROLE desligado salvo, TRABALHO pendente e uma edição de configuração já concluída durante a pausa.
- when: reiniciar normalmente web/worker com o mesmo banco.
- then:
  - A intenção global permanece desligada.
  - Nenhuma nova unidade operacional é iniciada automaticamente por reinício/configuração.
  - Filas, checkpoints, escolhas manuais, pesos, sessões e recibos preservados continuam disponíveis.

#### `WRK-PAUSA-10` — Entrada obsoleta e recurso ainda ocupado
- given: TRABALHO desligado com revisão antiga na fila e operação de navegador/GPU ainda em conclusão, além de estado mais recente para o mesmo anúncio.
- when: ligar e reconciliar as pendências.
- then:
  - Recurso exclusivo não é usado concorrentemente por ignorar a operação anterior.
  - Resultado da revisão antiga não substitui a revisão vigente.
  - A retomada mantém a identidade dos efeitos, sem redescoberta ou primeiro alerta duplicado.

#### `WRK-PAUSA-11` — Adoção compatível com dados existentes
- given: LEGADO no schema anterior, com worker antigo parado pelo lifecycle próprio e inventário conhecido.
- when: aplicar as migrations e adotar o controle F22.
- then:
  - Sem escolha global anterior, o estado habilitado conserva a regra de início somente após configuração concluída.
  - Nenhum processo é iniciado/encerrado pela migration.
  - Configuração, pausas individuais, dados, filas, corpos e recibos conservam seu conteúdo.
  - Worker sem a barreira F22 não é tratado como compatível para declarar a função disponível.
  - Autorização legada ainda em curso ou indeterminada permanece no diagnóstico, sem nova autorização ou falsa conclusão por falta de permissão F22 anterior.

## E2E

**Verification mode:** Executar a jornada pelo navegador com web/worker/PostgreSQL reais e I/O externo programável. Observar estado, leitura de ofertas, chamadas, checkpoints e mensagens sintéticas entre as superfícies.

### Robô global

#### `E2E-ROBO-01` — Desligar durante atividade
- given: CONTROLE ligado, TRABALHO em andamento e ENVIO retido após autorização, com unidades seguintes já na fila.
- when: clicar em “Desligar robô”.
- then:
  - A pausa é persistida e a interface distingue sua confirmação da drenagem.
  - Unidades previamente autorizadas podem concluir, preservando checkpoint/recibo, sem começar as seguintes.
  - Ofertas/configuração continuam acessíveis enquanto novos trabalhos ficam bloqueados.
  - Mensagem sintética já autorizada mantém corpo, referência e vínculo.

#### `E2E-ROBO-02` — Reiniciar preservando pausa
- given: CONTROLE desligado após E2E-ROBO-01, com pedidos e ENVIO preservados.
- when: reiniciar normalmente a instância de teste.
- then:
  - A pausa permanece e os dados continuam consultáveis.
  - Não há novas operações de garimpo nem novo POST do envio anterior.
  - Operação de término indeterminado continua identificada até ser reconciliada, sem falsa confirmação de parada.

#### `E2E-ROBO-03` — Ligar e retomar trabalho válido
- given: CONTROLE desligado com parte de TRABALHO ainda válida, parte vencida e ENVIO anterior confirmado/incerto conhecido.
- when: clicar em “Ligar robô”.
- then:
  - Trabalho válido progride dos checkpoints preservados, respeitando as permissões individuais.
  - Trabalho vencido ou ultrapassado não é publicado como atual nem autoriza primeiro alerta vencido.
  - Efeitos anteriores não são repetidos por ligar; a incerteza conserva a referência original.
  - Nenhuma evidência depende de alterar fonte, perfil ou canal real do usuário.
