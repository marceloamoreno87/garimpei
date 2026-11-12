# ADR-004: Separar o worker e persistir tarefas em PostgreSQL sem Redis inicial

**Status:** Aceito
**Data:** 10-11-2026
**ADRs relacionados:** [ADR-003](ADR-003-postgresql-django-orm.md), [ADR-005](ADR-005-operacao-local-wsl2.md)

## 1. Contexto e problema

Coleta, avaliação e alertas precisam continuar enquanto os processos
necessários estiverem ativos, independentemente de uma aba aberta. O
sistema deve retomar acompanhamento e alertas elegíveis após
interrupções, preservando histórico. Uma tarefa em memória não
representa por si só a persistência da necessidade de trabalho.

A proposta inicial colocava tarefas no processo web. Na revisão, o
usuário aprovou worker Python separado e tarefas persistentes no
PostgreSQL, em um projeto compartilhado e sem Redis inicialmente. Nada
disso está implementado. A direção aceita não fixa biblioteca nem
promete entrega exatamente uma vez.


## 2. Motivadores da decisão

- Desvincular o monitoramento do ciclo de vida das requisições web.
- Preservar trabalho recuperável e histórico entre falhas e reinícios.
- Conter a quantidade de serviços da execução local.
- Permitir controle explícito de concorrência e execução das tarefas.
- Distinguir resultado técnico da fila e confirmação do efeito
  externo.

## 3. Opções consideradas

- Worker separado com tarefas persistentes em PostgreSQL.
- Execução de tarefas apenas no processo web.
- Worker com broker adicional, como Redis.

## 4. Resultado da decisão

Escolhida a opção worker separado com tarefas persistentes em
PostgreSQL. Os processos compartilham código e banco; a separação não
exige microserviços ou repositórios independentes. Redis não entra
inicialmente porque não há necessidade demonstrada que compense outro
serviço.

A biblioteca permanece fora da decisão: Procrastinate é candidato, não
adoção concluída. A integração entre gravação dos dados e persistência
das tarefas também depende de validação. Trabalho durável é a
propriedade aceita; o mecanismo concreto ainda não foi fechado.


## 5. Prós e contras das opções


### Worker e tarefas no PostgreSQL

- Favorável: separa execução contínua do processo que atende a
  interface.
- Favorável: aproveita o banco escolhido para persistir trabalho.
- Desfavorável: acrescenta processo a supervisionar e um ciclo de
  recuperação.
- Desfavorável: exige demonstrar integração transacional, concorrência
  e falhas.

### Tarefas apenas no processo web

- Favorável: reduz o número inicial de processos da aplicação.
- Favorável: simplifica a montagem de um protótipo com pouco
  processamento.
- Desfavorável: acopla a execução contínua ao processo web.
- Desfavorável: manter tarefas em memória não oferece persistência ou
  retomada.

### Worker com broker adicional

- Favorável: permite ferramentas construídas em torno de um broker.
- Favorável: separa coordenação técnica do serviço relacional.
- Desfavorável: acrescenta configuração e recuperação de outro
  serviço.
- Desfavorável: o custo adicional não foi justificado por requisito ou
  volume medido.

## 6. Consequências

Início, prontidão e parada precisam reconhecer web e worker
separadamente. Acompanhamento e alertas dependem de estado persistido,
não de uma execução continuar viva. Trabalho interrompido deverá
possuir tratamento definido antes da conclusão das features
correspondentes.

A confirmação de envio via WAHA permanece um problema de integração
externa. A fila não elimina a ambiguidade de uma mensagem enviada
antes de uma queda que impeça registrar confirmação. Tentativas e
reconciliação continuam pendentes no PRD, sem serem decididas pela
escolha do worker.


## 7. Referências

- [docs/stack.md:12](../stack.md)
- [docs/PRD.md:41](../PRD.md)
- [docs/stack-reavaliacao.md:90](../stack-reavaliacao.md)
