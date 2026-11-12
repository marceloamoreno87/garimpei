# Ferramentas do laboratório visual

A combinação foi ajustada à stack aprovada: **UI UX Pro Max + Frontend Design + tokens/HTML/CSS compartilhados + Storybook HTML/Vite + crítica visual orientada pelo Impeccable e frontend-ui-design**. As ferramentas ajudam a produzir e avaliar o design; o PRD e a direção do usuário governam o resultado.

## Skills locais

Instaladas em `.agents/skills/`, sem alterar a configuração global do Codex:

| Skill | Fonte | Aplicação nesta rodada |
|---|---|---|
| [UI UX Pro Max](../../.agents/skills/ui-ux-pro-max/SKILL.md) | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Consulta de direção e UX, foco e validação de formulários |
| [Frontend Design](../../.agents/skills/frontend-design/SKILL.md) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Direção editorial, composição, tipografia e conteúdo específico do produto |
| [Impeccable](../../.agents/skills/impeccable/SKILL.md) | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | Referências de acabamento e crítica manual do resultado |

O instalador oficial de skills do Codex copiou as pastas upstream (`skills/frontend-design`, `.claude/skills/ui-ux-pro-max`, `.agents/skills/impeccable`) para os nomes acima. O carregamento automático de skills adicionadas depende da próxima sessão; os arquivos foram lidos diretamente nesta execução. Não foi instalado um pacote global `uipro` nem alterado `~/.codex/config.toml`.

A consulta geral ao UI UX Pro Max para marketplace devolveu sugestões de landing page, depoimentos e roxo, pouco adequadas ao painel local. A segunda consulta para inventário ajudou no vocabulário visual, mas também sugeriu seções de marketing. Essas estruturas foram descartadas. As consultas específicas sobre foco e erros foram aplicadas. O arquivo canônico de tokens foi elaborado para o Garimpei, sem promover a saída automática a requisitos.

O comando de contexto do Impeccable foi tentado uma vez e retornou `Permission denied` no launcher instalado. O contexto e as referências foram lidos diretamente; **não houve auditoria executável do Impeccable**. A avaliação visual usa suas referências e o processo local [frontend-ui-design](../../.agents/skills/frontend-ui-design/SKILL.md), com [playwright-cli](../../.agents/skills/playwright-cli/SKILL.md).

## Componentes e prototipação

[Storybook HTML/Vite](https://storybook.js.org/docs/get-started/frameworks/html-vite) está instalado como laboratório isolado, com versões diretas fixadas no [package.json](storybook/package.json) e resolução no lockfile. Seus exemplos importam os mesmos tokens, CSS e funções HTML do protótipo. A documentação oficial foi consultada para CSF e renderização HTML. O build não adiciona runtime Node ao produto Django.

shadcn MCP já estava disponível, mas shadcn/ui e 21st.dev se orientam a componentes React. Não foram adicionados ao runtime aprovado. Uma troca para React exigiria reabrir a decisão de stack, sem benefício necessário para este protótipo. Também não foram criados design systems paralelos em Figma/Penpot/Stitch nem provisionadas credenciais ou publicações externas. A prévia HTML local responde à pergunta visual com menos dependências operacionais.

Se futuramente uma dessas ferramentas entrar no fluxo, importar/exportar os tokens da fonte JSON e conferir a sincronização antes de aceitar os artefatos. O laboratório atual já oferece uma rota navegável, cenários e biblioteca verificável, sem depender de acesso externo durante o uso.

## Verificação da versão 0.2

axe-core foi adicionado como dependência de desenvolvimento isolada da biblioteca, com versão fixada e lockfile. É injetado pelo playwright-cli nas verificações; o protótipo não o carrega no uso normal e o produto Django não recebe essa dependência. A [API oficial](https://github.com/dequelabs/axe-core/blob/develop/doc/API.md) foi consultada para regras A/AA e resultados inconclusivos. A análise automática não substitui leitor de tela ou validação completa de acessibilidade.

Storybook documenta estados visuais das jornadas usando `prototypes/views.js`, sem importar o controlador da aplicação. O próprio laboratório apresenta as transições. `predev`/`prebuild` verificam drift dos três CSS gerados e dos tokens; a [referência de fluxos](flows-reference.md) explica a autoria nos arquivos `.css.in`.
