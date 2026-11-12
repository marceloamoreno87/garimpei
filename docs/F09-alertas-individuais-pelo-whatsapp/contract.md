# Contract — F09 Alertas individuais pelo WhatsApp

*Gerado por spec-writer. Alterações manuais são sobrescritas na regeneração.*

## Prerequisites

### Runtime services

- Preparar ambiente descartável F02 com PostgreSQL, web e worker Procrastinate. Instalar versões travadas, aplicar migrations, iniciar com `./scripts/init.sh` e conferir a instância, o prefixo `garimpei_` e o probe do worker conforme [operações F02](../F02-fundacao-tecnica-e-ambiente-local/operations.md).
- Para cenários determinísticos, iniciar servidor local programável com as rotas WAHA usadas pela aplicação. Injetar seu endereço na composição de teste. Conferir log de chamadas, conteúdo e ACKs do chat sintético. Para interrupção, parar somente o worker de teste identificado pelo manifesto. Reiniciar com o mesmo banco e histórico do servidor local.

### Persistent state

- Criar histórico pelo fluxo de F04, usando configuração confirmada e fonte de fixture. Conferir eventos, observações, marco e sequência pela leitura pública. Produzir classificação F05 e estimativa F07 pelo fluxo integrado. Preparar dados dos testes de avaliação assíncrona mediante controle de disponibilidade da consulta, preservando identidade e versão da observação.
- Para cenário já alertado, processar uma descoberta até que o ACK e a intenção estejam confirmados. Conferir o histórico persistido e a contagem de mensagens antes de prosseguir. Para cenários de falha, pausar nos pontos indicados de autorização, chamada, resposta ou commit e verificar a barreira antes da interrupção.

### Static inputs

- A implementação deve fornecer cenários versionados em `apps/backend/tests/fixtures/alert/` e factories em `apps/backend/tests/factories/`. Criar ofertas distintas para lucro positivo, zero e negativo na lista principal, e para carga silenciosa, defeito, condição não confirmada, cobertura desconhecida e estimativa final indisponível. Criar uma descoberta de preço BRL 2300 e reduções para 2299,99, para 2200 e, depois de uma alta, novamente para 2200. As avaliações de cada versão têm valores de lucro distintos. Conferir a matriz pelo feed, pelas leituras de F05/F07 e pelo vínculo de observação.
- Preparar respostas programáveis de sessão pronta e expirada, pré-envio comprovadamente rejeitado, ACK pendente e positivo, resposta perdida após registrar a mensagem, resposta perdida sem registro e histórico ambíguo. As respostas incluem outro chat, mensagem de entrada e referência diferente para controles negativos. Conferir o estado e a contagem de POSTs e consultas do servidor local.

### Configuration

- Habilitar alertas de teste com sessão e chat sintéticos, API key privada e relógio controlável. Conferir que o cenário usa o servidor programável. Fixar e registrar tick, timeout, agenda de espera e janela de reconciliação. Avançar o relógio aos prazos configurados, sem depender de espera real nos casos determinísticos.

### External dependencies

- Para `E2E-WHATSAPP-01` e `E2E-WHATSAPP-02`, usar a imagem GOWS fixada na [F02](../F02-fundacao-tecnica-e-ambiente-local/versions.md), volume próprio, sessão em `WORKING`, conta pareada e chat direto de teste autorizado para receber a mensagem. Obter o ID canônico do chat, conferir conta e destinatário no WAHA local e verificar chave de API sem expor material de sessão. Usar oferta sintética e registrar o recibo com identificadores redigidos. Ausência de conta, sessão, autorização ou evidência deixa a prova real pendente. Um servidor programável verifica a lógica local e seus efeitos, e a imagem real comprova o canal de envio.

## Quality gates

Cada gate precisa passar para a feature ser considerada pronta. Executar da raiz com dependências travadas e ambiente de teste isolado.

