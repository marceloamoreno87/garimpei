# Correção 2 — fronteira financeira determinística

Entrada: `eval-report-2026-11-12T14-48-17Z.md`. Orçamento: 2 de até 3 correções. O full anterior terminou interrompido em 54 PASS/1 FAIL, exit2, com os 431 hashes before/after idênticos. O FAIL não foi ignorado nem promovido a aprovação.

O caso financeiro passou isoladamente com instrumentação (1 PASS/36,13s). A ordem pública `SendAlertUseCase(binding=None)` antes do cliente explícito reproduziu a recusa: `state=blocked`, `reason=configuration_missing`, `next_action=18:03:19Z`, `clock=18:03:04Z`, `lease=None`, `attempts=0`. O claim respeitava os 15 segundos de backoff. O full não havia capturado esses campos; a reprodução confirma o mecanismo da ordem legítima de estágios, sem afirmar um snapshot retroativo inexistente.

A mudança fica exclusivamente no preparo do teste financeiro. Com o worker pausado, ele verifica que a intenção não tem corpo, lease ou tentativa, comprova recusa antes da próxima ação, valida o limite de backoff e move o relógio controlado até a maior ação persistida pertinente. O claim seguinte precisa obter delivery. Nenhum next_action, lease, corpo, snapshot ou estado de produção é reescrito pelo teste, e nenhum prazo é ignorado pelo produto.

Permanecem todas as verificações: evento da redução com compra R$1.000 enquanto latest vale R$900; consulta F07 event=True; compra/venda/lucro próprios; preço anterior R$1.200; ausência de R$900 no corpo; trio positivo/zero/negativo; taxa e arredondamento fracionários; confirmação e seis POSTs totais no WAHA sintético. As três fronteiras explícitas do mesmo cenário consideram o agendamento já persistido, evitando depender da velocidade do worker.

`f16-financial-order-red.log` conserva o RED. GREEN: três testes financeiros passaram em 66,27s; o trio final passou novamente em 37,03s após o ajuste de anotação e parametrização do SQL. Seis gates, Django, drift, build e harness passaram novamente com exit0. Nenhum arquivo de produto ou recurso real foi alterado neste ciclo. O grupo real não receberá outra mensagem.
