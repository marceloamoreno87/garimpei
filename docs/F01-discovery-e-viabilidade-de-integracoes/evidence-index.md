# F01 — Índice de evidências

Complemento posterior: **E-PS5-OLX-01**, **E-PS5-FB-01** e **E-PS5-ENJ-01** são observações práticas de 2026-11-10, descritas na [prova de busca por PlayStation 5](probe-playstation5-2026-11-10.md), com [dados sanitizados](evidence/ps5-2026-11-10/results.json) e screenshots. **E-PS5-DEC-01** registra a aprovação explícita de Facebook Marketplace pelo usuário em [decisions.md](decisions.md); L-08 está resolvida. As afirmações abaixo de ausência de coleta e escolha referem-se à execução documental original; as demais lacunas não estão automaticamente encerradas.

Consulta: **2026-11-10 UTC**, execução `2026-11-10T19-07-31Z`. Fontes primárias consultadas por busca e abertura com a ferramenta web; Context7 usado complementarmente para persistência WAHA. Sínteses abaixo são paráfrases. Uma leitura documental não é prova de integração. Os IDs são usados em [report.md](report.md), [environment.md](environment.md) e [decisions.md](decisions.md).

## Método e estados

- **D**: conteúdo oficial aberto e lido; descreve a documentação, sem comprovar funcionamento local.
- **I**: conteúdo de domínio oficial recuperado no índice de busca, com abertura bloqueada. Evidência documental parcial, sujeita a revalidação.
- **O**: observação local ou do acesso documental nesta execução; não generalizar para contas, APIs ou navegador do usuário.
- **H**: hipótese/inferência nossa, identificada como tal no relatório.
- **L**: lacuna, com impacto e próximo passo; ausência de resultado não demonstra impossibilidade.

Não houve coleta de anúncios, sessão autenticada, PoC, instalação, contratação ou mensagem. Não foram consultados cookies, arquivos de credenciais ou dados de contêineres existentes. Buscas que retornaram artigos de terceiros não foram usadas para sustentar capacidades.

## Plataformas