- **Seis gates backend** — `node scripts/run-gates.mjs` — tipos, lint, limites de dependência, arquitetura, ciclos e código/dependências sem uso.
- **Testes Python e PostgreSQL** — `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests` — política, integração e concorrência, regressões das dependências e falhas controladas com os serviços requeridos.
- **Django** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check` — configuração e registro consistentes.
- **Migrations** — `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py makemigrations --check --dry-run` — modelos versionados. Verificar também a aplicação das migrations sobre dados preexistentes e a conservação do histórico das dependências.

## Coverage Manifest

| Critério de aceite do PRD §9 | Itens |
|---|---|
| **F09-AC01**: uma nova oferta identificada após a carga inicial, da lista principal e com estimativa disponível, gera alerta individual via WAHA; não se aplica corte por lucro mínimo. | WRK-ELEGIBILIDADE-01, WRK-ELEGIBILIDADE-03, WRK-ELEGIBILIDADE-08, E2E-WHATSAPP-01 |
| **F09-AC02**: carga inicial, ofertas com defeitos/reparo/peças, condição não confirmada e estimativa indisponível não geram alertas. | WRK-ELEGIBILIDADE-02, WRK-ELEGIBILIDADE-03, WRK-ELEGIBILIDADE-06, WRK-RETOMADA-01 |
| **F09-AC03**: reiniciar não reenvia alertas registrados nem transforma a carga inicial silenciosa em pendências; a retomada envia ofertas elegíveis ainda não alertadas que a fonte disponibilizar. | WRK-ELEGIBILIDADE-07, WRK-RETOMADA-01, WRK-RETOMADA-02, WRK-RETOMADA-03, WRK-ENVIO-06, E2E-WHATSAPP-02 |
| **F09-AC04**: anúncio já alertado com redução de preço gera novo alerta se continuar elegível, usando lucro recalculado; repetir a coleta do mesmo preço reduzido não repete o evento. | WRK-ELEGIBILIDADE-04, WRK-ELEGIBILIDADE-05, WRK-ELEGIBILIDADE-09 |
| **F09-AC05**: falha de WAHA/sessão ou confirmação incerta não é registrada como envio confirmado; o aceite das tentativas e da reconciliação depende da política ainda a especificar. | WRK-ENVIO-01, WRK-ENVIO-02, WRK-ENVIO-03, WRK-ENVIO-04, WRK-ENVIO-05, WRK-ENVIO-06, WRK-ENVIO-07, E2E-WHATSAPP-01 |
| **F09-AC06**: classificar manualmente uma oferta incerta como “funciona bem” ou corrigir uma escolha manual já salva muda sua aba após gravação e não gera alerta nem pendência de envio por essa ação para uma retomada posterior. | WRK-ELEGIBILIDADE-06, E2E-CLASSIFICACAO-01, E2E-CLASSIFICACAO-02, E2E-CLASSIFICACAO-03 |

Os itens de elegibilidade e retomada cobrem a contribuição F09 para INT-07 e INT-08. Os itens de classificação cobrem INT-10. Em INT-11, o worker decide e envia sem depender da aplicação visual de novas ofertas.

## Worker

**Verification mode:** Executar o worker com PostgreSQL e WAHA programável. Observar o feed, as mensagens e chamadas no chat sintético, além dos estados, recibos e diagnósticos persistidos pelo sistema.

### Elegibilidade

#### `WRK-ELEGIBILIDADE-01` — Descoberta com lucro positivo, zero ou negativo
- given: carga inicial concluída e três descobertas distintas, da lista principal, cobertas pelos interesses, com lucro positivo, zero e negativo.
- when: processar os eventos prontos.
- then:
  - Cada descoberta gera uma mensagem individual no chat configurado.
  - As mensagens identificam título, origem, preço observado, lucro estimado com sinal, data e link.
  - Cada evento mantém uma identidade de envio própria, mesmo sem ação de atualização da lista.

#### `WRK-ELEGIBILIDADE-02` — Condições que excluem alerta
- given: feed com evento silencioso, oferta com defeito, oferta incerta, cobertura desconhecida e descoberta com lucro definitivamente indisponível.
- when: processar o feed.
- then:
  - O chat permanece sem novas mensagens para essas identidades.
  - As decisões de exclusão têm motivo persistido e ficam sem intenção de envio.

#### `WRK-ELEGIBILIDADE-03` — Avaliação ainda em processamento
- given: a descoberta coberta está na lista principal, com avaliação F07 pendente para a observação do evento e lucro disponível apenas para outra observação.
- when: processar a decisão.
- then:
  - A decisão permanece em espera recuperável, sem POST e sem usar o lucro da outra observação.

#### `WRK-ELEGIBILIDADE-04` — Redução de anúncio já alertado
- given: anúncio alertado a 2300,00 BRL, ainda elegível, com evento de queda de 0,01 BRL e lucro calculado para o preço novo.
- when: processar a redução.
- then:
  - Uma mensagem distinta de redução informa o preço anterior, o novo preço e o lucro vinculado ao novo preço.
  - O histórico mantém a confirmação anterior e a referência distinta da redução.

#### `WRK-ELEGIBILIDADE-05` — Repetição e nova queda ao mesmo valor
- given: há redução confirmada a 2200,00 BRL e um feed com repetição técnica do mesmo evento, alta posterior e queda distinta ao mesmo valor.
- when: processar o feed.
- then:
  - O mesmo evento de redução continua com um envio.
  - A alta não cria alerta. A nova queda elegível cria outro alerta.

#### `WRK-ELEGIBILIDADE-06` — Revalidação antes do POST
- given: uma intenção elegível está aguardando o canal e a oferta já mudou para aba excluída ou deixou o escopo confirmado.
- when: o worker tentar despachar após restabelecer o canal.
- then:
  - O POST para essa intenção não ocorre.
  - O encerramento da intenção registra a condição ou o escopo que deixou de ser elegível.

#### `WRK-ELEGIBILIDADE-07` — Edição de interesse e republicação
- given: escopo vigente inclui interesse novo depois do marco e o feed contém uma descoberta de identidade nova, uma republicação com ID distinto e uma identidade anterior sem novo evento elegível.
- when: processar o feed atualizado.
- then:
  - As identidades novas elegíveis geram alertas próprios.
  - A identidade anterior sem evento elegível conserva seu histórico sem outro alerta.

#### `WRK-ELEGIBILIDADE-08` — Publicação da avaliação correspondente
- given: decisão em espera pela composição F07 e composição concluída para a observação e preço do evento, com as demais condições mantidas.
- when: executar a avaliação agendada.
- then:
  - A decisão associa a composição correspondente ao evento.
  - O alerta individual usa os valores dessa composição.

#### `WRK-ELEGIBILIDADE-09` — Redução sem alerta anterior confirmado
- given: anúncio com redução e lucro disponível, sem envio anterior confirmado ou ainda em processamento.
- when: processar a redução.
- then:
  - A decisão registra ausência de envio anterior confirmado.
  - A redução permanece sem intenção de envio.

### Retomada

#### `WRK-RETOMADA-01` — Histórico, carga silenciosa e recuperação
- given: carga inicial silenciosa, alerta confirmado antes da parada e descoberta elegível recuperada pela F04 durante a retomada.
- when: reiniciar o worker no mesmo banco.
- then:
  - A descoberta recuperada gera um alerta.
  - O recibo anterior permanece com a mesma identidade e sem outro POST.
  - A carga inicial continua sem intenções de envio.

#### `WRK-RETOMADA-02` — Histórico indisponível
- given: a leitura do histórico durável está falhando e há trabalho ainda não despachado.
- when: executar a retomada.
- then:
  - O sistema registra indisponibilidade de histórico e suspende novas autorizações de envio.
  - O cursor e os recibos conhecidos permanecem preservados para recuperação.

#### `WRK-RETOMADA-03` — Cursor e decisão após falha de commit
- given: a decisão do evento e o avanço do cursor sofreram rollback, e o banco voltou a aceitar gravações.
- when: repetir o ciclo de consumo.
- then:
  - O evento é recuperado e a decisão passa a existir uma única vez.
  - O cursor avança junto com a decisão durável.

### Envio

#### `WRK-ENVIO-01` — Sessão indisponível antes do POST
- given: intenção elegível e sessão não pronta ou autenticação inválida na verificação.
- when: executar o despacho.
- then:
  - O estado indica bloqueio recuperável, com motivo sanitizado.
  - Nenhum POST de mensagem ocorre e o estado confirmado não é produzido.

#### `WRK-ENVIO-02` — Nova tentativa comprovadamente segura
- given: houve falha comprovadamente anterior à transmissão, o canal voltou e a oferta segue elegível.
- when: executar o despacho no próximo instante agendado.
- then:
  - O worker transmite uma única mensagem ao chat esperado, com a referência original.
  - O histórico distingue a falha segura da nova tentativa e registra confirmação somente com ACK aplicável.

#### `WRK-ENVIO-03` — ID conhecido com ACK pendente
- given: o WAHA retornou um ID para o POST e a mensagem correspondente ainda tem ACK pendente.
- when: executar a reconciliação por ID.
- then:
  - Enquanto o ACK estiver pendente, a intenção permanece sem confirmação.
  - O reconciliador não faz novo POST.

#### `WRK-ENVIO-04` — Resposta perdida com prova positiva posterior
- given: a resposta do POST se perdeu, e há exatamente uma mensagem de saída no chat e conta corretos, com o corpo/referência da tentativa e ACK de servidor.
- when: executar a reconciliação.
- then:
  - A tentativa original é confirmada com o ID encontrado e a evidência do ACK.
  - A contagem de POSTs permanece a mesma.

#### `WRK-ENVIO-05` — Resultado que continua incerto
- given: tentativa incerta, com busca vazia, resultado conflitante ou resultado que só coincide em outro chat ou em mensagem de entrada.
- when: executar a última reconciliação automática prevista na janela configurada.
- then:
  - Nenhum envio é confirmado.
  - A tentativa segue disponível para revisão, com diagnóstico e sem novo POST.

#### `WRK-ENVIO-06` — Queda entre autorização e confirmação
- given: o worker anterior gravou a tentativa autorizada e parou sem confirmar o resultado. A lease expirou e o estado externo pode já ter sido alterado.
- when: reiniciar o worker no mesmo banco.
- then:
  - O trabalho recuperado entra em reconciliação da tentativa original, sem outro POST.
  - Se houver prova positiva, o ID confirmado fica vinculado à intenção original. Sem prova, a incerteza permanece.
  - Uma resposta da geração anterior não sobrescreve o estado recuperado.

#### `WRK-ENVIO-07` — Configuração alterada após vincular destino
- given: intenção pendente vinculada a uma conta, sessão e destino anteriores, com alteração em um desses campos.
- when: executar o despacho com a configuração atualizada.
- then:
  - O worker suspende a intenção vinculada à configuração anterior.
  - Nenhum POST dessa intenção segue para o destino novo.

## E2E

**Verification mode:** Usar os fluxos públicos de classificação da F05 e o worker com dados integrados. Para o canal real, observar o recebimento no chat autorizado, o ACK do WAHA e o recibo durável da aplicação.

### Classificação

#### `E2E-CLASSIFICACAO-01` — Classificação manual de oferta incerta
- given: oferta incerta com descoberta anterior, lucro disponível e sem alerta.
- when: salvar a classificação manual “Funciona bem” na F05.
- then:
  - A oferta passa à lista principal após a gravação.
  - A ação deixa a descoberta anterior sem intenção de envio e o chat sem nova mensagem, inclusive após retomar a fila.

#### `E2E-CLASSIFICACAO-02` — Correção manual persistida
- given: oferta com escolha manual “Não funciona bem” e evento anterior sem alerta.
- when: corrigir a escolha para “Funciona bem” na F05.
- then:
  - A aba muda após a correção confirmada.
  - A ação não cria intenção nem envio, inclusive na retomada.

#### `E2E-CLASSIFICACAO-03` — Evento atrasado após correção
- given: a oferta estava na aba incerta quando ocorreu a descoberta, o consumo ficou parado e a classificação manual foi salva como “Funciona bem” antes de o worker ler o evento.
- when: retomar o consumo da descoberta anterior.
- then:
  - A decisão usa o corte de classificação do evento e exclui a descoberta.
  - A condição vigente permanece na lista principal, sem pendência de WhatsApp pela ação manual.

### WhatsApp

#### `E2E-WHATSAPP-01` — Entrega observada pelo canal real
- given: imagem GOWS fixada, sessão pronta, conta pareada, chat de teste autorizado e descoberta sintética elegível.
- when: processar o alerta no perfil operacional documentado.
- then:
  - O chat autorizado recebe uma mensagem individual com os dados e a referência esperados.
  - O WAHA permite consultar a mesma mensagem e obter ACK de servidor ou posterior.
  - A aplicação conserva o recibo associado ao evento e os tempos medidos, com evidência sanitizada.

#### `E2E-WHATSAPP-02` — Sessão e recibo após parada normal
- given: houve alerta confirmado na prova real e os processos locais estão parados normalmente com a mesma configuração e volume.
- when: reiniciar a instalação.
- then:
  - O WAHA recupera a sessão pareada e o recibo permanece acessível.
  - O alerta confirmado continua registrado no mesmo evento, sem novo POST para ele.
