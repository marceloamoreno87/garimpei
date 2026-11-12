# F01 — Discovery e viabilidade de integrações

Complemento prático posterior, em 2026-11-10: [prova de busca por PlayStation 5](probe-playstation5-2026-11-10.md). Facebook e Enjoei permitiram extrair busca/detalhe sem login; OLX retornou 403 do Cloudflare. O usuário aprovou Facebook Marketplace, com sessão privada se necessária, conforme [decisions.md](decisions.md), E-PS5-DEC-01. As afirmações abaixo de ausência de PoC e escolha pendente descrevem a execução documental original. A avaliação F01 precisa ser atualizada com estas evidências antes da conclusão.

Data: **2026-11-10**. Resultado: **comparação documental concluída; recomendação condicionada, escolha final pendente**. Não há acesso automatizado ou cobertura integral do MVP demonstrados para qualquer candidata. A decisão de plataforma e estratégia está separada em [decisions.md](decisions.md); o aceite F01 depende da avaliação de todos os itens do [contrato](contract.md).

O pedido atual autoriza executar a F01 anteriormente apenas especificada. Foram consultadas fontes primárias e feita inspeção local de leitura, conforme [environment.md](environment.md). Não houve coletor, login, sessão com cookies, PoC de anúncios, instalação ou mensagem. O scaffold será integrado na F02, com o mapa de preservação já preparado.

## Como ler a evidência

[evidence-index.md](evidence-index.md) contém URL, data, método, suporte e limite por ID. **D** = documentação oficial lida; **I** = conteúdo oficial apenas no índice, abertura bloqueada; **O** = observação desta execução; **H** = inferência; **L** = lacuna. As classificações descrevem o conhecimento disponível; D/I não significam integração testada.

Fontes de requisitos: [PRD](../PRD.md), [stack](../stack.md), [arquitetura](../architecture/README.md). Requisito não demonstrado permanece aberto mesmo quando o contrato permite avaliar sua lacuna.

## Comparação de acesso, esforço e operação

Cada célula sem capacidade comprovada indica a lacuna correspondente. Esforço é avaliação qualitativa **H**, sem estimativa de prazo ou comparação de desempenho medida. Não foram obtidas cotações; custo desconhecido não significa zero.

| Dimensão | OLX | Facebook Marketplace | Enjoei | Mercado Livre |
|---|---|---|---|---|
| API | **D**: integração de inventário do anunciante, não descoberta geral demonstrada (E-OLX-01). | **L**: API geral de busca de ofertas não identificada nas fontes acessíveis; não afirmar inexistência (L-01/E-FB-03). | **L**: API pública de monitoramento não identificada nas fontes consultadas (E-ENJ-01/L-01). | **I**: exemplos oficiais de itens/buscas; permissões/cobertura atuais não confirmadas (E-ML-01/04). |
| Páginas públicas | **D**: ajuda descreve busca por categorias/texto/local; extração e acesso sem conta não testados (E-OLX-02). | **L**: conteúdo Marketplace sem conta não testado; ajuda redirecionou para login/bloqueio (E-FB-03). | **D**: página inicial acessível como texto público; não demonstra coletor estável (E-ENJ-03). | **L**: não houve leitura de páginas de anúncios ou avaliação de extração (L-01). |
| Sessão/cookies | **L**: nenhuma sessão usada; necessidade e duração para descoberta desconhecidas. OAuth documentado atende outro escopo (E-OLX-01). | **O/L**: login exigido para documentos consultados; sessão real e elegibilidade não verificadas (E-FB-02/03). | **D/L**: cadastro/login descritos para conta, acesso autenticado de coleta não testado (E-ENJ-01). | **I/L**: exemplos usam token; cookies não testados e não substituem permissão API (E-ML-01). |
| Scraping avançado | **H/L**: navegador poderia ser investigado; extração, permissão, CAPTCHA e limites desconhecidos (L-01). | **D/L**: Meta descreve defesas; viabilidade e autorização não demonstradas (E-FB-01/02). | **H/L**: navegador seria hipótese; dados dinâmicos, permissão e antirrobô não verificados (L-01). | **H/L**: hipótese alternativa, sem evidência de estabilidade, autorização ou superação de bloqueios (L-01/09). |
| Autenticação/antirrobô | **L**: controles do acesso de comprador não medidos; não confundir com OAuth de inventário. | **D/O**: fornecedor descreve limitação de volume/comportamento; documentos também bloquearam esta consulta (E-FB-01/02). | **L**: mecanismos de coleta não medidos; cadastro não comprova acesso automatizado. | **O/I**: documentos 403; causa não diagnosticada e API não chamada (E-ML-01/04). |
| Dados úteis / atualização | **D/L**: funcionalidades de busca documentadas; campos e mudanças por anúncio pendentes das tabelas abaixo. | **L**: campos/atualização de ofertas não verificados. | **D/L**: novos/usados e preços públicos documentados; atualização não medida (E-ENJ-01/03). | **I/L**: categorias e buscas parcialmente documentadas; disponibilidade de itens de terceiros não comprovada. |
| Custo de integração / uso | Plano de anunciante pode ser necessário para aquela API; custo de descoberta desconhecido (E-OLX-03). | Custo e condições do acesso pretendido desconhecidos; nenhuma contratação (L-07). | Termos comerciais existem; tarifa de integração desconhecida (E-ENJ-01/L-07). | Custo do uso pretendido, quotas e elegibilidade desconhecidos (L-07/09). |
| Esforço inicial / uso local | **H**: validar páginas de busca/detalhe e geografia antes de construir adaptador; possível dependência de navegador. | **H**: esclarecer permissão/acesso de conta antes de PoC; incerteza elevada, recursos de navegador não medidos. | **H**: esclarecer acesso, taxonomia e disponibilidade de eletrônicos; dependência de navegador não confirmada. | **H**: primeiro validar credenciais/escopo de busca. API elegível poderia reduzir dependência de navegador, sem benchmark. |
| Estabilidade / manutenção | **H/L**: parser dependeria do site; contrato de descoberta e frequência não demonstrados. | **H/L**: conta e controles podem impedir continuidade; não há disponibilidade demonstrada. | **H/L**: estrutura pública não é API estável; manutenção de parser e acesso desconhecida. | **H/L**: API documentada pode reduzir acoplamento ao HTML, mas permissões e mudanças exigem verificação; sem SLA. |

