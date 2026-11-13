# Garimpei

Vocabulário do garimpo de eletrônicos usados para revenda, conforme o [PRD](docs/PRD.md).

## Linguagem

**Interesse de monitoramento**:
Seleção de uma categoria da plataforma ou cadastro de um produto por nome/modelo para acompanhar anúncios.

**Produto cadastrado**:
Nome/modelo informado pelo usuário como interesse de monitoramento, sem exigir atributos adicionais.

**Anúncio**:
Publicação de uma oferta de venda na plataforma de origem, com as informações que essa fonte disponibilizar.

**Oferta**:
Anúncio apresentado no Garimpei para avaliação, inclusive quando houver defeito, condição incerta ou estimativa indisponível.

**Condição**:
Classificação de funcionamento atribuída ao anúncio; não comprova o estado real do produto.

**Condição não confirmada**:
Classificação usada quando as informações do anúncio não permitem concluir se o produto funciona bem.

**Comparável usado**:
Anúncio de produto usado equivalente por modelo/variante, com disponibilidade e funcionamento explícitos. A política aplica idade, amostra mínima e dispersão; são preços pedidos, não vendas realizadas.

**Referência de novo**:
Preço de um produto novo usado como referência distinta dos comparáveis usados.

**Preço estimado de revenda**:
Valor estimado a partir de uma amostra de usados semelhantes, sem equivaler a preço de venda efetivamente realizado.

**Estimativa indisponível**:
Ausência de dados suficientes para estimar a revenda com confiança; não significa preço ou lucro igual a zero.

**Lucro estimado**:
Preço estimado de revenda menos preço de compra e taxa provisória de revenda, sem descontar logística e sem garantia de retorno.

**Lucro potencial antes de frete/transporte**:
Termo histórico para a estimativa sem desconto de logística; a apresentação atual usa “lucro estimado”. Não representa lucro líquido realizado ou retorno garantido.

**Publicação comprovadamente nova**:
Anúncio cuja data de publicação na fonte foi confirmada como posterior ao início do monitoramento. Pode gerar alerta elegível mesmo enquanto a recuperação do histórico continua parcial.

**Categoria validada**:
Categoria cuja consulta foi conferida no Marketplace com contexto correspondente e resultado ou vazio verificável. Uma rota que retorna à página geral não comprova essa categoria.

**Taxa provisória de revenda**:
Percentual configurável sobre a revenda estimada, sem representar uma tarifa confirmada de canal de venda.

**Carga inicial**:
Recuperação do estoque anterior ao início do monitoramento, mantida silenciosa. Publicações comprovadamente novas podem alertar mesmo durante essa recuperação; marco e histórico persistem entre execuções.

**Nova oferta identificada**:
Oferta cuja publicação na fonte foi comprovada após o início do monitoramento e antes da observação atual; o momento de identificação pode diferir da publicação.

**Redução de preço**:
Queda do preço de compra de um anúncio acompanhado, distinguível do evento de sua descoberta.

**Oferta elegível para alerta**:
Oferta que satisfaz a política vigente de condição, identidade, evidências, estimativa e prazo para um evento abrangido pelas regras de alerta. Estar na lista ou ter preço baixo não comprova elegibilidade; autorização e resultado do envio são estados distintos.

**Retomada**:
Atualização do acompanhamento após interrupção, limitada aos anúncios que a fonte ainda disponibilizar.

**Primeira revenda lucrativa**:
Resultado de validação observado fora do Garimpei, com receita e custos efetivamente realizados.

**Alerta ouro**:
Alerta de uma oferta com evidências suficientes de condição textual/visual, identidade e histórico comparável, com lucro estimado estritamente positivo após a taxa. Sua qualificação não comprova funcionamento interno, liquidez ou retorno realizado.

**Primeira elegibilidade**:
Primeiro momento em que uma oferta satisfaz os requisitos de alerta dentro do prazo aplicável de publicação; pode ocorrer depois da coleta, quando chegam evidências ou referências suficientes.

**Controle global do robô**:
Escolha persistente de permitir ou pausar novas unidades de trabalho automático, preservando ofertas, configurações e histórico e respeitando os demais bloqueios.

**Desligando**:
Estado em que a pausa já foi confirmada e operações previamente autorizadas ainda podem concluir; não significa cancelamento imediato do que estava em curso.
