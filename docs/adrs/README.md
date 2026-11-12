# Registros de decisões arquiteturais

Data: 2026-11-10. Geração em português pela operação `generate` da skill local [adrs-management](../../.agents/skills/adrs-management/SKILL.md), adaptadora do plugin `adrs-management@fullcycle-claude-marketplace`.

## Estado e fonte da decisão

Todos os registros abaixo têm status **Aceito** para a direção documentada no PRD, na stack e nas instruções canônicas. **Nenhuma implementação da aplicação foi demonstrada.** O status de um ADR não altera o progresso de F01–F09.

As fontes de entrada foram as decisões aprovadas nesta conversa e confirmadas nos documentos atuais. Não existiam ADRs anteriores nem arquivos de potenciais ADRs de uma aplicação implementada. Por isso, a geração usa diretamente essas evidências documentais e entrega os arquivos finais numerados neste diretório, com relações explícitas; não simula descoberta de decisões em código ou histórico Git.

O formato segue sete seções MADR da referência Full Cycle: contexto, motivadores, opções, resultado, prós/contras, consequências e referências. As alternativas explicitam os trade-offs discutidos e o contraste arquitetural de cada decisão; não indicam que protótipos ou benchmarks tenham sido executados. As referências locais incluem indicação de linha no texto do link, relativa à revisão documental atual.

## Índice

| Registro | Decisão | Estado da execução |
|---|---|---|
| [ADR-001](ADR-001-python-django.md) | Python/Django como base da aplicação | Pendente de F02 |
| [ADR-002](ADR-002-templates-htmx.md) | Templates Django e HTMX | Pendente de F02/F08 e jornadas correspondentes |
| [ADR-003](ADR-003-postgresql-django-orm.md) | PostgreSQL com Django ORM/migrations | Pendente de F02 e modelagem das features |
| [ADR-004](ADR-004-worker-fila-postgresql.md) | Worker separado, tarefas persistentes em PostgreSQL e ausência inicial de Redis | Pendente de F02/F04/F09 |
| [ADR-005](ADR-005-operacao-local-wsl2.md) | Aplicação no WSL2, dependências Docker e acesso somente local sem login | Pendente de viabilidade F01 e ambiente F02 |
| [ADR-006](ADR-006-isolamento-regras-negocio.md) | Regras e casos de uso independentes de framework/I/O | Princípio canônico; tradução executável Python pendente de F02 |

Os seis registros tratam decisões relacionadas, mas distintas: aplicação, apresentação, armazenamento, processamento contínuo, operação e direção das dependências. Não há um ADR para cada biblioteca ou requisito funcional.

## Propostas e pendências que não viraram decisões aceitas

- Procrastinate continua como primeiro candidato a validar para tarefas.
- Plataforma e estratégia de acesso, incluindo eventual automação de navegador, dependem de F01.
- Layout dos pacotes Django, registro ORM, composição e integração transacional são propostas em [organização](../architecture/organizacao-e-dependencias.md) e [confiabilidade](../architecture/dados-fluxos-e-confiabilidade.md).
- Máquina de estados de envio, reconciliação de resultado incerto, tentativas e políticas de classificação/amostragem continuam pendentes no PRD.
- Ferramentas e comandos dos gates Python ainda precisam ser definidos e implementados em F02.

Não foram criados ADRs aceitos para essas escolhas em aberto. As lacunas não impedem registrar as decisões de direção que já possuem evidência; elas impedem declarar suas implementações concluídas.

## Navegação e fontes canônicas

- [Arquitetura proposta](../architecture/README.md).
- [Stack aprovada](../stack.md).
- [PRD](../PRD.md).
- [Reavaliação de tecnologias](../stack-reavaliacao.md).
- [Instruções do projeto](../../AGENTS.md).

Uma revisão que substitua uma decisão deve manter o registro anterior e explicitar a relação com o novo ADR. Aprovação documental, verificação do formato e validação da aplicação são evidências diferentes.
