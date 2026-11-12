# F13 + F16 — ajuste do cenário composto

Escopo autorizado: somente testes/factories na master; nenhuma alteração de produção, spec, contrato ou progresso. Nenhum commit criado. Os hashes de 485 arquivos protegidos foram comparados: somente os três arquivos de teste listados no JSON mudaram.

## Causas confirmadas e mudanças

1. **Origem de intenção:** o RED original falhou após 72,36 s na consulta de 9142, restrita ao evento F09. SQL e HISTORY agora consultam tanto decision→event quanto first_decision→identity. O snapshot inclui ambas as referências, corpo, formato, financial, datas, ACK e os campos imutáveis das tentativas. Exige explicitamente IDs 9141/9142, dois intents e duas tentativas vinculadas; antes/depois continuam comparados integralmente.
2. **Sincronização:** esperar um confirmado global podia ser satisfeito por outro anúncio e deixava 9141 ainda bloqueado, sem tentativa. A espera agora é específica de 9141 antes da mudança para lost_empty. Os contadores globais de POST permanecem estritos.
3. **Estoque comparador:** REDs concretos registraram POST adicional de 614 após escolha manual + nova entrada automática e, depois, de 610 confirmado. Isso é permitido pela F16 para estoque recente elegível. O cenário passou a reutilizar HistoricalAlertSource e exatamente o preseed de comparadores já existente na factory F16. A extração para seed_historical_comparators mantém o comportamento da factory original; preços, amostra, condições e IDs frescos permanecem. A correção pontual experimental de 614 foi substituída pelo preparo compartilhado.
4. **Diagnóstico atual:** preservada a ausência de discovery para 9003 e acrescentada a razão publication_missing. O tombstone F09 de 9004 foi mantido, junto da razão efetiva F16 condition_excluded. Ambos precisam estar sem intenção por qualquer das duas origens.

## Evidências

| Arquivo | Resultado |
|---|---|
| navigation-red-before.txt | 1 FAIL / 72,36 s — consulta antiga de 9142 |
| navigation-red-after-dual-origin.txt | 1 FAIL / 46,66 s — POST adicional |
| navigation-red-manual-target.txt | 1 FAIL / 46,39 s — identifica 614 incerto, além de 9141/9142 |
| navigation-red-receipt-count.txt | 1 FAIL / 46,29 s — proteção de não-vacuidade |
| navigation-red-receipt-diagnostic.txt | 1 FAIL / 46,56 s — 9141 bloqueado e sem tentativa |
| navigation-red-global-wait.txt | 1 FAIL / 54,39 s — espera global inadequada |
| navigation-red-baseline-610.txt | 1 FAIL / 46,18 s — identifica 610 confirmado após espera específica |
| navigation-green.txt | **1 PASS / 68,57 s, exit 0** |

Comando focal: cwd apps/backend, `uv run --frozen --no-sync pytest -q tests/integration/test_navigation_events.py`. Ruff check, Ruff format --check dos três arquivos e git diff --check: exit 0. Nenhuma suíte ampla ou gate global foi executado durante as edições; o coordenador fará a validação conjunta.

As provas originais de rollback antes do recibo, continuidade, observações/eventos únicos, escolhas manuais e histórico anteriores, conteúdo hostil sem leitura do canário, zero POST por sugestão/prévia/adoção e um POST por 9001/9002 passaram. Os dois recibos anteriores são reais no canal fake: 9141 confirmado e 9142 incerto, uma tentativa cada, sem retransmissão.

A fixture encerrou normalmente e removeu seus recursos descartáveis; nenhum Facebook/WhatsApp real foi usado e nenhum recurso principal foi parado ou reiniciado. Os logs públicos têm apenas whitespace final normalizado; originais privados permanecem em .runtime. Hashes e comando estão em navigation-test-hash-diff.json.
