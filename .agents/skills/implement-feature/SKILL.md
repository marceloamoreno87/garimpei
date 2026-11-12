---
name: implement-feature
description: Implementar uma feature já especificada do Garimpei seguindo spec.md, plan.md e contract.md, preparando os artefatos necessários à avaliação.
---

# Implementar uma etapa

1. Resolva `docs/FXX-slug/` e leia PRD, `spec.md`, `plan.md`, `contract.md`, `AGENTS.md` e progresso. Se documentos essenciais faltarem, informe exatamente quais; não invente o escopo.
2. Confira dependências concluídas, estado do Git e trabalho do usuário. Preserve alterações existentes. Se isolamento for necessário, reutilize uma worktree adequada; não misture features.
3. Execute as fases autorizadas na ordem do plano. Carregue `clean-arch` para backend e `playwright-cli` para navegação. Na fundação, gere scaffolding em pasta temporária e integre seletivamente, preservando o harness e suas instruções.
4. Crie também migrations, fixtures, sementes e configurações declaradas em Prerequisites. Segredos são referências a variáveis de ambiente. Atualize apenas a entrada desta feature para `implementing` durante a execução.
5. Verifique cada fase com os testes e gates aplicáveis. Reproduza defeitos antes de corrigi-los. Respeite o escopo pedido de commits; registre mudanças e resultados por fase mesmo quando não houver commit autorizado.
6. Ao terminar, execute as verificações finais e escreva `impl-report.md` com arquivos alterados, fases, pré-requisitos produzidos, comandos/resultados e pendências por item do contrato. Atualize para `implemented` quando o trabalho estiver pronto para avaliação; em falha terminal use `fail` com motivo.

`implemented` indica prontidão preliminar. O veredito `done` pertence à avaliação completa do contrato. Preserve spec/plano/contrato; uma alteração de requisito precisa ficar explícita e refletir a instrução atual do usuário.
