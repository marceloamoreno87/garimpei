# Plano de implementação — F06

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-11T17-41-40Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

**Pré-requisitos.** F02 operacional com dependências do lock e instância descartável conforme [operações](../F02-fundacao-tecnica-e-ambiente-local/operations.md). F04 integrada e avaliada, com evidência da identidade dos anúncios, da identificação de produto e das observações confirmadas. A decisão sobre método e fonte de novo será registrada conforme a [spec §3](spec.md#3-decisões-técnicas-propostas).

## Fase 1 — Validar dados e política

**1. Reproduzir e medir o recorte.** Usar observações reais de F04 para PlayStation 5 e uma segunda família de eletrônicos. Verificar se a F04 consegue entregar variante, condição do candidato, disponibilidade, preço integral e identidade. Exercitar a fonte candidata de novo, registrar escopo, acesso, limites, preço à vista e equivalência. Guardar em `evidence/` a prova sanitizada e a reprodução do método.

**Verificação.** Recalcular a mediana de uma amostra real suficiente, reproduzir uma indisponibilidade com dados insuficientes e localizar a cotação real de novo com variante equivalente. Fixar parâmetros, formato de entrada e política de retry da fonte. Se a evidência mudar a proposta, atualizar os três documentos antes da implementação afetada.

## Fase 2 — Avaliar e servir evidências

**2. Implementar a política e os adapters de entrada.** Projetar as observações confirmadas de F04 no contrato de avaliação, ligar o adaptador de novo e aplicar as regras puras da spec. Entregar factories, fixtures e fakes nomeados para observar as fronteiras e falhas de fonte.

**3. Persistir e consultar avaliações.** Aplicar migration aditiva sobre dados F04. Guardar resultado, evidências e versão juntos e entregar as consultas tipadas para F07/F08. Exercitar leitura vigente, leitura por ID, preservação da oferta e prazo das duas referências.

**Verificação.** Rodar os testes da política, as migrations, os itens SVC do [contrato](contract.md) em PostgreSQL e os seis gates após alterações estruturais. Reproduzir ao menos o conjunto suficiente e a cotação real com o adaptador implementado e comparar com os valores observados.

## Fase 3 — Integrar processamento em segundo plano

**4. Ligar o worker à publicação confirmada de F04.** Processar a carga inicial e mudanças de candidatos/identificação, agendar reavaliações por vencimento e testar retomada, gravação interrompida, falha de origem, repetição e concorrência. Usar a integração durável de F02/F04 e evidenciar que o cálculo publicado corresponde à revisão exibida pela consulta.

**Verificação.** Exercitar os itens WRK com worker e PostgreSQL reais em instância própria. Conferir por consulta a revisão vigente e a histórica em cenários de reentrega, reinício e conclusão fora de ordem.

## Fase 4 — Verificar entrega

**5. Executar os gates e conferir cobertura.** Executar todos os comandos do contrato, registrar a preparação reproduzível, os resultados por item, a evidência externa e os limites constatados. Conferir os três critérios de aceite do PRD e as interfaces de integração com F04, F07 e F08.
