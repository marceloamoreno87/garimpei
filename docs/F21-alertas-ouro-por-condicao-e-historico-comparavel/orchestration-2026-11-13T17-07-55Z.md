# Orchestration Journal — F21 Alertas ouro

**Run:** `2026-11-13T17-07-55Z`
**Branch:** `wave/20261113-f21`
**Started at:** `2026-11-13T17:07:55.571673+00:00`
**Retry budget:** 3
**Status:** running

Implementação e avaliação autorizadas pelo usuário; integração/push pertencem ao coordenador. F22 tem prioridade nos arquivos compartilhados; F21 reserva migration 0027 após 0026.

## Cycle Log

| # | Kind | Status | Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | running | módulos exclusivos, laboratório e corpus | — |

## Pendências conhecidas

E2E-REAL-01 exige corpus real positivo e revisão humana própria; a referência assistida por IA da F15 não comprova esse requisito.

## Implementação inicial em andamento

- Núcleo puro, evidências versionadas, qualificação por conjunção, fingerprint próprio e política persistente entregues.
- Migration 0027 aditiva, trigger PostgreSQL de compatibilidade de consumidor e autorização final para primeiro alerta/redução integrados.
- Fotos/manuais/histórico/composição não são confundidos com assinatura semântica manual F16.
- Primeira execução focal: 12 unitários + 7 integrações PASS (84,78s), com PostgreSQL, F15 fake identificado e WAHA fake; exatamente um POST/recibo na BASE.
- Validação intermediária: tipos, lint, limites, arquitetura e ciclos passaram; não utilizados pendente no símbolo `admitted_unit` da fundação F22, que ainda aguarda integração final nesta worktree.
- Backup recebeu schema F21 e restauração conservadora da barreira de política; testes próprios ainda em preparação.
- Coleta real autorizada posteriormente pelo usuário: 2 consultas/4 páginas/24 detalhes, 43 fotos baixadas e SHA256 verificados; artefato `evidence/real-corpus.json`. Uma coleta suplementar dos IDs já descobertos ocorre pelo agente do coordenador. Humano/inferência/qualificação real positiva continuam pendentes.
