# F01 — Prova prática de busca por PlayStation 5

Executada em **2026-11-10**, aproximadamente **19:36–19:40 UTC** (16:36–16:40 em São Paulo), como complemento ao discovery documental anterior. Escopo autorizado nesta conversa: comparar OLX, Facebook Marketplace e Enjoei buscando PlayStation 5, tentar extrair anúncios e explicar falhas; solicitar sessão se necessária. Mercado Livre ficou fora deste teste.

**Resultado:** busca e detalhe extraídos em Facebook e Enjoei sem autenticação fornecida. OLX bloqueou busca e página inicial com HTTP 403 do Cloudflare. A recomendação documental anterior de investigar OLX primeiro foi reconsiderada diante desta observação. Após os testes, o usuário aprovou **Facebook Marketplace** como primeira plataforma, com sessão privada se necessária, conforme [decisions.md](decisions.md), E-PS5-DEC-01. Este teste e a aprovação documental não concluem automaticamente F01 nem liberam F02 sem reavaliação.

## Método e alcance

Navegação real com `playwright-cli`, Chromium headless e três sessões isoladas, usando a configuração do repositório. Consulta normalizada: `playstation 5`. Nenhum cookie de conta, senha, token ou perfil pessoal foi fornecido/importado. Cookies anônimos eventualmente criados pelos sites não são autenticação do usuário. Não houve contato com vendedores, mensagem, compra ou alteração de conta.

O teste leu o DOM renderizado das buscas e de um detalhe por fonte acessível, extraiu links/IDs/textos e fez uma ação de continuação por fonte acessível. Não foi implementado adaptador de produção. Não foram usados proxies, resolução de desafios ou alterações para disfarçar o navegador. O número de subrequisições dos sites não foi instrumentado. Sem medição de SLA, frequência sustentável ou estabilidade ao longo do tempo.

A ferramenta web textual falhou ao abrir as três buscas; esses erros não foram tratados como ausência de anúncios. Os resultados abaixo vêm do navegador local. Dados sanitizados com instantes de observação: [results.json](evidence/ps5-2026-11-10/results.json). URLs de anúncios estão sem parâmetros de rastreamento; perfis de navegador e logs brutos ficaram em temporário.

## Comparação observada

