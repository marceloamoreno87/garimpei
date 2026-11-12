---
name: project-analizer
description: Analisar a arquitetura, componentes e dependências do Garimpei, produzindo relatório fundamentado com o plugin Project Analyzer da Full Cycle.
---

# Project Analyzer Full Cycle no Codex

O identificador `project-analizer` mantém a grafia do plugin instalado. Entrada: `$project-analizer architecture|component|dependencies [escopo]`.

- Arquitetura: [generate-architectural-report](references/upstream/commands/generate-architectural-report.md) e `references/upstream/agents/architectural-analyzer.md`.
- Componente: `references/upstream/agents/component-deep-analyzer.md`.
- Dependências: [run-dependency-audit](references/upstream/commands/run-dependency-audit.md) e `references/upstream/agents/dependency-auditor.md`.

Leia as referências selecionadas e execute com ferramentas do Codex na sessão atual. Exemplos de `Task`, `Read`, `Glob`, `Grep` e Claude são descrições do mecanismo de origem; use ferramentas equivalentes disponíveis. Agentes paralelos exigem autorização no pedido atual.

Analise o código do projeto, excluindo dependências geradas e templates do próprio harness das conclusões sobre o produto. Antes do scaffold, informe que somente o harness existe. Cite arquivos e relações observadas; diferencie problema confirmado de hipótese. Auditoria não instala ou atualiza dependências automaticamente. Entregue o relatório no destino solicitado e os comandos/evidências usados.
