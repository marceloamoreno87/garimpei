# Plugins Full Cycle no Codex

Fonte solicitada: https://github.com/devfullcycle/claude-mkt-place/tree/main

Os quatro pacotes foram instalados pelo CLI no marketplace `fullcycle-claude-marketplace`, versão `1.0.0`, e habilitados para este projeto em `.codex/config.toml`.

| Plugin instalado | Skill adaptada para Codex | Operações |
|---|---|---|
| `adrs-management` | `$adrs-management` | `map`, `identify`, `generate`, `link` |
| `diagrams-generator` | `$diagrams-generator` | `c4`, `mermaid` |
| `project-analizer` | `$project-analizer` | `architecture`, `component`, `dependencies` |
| `development-guidelines` | `$development-guidelines` | linguagem e parâmetros de stack |

Exemplos para quando houver requisitos/código:

```text
$adrs-management map
$adrs-management identify AUTH
$diagrams-generator mermaid docs/F01-exemplo/spec.md
$project-analizer architecture
$development-guidelines TypeScript --testing=vitest
```

Os plugins originais têm comandos/agentes de Claude Code. As skills em `.agents/skills/` adaptam esse roteamento ao Codex, preservando referências upstream sem depender do executável `claude`. `project-analizer` mantém a grafia original do identificador.

Para reinstalar em outro perfil/máquina:

```bash
./scripts/setup-codex.sh
```

Para conferir os pacotes instalados e habilitados:

```bash
codex plugin list --marketplace fullcycle-claude-marketplace --json
```

A instalação é local ao perfil do Codex; o repositório fornece configuração e adaptações reproduzíveis. Origem e revisão estão em `.codex/harness-sources.json`. Para os workflows do projeto, consulte [docs/harness.md](docs/harness.md).
