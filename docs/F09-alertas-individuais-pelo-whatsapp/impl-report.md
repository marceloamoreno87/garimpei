# F09 — Relatório de implementação

Execução `2026-11-11T19-07-44Z`, branch `master`, checkout sem commits. Escopo: implementar, validar e avaliar F09; sem commit, push, PR, merge ou deploy. Dependências F04, F05 e F07 confirmadas como `done` nos arquivos atuais. Spec, plano e contrato preservados.

A implementação local está preparada. O usuário pediu expressamente para deixar a prova WhatsApp real pendente. Isso impede concluir o aceite completo e marcar F09 como `done`.

## Fases

| Plano | Entrega e verificação |
|---|---|
| 1 — Interfaces e viabilidade | Feed público F04, corte histórico F05 e composição financeira por evento F07 integrados. Protocolo WAHA conferido na documentação oficial e em HTTP programável; a imagem GOWS pareada permanece sem prova real. |
| 2 — Consumo e elegibilidade | Cursor e decisão na mesma transação; identidade por evento; exclusões explícitas; espera financeira e por confirmação anterior; valores financeiros congelados sem recalcular lucro na F09. Migração nova e upgrade com dados F04/F05/F06 exercitados. |
| 3 — Despacho e reconciliação | Intenção e tentativa persistidas antes do POST; revalidação sob o lock de publicação; binding privado; lease/geração; ACK validado; retry apenas antes da transmissão comprovada; reconciliação por ID ou referência/corpo exatos. SIGKILL após POST exercitado sem duplicação. |
| 4 — Operação e aceite | [operations.md](operations.md), fixtures, relógio controlável e testes preparados. Seis gates e checks Django aprovados; suíte completa com 227 testes aprovada, exit 0. E2E-WHATSAPP-01/02 pendentes. |

## Alterações

- `domain/alert/{alert,eligibility,ports}.py`: política, mensagem BRL, recibo e contratos puros.
- `usecase/alert/`: consumo, avaliação, envio e reconciliação injetados; falha financeira preserva diagnóstico recuperável e não bloqueia identidades distintas.
- `infra/repository/alert/`: transações de cursor/decisão, intenção única, autorização, backoff, geração e prova de confirmação.
- `infra/queries/alert/event_source.py`: condição na publicação e revalidação da versão corrente.
- `infra/gateway/alert/waha_gateway.py`: HTTP sem retry implícito, conta/sessão, ACK, consultas por ID e paginação conservadora.
- `infra/persistence/alert_models.py`, `listing_models.py`, `models.py` e `migrations/0008_alert_delivery.py`: estado durável, restrições, ordem compartilhada e baseline das escolhas manuais existentes.
- F04: `domain/listing/read_models.py`, `infra/queries/listing/postgres_queries.py` e `infra/repository/listing/postgres_repository.py` expõem/persistem a ordem de publicação.
- F05: `infra/repository/listing/condition_repository.py` grava o histórico manual na mesma transação e sob o mesmo lock de publicação.
- `main.py`, `config/env.py`, `infra/worker/alert_handler.py`, comando `runworker.py` e formatter de logs: composição, configuração privada, estágios independentes e logs sanitizados.
- `tests/fixtures/alert/cases.json`, `tests/factories/alert*.py`, `tests/unit/test_alert_policy.py` e `tests/integration/test_alert*.py`: matriz e cenários controlados.
- `tests/factories/runtime.py`: helpers de pausa/retomada com verificação de propriedade e ausência de transações abertas, compartilhados pelas verificações de migração e falhas.
- `tests/integration/test_listing_condition.py`: prepara o schema anterior com dados coletados reais e o worker pausado. Um binário atual não é executado contra colunas removidas deliberadamente.
- `tests/factories/condition_lab.py`: reset descartável das escolhas também limpa o histórico manual da fixture.
- `quality/entrypoints.json` e `vulture_whitelist.py`: colunas de auditoria descobertas/lidas pelo ORM e pelas consultas de diagnóstico.

