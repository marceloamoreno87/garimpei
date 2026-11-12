# Verificação do laboratório visual — versão 0.2

Data: 2026-11-10. Objeto: protótipos e biblioteca em `docs/design/`. Avaliação visual do próprio agente usando [frontend-ui-design](../../.agents/skills/frontend-ui-design/SKILL.md), referências do Impeccable e Chromium via [playwright-cli](../../.agents/skills/playwright-cli/SKILL.md). Não houve teste com usuário, avaliação independente ou implementação do produto Django.

## Entrega e critérios observados

| Resultado | Evidência |
|---|---|
| Configuração guiada com custos vazios e obrigatórios | [Custos em branco](evidence/setup-costs.png), [interesses](evidence/setup-interests.png), [falha ao concluir](evidence/setup-save-error.png) |
| Coleta liberada somente após sucesso, com carga inicial silenciosa | [Primeira coleta](evidence/initial-collection.png) e verificações de jornada |
| Classificação, correção e falha sem mudança indevida de aba | [Controles de classificação](evidence/classification-controls.png), [erro](evidence/classification-error.png) e verificações de retomada |
| Novos dados aguardam clique e preservam filtros | [Aviso de atualizações](evidence/updates-desktop.png), comparação dos dados antes/depois no percurso |
| Páginas de 20 com limites corretos | [Segunda página](evidence/pagination-second-page.png), verificações das três páginas de 47 ofertas |
| Comparáveis identificáveis | [Referência individual](evidence/comparable-detail.png), retorno aos detalhes e URL fictícia |
| Dados ausentes e origem indisponível sem lucro fabricado | [Compra ausente](evidence/missing-data-detail.png), [origem indisponível em janela estreita](evidence/source-unavailable-mobile.png) |
| Estados de operação distintos | [Coleta parcial](evidence/partial-desktop.png), [consulta indisponível](evidence/query-unavailable.png) |
| Sistema compartilhado na biblioteca | [Primeiro uso no Storybook em tema escuro](evidence/storybook-setup-night.png) |

Os arquivos com nomes herdados da primeira rodada continuam históricos. As evidências listadas neste documento são da versão 0.2; algumas capturas representam um ponto intermediário do percurso, antes de um refinamento semântico posterior. O resultado final das jornadas e das varreduras é registrado nos JSON abaixo.

## Verificações executadas

| Verificação | Resultado e limite |
|---|---|
| [Jornadas](evidence/flow-checks.json) | **58 verificações aprovadas**: configuração, campos obrigatórios, falha, pendência, tentativa posterior, criação/remoção/categorias, correção, retomada, atualização, paginação, comparáveis e estados |
| [Dados extremos](evidence/edge-checks.json) | **5 verificações aprovadas**: nome longo e escapado, ausência de overflow, custos grandes/resultado negativo e origem indisponível |
| [Reflow](evidence/responsive-checks.json) | **135 combinações** sem overflow horizontal da página: 320/375/768/1024/1440 px × três composições × nove superfícies/cenários. A tabela tem sua própria rolagem |
| Ampliação | Texto base a **200% (32 px)** em configurações, com captura [após ajuste da navegação lateral](evidence/text-200-settings.png). É ampliação por CSS para stress de texto, não teste do controle de zoom do navegador |
| Teclado e movimento | Abas por setas, entrada preservando setas, erro recebendo foco, menu/Escape devolvendo foco e redução de movimento verificados |
| [Acessibilidade automatizada](evidence/accessibility-checks.json) | **40 casos**, axe-core 4.14.0, tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`: **zero violações e zero resultados inconclusivos** nos casos executados |
| [Biblioteca](evidence/library-checks.json) | **36 histórias renderizadas**, imagens carregadas e tema escuro verificado |
| Tokens | Gerador e `--check` aprovados para os três CSS; nove pares de texto por tema, mínimo 5,32:1 nos claros e 5,54:1 no escuro; bordas de controle 3,05:1 e 8,07:1 |
| Gate de drift | Em cópia temporária, uma alteração deliberada no CSS foi rejeitada; regenerar restaurou o check. Nenhuma corrupção foi aplicada aos artefatos de trabalho |
| Build e dependências | Storybook compilado com `prebuild` de tokens, dependências diretas coerentes com o lockfile e módulos JS verificados por `node --check` |
| Harness | `node scripts/check-harness.mjs` verifica estrutura e progresso; isso não substitui gates da aplicação nem avaliação de feature |

As verificações foram orquestradas pelo playwright-cli, sem projeto paralelo de testes E2E. Os roteiros ficam em [verification/](verification/), enquanto saídas temporárias ficam em `.playwright-cli/`, ignorado. Resultados e capturas persistem nesta pasta de evidências. As ferramentas de cenários também permitem reproduzir manualmente as transições descritas em [flows-reference.md](flows-reference.md).

Com o protótipo e as dependências da biblioteca preparados, execute na raiz do repositório:

```bash
playwright-cli -s=garimpei-design-check open http://127.0.0.1:4173/prototypes/
playwright-cli -s=garimpei-design-check run-code --filename=docs/design/verification/journeys.cjs
playwright-cli -s=garimpei-design-check run-code --filename=docs/design/verification/reflow.cjs
playwright-cli -s=garimpei-design-check run-code --filename=docs/design/verification/edges.cjs
playwright-cli -s=garimpei-design-check run-code --filename=docs/design/verification/accessibility.cjs
playwright-cli -s=garimpei-design-check close
```

`library.cjs` usa uma sessão aberta em `http://127.0.0.1:6006/iframe.html`, com a biblioteca servida. Cada roteiro registra seu resultado em uma variável de diagnóstico da página (`__FLOW_CHECKS__`, `__RESPONSIVE__`, `__EXTRA_CHECKS__`, `__A11Y_RESULTS__`, `__LIBRARY_CHECKS__`), consultável com `playwright-cli eval`. Execute os roteiros sequencialmente por sessão; a verificação de acessibilidade falha se houver violações ou resultados inconclusivos. Esses roteiros pertencem ao laboratório e não substituem testes/contratos do produto.

