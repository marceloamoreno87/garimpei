# Avaliação visual do protótipo — 2026-11-10

Objeto: artefatos de design em `docs/design/`, sem aplicação Django. Avaliação realizada pelo próprio agente com [frontend-ui-design](../../.agents/skills/frontend-ui-design/SKILL.md), referências de acabamento do Impeccable e inspeção de screenshots produzidos por `playwright-cli`/Chromium. Não houve avaliação independente nem teste com o usuário.

Registro da avaliação anterior à escolha da composição editorial e às novas decisões de fluxo. A [auditoria de definição](definition-audit.md) registra essas decisões posteriores e o que ainda falta demonstrar; as capturas e resultados abaixo continuam referentes aos protótipos avaliados.

## Resultado observado

| Dimensão | Nota | Evidência e limite |
|---|---|---|
| Design, peso 2 | 8 | Papel claro, verde mineral e tipografia consistente; destaque reúne foto e leitura financeira. A direção escolhida é reconhecível nas telas de ofertas, detalhes e configuração. |
| Originalidade, peso 2 | 7 | Composição editorial e transparência de custos são próprias do fluxo de garimpo; navegação lateral e cards ainda usam convenções comuns de painéis. |
| Acabamento, peso 1 | 7 | Tokens e fontes locais, alinhamento de valores, contraste medido e largura da página preservada. A barra de estudo encobre parte do conteúdo visível e a versão estreita exige bastante rolagem. |
| Funcionalidade, peso 1 | 8 | Busca, filtros, classificação, cadastro, erros e recálculo demonstrados. Persistência, coleta, abertura real de anúncio e entrega de mensagem não existem nesta rodada. |

Média ponderada: `(8×2 + 7×2 + 7 + 8) / 6 = 7,50/10`. A pontuação expressa julgamento visual; não representa PASS de contrato de feature. Recomenda-se o editorial para revisão do usuário, preservando tabela e mesa de análise como alternativas.

## Evidências visuais

| Captura | O que foi inspecionado |
|---|---|
| [Editorial desktop, 1440×1050](evidence/editorial-desktop.png) | Hierarquia, fotografia, destaque de preço/lucro, navegação e filtros |
| [Comparação desktop](evidence/comparison-desktop.png) | Densidade e alinhamento entre valores |
| [Mesa de análise desktop](evidence/analysis-desktop.png) | Seleção com prévia e legibilidade do tema escuro |
| [Detalhes](evidence/detail-desktop.png) | Compra de R$ 1.850, revenda de R$ 2.800, taxa de R$ 336, frete de R$ 34 e lucro de R$ 580 |
| [Classificação](evidence/classification.png) | Oferta incerta e ações para escolher sua condição |
| [Erros de configuração](evidence/settings-errors.png) | Resumo focável, mensagens junto aos campos e conteúdo preservado |
| [Alertas](evidence/alerts-desktop.png) | Prévia fictícia, carga inicial silenciosa e confirmação incerta, sem envio real |
| [375 px, viewport](evidence/editorial-mobile-viewport.png) e [página completa](evidence/editorial-mobile.png) | Menu recolhido, filtros empilhados e leitura dos cards |
| [768 px, página completa](evidence/editorial-tablet.png) | Navegação compacta, duas colunas e destaque adaptado |
| [Componente no Storybook, tema escuro](evidence/storybook-dark.png) | Mesma marcação, CSS e tokens compartilhados |

Fotografias e modelos divergem em alguns exemplos e estão identificados como ilustrativos. A captura de alertas mostra o percentual alterado no percurso de configuração: lucro R$ 636 com taxa de 10%. A captura de detalhes anterior usa o cenário inicial de 12%, com lucro R$ 580. Essa diferença acompanha a edição em memória.

## Verificações executadas

`./scripts/init.sh` confirmou a ausência de scaffold. O protótipo foi servido por Python em `127.0.0.1:4173`, sem iniciar a aplicação ou contêineres. O Storybook foi compilado e sua saída estática foi servida localmente para inspeção.

- **39 verificações de jornada e matriz**, registradas em [browser-checks.json](evidence/browser-checks.json). Incluem busca/vazio, categoria/modalidade, setas das abas, as duas classificações, zero/negativo/indisponibilidade, composição de custos, erros e foco, cadastro/remoção por nome, recálculo com centavos, prévia de mensagem, estados de coleta, variantes, menu estreito/Escape e redução de movimento.
- **60 combinações sem overflow horizontal da página**: larguras 375/768/1024/1440, três composições e cinco superfícies. A tabela tem rolagem interna deliberada. Isso não equivale a inspeção visual minuciosa de todas as combinações; as capturas acima são as evidências de inspeção visual.
- **Dez histórias do Storybook renderizadas**: ações, condições, feedback, campos, carregamento, destaque, nova oferta, lucro negativo, zero e sem estimativa. Tema escuro confirmado no iframe; interface de navegação da biblioteca aberta em navegador.
- **Contraste e sincronização**: `python3 docs/design/generate_tokens.py --check` passou. Nove pares de texto por tema, mínimo 5,32:1 nos temas claros e 5,54:1 no escuro; borda de controle sobre superfície 3,05:1 nos claros e 8,07:1 no escuro. A verificação cobre esses pares, não todos os pixels/composições possíveis.
- **Build**: `npm --prefix docs/design/storybook run build -- --output-dir /tmp/garimpei-storybook` passou. O build emitiu aviso de bundle maior que 500 kB e de depreciação do Node; a interface do Storybook emitiu aviso de propriedade acessível que será obrigatória na versão 11. Sem erros de renderização. Esses avisos pertencem ao laboratório de documentação.
- **Sintaxe e estrutura**: `node --check` dos módulos do protótipo e componentes passou; `node scripts/check-harness.mjs` aprovou a estrutura do harness, seus scripts e o progresso com nove features.
- **Console e assets do protótipo**: zero erros/avisos na sessão final e nenhuma imagem quebrada no encerramento da jornada. Fotografias e fontes são locais.

Durante a revisão, foram corrigidos o crescimento indevido da imagem em destaque, o escape horizontal de texto acessível na tabela, a apresentação de centavos, a distinção visual de indisponibilidade e o foco ao fechar o menu. Confirmações de uma tela anterior são dispensadas ao navegar. O foco que cair sob a barra de estudo é trazido ao centro da área visível.

## Pontos para a próxima rodada

1. Revisar com o usuário a composição editorial frente às alternativas e decidir se a quantidade de filtros deve ser reduzida para antecipar os produtos em janelas estreitas.
2. Validar fotografias e descrições com a primeira fonte real; o conjunto ilustrativo não testa tamanhos, proporções ou ausência de imagens da integração.
3. Remover galeria, barra flutuante, inspector e variantes experimentais do fluxo final. O protótipo fica isolado em documentação, sem entrada no build do produto.
4. Especificar erros de gravação/classificação, carregamento incremental, desempates e posição de ofertas sem estimativa. O laboratório não resolve P06–P10 por conta própria.
5. Avaliar leitor de tela, zoom de 200%, navegadores adicionais e dados reais na implementação. A rodada atual verificou teclado, semântica observável, redução de movimento e pares de contraste; não certificou acessibilidade completa.

F01–F09 continuam pendentes. Gates de backend, persistência, integração, worker e WAHA não foram executados nem declarados aprovados por esta entrega visual.
