# Regressões verificadas antes das correções

- Política ausente: `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests/unit/test_profit.py -q`, saída 2, ModuleNotFoundError de garimpei.domain.valuation.profit; após implementação, saída 0.
- Frete conhecido com modalidade desconhecida: mesmo comando, 1 failed / 10 passed; esperado 40, observado None. Após preservar shipping_freight sem produzir lucro ou eleger modalidade, 11 passed, saída 0 (0,03 s).
- Diagnóstico técnico: teste PostgreSQL de indisponibilidade falhou no evento JSON (runtime_event em lugar de profit_read_failed); alinhamento dos campos error_code/event/profit_identity ao formatter corrigiu a falha. Nova execução: 1 passed (24,22 s), incluindo cotação de novo vigente com revenda vencida.
- Contagem rígida de ciclos de coleta após salto de 14 dias foi substituída pela espera da observação e revisão efetivamente publicadas. É sincronização da fixture, sem alteração no contrato ou runtime F04/F06.
