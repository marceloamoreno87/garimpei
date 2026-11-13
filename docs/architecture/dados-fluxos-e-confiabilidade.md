# Dados, fluxos e confiabilidade propostos

> Documento de desenho elaborado em 2026-11-10. As menções a implementação ou ferramentas pendentes descrevem aquela etapa. A aplicação já existe; consulte a [arquitetura implementada](implementation.md), a [operação atual](../harness.md) e o [estado das features](../status-atual.md) antes de aplicar o planejamento histórico.

Estado na elaboração original: **modelo conceitual e fluxos propostos, sem schema ou execução implementados**. Regras confirmadas vêm do [PRD](../PRD.md); políticas pendentes permanecem abertas.

## Informações que precisam sobreviver ao reinício

| Informação | Responsável proposto | Por que persistir | Pendência relevante |
|---|---|---|---|
| Interesses, CEP, parâmetros de custo e conclusão da configuração inicial | `monitoring` | Aguardar a conclusão guiada no primeiro uso e retomar a configuração salva nos reinícios | Categorias e validações detalhadas — P03/P04/P08; custos iniciais preenchidos pelo usuário |
| Identidade e observações do anúncio | `listing` | Acompanhar descobertas e reduções de preço sem tratar tudo como novo | Correspondência, duplicatas e republicações — P04 |
| Marco da carga inicial e progresso da coleta | `listing` | Reinício não transforma carga silenciosa em pendências | Semântica de inclusão de interesses — P04 |
| Evidência da condição e classificação manual | `listing` | Exibir condição e preservar a escolha manual para o mesmo anúncio nas próximas coletas | Critérios automáticos e apresentação de informações conflitantes — P06 |
| Comparáveis, referência de novo e resultado de avaliação | `valuation` | Explicar a estimativa exibida com os dados efetivamente usados | Equivalência, suficiência, atualidade e ausência de novo — P07 |
| Composição do lucro e parâmetros usados | `valuation` | Conservar coerência entre detalhe e alerta, inclusive após mudanças de preço/custos | Arredondamento e outros custos — P08 |
| Intenções de alerta, tentativas e confirmação | `alert` | Retomar trabalho e distinguir evento novo de envio já confirmado | Resultado incerto, tentativas e reconciliação — P09 |
| Tarefas e estado técnico de processamento | Infraestrutura de fila | Recuperar execução interrompida | Biblioteca e semântica de recuperação — F02/F09 |

Esse quadro não impõe um banco por módulo, uma tabela por linha nem event sourcing. Os módulos compartilham PostgreSQL. Agregados, constraints e retenção serão especificados nas etapas responsáveis.

Anúncio, oferta exibida, evento de preço e alerta são conceitos distintos. Um anúncio conhecido pode originar outro evento de redução e outro alerta. Usar apenas o preço atual ou um flag genérico de “já enviado” perde essa distinção. Por outro lado, um novo ID de tarefa técnica não deve criar por si só um novo evento de negócio.

## Identidade e rastreabilidade

Propõe-se separar ID interno gerado no domínio da identificação disponibilizada pela fonte. A associação entre fonte, ID externo e URL precisa da evidência de F01/F04; não há regra fechada para republicações ou URLs alteradas.

Observações conservam preço, momento da identificação e momento de publicação quando disponível. O tempo informado pela plataforma não é inventado quando faltar. Leituras repetidas do mesmo estado não criam repetidamente um evento de redução.

Comparáveis e custos usados por uma avaliação precisam permanecer identificáveis. A consulta de detalhes e o alerta devem se referir à mesma avaliação/preço correspondente ao evento, sem misturar silenciosamente preços de momentos diferentes. Versão de método e configuração são uma proposta de rastreabilidade; formato e política de recálculo aguardam as especificações.

Guardar evidência de classificação automática separada da classificação manual permite aplicar a precedência confirmada no PRD: a escolha manual é preservada nas próximas coletas do mesmo anúncio. A apresentação de novas informações conflitantes permanece para especificação; republicações dependem da identidade definida em F04. Não se propõe capturar HTML completo, imagens ou cookies como dados obrigatórios do domínio.

## Fluxo web

1. O adapter Django recebe formulário ou ação HTMX e valida formato e campos requeridos.
2. O handler chama o caso de uso com entrada tipada.
3. O caso de uso consulta/grava por contratos; a entidade ou política pura aplica invariantes.
4. A saída é convertida em DTO; o adapter renderiza a página ou fragmento HTML apropriado.
5. A interface só confirma gravação quando houver sucesso; falha mantém a incerteza e informa o campo ou operação afetados.

