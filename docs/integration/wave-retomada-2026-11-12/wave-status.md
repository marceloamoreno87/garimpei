# Retomada paralela — 2026-11-12

**Status:** all-failed (nenhuma avaliação concluída; três retomadas interrompidas)
**Modo:** agentes nativos, três worktrees; iniciada aproximadamente às 23:13 UTC e finalizada às 23:14 UTC.

| Feature | Branch | Resultado | Diário |
|---|---|---|---|
| F14 | wave/resume-f14 | aborted: prova da fonte requer perfil exclusivo, em uso pela instalação principal | [Diário](../../F14-coleta-e-exibicao-confiavel-de-imagens/orchestration-2026-11-12T23-13-09Z.md) |
| F17 | wave/resume-f17 | aborted: perfil preliminar e matriz fault ausente; seis gates passaram | [Diário](../../F17-resiliencia-operacional-e-progresso-verificavel/orchestration-2026-11-12T23-13-13Z.md) |
| F18 | wave/resume-f18 | aborted: prova da fonte requer perfil exclusivo, em uso pela instalação principal | [Diário](../../F18-identificacao-de-produtos-e-busca-ativa-de-comparaveis/orchestration-2026-11-12T23-13-16Z.md) |

As três branches foram integradas à master; as worktrees foram preservadas. Nenhuma avaliação completa foi produzida nesta rodada, e os estados anteriores foram preservados. F15 depende de F14; F21 depende de F15 e F18; F22 depende de F14 e F15. Suas dependências ainda não estão aprovadas, portanto não foram iniciadas. Os serviços existentes não foram interrompidos.
