# F05 — Classificação por condição

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-11T17-03-39Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

## 1. Visão técnica

**Complexidade** média · **Onda** 5 · **Dependência direta** F04

A F05 interpreta as informações de funcionamento da última observação válida de cada anúncio, preserva a escolha manual e publica uma única classificação efetiva. Web e consumidores de backend usam a mesma regra. A aba representa a avaliação dos dados do anúncio ou a escolha do usuário. O estado físico do produto continua sujeito à avaliação do comprador.

A entrega inclui a navegação mínima pelas três abas e os controles de classificação e correção nos detalhes, conforme o [design do Garimpei](../design/flows-reference.md). A exploração completa, com filtros, atualização de resultados e dados financeiros, pertence a F08. Eventos de coleta e preço pertencem a F04. A decisão completa de elegibilidade e o envio pertencem a F09.

## 2. Arquitetura e integração

~~~mermaid
flowchart LR
  F04["F04 — observação persistida do anúncio"] --> Read["Consulta de condição"]
  Manual["Escolha manual persistida"] --> Read
  Read --> Rule["Domínio — condição efetiva e aba"]
  Rule --> F08["Abas e detalhes · F08"]
  Rule --> F09["Condição do anúncio · F09"]
  Form["Formulário dos detalhes"] --> Save["Caso de uso de classificação"]
  F04 --> Save
  Save --> Manual
~~~

- **Entrada de F04** — identidade canônica e estável, origem, link, título e evidência disponível de funcionamento (rótulo de condição da fonte e descrição, se coletados). A consulta distingue observação válida, informação ausente e falha de leitura. Usa a ordem de observações aceita por F04 e os mesmos critérios de visibilidade da coleta. A F04 ainda precisa definir esses formatos e sua fronteira transacional. O plano inclui conferir o mapeamento antes da implementação.
- **Saída para F08** — consulta por ID e por aba com identidade, origem, link, condição efetiva, procedência automática/manual, classificação automática, escolha e revisão manual e indicador de conflito. A consulta de detalhes inclui os trechos reconhecidos e o campo de origem. As abas particionam a mesma população de ofertas disponíveis para exploração segundo F04.
- **Saída para F09** — consulta pelo ID do anúncio do evento de F04, com condição efetiva e aba. Só a lista principal satisfaz o requisito de condição para alertas. Uma gravação manual atualiza somente a escolha, sem publicar descoberta, alteração de preço ou intenção de alerta e sem reabrir eventos anteriores. Eventos futuros de F04 continuam sujeitos às regras de F09 e à condição então consultada. Indisponibilidade da consulta é um erro identificável.

## 3. Decisões propostas

### Classificação automática inicial

Usar declarações explícitas em português nos campos coletados. A [amostra de discovery](../F01-discovery-e-viabilidade-de-integracoes/probe-playstation5-2026-11-10.md) contém o rótulo genérico “Usado”. A regra mantém rótulos como esse e avaliações cosméticas como evidência insuficiente de funcionamento.

1. Normalizar Unicode, caixa, acentos e espaços para comparação, preservando o trecho original para exibição. Comparar o rótulo estruturado inteiro e frases declarativas completas do título e da descrição. Separar frases por quebra de linha ou pontuação final. Ignorar frases interrogativas e manter juntos trechos separados por vírgula ou travessão.
2. Usar a seguinte lista inicial de correspondências integrais. Frases com negação, ressalva, hipótese, citação ou menção a acessório são avaliadas como um todo, sem aceitar correspondências parciais. Por exemplo, “não sei se funciona bem”, “sem defeitos”, “funciona bem só na tomada” e “controle com defeito” ficam sem sinal nesta política. Essa restrição mantém casos ambíguos para avaliação manual.

   | Sinal | Declarações reconhecidas após normalização |
   |---|---|
   | Funcionamento | “funciona bem”, “funciona perfeitamente”, “funcionando perfeitamente”, “todas as funções funcionam”, “o aparelho funciona perfeitamente” |
   | Defeito, reparo ou peças | “com defeito”, “com defeitos”, “defeituoso”, “o aparelho está com defeito”, “precisa de reparo”, “para conserto”, “para peças”, “vendo para peças”, “não funciona”, “não liga” |
