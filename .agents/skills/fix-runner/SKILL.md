---
name: fix-runner
description: Corrigir itens reprovados de uma avaliação de feature do Garimpei ou resolver conflitos de integração explicitamente solicitados.
---

# Correção dirigida

No modo de avaliação, receba o caminho do relatório, IDs dos itens reprovados e ciclo. No modo de conflito, receba o merge/rebase em andamento ou referência cuja integração foi solicitada. Não inicie um merge apenas porque há uma referência a PR.

1. Leia `AGENTS.md`, a especificação, o contrato e a evidência original. Liste causa e efeito esperado para cada item antes de editar.
2. Reproduza a falha na fronteira relevante. Para defeitos de comportamento, mantenha uma regressão significativa.
3. Corrija apenas código, testes, fixtures, sementes ou configurações necessários. Use `clean-arch` no backend. Preserve contrato, spec, plano e histórico de relatórios.
4. Execute testes e gates aplicáveis; registre os resultados. Falta de ferramenta/credencial não pode ser resolvida simulando sucesso.
5. Entregue IDs tratados, alterações, resultados e pendências para nova avaliação canônica. Registre o ciclo na entrada correspondente do progresso; não declare `done`.

Se commits fizerem parte da autorização atual, use um commit por ciclo, por exemplo `fix(F03): cycle 1 — address API-EXAMPLE-01`. Push, PR e integração seguem o escopo autorizado. Preserve conflitos/arquivos do usuário e relate quando a resolução exigir decisão de produto.