**Restrições documentadas:** a posição histórica da Meta sobre automação sem permissão e suas defesas consta em E-FB-01; o texto vigente de termos ficou inacessível (E-FB-02). Para as demais candidatas, regras específicas do monitoramento automatizado e limites de volume não foram confirmados nesta revisão. Isso requer esclarecimento antes de PoC, sem inferir permissão do fato de uma página ser pública. Não houve tentativa de contornar bloqueio.

### Ausências e acessos malsucedidos

Em **2026-11-10**, aberturas das páginas ML de itens/buscas, categorização e frete retornaram **403**, com conteúdos parciais disponíveis no índice oficial (E-ML-01–03). Documentos Facebook levaram a login/bloqueio (E-FB-02/03). Esses resultados descrevem acesso documental desta ferramenta. Não são chamadas à API do produto, listas vazias, teste de conta, prova de proibição universal ou impossibilidade definitiva.

Impacto: restringem a confiança na seleção e impedem declarar acesso validado. Próximo passo: revalidar documentos e acesso elegível na candidata selecionada, com escopo delimitado. L-01/L-09 detalham destinos. Nenhuma prova citada como integração real foi executada; E-SCOPE-01 e o ambiente permitem verificar essa distinção.

## Cobertura de interesses

| Candidata | Categorias/subcategorias e anúncios associados | Busca por nome/modelo | Correspondência e sobreposição |
|---|---|---|---|
| OLX | **D**: filtros descritos; enumeração programática da árvore e associação reproduzível pendentes (E-OLX-02). | **D**: busca textual descrita; recall de modelos/variantes não medido. | **H/L**: texto não prova modelo exato; categoria e texto podem atingir a mesma oferta. Deduplicação/vínculo para F04, critérios de nome para F03/F06. |
| Facebook Marketplace | **L**: árvore, filtros e associação não verificados; acesso de ajuda bloqueado (E-FB-03). | **L**: pesquisa e cobertura por modelo não verificadas. | **L**: nenhuma precisão, equivalência ou ausência de sobreposição demonstrada. |
| Enjoei | **D**: navegação tem Eletrônicos; subcategorias e enumeração de anúncios não verificadas (E-ENJ-03). | **L**: fluxo de busca/modelo não exercitado. | **L**: taxonomia e qualidade da correspondência ainda sem amostra; não inferir equivalência por marca. |
| Mercado Livre | **I**: hierarquia/atributos e consultas por categoria aparecem na documentação parcial; vínculo com ofertas gerais MLB não demonstrado (E-ML-01/02). | **I/L**: exemplos de consulta não comprovam busca atual para este projeto. | **H/L**: atributos podem auxiliar; variantes/catálogo não garantem equivalência de condição e acessórios. |

Nenhuma candidata autoriza declarar que todos os anúncios são cobertos. Os dois interesses do MVP continuam obrigatórios; falha de categoria não será compensada silenciosamente por busca textual.

