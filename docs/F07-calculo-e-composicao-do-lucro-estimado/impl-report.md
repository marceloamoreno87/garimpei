# Relatório de implementação — F07

Escopo autorizado: implementar e avaliar F07 nesta sessão, até três correções, sem delegação, commit, push ou PR. Checkout inicial sem commit e arquivos prévios preservados. Requisitos e contrato mantidos.

| Fase | Resultado |
|---|---|
| 1 · política | Decimal BRL, taxa HALF_UP antes da subtração, estado/origem dos componentes, retirada prioritária e alternativas, zeros e negativos preservados |
| 2 · consultas | composição vigente e por evento via main.py, observação imutável do evento, configuração confirmada, compatibilidade/validade F06 e snapshot PostgreSQL REPEATABLE READ |
| 3 · verificação | 11 casos unitários; quatro jornadas PostgreSQL; 199 testes completos e seis gates aprovados, Django/build aprovados; contrato completo aprovado pelo avaliador |

## Arquivos e integração

Novos: `domain/valuation/profit.py`, `domain/valuation/profit_queries.py`, `usecase/valuation/read_profit_usecase.py`, `infra/queries/valuation/profit_queries.py`, `tests/unit/test_profit.py`, `tests/integration/test_profit.py`. Integração em `main.py`, diagnóstico seguro em `infra/runtime/logging.py`, factories/fixture de valuation e registro exato dos consumidores públicos de F07 no gate de não utilizados. Sem novas tabelas, migrations, endpoints ou tarefas.

Pré-requisitos reproduzíveis e interface pública: [operations.md](operations.md). ATIVA/RASCUNHO usam factories F03; OFERTA e REDUCAO usam coleta F04 e worker F06 reais com fonte HTTP sintética e relógio controlado. Manifesto próprio, prontidão 200 e limpeza descartável são verificados pelos testes.

## Verificação durante implementação

- Antes da política: `pytest tests/unit/test_profit.py` reproduziu `ModuleNotFoundError: garimpei.domain.valuation.profit`, saída 2; após implementação, onze casos aprovados, incluindo indisponibilidade de frete, avaliação pendente e conservação do frete conhecido sem modalidade confirmada.
- Matriz PostgreSQL inicial: três testes aprovados (50,96 s).
- Diagnóstico: teste comprovou log sem código/UUID antes de alinhar os campos ao formatter JSON; após correção, cenário aprovado.
- Concorrência: troca atômica de ponteiros por segunda conexão entre leituras conserva compra/avaliação do mesmo snapshot (13,67 s). Nenhum registro imutável é editado pela prova.
- Expiração: usada vencida com nova cotação ainda válida conserva compra/frete/percentual e omite lucro; cenário também cobre amostra insuficiente, falha técnica e rascunho (24,22 s).
- Gates intermediários detectaram tipos, formatação e campos públicos com consumidores dinâmicos; corrigidos e registrados pelos consumidores reais. Verificação final canônica consta na avaliação.

Nenhum desvio de requisito. Limitação de integração: consulta dentro de transação externa exige REPEATABLE READ/SERIALIZABLE; READ COMMITTED recebe falha identificável, conforme operações. F08 deve usar evaluation_id histórico para comparáveis; F09 deve conservar o DTO junto à decisão. Pendências por item: nenhuma identificada na implementação; aprovação depende da avaliação completa.

Avaliação final: [20/20 itens, 4/4 critérios, clean](eval-report-2026-11-11T17-53-22Z.md). Progresso F07: done, cycles=0. Diário: [orchestration-2026-11-11T17-43-16Z.md](orchestration-2026-11-11T17-43-16Z.md).