3. Uma declaração explícita de defeito, reparo ou peças determina a aba **Com defeito**, inclusive quando há também uma declaração positiva reconhecida. Se houver apenas sinal de funcionamento, usar **Funcionam bem**. Na ausência dos dois sinais, usar **Condição não confirmada**. “Usado”, “como novo”, “bom estado”, fotos, preço, categoria e modalidade de compra, isoladamente ou em conjunto, são insuficientes. A lista inicial cobre declarações diretas e mantém os demais textos sujeitos à classificação manual.
4. Recalcular a partir da observação aceita mais recente de F04. Uma falha de acesso ou atualização que F04 não aceitou como nova observação mantém os últimos dados válidos. Se F04 aceitar uma observação em que a evidência de funcionamento está ausente, aplicar a regra de insuficiência a essa observação.

### Escolha manual e conflito

A oferta incerta aceita **Funciona bem** ou **Não funciona bem**. Uma oferta já classificada manualmente permite corrigir para a outra opção nos detalhes. Uma oferta classificada automaticamente com resultado conclusivo e sem escolha manual fica fora desse controle. A gravação valida a elegibilidade e a revisão na transação, de modo que uma página antiga não substitua uma escolha posterior ou classifique uma oferta que já deixou de estar incerta. Reenviar a escolha já salva com a revisão atual mantém o estado.

A última escolha manual confirmada prevalece sobre o resultado automático para a identidade de F04. Se houver resultado automático conclusivo oposto à escolha atual, exibir nos detalhes **A informação do anúncio diverge da sua classificação**, com o trecho reconhecido atribuído à fonte e a escolha manual ainda ativa. Evidência insuficiente ou compatível retira o aviso. Uma republicação que F04 identificar como novo anúncio recebe sua própria classificação, sem herdar a escolha de outra identidade.

**Pendências** — confirmar as correspondências iniciais com anúncios representativos e validar a apresentação do conflito com o usuário (P03/P06). F04 define a identidade em republicações, a semântica de observação válida e o mapeamento de campos. A regra de funcionamento independe de critérios de transporte, inspeção por modalidade ou custo de reparo.

## 4. Componentes

Os caminhos são relativos a `apps/backend/src/garimpei/`. Os nomes de módulos de anúncio serão alinhados com os que F04 entregar.

| Componente | Responsabilidade |
|---|---|
| `domain/listing/condition.py` e portas de anúncio no domínio | Valores de condição, precedência, agrupamento, sinais reconhecidos, elegibilidade da alteração e contratos de leitura/gravação. |
| `usecase/listing/read_condition_usecase.py` e `usecase/listing/classify_condition_usecase.py` | Consultar a projeção e aplicar a escolha dentro da transação, via dependências injetadas. |
| `infra/queries/listing/` e `infra/repository/listing/` | Projetar observação e escolha a partir de uma leitura consistente e gravar a escolha com controle de concorrência no PostgreSQL. |
| `infra/persistence/` | Descoberta ORM, transação e migration da escolha manual. |
| `infra/http/listing/`, `infra/http/templates/listing/` e `infra/http/urls.py` | Validar entrada, invocar casos de uso, renderizar abas e detalhes com o padrão de formulário aprovado. |
| `main.py` e `infra/http/error_handler.py` | Composição explícita e tratamento central de falhas com estado recuperável e logs estruturados. |

## 5. Interfaces HTTP

Rotas HTML propostas para reaproveitamento por F08. Entrada pelo navegador local, com CSRF nas mutações. Links entre abas e formulário funcionam via navegação HTML. A opção de melhorar a interação com HTMX segue os mesmos estados e casos de uso.

| Método e caminho | Entrada e validação | Resultado |
|---|---|---|
| `GET /ofertas/` | `aba` opcional com valores `funcionam`, `defeitos` e `incerta`. Padrão `funcionam`. | `200` com a aba selecionada, estado vazio ou ofertas com link para detalhes. Valor inválido recebe `400`. |
| `GET /ofertas/<id>/` | Identificador interno de F04, conforme o conversor correspondente na rota. | `200` com anúncio, origem, link original, classificação, procedência, controles aplicáveis, conflito quando presente e link para a aba efetiva. ID desconhecido ou malformado recebe `404`. |
| `POST /ofertas/<id>/condicao/` | Formulário com `choice` obrigatório (`good` ou `defect`), `revision` obrigatória (inteiro não negativo) e token CSRF. | `303` para os detalhes após commit, com confirmação e link para a aba efetiva. `400` para entrada inválida, `403` para CSRF, `404` para ID desconhecido ou malformado, `409` para revisão antiga ou mudança de elegibilidade. |

