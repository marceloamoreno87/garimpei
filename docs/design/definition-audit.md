# Auditoria de definição — design e fronteiras do MVP

Data: 2026-11-10. Escopo: cruzamento do PRD, arquitetura, decisões da conversa, design, código demonstrativo e evidências existentes. Esta é uma revisão de definição, não uma nova avaliação visual nem uma aprovação de implementação.

**Atualização após a complementação:** as lacunas visuais abaixo foram trabalhadas na versão 0.2. Este documento preserva o diagnóstico anterior; o estado atual e suas evidências estão em [flows-reference.md](flows-reference.md) e [verification-v02.md](verification-v02.md). A complementação implementa o laboratório, sem concluir features do produto.

**Resultado:** há base para continuar a especificação, mas ainda não há definição completa de todas as jornadas nem implementação do produto. A direção e a composição visual estão escolhidas. Sete decisões foram esclarecidas nesta rodada; lacunas restantes têm destino e momento de resolução abaixo.

## Decisões confirmadas nesta rodada

O [PRD](../PRD.md) é a fonte canônica do comportamento. Esta tabela serve de índice para as decisões e para as diferenças em relação aos artefatos atuais.

| Decisão confirmada com o usuário | Rastreabilidade | Estado dos artefatos |
|---|---|---|
| Configuração guiada; primeira coleta ao concluir com sucesso; retomada com configuração salva nos reinícios | F03-AC04/AC05, F04-AC05, INT-09 | Definida; fluxo documentado em journeys.md; ainda sem protótipo guiado |
| Frete estimado e percentual provisório inicialmente em branco e obrigatórios para concluir | F03-AC04, P08 | Definida; R$ 35 e 12% continuam apenas fixtures de um cenário posterior à configuração |
| Classificar manualmente muda a aba, sem disparar alerta pela ação | F09-AC06, INT-10, P06 | A mudança de aba é demonstrada em memória; ausência de intenção de envio persistente depende da implementação |
| Preservar classificação manual nas próximas coletas do mesmo anúncio | F05-AC04, P06 | Definida; protótipo não possui coleta nem persistência para demonstrá-la |
| Permitir corrigir nos detalhes uma classificação manual já salva, também sem disparar alerta | F05-AC05, F09-AC06, P06 | Definida; amplia F05 sem criar outra feature. O protótipo só permite classificar ofertas incertas e precisa ganhar essa transição |
| Adotar a composição editorial | Direção de interface no PRD, MASTER.md, P10 | Protótipo existente; tabela/mesa de análise continuam estudos |
| Avisar novos dados e atualizar a lista ao clicar, preservando filtros | F08-AC05, INT-11, P10 | Definida; aviso e transição ainda sem protótipo. Mecanismo/frequência de detecção não escolhidos |

Essas decisões não alteram Django/templates/HTMX, PostgreSQL, worker separado, WSL2/Docker, acesso somente local ou ausência de login. Não criam autenticação, painel de infraestrutura, app móvel ou um sistema de tutoriais.

## Lacunas identificadas antes da complementação

“Definir” descreve um contrato observável ainda incompleto. “Prototipar” significa tornar uma decisão visível para revisão. “Verificar” exige evidência na implementação. São trabalhos diferentes.

