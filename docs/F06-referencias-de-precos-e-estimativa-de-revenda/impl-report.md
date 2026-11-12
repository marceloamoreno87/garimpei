# Relatório de implementação — F06

Escopo: implementação, avaliação completa e até três correções autorizadas. Executada no checkout atual sem commit base; nenhuma delegação nem operação Git externa.

| Fase | Resultado |
|---|---|
| 1 · dados e método | 148 releituras reais; PS5 Slim Digital 825GB suficiente (mediana 3900,00), iPhone 13 Pro Max insuficiente por defeito; fonte KaBuM! verificada; phase-1.md registra parâmetros e limites |
| 2 · política e consultas | equivalência conservadora, Decimal/mediana, estados indisponíveis, novo independente, snapshot imutável, migration aditiva e consulta tipada vigente/histórica |
| 3 · processamento | reconciliação durável F04/worker, publicação atômica/condicional, TTL e retry, retomada e proteção contra repetição/conclusão antiga |
| 4 · validação | 184 testes da suíte, 12 focados, seis regressões atuais; seis gates, Django, migrations, build e harness aprovados |

## Arquivos

Novos pacotes `domain/valuation`, `usecase/valuation`, `infra/repository/valuation`, `infra/queries/valuation` e `infra/gateway/valuation`, modelo valuation_models, migration 0006 e valuation_handler. Integrações restritas a main.py, config/env.py, descoberta ORM, runworker e registro de entrypoints dos gates. Factories, cases.json, testes unitários e PostgreSQL/worker junto do backend. [Relação e hashes](evidence/2026-11-11T17-07-37Z/reviewed-inputs.json).

## Evidência e pré-requisitos

Dados e preparação em [operações](operations.md), [fase 1](phase-1.md) e [avaliação](./eval-report-2026-11-11T17-41-40Z.md). A entrada do worker e as consultas são as de produção; somente os adapters de fonte/relógio são determinísticos no ambiente eval. Testes de falha usam trigger PostgreSQL e controle de conclusão reais. Dados externos foram relidos de fato; o replay posterior conserva sua proveniência e identifica explicitamente seu relógio de confirmação.

Testes iniciais reproduziram ausência da política, fronteira de parcela e contradição de modelo. As correções ocorreram antes da avaliação canônica inicial. Nenhum requisito, contrato ou plano foi reduzido. Pendências por item: nenhuma após avaliação completa. Limitações: catálogo inicial de novo com um SKU, atributos explícitos nas famílias suportadas, preços anunciados e identidade conforme F04.

Sem commits ou PR autorizados. Os três critérios do PRD e todos os 20 itens são projetados pelo avaliador, não por este relatório.
