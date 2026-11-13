# Garimpei

Garimpei é uma aplicação local para explorar eletrônicos usados, acompanhar anúncios e comparar evidências de condição, preços e revenda. Usa Python/Django com templates/HTMX, PostgreSQL, worker separado, Facebook Marketplace por navegador dedicado, inferência local por Ollama/GPU e WhatsApp via WAHA.

F01–F20 e F22 têm avaliação `done`. F21, qualificação de alertas ouro, está integrada como `implemented`, com prova real positiva ainda bloqueada. O [estado atual](docs/status-atual.md) reúne os relatórios e as limitações; status não é garantia de disponibilidade da fonte externa.

- [PRD e requisitos](docs/PRD.md) · [progresso por feature](docs/prd_progress.json)
- [Preparação e operação](docs/F02-fundacao-tecnica-e-ambiente-local/operations.md)
- [Stack](docs/stack.md) · [arquitetura implementada](docs/architecture/implementation.md)
- [Interface e design system](docs/design/implementation.md) · [auditoria de UI](docs/design/audit-2026-11-13/README.md)
- [Controle global do robô](docs/F22-controle-global-do-robo/operations.md) · [operação e backups](docs/F17-resiliencia-operacional-e-progresso-verificavel/operations.md)
- [Harness](docs/harness.md) · [guia de desenvolvimento](docs/guia-desenvolvimento.md) · [instruções](AGENTS.md)

Prepare dependências, imagens e um arquivo privado de ambiente conforme a operação F02. Na raiz:

```bash
GARIMPEI_ENV_FILE=/caminho/privado/garimpei.env ./scripts/init.sh
```

Abra a URL local anunciada após `Ready`. O script verifica web, worker e dependências. Para encerrar os recursos próprios preservando os dados:

```bash
GARIMPEI_ENV_FILE=/caminho/privado/garimpei.env ./scripts/stop.sh
```

Ligar/desligar o robô pelo acompanhamento controla o trabalho automático sem encerrar os serviços. Fechar a aba conserva o processamento enquanto máquina, worker e dependências permanecem ativos. Login/desafios do Facebook e pareamento do WhatsApp são feitos pelo usuário.

Validações, com dependências Python instaladas:

```bash
node scripts/run-gates.mjs
node scripts/check-harness.mjs
node --test scripts/test/harness.test.mjs
```

Para a suíte Python, execute de `apps/backend/`:

```bash
uv run --frozen --no-sync pytest
```

Testes de integração criam recursos próprios em Docker; use temporários privados fora do checkout e com espaço disponível. O backup exige reserva mínima de armazenamento. Evidências de navegador e seus limites estão junto da auditoria e das features.

O [laboratório visual histórico](docs/design/README.md) continua disponível por `python3 docs/design/serve.py`, em `http://127.0.0.1:4173/prototypes/`. Seus dados e ações são simulações independentes da aplicação Django.
