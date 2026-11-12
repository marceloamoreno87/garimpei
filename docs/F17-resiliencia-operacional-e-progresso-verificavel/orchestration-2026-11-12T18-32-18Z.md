# Orchestration Journal — F17 Resiliência operacional e progresso verificável

**Run:** `2026-11-12T18-32-18Z`
**Feature folder:** `docs/F17-resiliencia-operacional-e-progresso-verificavel/`
**Branch:** `feat/F17-resiliencia-operacional`
**Started at:** `2026-11-12T18:32:18.093465+00:00`
**Retry budget:** 3
**Status:** running

## Overrides applied

- Delegação autorizada pelo usuário; worktree própria. Sem acesso/canal reais ou push.
- Base já inclui F13/F16/F19/F20; diagnóstico usa capacidades atuais sem reverter semântica.

## Cycle Log

| # | Kind | Status | Counts / Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | running | Fase 1: laboratório e calibração obrigatória | — |

## Cycle Detail

### Cycle 0

Calibração precede políticas; perfil operacional ainda não confirmado.

## Primeiro incremento — 2026-11-12

Calibração inicial em duas instâncias eval próprias: cinco controles e cinco timeouts por adaptador com prazos operacionais; cinco percursos completos F16 com recibo fake. Fonte 20,019–20,021 s, valoração 30,024–30,030 s, canal 10,002–10,011 s; percursos em 19,30–20,02 s incluindo startup. Nenhum canal/perfil real usado. A primeira tentativa de massa saudável continha declaração “não foi testado”; o ensaio foi corrigido enriquecendo a oferta pela fonte e por novo ciclo, sem alterar a condição protegida de produto.

Primeiro incremento experimental inclui progresso durável, arquivo de dados versionado, snapshot MVCC, catálogo, exportação idempotente, restauração eval com barreira dupla e consumidores reservados. Habilitação automática permanece falsa enquanto calibração final/contrato estão pendentes. Assinaturas de URLs de mídia são excluídas por schema, mantendo identidade da observação e declarando a exclusão; campos inesperados de credenciais em JSON são rejeitados.

Seis grupos Python aprovados: `evidence/increment-gates.txt`. Onze testes unitários e um percurso PostgreSQL backup/exportação/restauração aprovados: `evidence/increment-tests.txt`. O último ensaio verificou dados não vazios, identidade/observação preservadas, cópia sem assinatura transitória, exportação byte a byte e barreira persistente de despacho. Não equivale à avaliação completa do contrato. Integração de bytes/pins de mídia F14, testes adversos, interface e avaliação final continuam em execução.