## Geografia, entrega e frete

Requisitos preservados: **retirada em São Paulo (SP) até 20 km do CEP configurado** e **ofertas nacionais com entrega naquele CEP**, avaliadas separadamente. Nenhum CEP pessoal foi fornecido/utilizado; não há destino real validado (L-02).

| Candidata | Retirada / origem e precisão | Entrega nacional no CEP | Frete informado versus estimado |
|---|---|---|---|
| OLX | **D/L**: filtros locais documentados; precisão e ponto de retirada insuficientes para confirmar raio exato. A própria ajuda admite resultados associados a localidades próximas (E-OLX-02). | **D/L**: busca distingue opção de entrega; isso não comprova atendimento ao destino. | **L**: consulta do valor para destino e sua extração não verificadas. |
| Facebook Marketplace | **L**: raio disponível, unidade, origem das coordenadas e exatidão não verificados (E-FB-03). | **L**: modalidade brasileira e elegibilidade por anúncio/destino não verificadas. | **L**: nenhum valor consultado; negociação externa não substitui prova de entrega. |
| Enjoei | **D/L**: entrega em mãos documentada condicionalmente; localização precisa para 20 km não verificada (E-ENJ-01). | **D/L**: operação logística descrita, cobertura pré-compra por CEP pendente (E-ENJ-02). | **L**: cotação automatizada e custos no destino não verificados. |
| Mercado Livre | **L**: localização utilizável e modalidade de retirada não verificadas; endereço do vendedor não necessariamente é retirada. | **I/L**: documentação parcial mostra opções anúncio/CEP com token (E-ML-03); acesso e resultado brasileiros não testados. | **I/L**: potencial valor cotado requer verificar permissões, destino e instante; não há valor obtido. |

Uma cidade/bairro ou coordenada aproximada não comprova distância exata; converter CEP em centroide seria inferência a validar, sem declarar raio atendido. Frete informado exige origem, destino, moeda e instante. Na sua ausência, usa-se apenas a **estimativa configurável** prevista no PRD para custo; ela **não confirma entrega**. Falta de custo não vira zero, e falta de cobertura não vira entrega nacional presumida. Políticas de precisão/confirmação: F03/F04; composição: F07.

## Identidade, alterações e retomada

Não foram coletados anúncios; a tabela registra campos ainda necessários e a força de evidência por fonte. Não confundir status de anúncio do próprio vendedor com histórico de todo o marketplace.

| Candidata | Identidade, link, preço, condição e localização | Atualização, remoção, duplicatas e republicações | Janela histórica, paginação e retomada |
|---|---|---|---|
| OLX | **L**: ID estável, URL canônica, preço atual, texto de condição e localização por oferta ainda não extraídos. Integração do anunciante não resolve esses campos para terceiros (E-OLX-01). | **D/L**: ajuda admite desatualização/remoção na busca; nenhum histórico medido. Mesmo título/foto não comprova republicação (E-OLX-02). | **L**: ordenação recente não garante histórico completo; limite de páginas, anúncios retirados e alterações durante parada desconhecidos. |
| Facebook Marketplace | **L**: os cinco campos não verificados no contexto elegível de conta/país. | **L**: sem observação de edição/remoção, vínculo de duplicatas ou novo ID. | **L**: janela, paginação e critérios de exibição não verificados; personalização poderia afetar amostra (**H**). |
| Enjoei | **D/L**: links/preços públicos vistos; estabilidade do ID, condição e localização dos itens alvo não verificadas (E-ENJ-03). | **L**: sem série temporal ou garantia de vínculo entre publicações. | **L**: paginação, esgotamento, janela e visibilidade após interrupção não medidos. |
| Mercado Livre | **I/L**: referências a identificadores de item/categoria aparecem nos exemplos oficiais; os cinco campos de ofertas de terceiros não foram validados (E-ML-01–03). | **L**: mudanças de preço/status e vínculo de republicações sem prova; eventos do vendedor não implicam cobertura global. | **L**: buscas de inventário não demonstram janela geral recuperável; nenhuma paginação autorizada executada. |

F04 precisa persistir identidade/observações/marcos e distinguir indisponibilidade de remoção. F09 precisa preservar o marco inicial silencioso, histórico de envios e reduções; pausa não permite reconstruir dados já removidos pela fonte. Não há promessa de recuperação integral de publicações ou de mudanças não mais disponíveis (L-03/P09).

## Referências de usados e novos

Preço anunciado não prova preço de venda. Nenhum conjunto de comparáveis foi coletado; quantidade observada de amostras de preços nesta investigação: **zero**. A lacuna não significa inexistência de anúncios.

