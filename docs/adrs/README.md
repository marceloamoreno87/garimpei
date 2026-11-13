# Registros de decisões arquiteturais

Data: 2026-11-10. Geração em português pela operação `generate` da skill local [adrs-management](../../.agents/skills/adrs-management/SKILL.md), adaptadora do plugin `adrs-management@fullcycle-claude-marketplace`.

## Estado e fonte da decisão

Todos os registros abaixo têm status **Aceito** para a direção documentada no PRD, na stack e nas instruções canônicas. Na elaboração de 2026-11-10, ainda não havia demonstração da aplicação. A execução posterior está na tabela abaixo e no [estado atual](../status-atual.md); aceitar um ADR não altera automaticamente o progresso de uma feature.

Na geração original, as fontes de entrada foram as decisões aprovadas e os documentos então disponíveis. Ainda não existiam ADRs anteriores nem arquivos de potenciais ADRs de uma aplicação implementada. Por isso, a geração usa diretamente essas evidências documentais e entrega os arquivos finais numerados neste diretório, com relações explícitas; não simula descoberta de decisões em código ou histórico Git.

O formato segue sete seções MADR da referência Full Cycle: contexto, motivadores, opções, resultado, prós/contras, consequências e referências. As alternativas explicitam os trade-offs discutidos e o contraste arquitetural de cada decisão; não indicam que protótipos ou benchmarks tenham sido executados. As referências locais incluem indicação de linha no texto do link, relativa à revisão documental atual.

## Índice

| Registro | Decisão | Estado da execução |
|---|---|---|
| [ADR-001](ADR-001-python-django.md) | Python/Django como base da aplicação | Implementado e avaliado em F02 |
| [ADR-002](ADR-002-templates-htmx.md) | Templates Django e HTMX | Interface Django implementada em F03/F08 e refinada na auditoria de UI |
| [ADR-003](ADR-003-postgresql-django-orm.md) | PostgreSQL com Django ORM/migrations | ORM/migrations implementados em F02 e features seguintes |
| [ADR-004](ADR-004-worker-fila-postgresql.md) | Worker separado, tarefas persistentes em PostgreSQL e ausência inicial de Redis | Web/worker e tarefas implementados em F02/F04/F09 |
| [ADR-005](ADR-005-operacao-local-wsl2.md) | Aplicação no WSL2, dependências Docker e acesso somente local sem login | Operação local implementada e avaliada em F01/F02 |
| [ADR-006](ADR-006-isolamento-regras-negocio.md) | Regras e casos de uso independentes de framework/I/O | Princípio aplicado e verificado pelos gates Python de F02 |

Os seis registros tratam decisões relacionadas, mas distintas: aplicação, apresentação, armazenamento, processamento contínuo, operação e direção das dependências. Não há um ADR para cada biblioteca ou requisito funcional.

## Decisões de implementação posteriores e limites do registro

- Procrastinate foi adotado e validado em F02; o acesso por navegador dedicado ao Facebook foi implementado em F11/F13.
- Layout Django, composição, integração transacional, política de alertas, classificação/amostragem e gates foram detalhados nos contratos e implementações correspondentes.
- Esses avanços não criam retroativamente um ADR para cada biblioteca. Os seis registros originais mantêm suas decisões e datas; o [mapa atual](../architecture/implementation.md) aponta os módulos e o [estado atual](../status-atual.md) aponta os aceites e bloqueios, inclusive F21.

## Navegação e fontes canônicas

- [Arquitetura proposta](../architecture/README.md).
- [Stack aprovada](../stack.md).
- [PRD](../PRD.md).
- [Reavaliação de tecnologias](../stack-reavaliacao.md).
- [Instruções do projeto](../../AGENTS.md).

Uma revisão que substitua uma decisão deve manter o registro anterior e explicitar a relação com o novo ADR. Aprovação documental, verificação do formato e validação da aplicação são evidências diferentes.
