---
name: implement-and-evaluate
description: Executar uma feature especificada do Garimpei em ciclo de implementação, avaliação por contrato e correção com orçamento de tentativas e diário.
---

# Implementar, avaliar e corrigir

Resolva a feature com seus três documentos. Leia `AGENTS.md` e o protocolo de progresso em `docs/harness.md`. Este fluxo coordena as skills irmãs `implement-feature`, `evaluator` e `fix-runner`.

1. Confira dependências e o estado do trabalho; mantenha um lock exclusivo por feature com PID, host, branch e início, criado com exclusividade. Se existir lock ativo, relate a execução concorrente; remova lock antigo somente com evidência de que o proprietário terminou.
2. Crie `orchestration-<timestamp-UTC>.md` conforme [journal-template.md](references/journal-template.md). Registre entrada, escopo autorizado, orçamento e cada ciclo conforme acontece.
3. Execute `implement-feature` uma vez, ou preserve a implementação existente se o pedido for retomar uma avaliação. Em seguida execute `evaluator`, que é o responsável pelo veredito canônico.
4. Se houver FAIL corrigível, execute `fix-runner` com relatório e IDs; incremente `cycles` e reavalie. O padrão é até três ciclos de correção, além da implementação inicial. `no retries` limita à avaliação inicial; `max N retries` ajusta o orçamento.
5. Interrompa se as causas não forem corrigíveis localmente, se os mesmos itens falharem sem ganho após uma correção, ou se o orçamento terminar. Registre respectivamente `aborted`, `stuck` ou `exhausted`. Pendências manuais sem falha resultam em `manual-pending`, nunca sucesso.
6. `success` exige avaliação completa e limpa. Finalize o diário e progresso, libere somente o lock desta execução e reporte caminhos, evidências e pendências. Crie commit/PR ou faça push apenas se isso já fizer parte da tarefa autorizada.

Execute as etapas na sessão atual. Use agentes separados somente quando a solicitação atual autorizar delegação; nesse caso, forneça feature, skill, fontes canônicas e limites de escrita a cada agente. A skill não exige o `Task` do Claude nem o executável `claude`.

Honre `pause between cycles` quando pedido e `keep eval env` na avaliação final. Repasse escopos explícitos às etapas apropriadas e registre filtros; eles não podem transformar execução parcial em conclusão completa.