| ID / estado | Fonte primária e método em 2026-11-10 | Observação sanitizada | Limite e próximo passo |
|---|---|---|---|
| E-OLX-01 / D | [API de integração](https://developers.olx.com.br/anuncio/api/home.html), abertura integral | Fluxo de OAuth e gestão de inventário do anunciante, com status e anúncios publicados. | Não prova busca de todo o marketplace. Confirmar com OLX um acesso de descoberta adequado antes de escolher API. |
| E-OLX-02 / D | [Como fazer uma busca](https://form-ajuda.olx.com.br/s/article/como-fazer-busca), abertura integral | A ajuda descreve categorias/subcategorias, texto, localização e ordenação. | É experiência de uso, não contrato de extração. Validar separadamente geografia e dados acessíveis em uma PoC delimitada. |
| E-OLX-03 / I | [Importação](https://developers.olx.com.br/anuncio/api/import.html), conteúdo oficial na busca | OAuth em nome do anunciante; integração pode depender de plano compatível. | Não é cotação de acesso a ofertas de terceiros. Custo/permissão do caso Garimpei desconhecidos. |
| E-ML-01 / I+O | [Itens e buscas](https://developers.mercadolivre.com.br/pt_br/itens-e-buscas), busca oficial e abertura; variante [em inglês](https://developers.mercadolivre.com.br/en_us/items-and-searches) | O índice mostra exemplos com Bearer token e consultas por vendedor/categoria. Aberturas retornaram **403 Forbidden** nas duas versões. | Não foi chamada a API de anúncios. Não concluir que pesquisa geral está disponível ou extinta; verificar escopo atual com documentação acessível e aplicação autorizada. |
| E-ML-02 / I+O | [Categorização de produtos](https://developers.mercadolivre.com.br/pt_br/categorizacao-de-produtos/), busca oficial e abertura | Índice descreve árvore, categorias e condições; abertura retornou **403**. | Exemplos não comprovam cobertura de eletrônicos brasileiros. Revalidar árvore MLB e associação a ofertas. |
| E-ML-03 / I+O | [Cálculo de frete](https://developers.mercadolivre.com.br/en_us/calculate-shipping-costs-handling-time), busca oficial e abertura | Índice documenta opções por anúncio/CEP com token; abertura retornou **403**. | Sem cotação nem verificação do CEP do usuário. Testar permissões, anúncio ativo, destino, custo e momento da cotação. |
| E-ML-04 / I | [Erro 403](https://developers.mercadolivre.com.br/pt_br/guia-para-produtos/erro-403), busca oficial | Fornecedor lista várias causas possíveis, incluindo permissões, usuário, aplicação e IP. | Não identifica a causa dos bloqueios documentais desta execução. Não presumir token inválido, pois nenhum foi usado. |
| E-FB-01 / D | [How We Combat Scraping](https://about.fb.com/news/2021/04/how-we-combat-scraping/amp/), abertura integral; publicação histórica de 2021 | Meta descreve autorização prévia e controles de volume/comportamento. | Não é prova de permissões atuais para o projeto nem de API geral do Marketplace. Revalidar condições atuais. |
| E-FB-02 / O | [Termos de coleta automatizada](https://www.facebook.com/legal/automated_data_collection_terms), abertura | Redirecionamento para login e mensagem de bloqueio temporário. | Texto vigente não lido integralmente; não usar cópia de terceiro como substituto. Obter documento oficial acessível antes de PoC. |
| E-FB-03 / O | [Ajuda Marketplace](https://www.facebook.com/help/561376580709359/), abertura | Redirecionamento para login/bloqueio, sem conteúdo de ajuda verificável. | Não comprova disponibilidade por conta/país, categorias, raio ou entrega. Revisar com acesso autorizado. |
| E-ENJ-01 / D | [Termos de uso](https://www.enjoei.com.br/ajuda/sobre-o-enjoei/sobre-os-termos-de-uso/termos-de-uso-do-enjoei), abertura integral; versão indicada 2026-07-10 | Intermediação de novos/usados, cadastro e condições comerciais; entrega em mãos existe como modalidade condicionada. | Não documenta API de monitoramento nem garante acesso automatizado. Esclarecer permissão e custos do uso pretendido. |
| E-ENJ-02 / D | [Envios e entregas](https://www.enjoei.com.br/ajuda/sobre-envios-e-entregas-no-enjoei/sobre-envios-e-entregas-no-enjoei), abertura integral | Logística e rastreio de compras são descritos. | Não prova consulta prévia automatizada por CEP nem cobertura nacional de cada anúncio. |
| E-ENJ-03 / D | [Página pública](https://www.enjoei.com.br/), leitura textual pontual, sem interação | Navegação inclui Eletrônicos, Eletrodomésticos e links de produtos/preços. | Documento público amostrado, sem busca, paginação ou extração de ofertas. Subcategorias/modelos e estabilidade ficam não verificados. |

## WAHA

| ID / estado | Fonte primária e método em 2026-11-10 | Observação sanitizada | Limite e próximo passo |
|---|---|---|---|
| E-WAHA-01 / D | [FAQ](https://waha.devlike.pro/docs/overview/faq/), abertura e seções de requisitos/custo | Fornecedor recomenda 2 CPU/4 GB para o projeto e informa unificação gratuita desde 2026.6.1. | Referência do fornecedor, não benchmark local nem custo total zero. Rever na versão fixada. |
| E-WAHA-02 / D | [Engines](https://waha.devlike.pro/docs/how-to/engines/), abertura das seções pertinentes | WEBJS/WPP usam navegador; NOWEB/GOWS usam WebSocket. Existem variantes x86 e ARM. | Suporte varia por engine; validar imagem/digest e endpoints necessários antes de instalar. |
| E-WAHA-03 / D | [Release 2026.10.1](https://github.com/devlikeapro/waha/releases/tag/2026.10.1), abertura | Release publicada em 2026-10-28, considerada como referência de avaliação. | Tag de código não comprova disponibilidade da imagem Docker ou digest. Nenhuma imagem baixada. |
| E-WAHA-04 / D | [Sessões](https://waha.devlike.pro/docs/how-to/sessions/), abertura e busca por WORKING | Estados de sessão são distintos; há restrições de envio possíveis mesmo com sessão WORKING. | Não houve sessão nem envio. F09 precisa distinguir aceitação, entrega e resultado incerto. |
| E-WAHA-05 / D | [Storages](https://waha.devlike.pro/docs/how-to/storages/), abertura; corroborada pelo [arquivo oficial](https://github.com/devlikeapro/waha-docs/blob/main/content/docs/how-to/storages/index.md) via Context7 `/devlikeapro/waha-docs` | Persistência local usa volume em `/app/.sessions`; exemplo Compose publica em loopback. | Persistência real após reinício ainda não testada. Manter namespace/volumes próprios por ambiente. |
| E-WAHA-06 / D | [LICENSE na tag 2026.10.1](https://github.com/devlikeapro/waha/blob/2026.10.1/LICENSE), abertura e inspeção do cabeçalho | Código dessa tag identifica Apache License 2.0. | Não equivale a auditar todas as dependências nem a permissão de operação da conta WhatsApp. |

## Execução local e preservação

| ID / estado | Método / instante UTC | Resultado e limite |
|---|---|---|
| E-LOCAL-01 / O | Comandos de leitura em [environment.md](environment.md#inventário-local), **2026-11-10T19:09:15Z**, uma amostra, sem carga de produto | Kernel WSL2 x86_64; recursos e versões registrados. Não revela memória física total do Windows nem consumo sob carga. |
| E-GATE-01 / O | `node scripts/check-harness.mjs`, exit 0 na preparação | 14 skills, sintaxe de 28 scripts, progresso de 9 features; aprovação estrutural. Execução canônica final fica no relatório de avaliação. |
| E-GATE-02 / O | `node --test scripts/test/harness.test.mjs`, exit 0 na preparação | 4 testes, 4 aprovados, 0 falhas. Não valida Python ou integração externa. |
| E-PRESERVE-01 / O | Snapshot SHA-256 de **492 arquivos preexistentes**, antes da escrita de artefatos, guardado privadamente em temporário | Comparação final deve admitir somente alteração da entrada F01 no progresso. Sem commit base; `git diff` sozinho não verifica arquivos não rastreados. Resultado final no relatório canônico. |
| E-SCOPE-01 / O | Pedido atual do usuário e [escopo operacional](environment.md#escopo-desta-execução) | Ciclo F01, até três correções, preservar harness, sem commit/push/PR. Não há decisão do usuário sobre plataforma, sessão ou destinatário. |

## Lacunas rastreadas

Todas abertas em **2026-11-10**, após revisão documental. A coluna de próximo passo indica ação futura, não execução já autorizada.

| ID | Contexto / impacto | Próximo passo / destino |
|---|---|---|
| L-01 | Permissão e via estável de descoberta não demonstradas para nenhuma candidata; risco de inviabilizar coleta. | Escolher candidata/estratégia condicional e delimitar PoC antes de F02/F04; P01 do PRD. |
| L-02 | CEP privado não fornecido/usado e precisão de localização não validada; raio de 20 km e entrega não comprovados. | Prova de geografia/destino com entrada privada em F01 complementar; políticas em F03/F04 (P03/P05). |
| L-03 | Sem histórico/paginação medidos; recuperação e vínculo de republicação desconhecidos. | Amostrar dados autorizados e definir identidade/janela em F04/F09 (P09). |
| L-04 | Sem amostra de usados/novos; qualidade e quantidade insuficientemente conhecidas. | Validar fontes e equivalência; limiares/método em F06 (P07), sem estimativa confirmada. |
| L-05 | Sem carga conjunta; RAM física do host, limites Windows/WSL configurados e interferência de outros serviços desconhecidos. | Medir com base/worker/coletor/WAHA próprios; F02 (P02). |
| L-06 | Imagem/digest e engine WAHA não verificados localmente; sem sessão ou recebimento. | Fixar artefato e validar ciclo de vida em F02; envio somente com autorização/destinatário em F09 (P02/P09). |
| L-07 | Acesso e limites não medidos; não há intervalo, custo total ou latência ponta a ponta demonstrados. | Prova delimitada e medição com eventos correlacionados; F04/F09, recursos em F02. |
| L-08 | Plataforma/estratégia ainda sem decisão explícita. | Revisar [decisions.md](decisions.md); bloqueia conclusão F01 e passagem para F02. |
| L-09 | API/categorias/frete ML apenas parcialmente acessíveis no índice; Facebook exige acesso documental adicional. | Revalidar nas fontes oficiais; não usar 403/login como ausência de anúncios ou indisponibilidade universal. |
