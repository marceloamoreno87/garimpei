# Implementação — F08

**Status:** pronta e avaliada. **Fases:** 3/3. **Commits:** 0 (fora do escopo autorizado).

A exploração editorial entrega abas, busca normalizada, categorias, modalidades e páginas de20, ordenadas pelo lucro principal antes de paginar. Detalhes apresentam a avaliação e a composição compatíveis da revisão selecionada, referências separadas, link original e classificação F05. Novos dados ficam disponíveis por aviso e aplicação explícita; falhas conservam a leitura.

## Fases

1. Contratos e projeção: modelos/migration0007, publicação serializada e atômica em PostgreSQL, fontes em lote, queries consistentes, assinatura comercial, overlay manual, expiração e histórico. F07 deriva valores na fronteira de snapshot; não há fórmula financeira duplicada na web.
2. Lista e detalhes: HTML/HTMX com URLs tipadas, validação/erros centrais, filtros/paginação, retornos, estados locais, mídia/fallback e composição editorial do design aprovado. Extensão opcional image_url em F04 preserva registros antigos.
3. Atualização e aceite: polling visível30s e ao retornar, abort/contexto de respostas antigas, aplicação com confirmação/foco e ajuste de página, massa de49 ofertas e dez auxiliares, testes e jornadas reais.

## Arquivos e integração

- `domain/listing/exploration.py`; quatro usecases de leitura/publicação; `infra/persistence/exploration_models.py` e migration0007.
- `infra/queries/listing/exploration_{source,mapper,queries}.py`; `infra/repository/listing/exploration_repository.py`; leitura em lote F06 em `infra/queries/valuation/postgres_queries.py`.
- Composição `main.py`, configuração central, reconciliador do worker, rotas/handler/apresentação/erros e templates/estáticos listing.
- Campo opcional de imagem em Evidence, consolidação, mapper e parsers; HTTPS validado no adaptador. Assets financeiros e fontes existentes preservados.
- `tests/unit/test_exploration.py`, `tests/integration/test_exploration.py`, fixture e factories de exploração/estados; testes F05 aguardam publicação assíncrona; teste F07 aguarda commit do backoff antes de avançar relógio.
- Registry de hooks/fields dinâmicos e documentação operacional. Spec, plan, contract, PRD e relatórios de outras features preservados.

## Pré-requisitos produzidos

Factory reproduzível com setup F03 e coleta/avaliação no worker, mapa de identidades determinístico, ações A/B/C, preparação de falhas e estados somente em testes, catálogo sintético restrito a eval. Segredos ficaram em diretórios temporários privados; ambientes próprios limpos após avaliação. Sem rotas de teste no produto.

## Verificação

203 testes aprovados; seis gates Python, Django, migrations, estáticos, build, tokens e harness aprovados. Duas integrações F08 adicionais passaram em52,11s. UI/E2E por playwright-cli, teclado/foco,360/768/1440, reflow200%, mídia, falhas e concorrência. [Relatório canônico](eval-report-2026-11-11T19-05-22Z.md), [operações](operations.md), [evidências](evidence/2026-11-11T18-18-36Z/).

Sem itens pendentes do contrato. F09/WhatsApp real e equivalência de câmeras não fazem parte desta avaliação sintética, conforme pré-requisitos autorizados. Não houve commit, push, PR ou deploy.
