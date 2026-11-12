# Plano de execução: F01 — Discovery e viabilidade de integrações

Data: 2026-11-10. Dependências: nenhuma. Onda: 1. Execução sequencial. Referências: [especificação](spec.md), [contrato](contract.md), [PRD](../PRD.md) e [stack](../stack.md).

Este plano descreve trabalho **futuro**. A solicitação atual entrega somente os três documentos da feature; não executa fases, provas, instalações ou mudanças na aplicação/progresso.

## Pré-requisitos e preparação

| Entrada | Preparação | Verificação |
|---|---|---|
| Checkout e requisitos atuais | Preservar alterações existentes; conferir PRD, stack, arquitetura e harness | Estado do Git e leitura das fontes, sem pressupor aplicação existente |
| Ferramentas do harness | Disponibilizar Git, Bash e Node; registrar versões usadas na execução | Comandos de versão e verificações do harness definidas no contrato |
| Área de execução | Reservar temporário do sistema para provas e artefatos brutos, se necessários | Caminho privado identificado; nenhum temporário na raiz do repositório |
| Escopo prático | Registrar proposta, ações permitidas, plataformas, entradas, limites, custos e limpeza antes da prova | Referência à autorização; enquanto ausente, execução prática bloqueada |
| Serviços/contas opcionais | Preparar somente o necessário ao escopo aprovado, conforme spec §2 | Propriedade, configuração privada e prontidão específicas; ausência registrada por cenário |

Não exigir Python/Django, banco do produto, fixtures ou sessão WAHA real para leitura e comparação documental. Hardware e permissões indisponíveis são lacunas a explicitar. Nenhuma instalação de dependência ou contratação é implícita.

## Fase 1: delimitar investigação e ambiente

**1. Protocolo de investigação** — Definir as perguntas para as quatro candidatas, fontes de evidência e separação entre pesquisa documental e provas práticas. Registrar os limites operacionais e as autorizações necessárias em `environment.md`, conforme spec §§2–3.

**2. Inventário e requisitos locais** — Registrar recursos e ferramentas conhecidos, lacunas do host/WSL2/Docker e requisitos dos componentes considerados. Distinguir compatibilidade documentada de compatibilidade efetivamente observada, conforme spec §2.

**Verificação da fase:** protocolo e ambiente indicam origem, data e condições das informações; ações práticas sem autorização continuam pendentes. Aplicação ausente não é declarada pronta. Itens associados: DOC-AMBIENTE-01, DOC-AMBIENTE-04.

## Fase 2: comparar acesso e cobertura

**3. Comparação das plataformas** — Produzir a matriz de OLX, Facebook Marketplace, Enjoei e Mercado Livre em `report.md`, com modalidades de acesso, autenticação, dados, custos e esforço. Manter referências rastreáveis e limites por alternativa, conforme spec §5.

**4. Cobertura e referências** — Analisar interesses por categoria e nome/modelo, geografia, entrega, frete, identidade e retomada, além de usados comparáveis e referências de novos. Explicitar dados ausentes e consequências para as features consumidoras, sem criar regras de negócio pendentes.

**Verificação da fase:** abrir evidências de cada conclusão e conferir todas as dimensões do contrato; acesso bloqueado ou não pesquisado não pode virar capacidade confirmada. Provas eventualmente autorizadas precisam de entrada, ação e observação reproduzíveis. Itens associados: DOC-COMPARACAO-01–03 e DOC-COBERTURA-01–04.

## Fase 3: avaliar operação e preparar a fundação

**5. Viabilidade operacional** — Avaliar WAHA, recursos/custos locais e intervalo/latência sustentáveis com base nas evidências disponíveis. Registrar limitações, condicionantes e ausência de medição, distinguindo prontidão técnica de sessão e entrega, conforme spec §5.

**6. Passagem técnica para F02** — Preparar o mapa de integração seletiva do scaffold e adaptação do lifecycle, migrations e gates. Indicar o que preservar e como F02 verificará cada adaptação, mantendo a geração em temporário e a integração na árvore do produto como trabalho futuro da fundação.

**Verificação da fase:** cada alegação operacional tem suporte ou lacuna; o mapa abrange os scripts atuais e as seis finalidades dos gates, sem apresentar TypeScript como validação Python. Itens associados: DOC-AMBIENTE-01–04.

## Fase 4: recomendar, registrar decisão e revisar

**7. Recomendação e decisão** — Apresentar plataforma e estratégia sugeridas com trade-offs e condições, ou a inviabilidade identificada. Registrar separadamente em `decisions.md` a escolha explícita do usuário ou a pendência, com os impactos no PRD e nas etapas seguintes, conforme spec §5.

**8. Consolidação documental** — Consolidar comparação, índice de evidências, ambiente e decisões junto da feature, com referências entre requisitos e consumidores. Preservar estados e histórico; relatórios de execução/avaliação futuros ficam separados do contrato.

**Verificação da fase:** todos os itens do contrato têm evidência por item ou impedimento identificado; não há aprovação deduzida da recomendação, links quebrados ou segredos. Executar as duas verificações do harness listadas no contrato e registrar seus resultados. Itens associados: DOC-RECOMENDACAO-01–03 e todos os itens de cobertura.

## Testes e gates por etapa

| Etapa | Verificação | Critério |
|---|---|---|
| Esta preparação de documentos | Consistência de spec/plano/contrato, cobertura literal F01-AC01–AC04, links locais e fontes preservadas | Três arquivos coerentes; sem alterar o progresso nem afirmar discovery concluído |
| Execução/avaliação futura de F01 | Revisão dos itens GWT e seus resultados documentais; `node scripts/check-harness.mjs`; `node --test scripts/test/harness.test.mjs` | Evidências de cada item e comandos aprovados; pendência externa permanece pendência |
| Fundação futura F02 | `node scripts/run-gates.mjs`, após adaptação às seis coberturas Python, mais testes/build pertinentes definidos no próprio contrato | Cada comando real executado e aprovado; erro de pré-requisito ou verificação ausente impede concluir F02 |

## Condições de passagem

A F01 não é concluída pela produção deste plano. Sua avaliação exige os entregáveis futuros e evidências do contrato; a decisão da primeira plataforma/acesso precisa ser explícita para encerrar o aceite da escolha. Lacunas reconhecidas não constituem prova positiva da capacidade ausente.

F02 recebe a escolha registrada, restrições de operação/recursos, lacunas com destino e mapa de preparação/scaffold/gates. Decisão ainda pendente ou incompatibilidade que inviabilize requisito obrigatório impede executar a fundação dependente até resolução. Mudança de escopo ou operação exige decisão explícita; não adaptar o PRD implicitamente.

F02 especificará versões, gerenciador, biblioteca de tarefas, comandos Python e integração efetiva antes de implementar sequencialmente. F01 não altera scaffold ou validadores para liberar essa dependência.
