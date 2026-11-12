---
name: adrs-management
description: Mapear decisões arquiteturais do Garimpei, identificar ADRs, gerar registros e ligar decisões relacionadas usando o plugin Full Cycle.
---

# ADRs Full Cycle no Codex

Adaptação dos comandos do plugin instalado `adrs-management@fullcycle-claude-marketplace`. Use `$adrs-management map|identify|generate|link` com os módulos ou caminhos desejados.

| Operação | Referência do comando | Procedimento detalhado |
|---|---|---|
| map | [adr-map](references/upstream/commands/adr-map.md) | `references/upstream/agents/adr-analyzer.md`, Phase 1 |
| identify | [adr-identify](references/upstream/commands/adr-identify.md) | `references/upstream/agents/adr-analyzer.md`, Phase 2 |
| generate | [adr-generate](references/upstream/commands/adr-generate.md) | `references/upstream/agents/adr-generator.md` |
| link | [adr-link](references/upstream/commands/adr-link.md) | `references/upstream/agents/adr-linker.md` |

Leia apenas as referências da operação selecionada, resolva parâmetros e execute na sessão atual com as ferramentas disponíveis no Codex. Os exemplos de `Task`, `subagent_type` e slash commands nas referências descrevem a interface original do Claude; não exigem esses recursos nem delegação. Delegue somente quando a solicitação atual autorizar agentes.

Baseie ADRs no código e nas decisões reais, diferenciando proposta de decisão tomada. O destino padrão é `docs/adrs/`; preserve registros existentes e crie ligações relativas válidas. Para projeto ainda sem aplicação, declare a limitação em vez de inventar arquitetura implementada. Entregue os arquivos produzidos e as evidências consultadas.
