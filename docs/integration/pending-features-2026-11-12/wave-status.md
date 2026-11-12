# Wave Status — pendências F14/F15/F17/F18

**Status de aceite:** `all-failed` (zero features com aceite contratual limpo). **Integração do código:** aprovada,676 testes e seis gates PASS. Este vocabulário não indica falha da integração.

**Início:**2026-11-12T20:51:30Z. **Fim da validação:**2026-11-12T22:46:37.683458+00:00. Modo agentes nativos, sem tmux; até três agentes auxiliares, uma worktree por feature, coordenador como único consolidador do progresso. Escritores originais foram reutilizados, sem duplicação.

| ID | Branch | Veredito | Ciclos | Relatório |
|---|---|---|---|---|
| F14 | feat/F14-imagens-locais | manual-pending |2| docs/F14-coleta-e-exibicao-confiavel-de-imagens/eval-report-2026-11-12T20-12-37Z.md |
| F15 | feat/F15-avaliacao-multimodal | manual-pending |2| docs/F15-avaliacao-conjunta-de-imagens-e-descricao/eval-report-2026-11-12T22-00-00Z.md |
| F17 | feat/F17-resiliencia-operacional | stuck |0| docs/F17-resiliencia-operacional-e-progresso-verificavel/eval-report-2026-11-12T22-04-00Z.md |
| F18 | feat/F18-identificacao-comparaveis | manual-pending |1| docs/F18-identificacao-de-produtos-e-busca-ativa-de-comparaveis/eval-report-2026-11-12T22-01-57Z.md |

F14:34PASS/1BLOCKED, faltam duas resoluções reais da mesma foto. F15:28PASS/3BLOCKED, rótulos humanos/qualidade real adiados pelo usuário; ensaios integrais de versões e imagem hostil pendentes. F17:58BLOCKED nos pré-requisitos, faltam subcomando fault/matriz e confirmação do perfil; CLI calibrate corrigida, sem habilitação real. F18:25PASS/1BLOCKED, raio nativo6km diverge dos500km solicitados; pesquisa automática permanece desativada.

Todos os incrementos e relatórios das worktrees foram incluídos no candidato `e6bbc22`. A integração usa `integration/pending-features-2026-11-12`; os quinze diretórios, incluindo master, são preservados. Inventário completo em `worktree-inventory-before-merge.json`. Formulários humanos F15 permanecem acessíveis na worktree e na master após merge.

Não houve PR, push ou deploy. Não houve timeout de equipe aplicado; os agentes concluíram seus checkpoints e encerraram seus recursos próprios. Diários e evidências permanecem nos diretórios das features e neste diretório de integração. [Relatório da integração](integration.md), [calibração](calibration-supplement.md), [revisão final](evidence/review-runtime-calibration.md).