| Fonte possível | Usados semelhantes | Produto novo | Qualidade disponível / lacunas |
|---|---|---|---|
| OLX | **H/L**: potencial candidata a comparáveis locais; acesso e amostra pendentes. | **L**: distinguir novo, seminovo e recondicionado sem evidência suficiente; não adotar o menor anúncio como novo. | Sem equivalência, data de coleta/publicação, quantidade, discrepantes ou confiança medidos (E-OLX-01/02, L-04). |
| Facebook Marketplace | **L**: acesso, distribuição e volume não verificados. | **L**: disponibilidade e verificação da condição não demonstradas. | Nenhum conjunto que permita avaliar qualidade; depende de resolver acesso (E-FB-03/L-04). |
| Enjoei | **D/L**: termos contemplam usados; amostra de eletrônicos equivalentes não obtida. | **D/L**: termos contemplam novos, sem validação da declaração por oferta. | Página/termos não demonstram atualidade, quantidade ou venda efetiva (E-ENJ-01/03). |
| Mercado Livre | **I/L**: atributos de condição são pista documental, sem ofertas recuperadas. | **H/L**: catálogo/atributos poderiam apoiar referência; variante e acesso precisam de prova. | Nenhuma estatística ou confiança demonstradas (E-ML-01/02, L-04/09). |
| Fabricante/loja oficial do modelo | Não substitui amostra de usados. | **H/L**: segunda via sugerida se houver página oficial para a variante; nenhuma fonte/modelo específico selecionado nesta execução. | Preço sugerido pode diferir de oferta atual; acesso, estoque e data pendentes, sem promessa de integração. |

Para F06: comparar geração, armazenamento, estado, acessórios, unidade/lote e moeda; registrar coleta e publicação quando confiável; quantidade antes/depois de exclusões, duplicação entre interesses/fontes e distribuição/discrepantes. Isso é proposta de observáveis para investigar, **sem definir limiares, mínimo de amostra, algoritmo ou pesos** (P07). Falta de referência produz **estimativa indisponível**, sem preço ou lucro zero e sem alerta; dados insuficientes não viram estimativa confirmada.

## Operação local e WAHA