| Plataforma / evidência | Busca e continuação | Detalhe amostrado | Login e limite |
|---|---|---|---|
| OLX / E-PS5-OLX-01 | [Busca](https://www.olx.com.br/brasil?q=playstation%205) e [início](https://www.olx.com.br/) retornaram 403, título `Attention Required! / Cloudflare`, mensagem de bloqueio. | Não acessado. Quantidade de anúncios **desconhecida**. | Bloqueio de segurança anterior à inspeção da busca; não houve exigência de login observável. Causa específica e utilidade de cookies desconhecidas. |
| Facebook / E-PS5-FB-01 | [Busca São Paulo](https://www.facebook.com/marketplace/saopaulo/search/?query=playstation%205): 19 IDs distintos inicialmente; após retornar à busca e rolar uma vez, 43 IDs, incluindo os 19 iniciais e 24 adicionais. | Título, ID, preço anunciado, condição, descrição e cidade extraídos. Exemplo abaixo. | Modal de convite para login apareceu; foi fechado pelo botão **Close** oferecido pelo próprio site. Busca, detalhe e uma continuação funcionaram sem login. Não prova acesso ilimitado. |
| Enjoei / E-PS5-ENJ-01 | [Busca](https://www.enjoei.com.br/s?q=playstation%205): 35 IDs distintos na primeira amostra. Após reabrir a busca e clicar em **próxima**, outros 35 IDs, dos quais 34 ausentes da amostra inicial. | Título, ID, preço anunciado, categoria, condição, descrição e cidade extraídos. Exemplo abaixo. | Nenhum login exigido nesse fluxo. Banner de consentimento apareceu e não impediu extração. Busca usa região padrão, sem CEP configurado. |

As contagens são links de anúncios no DOM amostrado, **não totais das plataformas nem contagens de consoles equivalentes**. O Enjoei incluiu jogos, controles, acessórios e outras gerações. Facebook exibiu algumas ofertas com rótulo `Free`; não converter esse rótulo em preço zero ou oportunidade confirmada. Valores são declarados pelos anunciantes, sem validação do produto ou da venda.

No Enjoei, a espera automatizada por `page=2` terminou com timeout de 30 segundos. A navegação usou o cursor `cc` e removeu `page` da URL; a extração seguinte encontrou um conjunto diferente de IDs. Isso comprova mudança da lista, mas o verificador baseado no número da página falhou. A comparação de IDs usa a primeira amostra, anterior a uma recarga da busca: a sobreposição de um anúncio não é uma taxa controlada de duplicação. Um adaptador deverá observar cursor e conteúdo, e tratar sobreposição.

## Exemplos extraídos

| Campo | Enjoei | Facebook Marketplace |
|---|---|---|
| Link / ID | [PS5 Slim 1 TB](https://www.enjoei.com.br/p/ps5-slim-1tb-versao-de-leitor-de-disco-pra-sair-rapido-153341902) / `153341902` | [PS5 com leitor](https://www.facebook.com/marketplace/item/1671631174339530/) / `1671631174339530` |
| Preço anunciado atual | R$ 3.350; outro preço exibido R$ 3.650 | R$ 3.550; outro preço exibido R$ 3.799 |
| Condição declarada | Usado | Usado, como novo |
| Localização declarada | Queimados, RJ | São Paulo, SP; o site informa localização aproximada |
| Categoria | Eletrônicos / videogames / consoles | Eletrônicos / consoles de videogame |
| Composição declarada | 1 TB, leitor de disco, um controle, cabos e jogo | 825 GB, leitor de disco, controle, cabos e caixa |
| Entrega | Entrega no CEP do usuário não verificada | Descrição menciona entrega por R$ 50; área coberta e entrega no CEP do usuário não verificadas |

Preços antigos e parcelas aparecem no texto; um parser de produção precisa distingui-los do preço atual. A descrição do Facebook foi recuperada do DOM; expansão visual de todo o texto não foi validada. Disponibilidade, condição e composição são alegações dos anúncios.

## Evidências visuais

- [OLX: bloqueio](evidence/ps5-2026-11-10/olx-bloqueio.png).
- [Enjoei: busca](evidence/ps5-2026-11-10/enjoei-busca.png) e [detalhe](evidence/ps5-2026-11-10/enjoei-detalhe.png).
- [Facebook: busca com convite de login](evidence/ps5-2026-11-10/facebook-busca.png), [detalhe com modal](evidence/ps5-2026-11-10/facebook-detalhe.png) e [detalhe após fechar o modal](evidence/ps5-2026-11-10/facebook-detalhe-sem-modal.png).

## Cookies e diagnóstico de falhas

**Facebook e Enjoei:** não foi necessário solicitar cookies para esta prova. Se um teste futuro exigir sessão, solicitar login interativo ou o caminho de um arquivo privado de estado do navegador, fora do repositório; não pedir senha nem colagem de cookies na conversa. Possuir sessão não demonstra estabilidade ou elegibilidade de toda a coleta.

**OLX:** o observado é recusa do Cloudflare, sem indicação suficiente para atribuir a IP, modo headless, reputação, país ou regra específica. A falha não comprova falta de anúncios nem inviabilidade permanente da plataforma. Cookies de autenticação não são solução demonstrada para esse bloqueio. Próximo diagnóstico possível: comparar a mesma URL no navegador habitual do usuário e, se necessário, com uma sessão local autorizada. Não houve esse teste nem acesso a perfil pessoal nesta execução.

## Recomendação para decidir

**Priorizar Facebook Marketplace para o foco local em usados em São Paulo**, com coleta por navegador inicialmente sem login e Enjoei como alternativa. Inferência baseada na amostra: Facebook entregou cidade nos cartões, detalhes úteis e continuação sem sessão. Enjoei também demonstrou acesso e continuação, mas a busca padrão trouxe acessórios/outras gerações e o primeiro console detalhado estava no RJ. Isso não constitui benchmark de precisão, volume total, custo ou estabilidade entre fontes.

Antes de assumir a integração como viável para todo o MVP, faltam: filtro e precisão do raio de **20 km** a partir do CEP privado; entrega e frete no destino; controle de região/ordenação; recuperação após interrupção; identidade em remoção/republicação; frequência sustentável; condições atuais do acesso automatizado; amostra de comparáveis com variantes e condições equivalentes. No Facebook a busca exibiu raio padrão de 65 km e o detalhe 64 km, insuficientes para o requisito de 20 km. No Enjoei o parâmetro padrão foi `near_regions`, sem validação geográfica.

OLX permanece candidata bloqueada neste ambiente, sem preferência prática demonstrada. A recomendação acima precedeu a aprovação explícita do Facebook pelo usuário, registrada separadamente em [decisions.md](decisions.md). Nenhum requisito foi reduzido, nenhuma feature foi marcada concluída e não houve commit, push ou PR.