Os primeiros exames detectaram nomes acessíveis inconsistentes nos links de foto e rótulos em elementos genéricos sem papel apropriado. Foram corrigidos e rechecados. A inspeção visual da ampliação de texto também levou à navegação com dimensões em rem; as abas estreitas passaram a quebrar texto, evitando ocultar a terceira condição.

O build da biblioteca emite aviso de bundle maior que 500 kB e depreciação do Node. Os avisos pertencem à ferramenta de documentação; o build terminou com sucesso. O protótipo e a renderização das stories terminaram sem erros de console nos percursos finais.

## Avaliação visual

| Dimensão | Nota | Evidência observável |
|---|---|---|
| Design, peso 2 | 8 | Verde mineral, hierarquia de produtos/custos e configuração guiada mantêm o mesmo vocabulário visual |
| Originalidade, peso 2 | 7 | Leitura de custo e referências é específica do garimpo; formulários e navegação usam convenções conhecidas |
| Acabamento, peso 1 | 8 | Tokens e breakpoints únicos, fallback de fotos, quebra de títulos e ampliação sem sobreposição na navegação; a barra de estudo ainda ocupa parte da área visível |
| Funcionalidade, peso 1 | 8 | Falhas, recuperação, correção e retomada simuladas de forma verificável; integrações e dados reais ainda não são avaliáveis |

Média ponderada: `(8×2 + 7×2 + 8 + 8) / 6 = 7,67/10`. É julgamento de design com evidências, não PASS de contrato de feature nem certificação de acessibilidade.

## Limites e próximos contratos

O laboratório usa fixtures, atraso artificial e estado em memória. Recarregar reinicia os exemplos; “Simular reinício” não prova armazenamento durável. O roteiro de primeiro uso demonstra a liberação da coleta, mas não implementa busca na fonte. Nomes/categorias não usam algoritmo de correspondência real. Comparáveis e URLs são fictícios; a política de anúncio removido não foi definida pela presença de uma fixture.

Fontes, critérios de equivalência, algoritmo de estimativa, categorias reais, parâmetros operacionais, sessão/destinatário WAHA, tentativas/reconciliação e persistência seguem dependentes de F01 e dos contratos correspondentes. Leitor de tela, zoom nativo, navegadores adicionais e dados reais ainda precisam de evidência na implementação. As verificações automatizadas não estabelecem conformidade integral com WCAG.

F01–F09 continuam `pending`. Nenhum banco, worker, integração ou envio de mensagem foi iniciado por esta complementação. A entrega concluída é o **laboratório visual e sua referência de interação**, dentro do escopo autorizado.
