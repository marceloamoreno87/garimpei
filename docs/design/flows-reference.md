# Referência de fluxos e estados — versão 0.2

Modo: **Operate**. Direção editorial preservada. Fonte de comportamento: [PRD](../PRD.md). Este documento especifica a experiência demonstrada no laboratório; os contratos das features e sua implementação Django continuam futuros. Protótipo executável não equivale a persistência, coleta ou envio implementados.

## Entradas para revisão

Com `python3 docs/design/serve.py` em execução:

| Jornada/cenário | Entrada |
|---|---|
| Configuração guiada | [Primeiro uso](http://127.0.0.1:4173/prototypes/?scenario=first-use) |
| Exploração editorial | [Lista preenchida](http://127.0.0.1:4173/prototypes/) |
| Dados novos aguardando aplicação | [Atualizações](http://127.0.0.1:4173/prototypes/?scenario=updates) |
| Volume e paginação | [Muitas ofertas](http://127.0.0.1:4173/prototypes/?scenario=many) |
| Imagem/preço/localização ausentes | [Dados ausentes](http://127.0.0.1:4173/prototypes/?scenario=gaps) |
| Coleta parcial | [Cobertura incompleta](http://127.0.0.1:4173/prototypes/?scenario=partial) |
| Acompanhamento interrompido | [Processamento parado](http://127.0.0.1:4173/prototypes/?scenario=stopped) |
| Consulta indisponível | [Erro de consulta](http://127.0.0.1:4173/prototypes/?scenario=unavailable) |

A barra inferior alterna cenários e composições. O botão de ferramentas oferece **Simular falha de gravação**, **Simular novos dados**, **Simular reinício** e **Concluir coleta simulada**. São instrumentos do laboratório, sem chamada a serviços reais. Selecionar outro cenário pode carregar novas fixtures; não é uma operação do produto.

## Primeiro uso e retomada

| Etapa | Entrada e transição | Falha e recuperação |
|---|---|---|
| Sua região | CEP, com rótulo e ajuda; continuar para custos | Formato inválido mantém a etapa e foca o resumo de erros. O formato não comprova localização/entrega |
| Custos | Frete estimado e percentual provisório começam em branco; ambos precisam ser preenchidos | Erros junto aos campos e no resumo; valores não são substituídos por sugestões |
| Interesses | Selecionar categorias de exemplo e/ou adicionar produto por nome/modelo; concluir | A conclusão exige interesse configurado. Campos anteriores e seleções são mantidos durante a sessão |
| Gravação | Botão fica ocupado e impede duplicação; só o sucesso conclui a configuração | Falha preserva o rascunho e não inicia coleta. O usuário pode tentar novamente |
| Primeira coleta | Estado em andamento, seguido da lista; nenhum alerta é criado | O laboratório avança após um atraso artificial, sem representar intervalo ou latência reais |
| Reinício simulado | Configuração concluída, custos, classificação e histórico são mantidos em memória | Configuração incompleta permanece incompleta e não libera coleta |

Voltar entre etapas conserva o rascunho da sessão. Uma alteração nas etapas intermediárias não inicia coleta. Recarregar o navegador restaura as fixtures: **o laboratório não grava dados em banco, localStorage ou disco**. O botão de reinício demonstra a transição com estado salvo em memória; não prova durabilidade do produto. Persistência real de configuração concluída, marcos e retomada pertence a F03/F04.

As categorias e ofertas são exemplos fixos. A demonstração conserva os interesses escolhidos, mas não implementa a correspondência entre nomes/categorias e uma fonte real. Esse algoritmo permanece em F01/F04.

## Gravação, classificação e correção

Configurações, cadastro/remoção de produto, categorias e classificação usam o mesmo padrão: entrada preservada → operação pendente → confirmação após sucesso ou erro recuperável. A simulação de falha mantém o último estado confirmado. A interface não move oferta de aba nem confirma remoção quando a gravação falha.

Nas ofertas incertas, os detalhes oferecem “Funciona bem” e “Não funciona bem”. Após gravação, a oferta muda de aba e fica identificada como classificação manual. Nos detalhes passa a existir “Corrigir sua classificação”, usando as mesmas duas opções. A última escolha gravada prevalece nas coletas seguintes do mesmo anúncio. Uma falha de correção conserva a escolha anterior.

Classificar ou corrigir não cria alerta pela ação, inclusive para a retomada. A simulação de novos dados inclui um exemplo de informação automática conflitante com escolha manual, que é preservada. Isso demonstra precedência, sem definir o algoritmo automático ou a identidade de republicações.

## Atualização, ordenação e volume

Novos dados processados geram o aviso “Há atualizações”. A lista corrente continua intacta até o clique em “Atualizar lista”. Aplicar os dados preserva aba, busca, categoria e modalidade. A página atual é conservada quando continua válida; se a quantidade de páginas diminuir, usar uma página existente. O foco retorna a uma oferta visível, com confirmação textual.

No laboratório, “Simular novos dados” produz patches fictícios em memória. Não escolhe polling, SSE ou WebSocket e não representa a execução do worker. No produto, a espera pela aplicação visual não deve pausar coleta ou WhatsApp.

| Regra escolhida | Comportamento observável |
|---|---|
| Ordem principal | Lucro estimado decrescente, incluindo zero e negativo |
| Ausência de estimativa | Depois de todas as calculáveis, com rótulo; nunca representa lucro zero |
| Empates | Identificação mais recente; identificador estável resolve igualdade final. Data de publicação ausente não é fabricada |
| Paginação | Filtrar e ordenar o conjunto antes de dividi-lo em páginas de 20 |
| Controles | Quantidade, intervalo exibido, página atual, anterior/próxima; desativar o que não se aplica |
| Mudança de filtros | Retornar à primeira página |
| Detalhes e retorno | Preservar o contexto de exploração em memória |

A fixture de volume tem 47 ofertas na lista principal e demonstra três páginas. Não expressa limite da fonte nem volume prometido.

## Estados de leitura

| Causa | Mensagem e informação preservada |
|---|---|
| Configuração não concluída | Orientar a configuração; coleta ainda não iniciada |
| Primeira coleta | Carregamento com indicação de carga silenciosa |
| Carregamento de consulta | Skeleton e status textual, sem preços inventados |
| Coleta válida sem resultados | Informar ausência de ofertas encontradas e permitir revisar interesses |
| Nenhuma oferta com filtros | Explicar o recorte e oferecer limpar filtros |
| Falha de fonte | Exibir último conjunto conhecido e informar falha de atualização |
| Acompanhamento interrompido | Mostrar horário anterior e orientar verificar processos; não fingir que a página acompanha dados novos |
| Dados desatualizados | Diferenciar histórico conhecido de preço/disponibilidade atuais |
| Coleta parcial | Identificar cobertura incompleta, preservando dados conhecidos |
| Consulta indisponível | Erro explícito com tentativa simulada; não mostrar o erro como lista vazia |
| Imagem ausente/falha | Fallback textual acessível, sem imagem quebrada |
| Compra, modalidade ou revenda ausente | Sem lucro fabricado; custos e referências conhecidos continuam legíveis |
| Anúncio indisponível na origem | Avisar que os dados são da última consulta e não confirmam disponibilidade atual |

O cenário de anúncio indisponível apenas demonstra linguagem visual. Sua retenção, retirada da lista e efeito em eventos/alertas aguardam a fonte e a especificação de F04/F09; manter uma fixture para revisão não aprova uma política de retenção.

Títulos extensos, nomes de produtos, URLs e valores podem quebrar linha sem escapar do componente. Foto ilustrativa recebe identificação; a indicação é removida quando só existe fallback.

## Referências identificáveis

Os comparáveis exibem título, preço anunciado, origem, ID e momento de observação. Cada um abre uma superfície local com sua identificação e URL fictícia, retornando aos detalhes da oferta. A referência de novo é separada e pode estar ausente sem substituir a de usado.

O domínio `exemplo.invalid` identifica dados fictícios; não é uma integração ou um link real de anúncio. As referências não demonstram equivalência estatística, amostra suficiente ou venda realizada. Fontes e método continuam em F01/F06. Exemplos de mensagens usam os valores do evento de demonstração, separados de alterações posteriores nas configurações.

## Biblioteca e fonte única

| Grupo | Implementação compartilhada / documentação |
|---|---|
| Botões, badges, avisos, campos e erros | `components/ui.js` e `components/components.css.in` |
| Foto/fallback, oferta e cálculo ilustrativo | Os mesmos exports usados no protótipo e nas stories |
| Abas, paginação, vazio e aviso de atualização | Componentes exportados e stories de navegação/resultados |
| Primeiro uso, formulários, correção, referências e estados | `prototypes/views.js`, com estados em `model.js` e stories de jornadas |
| Interações completas | `prototypes/app.js`; a biblioteca apresenta estados isolados, enquanto o protótipo demonstra transições |

Os valores reutilizáveis são definidos em [tokens.json](tokens.json). O gerador produz `tokens.css`, `components/components.css` e `prototypes/prototype.css`. Os dois últimos partem de fontes `.css.in`; macros de breakpoint consomem os tokens de layout. Edite o JSON/templates e gere novamente, preservando uma única definição de breakpoints.

```bash
python3 docs/design/generate_tokens.py
python3 docs/design/generate_tokens.py --check
```

O Storybook verifica sincronização automaticamente antes de `dev` e `build`. A fundação futura deverá chamar essa verificação ao consumir os mesmos estáticos. O laboratório permanece HTML/Vite; não acrescenta React ao produto.

## Critérios técnicos de acessibilidade

Objetivo de construção: [WCAG 2.2 AA](https://www.w3.org/TR/WCAG22/), com evidência parcial por ferramenta e jornada, sem alegação de conformidade integral. A checagem com [axe-core](https://github.com/dequelabs/axe-core/blob/develop/doc/API.md) usa regras A/AA pertinentes e registra separadamente resultados inconclusivos.

As jornadas precisam manter rótulos e nomes acessíveis coerentes com o texto visível; resumos de erro focáveis e associados aos campos; estado pendente identificável; feedback em região viva; foco perceptível e recuperado após navegação; abas com setas/Home/End; menu recolhido com Escape; controles do produto com área de toque adequada; redução de movimento; reflow e texto ampliado.

A barra de estudo é um recurso do laboratório e será removida da interface final. Seu conteúdo pode encobrir temporariamente parte da área visível, mas a página tem espaço de rolagem e traz ao centro um controle que receba foco sob a barra. Leitor de tela e navegadores adicionais exigem validação própria na implementação. Os resultados executados e suas limitações estão na [verificação da versão 0.2](verification-v02.md).
