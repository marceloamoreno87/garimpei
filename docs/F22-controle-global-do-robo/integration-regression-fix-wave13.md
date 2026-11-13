# Correção das regressões da onda F21/F22

Base integrada: `5f713bb8a13856819c1f45d5954a9cfcf9469cd4`. Somente três módulos de teste foram alterados; nenhuma implementação ou regra de produto mudou. O coordenador mantém o controle do progresso e dos gates integrados.

## Evidência e causas

O shard original registrou **3 FAIL / 294 PASS**, em 1433,47s, em `docs/wave-evidence-2026-11-13T17-06-11Z/final-shard-0.txt`. Seu conteúdo original é preservado pelo coordenador; o manifesto local registra seu SHA256.

- **Lucro:** o traceback confirmou a assert de amostra insuficiente após uma espera por revisão absoluta `>=2`. Avaliações intermediárias também incrementam revisões. A espera agora vincula a avaliação publicada à revisão atual do comparável 604, antes das mesmas afirmações financeiras. A passagem de 14 dias também aguarda `evaluated_at` no instante do limite antes de avançar mais 1 segundo. Os reruns anteriores sem alterações haviam passado isoladamente (1/47,70s) e como módulo (4/147,84s), sem apagar a falha original.
- **Sugestões:** o worker pode reservar a janela ociosa imediatamente após configurar Slim, antes de o teste disponibilizar o anúncio relacionado. A fonte agora contém essa evidência antes de abrir a janela; a confirmação pode pertencer ao worker concorrente e é aguardada com prazo limitado. O instante original de publicação, `clock+1 segundo`, é mantido, preservando o evento `discovered` posterior ao início do monitoramento. As afirmações de não monitorar automaticamente, confirmação explícita, histórico, recibos, retry e canário continuam presentes.
- **Migração F22:** a criação de legado sobre schema 0025 usava o modelo Python atual, que já inclui `gold_qualification_id` da 0027. Seeds agora usam `MigrationExecutor.loader.project_state(...).apps` da 0025; a leitura posterior usa os modelos históricos da 0026. Permanecem as verificações de corpo/financeiro/tentativa congelados, pausa individual, nenhum job adicional e duas autorizações indeterminadas. A falha `UndefinedColumn` foi reproduzida localmente:1 FAIL / 7,04s.

## Validação final

A primeira execução dos três módulos corrigidos terminou **5 PASS / 1 FAIL**, em 145,74s. Os quatro casos de lucro e o caso de migração passaram; sugestões já superou a falha original, mas uma antecipação incorreta do timestamp da fixture eliminou seu evento `discovered`. Esse resultado permanece em `evidence/integrated-regressions-attempt1-wave13.txt`, com saída 1.

Corrigido somente esse timestamp, o módulo de sugestões passou: **1 PASS / 53,14s**, saída 0, com JUnit em `evidence/integrated-navigation-final-wave13.xml`. Seu wrapper registra comando, nodeID, horários, hashes dos três arquivos antes/depois e ausência de diff de produção. A união cobre os seis nodeIDs: **6 PASS / 0 FAIL / 0 SKIPPED**. Não representa a primeira execução como verde nem substitui os gates integrados do coordenador.

O manifesto `evidence/integrated-regressions-final-wave13.json` reúne os resultados e os hashes atuais. A primeira execução não capturou hashes previamente nem JUnit; isso é declarado. Após ela, lucro recebeu apenas formatação sem mudança de AST, migração permaneceu igual e sugestões recebeu a correção do timestamp. Todas as 123 linhas de assert originais foram comparadas automaticamente com a base e preservadas exatamente (64 lucro, 48 sugestões, 11 migração). Ruff lint, Ruff format e `git diff --check` passaram. As fixtures encerraram os ambientes descartáveis pelo `stop.sh --clean`.

Comando da execução de cinco casos aprovados e uma falha preservada:

```sh
TMPDIR=/tmp/g13 uv run --directory apps/backend --frozen --no-sync pytest tests/integration/test_profit.py tests/integration/test_navigation_events.py tests/integration/test_robot_migration.py --basetemp=/tmp/g13-regressions-green -q
```

Comando final de sugestões, com caminho absoluto do XML registrado no manifesto:

```sh
TMPDIR=/tmp/g13 uv run --directory apps/backend --frozen --no-sync pytest tests/integration/test_navigation_events.py::test_alias_events_hostile_content_adoption_and_prior_receipts_survive_f13_retry --basetemp=/tmp/g13-navigation-final --junitxml=<evidence>/integrated-navigation-final-wave13.xml -q
```