Falha de persistência retorna erro recuperável `503`. Se a leitura permanecer disponível, exibir o último estado confirmado e a escolha submetida para nova tentativa. Se a leitura também falhar, informar indisponibilidade e oferecer recarregar os detalhes antes de tentar novamente. Um conflito `409` apresenta o estado atual e pede revisão explícita, sem reenvio automático. Métodos não suportados recebem `405`. Usar mensagens acessíveis de espera, sucesso e erro. Durante o envio, manter a condição e a aba confirmadas até a resposta. Os valores da fonte são exibidos como texto escapado.

## 6. Modelo de dados e concorrência

A migration adiciona uma escolha opcional por anúncio. A condição automática é calculada a partir da evidência persistida por F04, inclusive para anúncios coletados antes da migração. A condição efetiva e a aba são derivadas para leitura, mantendo uma única fonte para a classificação manual.

| Campo da escolha manual | Tipo e restrições |
|---|---|
| `listing_id` | Chave primária e FK 1:1 para a identidade de F04, com o mesmo tipo da PK. Reter enquanto a identidade de F04 for mantida, inclusive quando ficar temporariamente indisponível. Exclusão definitiva segue a política de retenção de F04. |
| `choice` | Texto obrigatório com `CHECK` para `good` ou `defect`. |
| `revision` | Inteiro positivo obrigatório, começa em 1 e cresce a cada mudança confirmada. A ausência da linha é apresentada como revisão 0. |
| `updated_at` | Instante com fuso, obrigatório, alterado em conjunto com a escolha. |

Serializar gravações manuais e substituições da observação relevante pela identidade do anúncio, com bloqueio do registro pai ou fronteira equivalente compartilhada com F04. A validação de revisão, o cálculo da elegibilidade e a gravação ocorrem sob a mesma transação. A consulta combina observação e escolha em um snapshot consistente. Falha antes do commit conserva os dados anteriores. As migrations devem ser verificadas com um anúncio preexistente de F04 e sem linha de escolha manual.

## 7. Estratégia de verificação

| Área | Evidência técnica prevista |
|---|---|
| `apps/backend/tests/unit/test_listing_condition.py` | Tabela de sinais positivos, negativos, insuficientes e mistos. Cobrir correspondência integral, normalização, conflito, precedência e cálculo da aba. |
| `apps/backend/tests/integration/test_listing_condition.py` | PostgreSQL real, migração com dados preexistentes, rollback, atualização simultânea de coleta e classificação, duas correções concorrentes, reaplicação da coleta e identidade nova. |
| `apps/backend/tests/http/test_listing_condition.py` | Contratos HTTP, isolamento entre ofertas, CSRF, mensagens, preservação do formulário, rejeição de requisição obsoleta e escape de conteúdo da fonte. |
| Contrato executado com `playwright-cli` | Navegação pelas três abas, classificação para ambos os destinos, correção, falha recuperável e retorno após reinício. Usar componentes do [design aprovado](../design/DESIGN.md) e verificar teclado, mensagens acessíveis e reflow. |
| Integração F04/F05/F09 | Injetar observações sintéticas no ponto de entrada da coleta F04. Comparar condição publicada, identidade, eventos e intenções antes e depois da ação manual. Exercitar F09 por seu contrato de consumo quando disponível. |

Usar os gates e pré-requisitos de [contract.md](contract.md), com as instruções de ambiente de [F02](../F02-fundacao-tecnica-e-ambiente-local/operations.md).

## Apresentação atual — 2026-11-13

Trocar condição conserva foco na aba selecionada; classificação manual e correção continuam com suas regras originais. Página de oferta inexistente apresenta título e recuperação para a lista. Veja as [convenções da interface](../design/implementation.md), a [auditoria original](../design/audit-2026-11-13/README.md) e a [verificação integrada](../design/audit-2026-11-13/integration-master.md). Este complemento preserva IDs e critérios do contrato original.