| Lacuna constatada | Evidência anterior e consequência | Encaminhamento recomendado | Resolver antes de |
|---|---|---|---|
| Primeiro uso, interrupção e retomada da configuração | O app.js inicia com fixtures preenchidas; o cenário vazio leva a interesses. Não demonstra sequência guiada nem conclusão persistida | Prototipar os campos existentes, validação, falha ao concluir e retorno após interrupção. Preservação de rascunho e navegação entre etapas ficam para o contrato, sem presumir novos mecanismos | F03/F04 |
| Estados distintos de ausência de resultados | O cenário vazio não separa integralmente “sem configuração”, “primeira coleta em curso”, “coleta concluída sem anúncios” e “nada com esses filtros” | Diferenciar causa e ação de recuperação; usar dados válidos anteriores quando existirem, sem chamar falha de vazio | F03/F04/F08 |
| Atualidade e operação percebidas | Há texto fixo de última coleta e um cenário de falha; não há demonstração de worker parado, fonte parcialmente indisponível ou aviso de novos dados | Explicar a última atualização bem-sucedida, o que está desatualizado e o que o usuário pode fazer. Especificar o aviso aprovado sem inventar intervalo nem adicionar controles de pausa/reenvio | F04/F08/F09 |
| Gravação em andamento e falha real | Loading de botão e aviso de falha existem na galeria, mas formulários e classificação sempre alteram memória local | Demonstrar falha e recuperação; preservar conteúdo, impedir duplicação enquanto pendente e só confirmar/mudar aba após gravação. O comportamento de falha já é exigido no PRD | F03/F05 |
| Identificação dos comparáveis | O detalhe repete três nomes e valores sintéticos, com contagem ilustrativa; não traz origem/URL/identidade dos anúncios comparados | Desenhar comparável identificável com os campos disponíveis e referência de novo separada. Fonte, equivalência e suficiência devem vir de F01/F06; não inventar selo de confiança | F06/F08 |
| Dados reais incompletos ou extensos | Fixtures têm imagem válida e poucos valores curtos. Origem real, data ausente e anúncios removidos não estão representados por completo | Definir fallback de foto, título longo, preço/localização/frete ausentes, origem e timestamps. Anúncio indisponível exige política de permanência/alerta compatível com a fonte, ainda não escolhida | F04/F06/F08/F09 |
| Ordenação e volume | Calculáveis em ordem decrescente estão cobertos; indisponíveis no fim é proposta. Sem desempate, paginação ou limites reais | Confirmar posição de indisponíveis, desempates e navegação de volume na especificação de F08; evitar decidir página infinita sem dados de uso/fonte | F08, P10 |
| Efeitos de alterações nos interesses e custos | Cadastro/remover em memória não demonstra sobreposição de interesses, nova carga inicial, recálculo persistente ou efeito nos alertas | Resolver regras de inclusão/remoção, republicações e recálculo com eventos rastreáveis. Evitar que editar custos ou classificar seja tratado implicitamente como anúncio novo | F03/F04/F07/F09, P04/P08/P09 |
| Histórico e conteúdo do alerta | A tela de histórico é proposta; destinatário, sessão, campos e recuperação de envio ainda não foram especificados | Confirmar a visibilidade mínima necessária e o conteúdo após viabilidade do WAHA. Histórico de domínio é necessário; uma nova tela administrativa, reconexão ou reenvio manual não está automaticamente aprovada | F09, P02/P09 |
| Catálogo e estados de componentes | Dez stories cobrem uma base, mas abas, filtros, seleção de categorias, vazios, aviso de atualização e transições completas de formulário não têm stories próprios | Inventariar componentes realmente usados, completar exemplos de estado necessários e explicitar seus contratos de teclado/foco. Preservar HTML/CSS compartilhados, sem trocar a stack | F02 e features de interface |
| Governança e sincronização dos tokens | Cores/fontes/escalas partem de tokens.json e CSS gerado. Breakpoints de 720/1100 px também aparecem como literais no CSS e exigem sincronização manual | Fechar exportação/verificação dos breakpoints e gate de drift antes do consumo em produção; documentar como os templates Django e o laboratório manterão a mesma marcação visual | F02/F08 |
| Critérios completos de acessibilidade | Existem foco, semântica, redução de movimento, checagem parcial de contraste e navegação em Chromium. Sem verificação de leitor de tela/zoom nem definição formal da cobertura | Recomenda-se [WCAG 2.2 AA](https://www.w3.org/TR/WCAG22/) como objetivo técnico e jornadas por teclado/zoom/leitor de tela como aceite a especificar. Não há certificação nem exigência de ferramentas extras aprovada por esta auditoria | Contratos de interface |

As recomendações acima completam o desenho das features existentes; não são autorização automática para novos recursos. Nenhuma dessas linhas muda o progresso para `done`.

## O que depende de discovery ou especificação técnica

| Grupo | O que continua aberto | Fonte e destino |
|---|---|---|
| Integração e ambiente | Escopo prático da investigação, primeira plataforma/acesso, CPU/RAM disponíveis, engine/sessão WAHA e custos externos | P01/P02; F01/F02/F09 |
| Catálogo e identidade | Categorias reais, correspondência por nome/modelo, sobreposição, duplicatas/republicações e efeito de novos interesses | P03/P04; F01/F03/F04/F09 |
| Geografia e condição | Localização insuficiente, confirmação de entrega, critérios automáticos, novas informações conflitantes com decisão manual e custo de reparo | P03/P05/P06/P08; F04/F05/F07 |
| Referências e dinheiro | Fontes, equivalência, amostra, método, atualidade, ausência de novos, validações de valores, arredondamento e demais custos | P07/P08; F01/F03/F06/F07 |
| Confiabilidade e operação | Intervalo/latência, confirmação incerta, tentativas/reconciliação, atomicidade de dados e tarefas, backup/restauração, versões e gates Python | P02/P09 e arquitetura; F01/F02/F04/F09 |
| Resultado do MVP | Prazo e forma de observar a primeira revenda lucrativa e demais métricas, sem criar acompanhamento comercial dentro do sistema | P11; validação externa do valor |

Não é útil escolher plataforma, intervalo, amostra ou engine por aparência da tela. Esses pontos devem ser fechados com evidência ou durante os contratos das features; o design precisa representar as incertezas enquanto isso.

## Sequência recomendada

1. Levar as decisões confirmadas ao PRD, MASTER/DESIGN, jornadas e arquitetura, preservando IDs e progresso.
2. Na próxima rodada de prototipação, demonstrar primeiro uso, atualização mediante clique, correção de classificação e falhas de gravação, além dos principais dados ausentes. Isso não é feito automaticamente por esta auditoria.
3. Concluir F01 antes de fechar categorias reais, comparáveis e limites operacionais. Evidências podem exigir ajustes nos protótipos.
4. Especificar por feature os estados, a acessibilidade, os componentes e o comportamento ainda aberto. F02 deve manter o laboratório isolado e adaptar os gates Python antes de declarar base pronta.

## Evidências e limites desta rodada

Foram lidos PRD, stack, arquitetura, MASTER/DESIGN/PRODUCT, jornadas, tokens/gerador, código dos protótipos, stories e a [avaliação visual anterior](review.md). O histórico recuperado foi tratado como contexto, com decisões confirmadas na conversa atual e nos arquivos canônicos.

A revisão anterior registra 39 verificações e uma matriz de 60 combinações de largura/composição/superfície sobre os protótipos existentes. Esses números não comprovam os novos fluxos definidos nesta rodada. Aqui foram atualizados documentos e o status descritivo dos tokens; não houve alterações de UI, servidor, coleta ou mensageria, nem nova execução dessas jornadas. Verificações documentais e de sincronização foram realizadas separadamente.

## Encaminhamento na versão 0.2

| Grupo do diagnóstico | Estado após a complementação |
|---|---|
| Primeiro uso, falhas e correção manual | Demonstrados em memória, com confirmação somente após sucesso e tentativa posterior |
| Ausência de resultados, atualidade, consulta e dados incompletos | Estados distintos, fallback de imagem e exemplo de origem indisponível |
| Comparáveis | Identificação, origem, momento e URL fictícia em superfície própria; fontes/método reais continuam em F01/F06 |
| Ordenação e volume | Escolhas confirmadas: sem estimativa no fim, empate pela identificação recente, páginas de 20; demonstradas no protótipo |
| Componentes e tokens | Biblioteca ampliada e breakpoints compilados da mesma fonte; drift rejeitado por verificação executável |
| Acessibilidade | Critérios descritos e evidências automáticas/teclado/reflow ampliadas; leitor de tela e conformidade integral continuam exigindo avaliação própria |
| Efeitos de interesses, referências e eventos de alerta | Recálculo e confirmação visual demonstrados; identidade, correspondência, republicações e eventos reais permanecem para discovery/contratos |
| Persistência, worker, fontes e WAHA | Continuam sem implementação de produto nesta etapa |
