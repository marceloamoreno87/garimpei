---
name: evaluator
description: Avaliar uma feature do Garimpei contra contract.md com evidências por item, projeção dos critérios de aceite e relatório persistido.
---

# Avaliação por contrato

Leia a feature, seu contrato e `AGENTS.md`. O avaliador escreve somente seu relatório, evidências de execução e a entrada da feature em `docs/prd_progress.json`; correções de implementação pertencem a `fix-runner`.

1. Resolva ambiente, migrations, seeds, drivers e comandos a partir de Prerequisites, documentos do projeto, spec e código. Use os scripts de ambiente. Para dados mutáveis, prepare ambiente descartável com marcador de propriedade e identificação desta execução.
2. Valide cada pré-requisito. Reutilize arquivos e fixtures existentes; não os altere para tornar a avaliação aprovada. Recursos externos indisponíveis geram evidência de bloqueio.
3. Execute os quality gates do contrato e o runner de backend quando aplicável. Registre comandos e códigos de saída. Se um gate falhar, marque os itens restantes bloqueados e ainda produza relatório.
4. Exercite itens em ordem Service → HTTP API → CLI → Worker → Event → UI → E2E, mantendo a ordem dentro de cada superfície. Use [assertion-patterns.md](references/assertion-patterns.md) para traduzir cada `then` em verificações. Registre interpretação quando necessária.
5. Para UI/E2E, use `playwright-cli`; capture e examine o estado aberto de menus, diálogos e overlays antes do próximo clique. Confira carregamento real de mídia, visibilidade, clipping e sobreposição. Quando relevante, teste a instância perto da borda da tela. Use `frontend-ui-design` para critérios visuais solicitados.
6. Atribua `PASS`, `FAIL`, `BLOCKED`, `MANUAL` ou `SKIPPED` a cada item, com esperado/observado e referência à evidência. Itens subjetivos sem critério observável ficam `MANUAL`. Um erro HTTP é resultado real; falha de transporte admite uma repetição. Três falhas de transporte consecutivas da mesma classe admitem um reinício do serviço desta execução; se não recuperar, aborte os itens restantes como bloqueados.
7. Projete cada AC pelo Coverage Manifest: todos os itens PASS = verificado; qualquer FAIL = falhou; BLOCKED/MANUAL/SKIPPED sem FAIL = indeterminado. Somente avaliação completa, sem pendências e com gates aprovados resulta em `clean` e status `done`.
8. Grave `eval-report-<timestamp-UTC>.md` conforme [report-template.md](references/report-template.md). Atualize apenas o progresso desta feature conforme [o protocolo](../../../docs/harness.md#progresso). Limpe apenas processos/dados criados e identificados nesta execução. `keep env` preserva o ambiente e registra o comando de limpeza sem revelar credenciais.

Filtros: `only <surface|ITEM-ID>`, `skip <surface>`, `only failed-last-run`, `pause on first failure`. Itens não executados ficam SKIPPED/BLOCKED; uma avaliação parcial não conclui a feature. Preservam-se relatórios anteriores e todos os contratos.
