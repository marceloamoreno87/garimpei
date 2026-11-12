---
name: implement-and-evaluate-tmux
description: Executar uma onda do Garimpei em paralelo quando o usuário pedir esse modo, com uma worktree por feature e consolidação de evidências; tmux é opcional.
---

# Ondas no Codex

O nome preserva a referência. O mecanismo padrão usa agentes do Codex com isolamento por worktree; tmux é uma alternativa quando solicitado. Carregar esta skill para consulta não autoriza lançar equipes.

1. Resolva `wave N`, `F03,F05` ou exclusões explícitas no PRD/progresso. Confira `spec.md`, `plan.md`, `contract.md` e dependências de cada selecionada. Serialize fundações e mudanças que compartilham arquivos.
2. Confira se há commit base e trabalho local não versionado: worktrees não recebem mudanças locais automaticamente. Prepare a base conforme autorização; se faltar base utilizável, informe o impedimento concreto antes de lançar equipes.
3. Reutilize worktrees ativas adequadas ou crie uma por feature em `.codex/worktrees/FXX-slug`, cada qual com branch, portas e banco próprios. Controle a concorrência pelos limites do Codex e pela independência real.
4. Invoque `implement-and-evaluate` em cada worktree com feature e parâmetros explícitos. No modo nativo, forneça o diretório ao agente e confirme seu uso. No modo tmux, use `scripts/team-driver.sh` desta skill e um diretório `.codex/worktrees/.wave-<run>/` com `wave.meta` e `status/`.
5. Preserve um único escritor do progresso compartilhado: equipes escrevem em sua própria worktree; o coordenador consolida somente as entradas das features selecionadas depois de ler os relatórios finais. Não copie JSON inteiro de uma equipe sobre outra.
6. Monitore conclusão e falhas, preserve worktrees com falha para inspeção e grave `wave-status.md` com IDs, branches, ciclos, vereditos, diários e limitações. Não execute merge ou publicação além do escopo atual.

Recursos do modo tmux: `scripts/team-driver.sh` lança Codex sem flags de bypass; `dashboard.sh` mostra o estado; `services-tail.sh` e `ports-tail.sh` exibem logs e portas. O formato de consolidação está em [wave-status-template.md](references/wave-status-template.md).