Inventário real: [environment.md](environment.md#inventário-local), E-LOCAL-01. Há WSL2 x86_64, 32 CPUs lógicas, 31 GiB de RAM visível e 789 GiB livres no filesystem amostrado. Docker responde; memória reportada pelo daemon não se soma à WSL. Recursos físicos totais do host, limites configurados e consumo conjunto continuam **L-05**. Não se afirma compatibilidade testada só por esses números.

A operação preserva Django/web e worker no WSL2, PostgreSQL/WAHA em Docker, publicação local e acesso via localhost sem login no Garimpei. Sem Redis inicial. A autenticação administrativa dos serviços e a sessão WhatsApp continuam necessárias e separadas do acesso à aplicação, conforme futura configuração F02/F09.

### WAHA considerado

| Dimensão | Avaliação / evidência |
|---|---|
| Versão | Release de referência **2026.10.1**, publicada em 2026-10-28; não instalada (E-WAHA-03). |
| Imagem/engine | Candidata inicial de menor dependência de navegador: GOWS/x86, família `devlikeapro/waha:gows`; alternativa WEBJS com Chromium, família `devlikeapro/waha:latest` (E-WAHA-02). Escolha é **H**, não adoção. Tag versionada/digest e manifesto precisam de verificação antes da instalação; não usar tag móvel como versão fixada. |
| Requisitos | A recomendação do fornecedor e as diferenças de engine constam em E-WAHA-01/02; não são consumo do Garimpei. Medir junto com coleta/banco/worker antes de concluir capacidade. |
| Sessão | Conta própria aprovada e pareamento privado pendentes. Serviço saudável, sessão autenticada e mensagem recebida são verificações diferentes (E-WAHA-04). Nada foi conectado/enviado. |
| Persistência | Volume privado de sessão, identidade própria por ambiente e teste após reinício, conforme E-WAHA-05. Parada normal deve manter sessão e dados; sem limpeza de volume pessoal. |
| Licença/custo | FAQ informa recursos unificados sem tier pago desde 2026.6.1; LICENSE da referência identifica Apache-2.0 (E-WAHA-01/06). Isso não torna energia, rede, conta, manutenção ou operação gratuitos; custo total não orçado. |
| Limites | Nenhuma prova local de prontidão, autenticação, envio ou recebimento. Endpoints/capacidades por engine, bloqueios de conta e resposta incerta ficam para validação F02/F09 (L-06). |

O WAHA é serviço separado consumido via HTTP; seu runtime interno não altera a stack Python do produto. Dependências persistentes devem ser verificadas sem expor chaves/QR/session state.

## Intervalo, latência e custo

**Não há intervalo viável validado nem SLA proposto.** Sem permissão, quota e tempo real de consulta, não há base para fixar 30 segundos, 1 minuto ou outro número. Nenhuma medição de integração ocorreu: **0 ciclos de coleta, 0 mensagens e 0 observações ponta a ponta** (L-07).

| Componente de tempo | Situação / como verificar no futuro |
|---|---|
| Fonte: publicação → visibilidade | Desconhecido; horário confiável pode faltar e busca pode atrasar. Não derivar latência real da data aproximada do site. |
| Espera pelo próximo ciclo + coleta | Depende do intervalo autorizado, páginas/interesses, quotas, navegador e backoff; medir requisições, duração e erros por ciclo em amostra delimitada. |
| Fila/processamento | Depende da carga e recursos; medir enfileiramento, início e fim com correlação persistente. |
| Envio → confirmação/recebimento | Depende de sessão/rede/engine; medir separado da aceitação HTTP, com envio específico autorizado. |

Modelo conceitual **H**, sem estimativa numérica: latência observável agrega esses componentes apenas quando houver relógios/eventos confiáveis. F04 deve definir intervalo após a PoC, limitar concorrência e reagir a 429/bloqueios; F09 define confirmação/reconciliação. O intervalo também afeta custo de tráfego/CPU e manutenção; não assumir disponibilidade em tempo real.

Custos ainda sem cotação: acesso/quota das fontes, eventual serviço de geocodificação, energia, armazenamento, conta/conectividade e manutenção. Nenhum serviço pago foi contratado. A prioridade de menor custo não autoriza prometer custo zero. O computador, WSL2, Docker, web/worker e dependências necessários devem estar em execução; não se exige operação 24 horas. Fechar a aba não deverá parar worker na implementação futura; computador/processos parados suspendem monitoramento/envio.

## Recomendação condicionada e próximos passos

**Sugestão: OLX como primeira candidata para uma PoC de descoberta por páginas de busca/detalhe, inicialmente sem sessão, somente se acesso e condições aplicáveis permitirem.** Ferramenta de extração ainda não escolhida; navegador é alternativa a validar se HTML simples for insuficiente. A API de inventário não é a estratégia sugerida para descoberta. A recomendação é **H**, baseada no alinhamento documental das jornadas, sem cobertura integral ou menor esforço demonstrados (E-OLX-01/02, L-01/02/03/04/07).

| Alternativa | Razão comparativa / condição para rever |
|---|---|
| OLX | Mais evidência acessível sobre categorias/texto/local/recência para as jornadas deste PRD. Custo, precisão, entrega e manutenção de parser ainda incertos; falhar requisito obrigatório impede adoção. |
| Mercado Livre | Alternativa a priorizar se houver acesso geral elegível e documentado a itens/categorias/frete. Pode favorecer dados estruturados e referência de novos, mas o bloqueio documental e o escopo atual não foram resolvidos. |
| Enjoei | Evidência pública de categorias/novos/usados; insuficiente para demonstrar busca, precisão geográfica, amostra de eletrônicos ou menor esforço. Reavaliar após obter acesso/dados representativos. |
| Facebook Marketplace | Permissões, acesso contextual e manutenção permanecem menos demonstrados nesta revisão; sem preferência como primeira integração até esclarecer essas condições. Não é declaração de inviabilidade definitiva. |

A decisão pode rejeitar a sugestão; não há ranking numérico nem pesos inventados. **Nenhuma candidata está aprovada para produção.** Se nenhuma demonstrar categorias, nome/modelo, retirada e entrega do MVP, levar a incompatibilidade ao usuário para decisão sobre fonte/PRD, preservando IDs. Não remover modalidades ou recuperação silenciosamente.

Destinos explícitos: L-01/L-08 impedem concluir a escolha e liberar F02; L-02 afeta F03/F04 e custos F07; L-03 afeta F04/F09; L-04 afeta F06; L-05/L-06 afetam F02, com envio em F09; L-07 afeta F04/F09; L-09 reduz confiança no comparativo. O mapa técnico para scaffold/lifecycle/migrations e seis coberturas Python está em [environment.md](environment.md#passagem-técnica-para-f02).

Para resolver a decisão, revisar [decisions.md](decisions.md). Para comprovar capacidades práticas, delimitar a PoC com entradas, duração/requisições/custo e limpeza; não antecipar fundação ou envio nesta execução.