## Pré-requisitos produzidos

Factories criam PostgreSQL/web/worker por `init.sh --disposable`, imagens fixadas e credenciais próprias. O WAHA programável atende apenas loopback. Há controles de sessão, autenticação, conta divergente, ACK pendente, resposta perdida, busca vazia/conflitante, outro chat, entrada e corpo divergente. Relógio controla prazos sem esperar 24 h. A barreira HTTP permite encerrar o worker somente após persistência da autorização e do efeito externo de teste.

Os testes verificam configuração/destino sintéticos, contagem de POSTs, recibos e integridade da observação financeira. Apenas os ambientes identificados das próprias fixtures são parados/limpos. Nenhum destinatário real foi contatado.

## Validação

- `node scripts/run-gates.mjs`: seis grupos aprovados, exit 0.
- `manage.py check` com test settings: sem problemas, exit 0.
- `manage.py makemigrations --check --dry-run`: sem mudanças, exit 0.
- Testes específicos F09: **24 passed**, inclusive PostgreSQL, HTTP, duas conexões, recuperação após SIGKILL e envio posterior.
- Regressões F03/F05 reproduzidas: **2 failed** antes da correção; **2 passed** após corrigir o scheduler ocioso e a preparação do schema histórico.
- Suíte completa final: **227 passed**, exit 0. Após a última correção de concorrência da confirmação, todos os testes F09 foram repetidos: **24 passed**, exit 0. A suíte ampla e a repetição dos casos afetados são evidências complementares; checksums registram o delta de dois arquivos.

A primeira validação ampla detectou dois problemas antes do fechamento de implementação: jobs de alerta eram criados sem eventos, e a antiga fixture F05 removia colunas enquanto deixava o coletor atual trabalhando. Os requisitos foram preservados: ausência de evento não cria trabalho de alerta, e o teste ainda verifica conservação das identidades/observações no upgrade histórico. Uma corrida adicional da fixture ao congelar o worker com transação aberta foi eliminada: a pausa agora verifica quiescência, e a edição de interesse é exercitada com o worker ativo.

## Limitações e pendências

`E2E-WHATSAPP-01` e `E2E-WHATSAPP-02`: falta executar com conta pareada e destinatário real autorizado, medir os intervalos operacionais e confirmar consulta/ACK na imagem fixa após parada normal. O usuário determinou adiamento. O servidor programável não substitui essas provas. Entrega/leitura ao aparelho não é inferida a partir do ACK SERVER.

A revisão final reproduziu uma corrida entre confirmação e avaliação dependente. `finish` agora usa a mesma ordem transacional de publicação; a regressão de duas conexões falhou antes da correção e passou depois.

Detalhes de evidência e projeção por critério de aceite ficam no [relatório canônico](eval-report-2026-11-11T19-58-06Z.md). A feature permanece sem `completed_at` enquanto houver essas pendências.

Fechado em 2026-11-11T19:58:06.964434+00:00. Avaliação: **22 PASS, 2 MANUAL, 0 FAIL**; 3 AC verificados e 3 indeterminados.

## Reavaliação 2026-11-11T21-54-20Z

Reavaliação real concluída: destino canônico direto LID aceito após resolução pelo WAHA; recibo GOWS com SenderAlt confirma a conta PN somente quando chat, saída, corpo e referência conferem. Uma mensagem sintética percorreu o worker integrado até o contato autorizado, com ACK 1, consulta/recibo e confirmação humana de recebimento. Reinício normal conservou sessão e mesmo recibo, sem novo POST. A latência de 247,331 s inclui a correção e a reconciliação agendada, não é benchmark. Segredos e ID externo continuam privados.

Validação ampla: 253 passed; após último patch HTTP, caso afetado repetido (1 passed), duas transições de navegador verificadas e seis gates finais aprovados. Relatório canônico novo registrado em prd_progress.json. Sem commit/push/PR.
