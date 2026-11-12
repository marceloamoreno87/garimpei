---
name: diagrams-generator
description: Gerar diagramas C4 ou Mermaid do Garimpei a partir de uma especificação de feature ou documento de arquitetura usando o plugin Full Cycle.
---

# Diagramas Full Cycle no Codex

Adaptação de `diagrams-generator@fullcycle-claude-marketplace`. Entrada: `$diagrams-generator c4|mermaid <documento> [pasta] [--no-images]`.

- C4: leia [c4-generate](references/upstream/commands/c4-generate.md) e `references/upstream/agents/c4-diagram-generator.md`.
- Mermaid: leia [mermaid-generate](references/upstream/commands/mermaid-generate.md) e `references/upstream/agents/mermaid-diagram-generator.md`.

Trate `spec.md` ou documento arquitetural fornecido como fonte, mesmo que a referência o chame FDD. Execute o procedimento na sessão atual com ferramentas do Codex; os exemplos de `Task`/Claude não exigem delegação. Use agentes somente quando autorizado no pedido atual.

Gere somente níveis/superfícies sustentados pela fonte. Preserve os fontes `.puml` ou `.mmd` e o texto de análise; não embuta todo o código na análise quando a referência pedir arquivos separados. Confira sintaxe e links. Renderize imagens quando solicitado ou previsto pela operação, se o renderer estiver disponível; reporte separadamente fonte criada e imagem efetivamente renderizada. Entregue caminhos e níveis omitidos com motivo.
