# Garimpei

Garimpei ajuda a explorar anúncios de eletrônicos usados e entender estimativas de revenda e custos. O repositório contém o harness, os requisitos, a arquitetura proposta e um laboratório visual. A base Python/Django oferece endpoints técnicos e execução separada de web/worker com PostgreSQL e WAHA. As funcionalidades de monitoramento do MVP ainda não foram implementadas.

- [Preparação e operação da aplicação](docs/F02-fundacao-tecnica-e-ambiente-local/operations.md)
- [Operação do harness](docs/harness.md)
- [PRD e escopo do MVP](docs/PRD.md)
- [Stack escolhida](docs/stack.md)
- [Arquitetura proposta](docs/architecture/README.md)
- [Design system e protótipos navegáveis](docs/design/README.md)
- [Guia de desenvolvimento: projetos novos e existentes](docs/guia-desenvolvimento.md)
- [Instruções do projeto](AGENTS.md)
- [Plugins Full Cycle](plugins.md)
- [Progresso das etapas](docs/prd_progress.json)

Para verificar a preparação:

```bash
node scripts/check-harness.mjs
node --test scripts/test/harness.test.mjs
```

Para iniciar a base Django, prepare as dependências/imagens e o arquivo privado conforme o guia de operação acima; depois execute `./scripts/init.sh`. O comando diagnostica configuração ausente e só anuncia Ready após prontidão real de web/worker/banco/WAHA.

Para visualizar a proposta de interface, execute `python3 docs/design/serve.py` e abra `http://127.0.0.1:4173/prototypes/`. As features do produto seguem pendentes; sua implementação depende das especificações e decisões registradas no PRD.
