# Orchestration Journal — F21 Alertas ouro

**Run:** `2026-11-13T17-07-55Z`
**Branch:** `wave/20261113-f21`
**Started at:** `2026-11-13T17:07:55.571673+00:00`
**Retry budget:** 3
**Status:** aborted — positivo real não demonstrado; implementação preservada para avaliação

Implementação, avaliação e commits autorizados; integração/master/push pertencem ao coordenador. Worktree exclusiva c6a4, migration 0027 após fundação F22 / migration 0026. Nenhum recurso real de WhatsApp foi usado.

## Cycle Log

| # | Kind | Status | Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature + evaluator | completed with pending real evidence | núcleo, DI, DB, adoção, backup, autorização e lab implementados; testes focais e corpus autorizados preparados | d4d94e7, b21ef1b; impl-report.md |
| 1 | fix-runner + evaluator | corrected | achado independente: mesmo relógio selecionava UUID antigo; gerações/fingerprint atuais corrigidos. JSON de F15 compactado sem perda, TDD e limites preservados | e03e829; controlled/same-clock-*.txt; controlled/schema-budget-*.txt |
| 2 | fix-runner + evaluator | corrected | achado independente: bloqueio Gold escondia suspensão de recuperação/histórico; prioridade restaurada com teste red→green |19d3cd8; controlled/suspension-diagnostic-*.txt |
| final | evaluator | pending |25 itens PASS; E2E-REAL-01 BLOCKED por ausência de conjunto real suficiente e positivo. Não done |eval-report-2026-11-13T18-20-00Z.md |

## Evidência controlada

14 testes puros Gold; integrações de primeiro/redução/concorrência/slowcheck/manual, backup/restore e HTTP; matrizes adicionais 10/10, legado/falhas 5/5, fronteiras/progresso 7/7 e redução após 48 h 1/1. PostgreSQL e regras reais, F15/fonte/WAHA explicitamente fakes. Fixtures de mídia produzem derivativos válidos para backup. Gates Python seis grupos passaram. Regressão completa e revisão visual independente são coordenadas pela root na integração, com fontes e manifesto próprios. Os três shards terminaram com 873 PASS / 3 FAIL, ainda em correção/validação consolidada de F22; nenhum full PASS é declarado. Browser F21 saudável/zero/negativo/falha de leitura PASS, em evidence/browser-observations-wave13.json e browser-and-visual-review-wave13.md. Registro final compartilhado: docs/wave-evidence-2026-11-13T17-06-11Z/final-validation.json (pendente nesta gravação).

## Corpus e aprovação documental

A instrução posterior do usuário autorizou coletar o corpus usando perfil dedicado existente, read-only, sem copiar perfil/cookies. PS5: 12 detalhes sem base; iPhone: 48 detalhes da consulta original,9 elegíveis textuais; RTX: 12 detalhes em consulta separada,0 elegíveis. Fonte encerrada. Coorte principal 8 IDs / 42 fotos com hashes. O usuário autorizou explicitamente referência assistida por IA no lugar de rótulo humano; sincronização documental 958bc43 preservou o requisito de positivo real. Coordenador viu 42 fotos e congelou referência SHA 7aa96649... ANTES de qualquer saída Qwen dessa coorte. Não houve revisão humana independente. Suplemento 9º iPhone e RTX não foram misturados às saídas da coorte.

## Inferência real e limitações

Qwen/Ollama fixados com volumes/tokenizer/modelo verificados; GPU própria exclusiva e replay local dos bytes originais.15 chamadas físicas: 3 partes succeeded, 11 generation_length_limit, 1 text_reference_mismatch.8/8 avaliações agregadas failed/uncertain, 0 cobertura integral, 0 Gold positivo, 0 POST fake/real. Prompt físico 779–912; orçamento máximo 3728 < 4096 com reservas/output inalterados. Cinco referências IA good tornaram-se abstenções por falha, não concordância de qualidade. Cinco anúncios 1600 parecem mesmo aparelho/republicação; independência de vendedores/unidades não demonstrada.

Driver externo teve erros iniciais de configuração preservados; depois um worker próprio já publicou 8 resultados enquanto driver esperava republicação idempotente no 4º caso. Driver interrompido com exit 130, consolidação somente dos resultados persistidos sem novas chamadas. Não declarar CLI limpa ou análise completa. Stop normal exit 0 encerrou web/worker/serviços; DB/volumes próprios retidos, abertos apenas para consolidar e novamente parados.

## Encerramento

A pendência positiva real não é corrigível por reclassificar fotos, afrouxar política, aumentar output/contexto ou substituir com fixture. Coleta autorizada foi encerrada e seus negativos são resultados válidos. O ciclo termina aborted com progresso implemented e completed_at nulo, mantendo evidências e implementação revisável. Lock próprio liberado após o commit final desta execução; somente a entrada que identifica branch e início próprios será removida. Galeria estática em http://127.0.0.1:42796/index-gold.html permanece disponível para o coordenador; arquivos privados em /tmp/garimpei-f21-wave13 e /tmp/garimpei-f21-real não contêm segredos versionados.

### Integração final — 2026-11-13T18:33:50.926264Z

887 casos únicos cobertos,0skip; seis gates Python/Django/migrations/wheel/harness exit0. Consulte docs/wave-evidence-2026-11-13T17-06-11Z/final-validation.json. F21 implemented/pending:25PASS/1BLOCKED; E2E-REAL positivo não demonstrado. Autorização de referência assistida por IA registrada; não há revisão humana independente.