A consulta das abas não coleta anúncios nem envia mensagens. Ela usa dados persistidos e deve informar indisponibilidades sem convertê-las em lucro zero ou estado confirmado. As ofertas com lucro calculado seguem ordem decrescente, inclusive zero/negativo; sem estimativa ficam no fim. Empates usam identificação mais recente e, em última instância, identificador estável. Filtragem e ordenação antecedem a paginação de 20 ofertas, conforme F08.

HTML/HTMX compartilham casos de uso. Classificar uma oferta incerta ou corrigir nos detalhes uma escolha manual já salva move a oferta para a aba correspondente após gravação, preservando a última escolha bem-sucedida e sem criar intenção de alerta pela ação, inclusive para retomada posterior. Falha mantém a escolha anterior. Isso não altera os critérios dos demais eventos de F09.

A configuração guiada precisa conservar sua conclusão para liberar a primeira coleta apenas após gravação bem-sucedida e retomá-la corretamente nos reinícios. Na exploração, dados novos são aplicados à lista ao clique em um aviso de atualização, preservando os filtros; a consulta não pausa o worker ou os alertas. As formas de persistir o marco e detectar mudanças serão especificadas nas features, sem introduzir outro serviço por essa decisão de interface.

## Coleta e carga inicial

```mermaid
sequenceDiagram
  participant W as Worker
  participant S as Plataforma
  participant U as Caso de uso
  participant D as PostgreSQL
  W->>D: Recuperar configuração e progresso persistido
  W->>S: Coletar conforme a estratégia definida em F01
  S-->>W: Dados disponíveis ou falha explícita
  W->>U: Apresentar observações normalizadas
  U->>D: Persistir observações e avanço consistente
  alt Carga inicial ainda não concluída
    U->>D: Preservar marco silencioso; não criar intenção de alerta
  else Acompanhamento ativo
    U->>D: Registrar eventos novos ou reduções distinguíveis
    U->>D: Preservar necessidade de avaliação/processamento
  end
```

O desenho exige progresso retomável, mas não define número de páginas, checkpoint ou condição de término da primeira coleta. F04 precisa estabelecer o que constitui carga inicial concluída na cobertura escolhida e testar interrupção antes/depois desse marco. Não se deve marcar toda carga como concluída antes de persistir seus anúncios.

Após desligamento, consultar a fonte e recuperar o que ela disponibilizar. A fila local não recupera anúncios que nunca foram obtidos e que já desapareceram. Nova configuração de interesses, duplicatas e republicações exigem política antes de implementar o comportamento afetado.

## Avaliação e elegibilidade

1. Dados coletados alimentam classificação e seleção de candidatos a comparáveis.
2. Uma política de equivalência e suficiência, ainda a definir, produz estimativa de revenda ou indisponibilidade, com as evidências.
3. O cálculo usa compra, revenda e custos; frete informado prevalece e o estimado configurado pode suprir o valor ausente, sem comprovar entrega.
4. A avaliação fica disponível à interface. Um evento abrangido pelas regras de alerta é avaliado com sua condição e estimativa.
5. Somente evento elegível gera intenção de envio; não há corte de lucro mínimo nem mínimo de redução definido.

Referência de produto novo não substitui revenda de usado. Amostra insuficiente mantém oferta visível sem lucro calculado. Uma fonte indisponível não equivale a amostra válida de tamanho zero ou a uma nova primeira execução.

O fluxo permite estágios separados sem exigir um barramento de eventos. Os contratos precisam impedir que um estágio anterior sobrescreva resultados mais novos em execução concorrente; a estratégia de versionamento/serialização é proposta a especificar, não uma regra já implementada.

## Limite transacional e publicação de trabalho

Propõe-se uma unidade de trabalho de infraestrutura para operações que alteram vários registros relacionados. Estado do anúncio/evento e necessidade de processamento devem ficar persistidos de modo coerente; intenção de alerta e atualização que a origina não podem depender apenas de uma chamada posterior em memória.

Há dois desenhos compatíveis a validar em F02, sem decisão antecipada entre eles:

- Gravar a tarefa na mesma transação/conexão efetivamente usada para os dados, se a biblioteca escolhida suportar a integração.
- Gravar uma intenção durável/outbox com o estado de negócio; um dispatcher no worker a converte em tarefa recuperável, com identificação que tolere repetição dessa conversão.

O outbox, quando necessário, é um registro transacional dentro do PostgreSQL existente. Não exige Kafka, Redis nem um terceiro processo de aplicação. O histórico de negócio continua separado do estado técnico da fila, mas a mesma intenção pode servir como registro durável, evitando duas fontes concorrentes de verdade.

`on_commit` do Django executa callbacks depois do commit; o callback não integra a transação já confirmada. Sua execução pode acelerar o aviso ao worker, mas não substitui o registro persistente de trabalho. [Transações Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).

A documentação atual de Procrastinate descreve uso de conexão externa para deferir trabalho na transação do chamador. Isso não comprova compatibilidade com a versão, o driver e a conexão Django que serão escolhidos. Mesmo banco com conexões diferentes não implica a mesma transação. A integração é um item de verificação, não fundamento para marcar a biblioteca como adotada. [Conexão externa Procrastinate](https://procrastinate.readthedocs.io/en/stable/howto/production/external_connection.html).

A proposta inicial prefere blocos transacionais síncronos curtos para o ORM. Se a coleta usar bibliotecas assíncronas, a passagem para persistência será explícita, conforme a versão escolhida; não se assume que uma transação ORM atravesse `await` arbitrários. [Django assíncrono](https://docs.djangoproject.com/en/5.2/topics/async/).

## Envio ao WAHA e recuperação

```mermaid
sequenceDiagram
  participant W as Worker
  participant U as Caso de uso de alerta
  participant D as PostgreSQL
  participant A as WAHA
  W->>U: Executar trabalho com identidade de negócio persistida
  U->>D: Carregar intenção e histórico; controlar concorrência
  D-->>U: Estado conhecido ou falha explícita
  U->>A: Enviar fora de transação longa do banco
  alt Confirmação aplicável recebida
    A-->>U: Resultado confirmado
    U->>D: Registrar confirmação e tentativa correspondente
  else Falha conhecida ou resultado incerto
    A-->>U: Falha, timeout ou resposta insuficiente
    U->>D: Preservar tentativa e incerteza sem marcar confirmado
  end
```

Conceitualmente, distinguir intenção pendente, execução reclamada, confirmação e resultado incerto. São categorias técnicas propostas, não uma máquina de estados ou política de reenvio já aprovada. Lease, recuperação de tarefa interrompida, limite de tentativas e reconciliação precisam de contrato em F09/P09.

Se a mensagem sair e o processo cair antes de registrar confirmação, pode haver ambiguidade. Repetir automaticamente pode duplicar o envio; não repetir pode perder um alerta. Nem uma constraint no banco nem a promessa de execução da fila resolve o efeito externo. Esse caso permanece uma decisão explícita de produto/integração antes de concluir F09.

Uma constraint contra duplicação deve identificar o evento de negócio conforme a política definida. Apenas anúncio + preço pode ser insuficiente quando o preço sobe e volta a cair ao mesmo valor; não se decide aqui se esse ciclo constitui novo alerta. A carga silenciosa nunca é convertida em intenção apenas por reinício.

## Cenários obrigatórios para as especificações

| Cenário | Propriedade a comprovar | Etapas |
|---|---|---|
| Interromper a carga inicial e reiniciar | Marco e progresso preservados; sem alertas da carga silenciosa | F04/F09 |
| Repetir a coleta e o mesmo trabalho técnico | Sem recriar evento já identificado nem reenviar confirmação registrada | F04/F09 |
| Atualizar preço de anúncio alertado | Evento de redução distinguível, avaliação coerente e intenção quando elegível | F04/F07/F09 |
| Falhar entre gravar evento e notificar worker | Trabalho recuperável no banco | F02/F04/F09 |
| Falhar após enviar e antes de registrar confirmação | Incerteza preservada; aplicar a política que vier a ser definida | F09 |
| Atualizar anúncio classificado manualmente | Aplicar a política de precedência aprovada, sem sobrescrita presumida | F05 |
| Amostra insuficiente ou referência ausente | Indisponibilidade correta, preservando a oferta; ausência apenas de novo tratada conforme P07 | F06/F08/F09 |
| Fonte falha durante retomada | Não declarar cobertura completa, primeira execução ou coleta bem-sucedida por suposição | F04 |

Esses cenários orientam futuros contratos e testes; nenhum foi executado como evidência da aplicação nesta fase documental.
